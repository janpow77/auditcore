"""Asynchronous, abortable variant of the harvest flow.

:class:`AsyncHarvestEngine` runs :class:`AsyncSourceAdapter` objects through
the same flow as :class:`~auditcore_harvest.engine.HarvestEngine` (checks,
deduplication, sink, checkpoints, limits and events are shared). In addition
a request in progress is aborted

* when :meth:`CancelToken.cancel` is called (result ``cancelled``), and
* when the run's time budget (``HarvestRequest.max_duration_seconds``) is used
  up (result ``partial`` with ``limit_reached``),

instead of ending only at the request's own timeout. Cancelling the task that
awaits :meth:`AsyncHarvestEngine.run` follows the asyncio convention: the
in-flight request is aborted and ``CancelledError`` propagates. In every case
the checkpoint stays at the last page the sink confirmed.

The time budget is measured with the injected :class:`Clock` and enforced
with :func:`asyncio.timeout`.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Mapping
from dataclasses import dataclass, field
from typing import Protocol, TypeVar, runtime_checkable

from .adapter import FetchContext
from .errors import Cancelled, ConfigError, HarvestError, LimitReached
from .flow import FlowCore, NullEvents, RunState, adapter_bug, as_page
from .model import JSON, Cursor, HarvestRequest, HarvestResult, PageResult, Source
from .policies import CancelToken, RateLimit, RetryPolicy
from .ports import Clock, CredentialProvider, EventSink, Response, Sink, StateStore
from .session import CookieSession, Hop
from .transport import DEFAULT_STATUS_POLICY, StatusPolicy

T = TypeVar("T")


@runtime_checkable
class AsyncTransport(Protocol):
    """Performs exactly one request asynchronously; cancellation aborts it."""

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        timeout: float,
    ) -> Response:
        """Return the response or raise ``TransportError``."""
        ...


@runtime_checkable
class AsyncSleeper(Protocol):
    """Asynchronous waiting; injectable for tests."""

    async def sleep(self, seconds: float) -> None:
        """Wait ``seconds`` without blocking the event loop."""
        ...


class AsyncioSleeper:
    """Default sleeper based on :func:`asyncio.sleep`."""

    async def sleep(self, seconds: float) -> None:
        """Wait ``seconds``."""
        await asyncio.sleep(seconds)


class _NoSyncTransport:
    """Placeholder for ``FetchContext.transport`` in asynchronous runs."""

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        timeout: float,
    ) -> Response:
        """Asynchronous adapters use ``await context.fetch(...)``."""
        raise ConfigError(
            "Asynchrone Adapter rufen 'await context.fetch(...)' auf, nicht context.transport."
        )


@dataclass(frozen=True)
class AsyncFetchContext(FetchContext):
    """:class:`FetchContext` of an asynchronous run; requests go through :meth:`fetch`."""

    async_transport: AsyncTransport | None = None

    async def fetch(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
    ) -> Response:
        """One request over the asynchronous transport with the run's request timeout."""
        if self.async_transport is None:
            raise ConfigError("Kein asynchroner Transport konfiguriert.")
        return await self.async_transport.request(
            method, url, params=params, headers=headers, data=data, timeout=self.timeout
        )


@runtime_checkable
class AsyncSourceAdapter(Protocol):
    """Asynchronous counterpart of :class:`~auditcore_harvest.adapter.SourceAdapter`."""

    @property
    def source(self) -> Source:
        """Declared source identity and capabilities."""
        ...

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """Raise ``ConfigError`` for invalid configuration; never contact the source."""
        ...

    async def fetch_page(self, context: AsyncFetchContext, cursor: Cursor | None) -> PageResult:
        """Fetch exactly one page."""
        ...


async def guarded(work: Awaitable[T], cancel: CancelToken, budget: float) -> T:
    """Await ``work`` but abort it on ``cancel`` or after ``budget`` seconds.

    Raises :class:`Cancelled` or :class:`LimitReached`; an external
    cancellation of the calling task propagates unchanged.
    """
    loop = asyncio.get_running_loop()
    task = asyncio.ensure_future(work)

    def abort() -> None:
        loop.call_soon_threadsafe(task.cancel)

    remove = cancel.on_cancel(abort)
    window = asyncio.timeout(max(0.0, budget))
    try:
        async with window:
            return await task
    except TimeoutError as error:
        if not window.expired():
            raise
        raise LimitReached("Zeitlimit des Laufs erreicht; laufende Anfrage abgebrochen.") from error
    except asyncio.CancelledError:
        current = asyncio.current_task()
        if cancel.cancelled and (current is None or current.cancelling() == 0):
            raise Cancelled("Abbruch angefordert; laufende Anfrage abgebrochen.") from None
        raise
    finally:
        remove()


