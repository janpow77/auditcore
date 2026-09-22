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
from typing import Any

from .adapter import FetchContext, SourceAdapter
from .errors import (
    Cancelled,
    CheckpointConflict,
    ConfigError,
    HarvestError,
    LimitReached,
    ParserError,
    RateLimitError,
    SinkError,
)
from .model import (
    CONTRACT_VERSION,
    Checkpoint,
    HarvestRecord,
    HarvestRequest,
    HarvestResult,
    PageResult,
    PageStatus,
    RecordIssue,
    RunStatus,
    SnapshotSemantics,
)
from .ports import Clock, CredentialProvider, EventSink, Sink, Sleeper, StateStore, Transport


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded exponential backoff with jitter; honours ``Retry-After`` up to a cap."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: float = 0.1
    max_retry_after: float = 300.0

    def delay(self, attempt: int, error: HarvestError, rng: random.Random) -> float | None:
        """Seconds to wait before the next attempt, or ``None`` to give up."""
        if attempt >= self.max_attempts or not error.retryable:
            return None
        if isinstance(error, RateLimitError) and error.retry_after is not None:
            if error.retry_after > self.max_retry_after:
                return None
            return max(0.0, float(error.retry_after))
        backoff = min(self.max_delay, self.base_delay * (2.0 ** (attempt - 1)))
        return backoff * (1.0 + self.jitter * rng.random())


@dataclass
class RateLimit:
    """Minimum interval between two requests of a run."""

    min_interval_seconds: float = 0.0
    _last: float | None = field(default=None, init=False, repr=False)

    def wait(self, clock: Clock, sleeper: Sleeper) -> None:
        """Sleep until the interval has passed."""
        now = clock.monotonic()
        if self._last is not None:
            remaining = self.min_interval_seconds - (now - self._last)
            if remaining > 0:
                sleeper.sleep(remaining)
        self._last = clock.monotonic()


@dataclass
class CancelToken:
    """Cooperative cancellation checked between pages and attempts."""

    cancelled: bool = False

    def cancel(self) -> None:
        """Request cancellation."""
        self.cancelled = True


