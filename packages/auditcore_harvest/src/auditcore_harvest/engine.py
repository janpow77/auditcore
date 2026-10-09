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

This engine is synchronous; a request in progress ends at its own timeout.
:class:`~auditcore_harvest.aio.AsyncHarvestEngine` runs the same flow with
asynchronous adapters and aborts a request in progress on cancellation or
when the run's time budget is used up.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

from .adapter import FetchContext, SourceAdapter
from .errors import Cancelled, HarvestError
from .flow import FlowCore, NullEvents, RunState, adapter_bug, as_page
from .model import JSON, Cursor, HarvestRequest, HarvestResult, PageResult
from .policies import CancelToken, RateLimit, RetryPolicy
from .ports import Clock, CredentialProvider, EventSink, Sink, Sleeper, StateStore, Transport
from .transport import DEFAULT_STATUS_POLICY, StatusPolicy

__all__ = ["CancelToken", "HarvestEngine", "RateLimit", "RetryPolicy"]


@dataclass
class HarvestEngine(FlowCore):
    """Runs any :class:`SourceAdapter` through the common flow."""

    transport: Transport
    credentials: CredentialProvider
    state: StateStore
    clock: Clock
    sleeper: Sleeper
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    rate_limit: RateLimit = field(default_factory=RateLimit)
    request_timeout: float = 30.0
    events: EventSink = field(default_factory=NullEvents)
    rng: random.Random = field(default_factory=lambda: random.Random(0))
    status_policy: StatusPolicy = DEFAULT_STATUS_POLICY

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
                wait = self._retry_wait(error, attempt, context.request, context.page, deadline)
                if wait is None:
                    raise
                self.sleeper.sleep(wait)
                continue
            except Exception as error:  # noqa: BLE001 - adapter bugs become structured errors
                raise adapter_bug(error) from error
            return as_page(page)

    def _pages(
        self,
        run: RunState,
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
                self.status_policy,
            )
            page = self._fetch(adapter, context, cursor, cancel, run.deadline, run.attempts)
            if self._accept(run, adapter.source, request, sink, page, cursor):
                return
            cursor = page.next_cursor

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
        settings = dict(config or {})
        run = self._new_run(request)
        try:
            cursor = self._begin(run, adapter, request, settings)
            self._pages(run, adapter, request, sink, settings, cursor, cancel or CancelToken())
            status = run.succeeded()
        except HarvestError as error:
            status = run.fail(error)
        return self._finish(run, adapter.source, request, status)
