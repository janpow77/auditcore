"""Issue #236 (1): asynchronous engine and transport; cancellation and deadline abort requests."""

from __future__ import annotations

import asyncio
import dataclasses
import random
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field

import pytest

from auditcore_harvest import (
    AuthKind,
    CancelToken,
    Capabilities,
    Cursor,
    HarvestRequest,
    PageResult,
    RateLimit,
    Response,
    RetryPolicy,
    RunStatus,
    SnapshotSemantics,
    Source,
    TransportError,
    page_result,
)
from auditcore_harvest.aio import (
    AsyncFetchContext,
    AsyncHarvestEngine,
    AsyncioSleeper,
    AsyncSessionTransport,
    AsyncSourceAdapter,
    AsyncTransport,
    guarded,
)
from auditcore_harvest.memory import FixedClock, ListSink, MemoryStateStore, StaticCredentials
from auditcore_harvest.model import JSON

SOURCE = Source(
    "test.aio",
    "Async",
    "test",
    "1.0.0",
    "1",
    "application/json",
    AuthKind.NONE,
    Capabilities(pagination=True),
    SnapshotSemantics.INCREMENTAL_UPSERT,
)


@dataclass
class SlowTransport:
    """Answers ``/p1`` at once; ``/hang`` waits until cancelled (records the abort)."""

    failures: int = 0
    aborted: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)

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
        self.calls.append(url)
        if self.failures:
            self.failures -= 1
            raise TransportError("kurz weg")
        if url.endswith("/hang"):
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                self.aborted.append(url)
                raise
        return Response(200, url.encode(), {}, url)


@dataclass
class PagingAdapter:
    """Page 1 from ``/p1`` with cursor to ``second``; page 2 from the configured URL."""

    second: str = "https://s.invalid/p2"
    source: Source = SOURCE

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        return None

    async def fetch_page(self, context: AsyncFetchContext, cursor: Cursor | None) -> PageResult:
        url = self.second if cursor else "https://s.invalid/p1"
        response = context.check(await context.fetch("GET", url))
        record = context.record(self.source, response.url, {}, {"u": response.url}, url)
        return page_result([record], next_cursor=None if cursor else {"next": 2})


@dataclass
class RecordingSleeper:
    clock: FixedClock
    sleeps: list[float] = field(default_factory=list)

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.clock.elapsed += seconds


def engine(transport: AsyncTransport, **options: object) -> AsyncHarvestEngine:
    clock = options.pop("clock", FixedClock())
    assert isinstance(clock, FixedClock)
    return AsyncHarvestEngine(
        transport,
        StaticCredentials(),
        MemoryStateStore(),
        clock,
        RecordingSleeper(clock),
        rng=random.Random(0),
        **options,  # type: ignore[arg-type]
    )


def request(seconds: float = 3600.0) -> HarvestRequest:
    return HarvestRequest("test.aio", "r", max_duration_seconds=seconds)


def test_async_run_pages_and_checkpoints() -> None:
    eng = engine(SlowTransport())
    sink = ListSink()
    result = asyncio.run(eng.run(PagingAdapter(), request(), sink))
    assert result.status is RunStatus.COMPLETE and result.pages == 2
    assert sorted(k[1] for k in sink.records) == ["https://s.invalid/p1", "https://s.invalid/p2"]
    assert result.checkpoint_after is not None and result.checkpoint_after.finished
    assert isinstance(PagingAdapter(), AsyncSourceAdapter)


def test_cancel_token_aborts_the_request_in_progress() -> None:
    transport = SlowTransport()
    eng = engine(transport)
    token = CancelToken()

    async def scenario() -> tuple[RunStatus, float, Mapping[str, JSON]]:
        asyncio.get_running_loop().call_later(0.05, token.cancel)
        started = time.monotonic()
        result = await eng.run(
            PagingAdapter("https://s.invalid/hang"), request(), ListSink(), cancel=token
        )
        return result.status, time.monotonic() - started, result.to_dict()

    status, took, view = asyncio.run(scenario())
    assert status is RunStatus.CANCELLED and took < 5
    assert transport.aborted == ["https://s.invalid/hang"]
    assert view["error_kind"] == "cancelled" and view["pages"] == 1
    assert view["checkpoint_after"]["pages_confirmed"] == 1


def test_cancel_from_another_thread() -> None:
    transport = SlowTransport()
    token = CancelToken()
    timer = threading.Timer(0.05, token.cancel)
    timer.start()
    result = asyncio.run(
        engine(transport).run(
            PagingAdapter("https://s.invalid/hang"), request(), ListSink(), cancel=token
        )
    )
    timer.join()
    assert result.status is RunStatus.CANCELLED and transport.aborted


