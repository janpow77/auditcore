"""Flow-Agent background work: ``X-Flow-Arbeit`` and the deferred 429 (contract 1.15).

Contract: flow-agent main fbfa3ef0 (``docs/hintergrundarbeit.md``,
``ai_gateway.HintergrundZurueckgestelltError``). Deferral is no failure: it
consumes no attempt, is not retried by the client and is no outage.
"""

from __future__ import annotations

import asyncio
import dataclasses

import pytest
from conftest import KEY, Gateway

from auditcore_llm_client import (
    AsyncLlmClient,
    BackgroundDeferredError,
    BreakerPolicy,
    BreakerState,
    CircuitBreaker,
    ClientConfig,
    ErrorKind,
    LlmClient,
    LlmClientError,
    Mode,
    RetryPolicy,
    RouterHealth,
    RouterHttpError,
    SecretValue,
    WorkType,
    safe_call,
)

FLOW = ClientConfig(
    base_url="https://agent.test",
    app_id="app",
    mode=Mode.FLOW_AGENT,
    api_key=SecretValue(KEY),
    work=WorkType.BACKGROUND,
    retry=RetryPolicy(max_attempts=3),
    breaker=BreakerPolicy(failure_threshold=1),
)
DETAIL = "Hintergrundarbeit zurückgestellt, erneut in 120 s: knoten-a: Nutzer aktiv"
DEFERRED: dict[str, object] = {
    "status": 429,
    "json": {"detail": DETAIL},
    "headers": {"Retry-After": "120", "X-Flow-Agent-Error": "hintergrund-zurueckgestellt"},
}
OK: dict[str, object] = {"json": {"choices": [{"message": {"content": "ok"}}]}}
EMBED_OK: dict[str, object] = {"json": {"data": [{"embedding": [0.5, 0.25]}]}}


def test_deferred_is_own_kind_not_retried_and_not_counted() -> None:
    gateway = Gateway([DEFERRED, OK])
    health = RouterHealth()
    sleeps: list[float] = []
    with LlmClient(
        FLOW, transport=gateway.transport(), health=health, sleep=sleeps.append
    ) as client:
        with pytest.raises(BackgroundDeferredError) as info:
            client.chat([{"role": "user", "content": "x"}])
        error = info.value
        assert error.kind is ErrorKind.DEFERRED and error.status_code == 429
        assert error.retry_after == 120.0 and "zurückgestellt" in error.message
        assert error.to_dict()["kind"] == "deferred"
        assert len(gateway.requests) == 1 and sleeps == []
        assert gateway.requests[0]["headers"]["x-flow-arbeit"] == "hintergrund"  # type: ignore[index]
        # Breaker (threshold 1) stayed closed, health counted no failure.
        assert health.to_dict()["consecutive_failures"] == 0
        assert health.last_error_message == ""
        assert client.chat([]).content == "ok"


def test_deferred_in_async_client_and_embeddings() -> None:
    health = RouterHealth()

    async def run() -> tuple[LlmClientError, list[list[float]]]:
        gateway = Gateway([DEFERRED, EMBED_OK])
        async with AsyncLlmClient(FLOW, transport=gateway.transport(), health=health) as client:
            with pytest.raises(BackgroundDeferredError) as info:
                await client.embed(["Text"])
            vectors = (await client.embed(["Text"])).embeddings
        assert gateway.requests[0]["headers"]["x-flow-arbeit"] == "hintergrund"  # type: ignore[index]
        return info.value, vectors

    error, vectors = asyncio.run(run())
    assert error.retry_after == 120.0 and vectors == [[0.5, 0.25]]
    assert health.consecutive_failures == 0


DEFERRAL_CASES = [
    # (status, header, retry_after, expected type)
    (429, "hintergrund-zurueckgestellt", "30", BackgroundDeferredError),
    (429, " Hintergrund-Zurueckgestellt", "30", BackgroundDeferredError),
    (429, "hintergrund-zurueckgestellt", None, BackgroundDeferredError),
    (503, "hintergrund-zurueckgestellt", "30", RouterHttpError),
    (429, None, "30", RouterHttpError),
    (429, "egress-denied", "30", RouterHttpError),
]


@pytest.mark.parametrize(("status", "header", "retry_after", "expected"), DEFERRAL_CASES)
def test_deferral_needs_header_code_and_status(
    status: int, header: str | None, retry_after: str | None, expected: type
) -> None:
    headers = {"X-Flow-Agent-Error": header} if header is not None else {}
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    gateway = Gateway([{"status": status, "json": {"detail": DETAIL}, "headers": headers}])
    config = dataclasses.replace(FLOW, retry=RetryPolicy())
    with (
        LlmClient(config, transport=gateway.transport()) as client,
        pytest.raises(LlmClientError) as info,
    ):
        client.chat([])
    assert type(info.value) is expected
    assert info.value.retry_after == (float(retry_after) if retry_after else None)


def test_plain_429_keeps_retry_and_outage_semantics() -> None:
    plain = {"status": 429, "json": {"detail": "busy"}, "headers": {"Retry-After": "1"}}
    gateway = Gateway([plain, OK])
    sleeps: list[float] = []
    with LlmClient(FLOW, transport=gateway.transport(), sleep=sleeps.append) as client:
        assert client.chat([]).content == "ok"
    assert sleeps == [1.0] and len(gateway.requests) == 2


def test_deferral_header_is_ignored_in_router_mode() -> None:
    gateway = Gateway([DEFERRED])
    router = ClientConfig(base_url="http://r.test", app_id="a")
    with LlmClient(router, transport=gateway.transport()) as client, pytest.raises(RouterHttpError):
        client.chat([])


@pytest.mark.parametrize(
    ("work", "expected"),
    [(None, None), (WorkType.INTERACTIVE, "interaktiv"), (WorkType.BACKGROUND, "hintergrund")],
)
def test_work_type_header(work: WorkType | None, expected: str | None) -> None:
    gateway = Gateway([OK, OK])
    flow = dataclasses.replace(FLOW, work=work)
    router = ClientConfig(base_url="http://r.test", app_id="a", work=work)
    for config in (flow, router):
        with LlmClient(config, transport=gateway.transport()) as client:
            client.chat([])
    for request in gateway.requests:
        assert request["headers"].get("x-flow-arbeit") == expected  # type: ignore[attr-defined]


def test_policy_and_breaker_ignore_deferral() -> None:
    error = BackgroundDeferredError("zurückgestellt", status_code=429, retry_after=5.0)
    assert not RetryPolicy(max_attempts=5, retry_status=frozenset({429})).should_retry(error, 1)
    breaker = CircuitBreaker(BreakerPolicy(failure_threshold=1))
    breaker.record_failure(error)
    assert breaker.state is BreakerState.CLOSED
    assert breaker.snapshot()["consecutive_failures"] == 0


def test_safe_call_reports_deferral_without_key() -> None:
    gateway = Gateway([DEFERRED])
    with LlmClient(FLOW, transport=gateway.transport()) as client:
        result, message = safe_call(client.chat, [])
    assert result is None and message is not None
    assert "zurückgestellt" in message and KEY not in message
