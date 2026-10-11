"""Steps of the harvest flow shared by the synchronous and the asynchronous engine.

Everything here is independent of how a page is fetched: checking a page,
deduplication, delivery to the sink, checkpointing, limits, events and the
bookkeeping of one run. :class:`~auditcore_harvest.engine.HarvestEngine` and
:class:`~auditcore_harvest.aio.AsyncHarvestEngine` only add the fetch loop.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from .errors import (
    Cancelled,
    ConfigError,
    HarvestError,
    LimitReached,
    ParserError,
    SinkError,
)
from .model import (
    CONTRACT_VERSION,
    JSON,
    Checkpoint,
    Cursor,
    HarvestRecord,
    HarvestRequest,
    HarvestResult,
    PageResult,
    PageStatus,
    RecordIssue,
    RunStatus,
    SnapshotSemantics,
    Source,
)
from .policies import CancelToken, RetryPolicy
from .ports import Clock, EventSink, Sink, StateStore


class DeclaredAdapter(Protocol):
    """What the shared flow needs of any adapter, synchronous or asynchronous."""

    @property
    def source(self) -> Source:
        """Declared source identity and capabilities."""
        ...

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """Raise ``ConfigError`` for invalid configuration."""
        ...


class NullEvents:
    """Default event sink that discards events."""

    def emit(self, event: Mapping[str, JSON]) -> None:
        """Discard the event."""
        return None


@dataclass
class RunState:
    """Mutable bookkeeping of one run."""

    started: str
    deadline: float
    pages: int = 0
    received: int = 0
    delivered: int = 0
    dup_run: int = 0
    dup_sink: int = 0
    attempts: list[int] = field(default_factory=lambda: [0])
    issues: list[RecordIssue] = field(default_factory=list)
    errors: list[dict[str, JSON]] = field(default_factory=list)
    seen: set[tuple[tuple[str, str], str]] = field(default_factory=set)
    before: Checkpoint | None = None
    current: Checkpoint | None = None
    exhausted: bool = False
    partial: bool = False
    from_beginning: bool = True
    last_error: HarvestError | None = None

    def succeeded(self) -> RunStatus:
        """Status of a run that read every page."""
        return RunStatus.PARTIAL if self.partial else RunStatus.COMPLETE

    def fail(self, error: HarvestError) -> RunStatus:
        """Record the error that ends the run and return the resulting status."""
        self.errors.append(error.to_dict())
        self.last_error = error
        if isinstance(error, Cancelled):
            return RunStatus.CANCELLED
        if isinstance(error, LimitReached) or self.current is not self.before:
            return RunStatus.PARTIAL
        return RunStatus.FAILED

    def result(
        self, source: Source, request: HarvestRequest, status: RunStatus, finished: str
    ) -> HarvestResult:
        """Freeze the bookkeeping into a :class:`HarvestResult`."""
        return HarvestResult(
            source_id=source.source_id,
            run_id=request.run_id,
            contract=CONTRACT_VERSION,
            status=status,
            started_at=self.started,
            finished_at=finished,
            pages=self.pages,
            records_received=self.received,
            records_delivered=self.delivered,
            duplicates_in_run=self.dup_run,
            duplicates_at_sink=self.dup_sink,
            issues=tuple(self.issues),
            errors=tuple(self.errors),
            checkpoint_before=self.before,
            checkpoint_after=self.current,
            source_exhausted=self.exhausted,
            snapshot_complete=(
                status is RunStatus.COMPLETE
                and self.exhausted
                and self.from_beginning
                and source.snapshot_semantics is SnapshotSemantics.FULL_SNAPSHOT_REPLACE
            ),
            attempts=self.attempts[0],
            http_status=None if self.last_error is None else self.last_error.http_status,
            error_kind=None if self.last_error is None else self.last_error.kind,
        )


def adapter_bug(error: Exception) -> ParserError:
    """Unexpected adapter exceptions become structured parser errors."""
    return ParserError(f"Adapter-Fehler {type(error).__name__}: {str(error)[:200]}")


def as_page(page: object) -> PageResult:
    """The adapter's return value, which must be a :class:`PageResult`."""
    if not isinstance(page, PageResult):
        raise ParserError("Adapter lieferte kein PageResult.")
    return page