def test_run_deadline_aborts_the_request_in_progress() -> None:
    transport = SlowTransport()
    started = time.monotonic()
    result = asyncio.run(
        engine(transport).run(PagingAdapter("https://s.invalid/hang"), request(0.2), ListSink())
    )
    assert time.monotonic() - started < 5
    assert result.status is RunStatus.PARTIAL and result.errors[0]["code"] == "limit_reached"
    assert result.error_kind is not None and result.error_kind.value == "limit"
    assert transport.aborted == ["https://s.invalid/hang"]


def test_external_task_cancellation_propagates_and_aborts() -> None:
    transport = SlowTransport()

    async def scenario() -> None:
        task = asyncio.create_task(
            engine(transport).run(PagingAdapter("https://s.invalid/hang"), request(), ListSink())
        )
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert transport.aborted == ["https://s.invalid/hang"]


def test_retries_wait_asynchronously_and_honour_the_rate_limit() -> None:
    clock = FixedClock()
    eng = engine(
        SlowTransport(failures=1),
        clock=clock,
        retry=RetryPolicy(base_delay=2.0, jitter=0.0),
        rate_limit=RateLimit(min_interval_seconds=5.0),
    )
    result = asyncio.run(eng.run(PagingAdapter(), request(), ListSink()))
    assert result.status is RunStatus.COMPLETE and result.attempts == 3
    sleeper = eng.sleeper
    assert isinstance(sleeper, RecordingSleeper)
    assert sleeper.sleeps == [2.0, 3.0, 5.0]


@dataclass
class BrokenAdapter:
    mode: str
    source: Source = SOURCE

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        return None

    async def fetch_page(self, context: AsyncFetchContext, cursor: Cursor | None) -> PageResult:
        if self.mode == "sync":
            context.transport.request("GET", "https://s.invalid/", timeout=1)
        if self.mode == "timeout":
            raise TimeoutError("eigene Zeitgrenze")
        if self.mode == "type":
            return "keine Seite"  # type: ignore[return-value]
        raise KeyError("fehlt")


@pytest.mark.parametrize(
    ("mode", "code"),
    [("sync", "config_error"), ("timeout", "parser_error"), ("type", "parser_error")],
)
def test_adapter_faults_are_structured(mode: str, code: str) -> None:
    result = asyncio.run(engine(SlowTransport()).run(BrokenAdapter(mode), request(), ListSink()))
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == code


def test_bug_and_missing_transport() -> None:
    result = asyncio.run(engine(SlowTransport()).run(BrokenAdapter("bug"), request(), ListSink()))
    assert result.errors[0]["code"] == "parser_error"
    context = engine(SlowTransport())._context(request(), {}, 1)
    bare = dataclasses.replace(context, async_transport=None)
    with pytest.raises(Exception, match="Kein asynchroner Transport"):
        asyncio.run(bare.fetch("GET", "https://s.invalid/"))


def test_guarded_and_token_helpers() -> None:
    token = CancelToken()
    calls: list[str] = []
    remove = token.on_cancel(lambda: calls.append("x"))
    remove()
    remove()
    token.cancel()
    assert calls == [] and token.cancelled
    assert asyncio.run(guarded(asyncio.sleep(0, "ok"), CancelToken(), 1.0)) == "ok"
    asyncio.run(AsyncioSleeper().sleep(0))


@dataclass
class RedirectingAsync:
    seen: list[Mapping[str, str]] = field(default_factory=list)

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
        self.seen.append(dict(headers or {}))
        if url.endswith("/start"):
            lines = (("Location", "/ziel"), ("Set-Cookie", "sid=1; Path=/"))
            return Response(302, b"", dict(lines), url, raw_headers=lines)
        return Response(200, b"ok", {}, url)


def test_async_session_keeps_redirect_cookies() -> None:
    inner = RedirectingAsync()
    session = AsyncSessionTransport(inner)

    async def scenario() -> Response:
        first = await session.request("GET", "https://a.invalid/start", timeout=1)
        await session.request("GET", "https://a.invalid/weiter", timeout=1)
        return first

    final = asyncio.run(scenario())
    assert final.body == b"ok" and [r.status for r in final.history] == [302]
    assert inner.seen == [{}, {"Cookie": "sid=1"}, {"Cookie": "sid=1"}]
    loop = [RedirectingAsync()]
    with pytest.raises(TransportError):
        asyncio.run(
            AsyncSessionTransport(loop[0], type(session.session)(max_redirects=0)).request(
                "GET", "https://a.invalid/start", timeout=1
            )
        )
