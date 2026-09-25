"""The harvest flow shared by all adapters.

fetch (with rate limit, timeout and bounded retry) → parse (adapter) →
validate → deduplicate → deliver to the sink → confirm → advance checkpoint.

Guarantees and limits:

* The checkpoint is written only after the sink confirmed every record of a
  page. A crash between confirmation and checkpoint write re-delivers that
  page on resume; sinks must therefore be idempotent. This is *at-least-once*
  delivery; no exactly-once claim is made.
* A page that is neither complete nor carries a new cursor, a cursor that does
  not advance, or records of another source are parser errors, never a
  silent end of data.
* Errors are structured. Non-retryable errors stop the run; what was already
  confirmed stays confirmed and the result says ``partial``.
* ``snapshot_complete`` is true only for a full-snapshot profile whose run
  started at the beginning and read every page without issues. Only then may
  a consumer apply its own replace/deletion rule; the core never deletes.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

from .adapter import FetchContext, SourceAdapter
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
from .policies import CancelToken, RateLimit, RetryPolicy
from .ports import Clock, CredentialProvider, EventSink, Sink, Sleeper, StateStore, Transport

__all__ = ["CancelToken", "HarvestEngine", "RateLimit", "RetryPolicy"]


class _NullEvents:
    """Default event sink that discards events."""

    def emit(self, event: Mapping[str, JSON]) -> None:
        """Discard the event."""
        return None


@dataclass
class HarvestEngine:
    """Runs any :class:`SourceAdapter` through the common flow."""

    transport: Transport
    credentials: CredentialProvider
    state: StateStore
    clock: Clock
    sleeper: Sleeper
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    rate_limit: RateLimit = field(default_factory=RateLimit)
    request_timeout: float = 30.0
    events: EventSink = field(default_factory=_NullEvents)
    rng: random.Random = field(default_factory=lambda: random.Random(0))

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

    def _fetch(
        self,
        adapter: SourceAdapter,
        context: FetchContext,
        cursor: Cursor | None,
        cancel: CancelToken,
        deadline: float,
        counter: list[int],
    ) -> PageResult:
        attempt = 0
        while True:
            attempt += 1
            counter[0] += 1
            if cancel.cancelled:
                raise Cancelled("Abbruch angefordert.")
            self.rate_limit.wait(self.clock, self.sleeper)
            try:
                page = adapter.fetch_page(context, cursor)
            except HarvestError as error:
                wait = self.retry.delay(attempt, error, self.rng)
                self._emit(
                    "fetch_error",
                    context.request,
                    page=context.page,
                    attempt=attempt,
                    error=error.code,
                    retry_in=wait,
                )
                if wait is None or self.clock.monotonic() + wait > deadline:
                    raise
                self.sleeper.sleep(wait)
                continue
            except Exception as error:  # noqa: BLE001 - adapter bugs become structured errors
                raise ParserError(
                    f"Adapter-Fehler {type(error).__name__}: {str(error)[:200]}"
                ) from error
            if not isinstance(page, PageResult):
                raise ParserError("Adapter lieferte kein PageResult.")
            return page

    @staticmethod
    def _check_page(adapter: SourceAdapter, page: PageResult, cursor: Cursor | None) -> None:
        source_id = adapter.source.source_id
        if any(r.source_id != source_id for r in page.records):
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

    def _start_cursor(
        self, adapter: SourceAdapter, request: HarvestRequest, before: Checkpoint | None
    ) -> Cursor | None:
        """Cursor to resume from; a checkpoint of another profile version is refused."""
        source = adapter.source
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

    def _limits(self, run: _Run, request: HarvestRequest, cancel: CancelToken) -> None:
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
    def _deliver(run: _Run, page: PageResult, sink: Sink, request: HarvestRequest) -> int:
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
        self,
        run: _Run,
        adapter: SourceAdapter,
        request: HarvestRequest,
        page: PageResult,
        fresh: int,
    ) -> None:
        """Advance the checkpoint after the sink confirmed the page (compare-and-set)."""
        source = adapter.source
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

    def _pages(
        self,
        run: _Run,
        adapter: SourceAdapter,
        request: HarvestRequest,
        sink: Sink,
        settings: Mapping[str, JSON],
        cursor: Cursor | None,
        cancel: CancelToken,
    ) -> None:
        """Fetch, check, deliver and confirm pages until the source reports completion."""
        while True:
            self._limits(run, request, cancel)
            context = FetchContext(
                request,
                settings,
                self.transport,
                self.credentials,
                self.clock,
                self.request_timeout,
                run.pages + 1,
            )
            page = self._fetch(adapter, context, cursor, cancel, run.deadline, run.attempts)
            run.pages += 1
            run.received += len(page.records)
            self._check_page(adapter, page, cursor)
            fresh = self._deliver(run, page, sink, request)
            self._confirm(run, adapter, request, page, fresh)
            cursor = page.next_cursor
            self._emit(
                "page_confirmed", request, page=run.pages, records=fresh, complete=page.complete
            )
            if page.complete:
                run.exhausted = True
                return

    def run(
        self,
        adapter: SourceAdapter,
        request: HarvestRequest,
        sink: Sink,
        *,
        config: Mapping[str, JSON] | None = None,
        cancel: CancelToken | None = None,
    ) -> HarvestResult:
        """Execute one bounded run and return a structured result.

        Source, parser, sink, checkpoint and limit problems are reported in the
        result; programming errors of the caller propagate.
        """
        source = adapter.source
        settings = dict(config or {})
        cancel = cancel or CancelToken()
        run = _Run(
            started=self.clock.now().isoformat(),
            deadline=self.clock.monotonic() + request.max_duration_seconds,
        )
        status = RunStatus.FAILED
        try:
            if request.source_id != source.source_id:
                raise ConfigError("Anfrage und Adapter betreffen verschiedene Quellen.")
            adapter.validate_config(settings)
            run.before = run.current = self.state.load(source.source_id)
            cursor = self._start_cursor(adapter, request, run.before)
            run.from_beginning = cursor is None
            self._emit("run_started", request, resume=cursor is not None)
            self._pages(run, adapter, request, sink, settings, cursor, cancel)
            status = RunStatus.PARTIAL if run.partial else RunStatus.COMPLETE
        except Cancelled as error:
            run.errors.append(error.to_dict())
            status = RunStatus.CANCELLED
        except LimitReached as error:
            run.errors.append(error.to_dict())
            status = RunStatus.PARTIAL
        except HarvestError as error:
            run.errors.append(error.to_dict())
            status = RunStatus.PARTIAL if run.current is not run.before else RunStatus.FAILED
        result = run.result(source, request, status, self.clock.now().isoformat())
        self._emit(
            "run_finished",
            request,
            status=result.status.value,
            pages=run.pages,
            delivered=run.delivered,
        )
        return result


@dataclass
class _Run:
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
        )