@dataclass
class AsyncHarvestEngine(FlowCore):
    """Runs any :class:`AsyncSourceAdapter` through the common flow, abortably."""

    transport: AsyncTransport
    credentials: CredentialProvider
    state: StateStore
    clock: Clock
    sleeper: AsyncSleeper = field(default_factory=AsyncioSleeper)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    rate_limit: RateLimit = field(default_factory=RateLimit)
    request_timeout: float = 30.0
    events: EventSink = field(default_factory=NullEvents)
    rng: random.Random = field(default_factory=lambda: random.Random(0))
    status_policy: StatusPolicy = DEFAULT_STATUS_POLICY

    def _context(
        self, request: HarvestRequest, settings: Mapping[str, JSON], page: int
    ) -> AsyncFetchContext:
        return AsyncFetchContext(
            request,
            settings,
            _NoSyncTransport(),
            self.credentials,
            self.clock,
            self.request_timeout,
            page,
            self.status_policy,
            self.transport,
        )

    async def _pause(self, seconds: float, cancel: CancelToken, deadline: float) -> None:
        if seconds > 0:
            await guarded(self.sleeper.sleep(seconds), cancel, deadline - self.clock.monotonic())

    async def _fetch(
        self,
        adapter: AsyncSourceAdapter,
        context: AsyncFetchContext,
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
            await self._pause(self.rate_limit.pending(self.clock), cancel, deadline)
            self.rate_limit.mark(self.clock)
            work = adapter.fetch_page(context, cursor)
            try:
                page = await guarded(work, cancel, deadline - self.clock.monotonic())
            except (Cancelled, LimitReached):
                raise
            except HarvestError as error:
                wait = self._retry_wait(error, attempt, context.request, context.page, deadline)
                if wait is None:
                    raise
                await self._pause(wait, cancel, deadline)
                continue
            except Exception as error:  # noqa: BLE001 - adapter bugs become structured errors
                raise adapter_bug(error) from error
            return as_page(page)

    async def _pages(
        self,
        run: RunState,
        adapter: AsyncSourceAdapter,
        request: HarvestRequest,
        sink: Sink,
        settings: Mapping[str, JSON],
        cursor: Cursor | None,
        cancel: CancelToken,
    ) -> None:
        while True:
            self._limits(run, request, cancel)
            context = self._context(request, settings, run.pages + 1)
            page = await self._fetch(adapter, context, cursor, cancel, run.deadline, run.attempts)
            if self._accept(run, adapter.source, request, sink, page, cursor):
                return
            cursor = page.next_cursor

    async def run(
        self,
        adapter: AsyncSourceAdapter,
        request: HarvestRequest,
        sink: Sink,
        *,
        config: Mapping[str, JSON] | None = None,
        cancel: CancelToken | None = None,
    ) -> HarvestResult:
        """Execute one bounded, abortable run and return a structured result."""
        settings = dict(config or {})
        run = self._new_run(request)
        try:
            cursor = self._begin(run, adapter, request, settings)
            await self._pages(
                run, adapter, request, sink, settings, cursor, cancel or CancelToken()
            )
            status = run.succeeded()
        except HarvestError as error:
            status = run.fail(error)
        return self._finish(run, adapter.source, request, status)


class AsyncSessionTransport:
    """Asynchronous :class:`~auditcore_harvest.session.SessionTransport`."""

    def __init__(self, inner: AsyncTransport, session: CookieSession | None = None) -> None:
        self.inner = inner
        self.session = session or CookieSession()

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        timeout: float,
    ) -> Response:
        """Perform the request, follow redirects and keep all cookies."""
        hop = Hop(method, url, params, dict(headers or {}), data)
        chain: list[Response] = []
        for _ in range(self.session.max_redirects + 1):
            response = await self.inner.request(
                hop.method,
                hop.url,
                params=hop.params,
                headers=self.session.headers_for(hop),
                data=hop.data,
                timeout=timeout,
            )
            outcome = self.session.step(hop, response, chain)
            if isinstance(outcome, Response):
                return outcome
            hop = outcome
        raise self.session.too_many()