class FlowCore:
    """Fetch-independent steps; subclasses provide the fields annotated here."""

    state: StateStore
    clock: Clock
    retry: RetryPolicy
    events: EventSink
    rng: random.Random

    def _emit(self, kind: str, request: HarvestRequest, **fields: object) -> None:
        self.events.emit(
            {
                "event": kind,
                "source_id": request.source_id,
                "run_id": request.run_id,
                "at": self.clock.now().isoformat(),
                **fields,
            }
        )

    def _new_run(self, request: HarvestRequest) -> RunState:
        return RunState(
            started=self.clock.now().isoformat(),
            deadline=self.clock.monotonic() + request.max_duration_seconds,
        )

    def _begin(
        self,
        run: RunState,
        adapter: DeclaredAdapter,
        request: HarvestRequest,
        settings: Mapping[str, JSON],
    ) -> Cursor | None:
        """Validate, load the checkpoint and return the start cursor."""
        if request.source_id != adapter.source.source_id:
            raise ConfigError("Anfrage und Adapter betreffen verschiedene Quellen.")
        adapter.validate_config(settings)
        run.before = run.current = self.state.load(adapter.source.source_id)
        cursor = self._start_cursor(adapter.source, request, run.before)
        run.from_beginning = cursor is None
        self._emit("run_started", request, resume=cursor is not None)
        return cursor

    def _finish(
        self, run: RunState, source: Source, request: HarvestRequest, status: RunStatus
    ) -> HarvestResult:
        result = run.result(source, request, status, self.clock.now().isoformat())
        self._emit(
            "run_finished",
            request,
            status=result.status.value,
            pages=run.pages,
            delivered=run.delivered,
        )
        return result

    def _retry_wait(
        self, error: HarvestError, attempt: int, request: HarvestRequest, page: int, deadline: float
    ) -> float | None:
        """Seconds to wait before retrying, or ``None`` to give up (event emitted)."""
        wait = self.retry.delay(attempt, error, self.rng)
        self._emit(
            "fetch_error", request, page=page, attempt=attempt, error=error.code, retry_in=wait
        )
        if wait is None or self.clock.monotonic() + wait > deadline:
            return None
        return wait

    @staticmethod
    def _check_page(source: Source, page: PageResult, cursor: Cursor | None) -> None:
        if any(r.source_id != source.source_id for r in page.records):
            raise ParserError("Seite enthält Datensätze einer anderen Quelle.")
        if not page.complete and page.next_cursor is None:
            raise ParserError(
                "Seite ist nicht abgeschlossen, nennt aber keine Folgeseite; "
                "das wäre ein stilles Ende des Abrufs."
            )
        if (
            not page.complete
            and cursor is not None
            and dict(page.next_cursor or {}) == dict(cursor)
        ):
            raise ParserError("Der Cursor schreitet nicht fort (Endlosschleife verhindert).")

    @staticmethod
    def _start_cursor(
        source: Source, request: HarvestRequest, before: Checkpoint | None
    ) -> Cursor | None:
        """Cursor to resume from; a checkpoint of another profile version is refused."""
        if before is None or not request.resume:
            return None
        if before.profile_version != source.profile_version:
            raise ConfigError(
                "Checkpoint stammt aus Profilversion "
                f"{before.profile_version}, Adapter nutzt {source.profile_version}; "
                "kein Wiederanlauf mit fremdem Cursor."
            )
        if not before.finished or source.snapshot_semantics is SnapshotSemantics.INCREMENTAL_UPSERT:
            return before.cursor
        return None

    def _limits(self, run: RunState, request: HarvestRequest, cancel: CancelToken) -> None:
        """Raise before the next page if a limit or cancellation applies."""
        if cancel.cancelled:
            raise Cancelled("Abbruch angefordert.")
        if run.pages >= request.max_pages:
            raise LimitReached(f"Seitenlimit {request.max_pages} erreicht.")
        if run.delivered >= request.max_records:
            raise LimitReached(f"Datensatzlimit {request.max_records} erreicht.")
        if self.clock.monotonic() > run.deadline:
            raise LimitReached("Zeitlimit des Laufs erreicht.")

    @staticmethod
    def _deliver(run: RunState, page: PageResult, sink: Sink, request: HarvestRequest) -> int:
        """Deduplicate, deliver and verify the receipt; returns the number of fresh records."""
        fresh: list[HarvestRecord] = []
        for record in page.records:
            marker = (record.key, record.content_hash)
            if marker in run.seen:
                run.dup_run += 1
                continue
            run.seen.add(marker)
            fresh.append(record)
        try:
            receipt = sink.deliver(fresh, run_id=request.run_id, page=run.pages)
        except HarvestError:
            raise
        except Exception as error:  # noqa: BLE001 - consumer storage failure
            raise SinkError(f"Senke meldet {type(error).__name__}.") from error
        confirmed = set(receipt.accepted) | set(receipt.duplicates)
        if confirmed != {r.key for r in fresh}:
            raise SinkError("Senke hat nicht genau die übergebenen Datensätze bestätigt.")
        run.delivered += len(receipt.accepted)
        run.dup_sink += len(receipt.duplicates)
        run.issues.extend(page.issues)
        run.partial = run.partial or bool(page.issues) or page.status is PageStatus.PARTIAL
        return len(fresh)

    def _confirm(
        self, run: RunState, source: Source, request: HarvestRequest, page: PageResult, fresh: int
    ) -> None:
        """Advance the checkpoint after the sink confirmed the page (compare-and-set)."""
        base = run.current if run.current and not run.current.finished else None
        checkpoint = Checkpoint(
            source_id=source.source_id,
            profile_version=source.profile_version,
            cursor=None if page.next_cursor is None else dict(page.next_cursor),
            run_id=request.run_id,
            updated_at=self.clock.now().isoformat(),
            pages_confirmed=(base.pages_confirmed if base else 0) + 1,
            records_confirmed=(base.records_confirmed if base else 0) + fresh,
            finished=page.complete,
        )
        self.state.save(checkpoint, run.current)
        run.current = checkpoint

    def _accept(
        self,
        run: RunState,
        source: Source,
        request: HarvestRequest,
        sink: Sink,
        page: PageResult,
        cursor: Cursor | None,
    ) -> bool:
        """Check, deliver and confirm one fetched page; ``True`` once the source is exhausted."""
        run.pages += 1
        run.received += len(page.records)
        self._check_page(source, page, cursor)
        fresh = self._deliver(run, page, sink, request)
        self._confirm(run, source, request, page, fresh)
        self._emit("page_confirmed", request, page=run.pages, records=fresh, complete=page.complete)
        run.exhausted = page.complete
        return page.complete