class _NullEvents:
    def emit(self, event: Mapping[str, Any]) -> None:
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

    def _emit(self, kind: str, request: HarvestRequest, **fields: Any) -> None:
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
        cursor: Mapping[str, Any] | None,
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
    def _check_page(
        adapter: SourceAdapter, page: PageResult, cursor: Mapping[str, Any] | None
    ) -> None:
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

    def run(
        self,
        adapter: SourceAdapter,
        request: HarvestRequest,
        sink: Sink,
        *,
        config: Mapping[str, Any] | None = None,
        cancel: CancelToken | None = None,
    ) -> HarvestResult:
        """Execute one bounded run and return a structured result (never raises for
        source, parser, sink or limit problems; programming errors propagate)."""
        source = adapter.source
        config = dict(config or {})
        cancel = cancel or CancelToken()
        started = self.clock.now()
        deadline = self.clock.monotonic() + request.max_duration_seconds
        errors: list[dict[str, Any]] = []
        issues: list[RecordIssue] = []
        pages = received = delivered = dup_run = dup_sink = 0
        counter = [0]
        exhausted = partial = False
        status: RunStatus | None = None
        before: Checkpoint | None = None
        current: Checkpoint | None = None
        started_from_beginning = True
        seen: set[tuple[tuple[str, str], str]] = set()

        def finish(final: RunStatus) -> HarvestResult:
            return HarvestResult(
                source_id=source.source_id,
                run_id=request.run_id,
                contract=CONTRACT_VERSION,
                status=final,
                started_at=started.isoformat(),
                finished_at=self.clock.now().isoformat(),
                pages=pages,
                records_received=received,
                records_delivered=delivered,
                duplicates_in_run=dup_run,
                duplicates_at_sink=dup_sink,
                issues=tuple(issues),
                errors=tuple(errors),
                checkpoint_before=before,
                checkpoint_after=current,
                source_exhausted=exhausted,
                snapshot_complete=(
                    final is RunStatus.COMPLETE
                    and exhausted
                    and started_from_beginning
                    and source.snapshot_semantics is SnapshotSemantics.FULL_SNAPSHOT_REPLACE
                ),
                attempts=counter[0],
            )

        try:
            if request.source_id != source.source_id:
                raise ConfigError("Anfrage und Adapter betreffen verschiedene Quellen.")
            adapter.validate_config(config)
            before = self.state.load(source.source_id)
            current = before
            cursor: Mapping[str, Any] | None = None
            if before is not None and request.resume:
                if before.profile_version != source.profile_version:
                    raise ConfigError(
                        "Checkpoint stammt aus Profilversion "
                        f"{before.profile_version}, Adapter nutzt {source.profile_version}; "
                        "kein Wiederanlauf mit fremdem Cursor."
                    )
                if not before.finished or (
                    source.snapshot_semantics is SnapshotSemantics.INCREMENTAL_UPSERT
                ):
                    cursor = before.cursor
            started_from_beginning = cursor is None
            self._emit("run_started", request, resume=cursor is not None)
            while True:
                if cancel.cancelled:
                    raise Cancelled("Abbruch angefordert.")
                if pages >= request.max_pages:
                    raise LimitReached(f"Seitenlimit {request.max_pages} erreicht.")
                if delivered >= request.max_records:
                    raise LimitReached(f"Datensatzlimit {request.max_records} erreicht.")
                if self.clock.monotonic() > deadline:
                    raise LimitReached("Zeitlimit des Laufs erreicht.")
                context = FetchContext(
                    request,
                    config,
                    self.transport,
                    self.credentials,
                    self.clock,
                    self.request_timeout,
                    pages + 1,
                )
                page = self._fetch(adapter, context, cursor, cancel, deadline, counter)
                pages += 1
                received += len(page.records)
                self._check_page(adapter, page, cursor)
                fresh: list[HarvestRecord] = []
                for record in page.records:
                    marker = (record.key, record.content_hash)
                    if marker in seen:
                        dup_run += 1
                        continue
                    seen.add(marker)
                    fresh.append(record)
                try:
                    receipt = sink.deliver(fresh, run_id=request.run_id, page=pages)
                except HarvestError:
                    raise
                except Exception as error:  # noqa: BLE001 - consumer storage failure
                    raise SinkError(f"Senke meldet {type(error).__name__}.") from error
                expected = {r.key for r in fresh}
                confirmed = set(receipt.accepted) | set(receipt.duplicates)
                if confirmed != expected:
                    raise SinkError("Senke hat nicht genau die übergebenen Datensätze bestätigt.")
                delivered += len(receipt.accepted)
                dup_sink += len(receipt.duplicates)
                issues.extend(page.issues)
                partial = partial or bool(page.issues) or page.status is PageStatus.PARTIAL
                checkpoint = Checkpoint(
                    source_id=source.source_id,
                    profile_version=source.profile_version,
                    cursor=None if page.next_cursor is None else dict(page.next_cursor),
                    run_id=request.run_id,
                    updated_at=self.clock.now().isoformat(),
                    pages_confirmed=(
                        current.pages_confirmed if current and not current.finished else 0
                    )
                    + 1,
                    records_confirmed=(
                        current.records_confirmed if current and not current.finished else 0
                    )
                    + len(fresh),
                    finished=page.complete,
                )
                try:
                    self.state.save(checkpoint, current)
                except CheckpointConflict:
                    raise
                current = checkpoint
                cursor = page.next_cursor
                self._emit(
                    "page_confirmed",
                    request,
                    page=pages,
                    records=len(fresh),
                    complete=page.complete,
                )
                if page.complete:
                    exhausted = True
                    break
            status = RunStatus.PARTIAL if partial else RunStatus.COMPLETE
        except Cancelled as error:
            errors.append(error.to_dict())
            status = RunStatus.CANCELLED
        except LimitReached as error:
            errors.append(error.to_dict())
            status = RunStatus.PARTIAL
        except HarvestError as error:
            errors.append(error.to_dict())
            status = RunStatus.PARTIAL if current is not before else RunStatus.FAILED
        result = finish(status)
        self._emit(
            "run_finished", request, status=result.status.value, pages=pages, delivered=delivered
        )
        return result
