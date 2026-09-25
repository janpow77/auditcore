"""Retries with backoff, circuit breaker and health tracking."""

from __future__ import annotations

import asyncio

import pytest
from conftest import Gateway

from auditcore_llm_client import (
    AsyncLlmClient,
    BreakerPolicy,
    BreakerState,
    CircuitBreaker,
    CircuitOpenError,
    ClientConfig,
    LlmClient,
    RetryPolicy,
    RouterHealth,
    RouterHttpError,
    RouterTimeoutError,
    RouterUnavailableError,
)

OK = {"json": {"status": "ok"}}


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _config(**kwargs: object) -> ClientConfig:
    return ClientConfig(base_url="http://r.test", app_id="t", **kwargs)  # type: ignore[arg-type]


def test_policy_decisions() -> None:
    policy = RetryPolicy(max_attempts=3)
    assert policy.should_retry(RouterHttpError("x", status_code=503), 1)
    assert not policy.should_retry(RouterHttpError("x", status_code=503), 3)
    assert not policy.should_retry(RouterHttpError("x", status_code=400), 1)
    assert policy.should_retry(RouterUnavailableError("x"), 1)
    assert not policy.should_retry(RouterTimeoutError("x"), 1)
    assert RetryPolicy(max_attempts=2, retry_timeout=True).should_retry(RouterTimeoutError("x"), 1)
    assert [policy.delay(n) for n in (1, 2, 3, 6)] == [0.5, 1.0, 2.0, 8.0]
    assert policy.delay(1, retry_after=3.0) == 3.0 and policy.delay(1, retry_after=99) == 8.0
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_default_is_one_attempt_like_legacy() -> None:
    gateway = Gateway([{"status": 503, "text": "x"}])
    with LlmClient(_config(), transport=gateway.transport()) as client, \
            pytest.raises(RouterHttpError):
        client.health()
    assert len(gateway.requests) == 1


def test_retries_with_backoff_and_retry_after() -> None:
    gateway = Gateway([{"status": 503, "text": "x"},
                       {"status": 429, "text": "x", "headers": {"Retry-After": "3"}},
                       {"raise": "connect"}, OK])
    sleeps: list[float] = []
    health = RouterHealth()
    config = _config(retry=RetryPolicy(max_attempts=4))
    with LlmClient(config, transport=gateway.transport(), sleep=sleeps.append,
                   health=health) as client:
        assert client.health() == {"status": "ok"}
    assert sleeps == [0.5, 3.0, 2.0]
    assert health.to_dict()["consecutive_failures"] == 0


def test_async_retries_use_async_sleep() -> None:
    gateway = Gateway([{"status": 502, "text": "x"}, OK])
    sleeps: list[float] = []

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    async def run() -> object:
        config = _config(retry=RetryPolicy(max_attempts=2))
        async with AsyncLlmClient(config, transport=gateway.transport(), sleep=sleep) as client:
            return await client.health()

    assert asyncio.run(run()) == {"status": "ok"} and sleeps == [0.5]


def test_breaker_state_machine() -> None:
    clock = Clock()
    breaker = CircuitBreaker(BreakerPolicy(failure_threshold=2, reset_timeout=10, clock=clock))
    breaker.record_failure(RouterHttpError("x", status_code=404))
    breaker.record_failure(RouterUnavailableError("x"))
    assert breaker.state is BreakerState.CLOSED
    breaker.record_failure(RouterHttpError("x", status_code=500))
    assert breaker.state is BreakerState.OPEN
    with pytest.raises(CircuitOpenError) as info:
        breaker.before_call("/x")
    assert info.value.retry_after == 10.0
    clock.now += 10
    assert breaker.state is BreakerState.HALF_OPEN
    breaker.before_call("/x")
    with pytest.raises(CircuitOpenError):
        breaker.before_call("/x")
    breaker.record_success()
    assert breaker.snapshot() == {"state": "closed", "consecutive_failures": 0}
    breaker.record_failure(RouterHttpError("x", status_code=429))
    breaker.record_failure(RouterHttpError("x", status_code=400))
    assert breaker.snapshot()["consecutive_failures"] == 0


def test_open_breaker_stops_requests() -> None:
    clock = Clock()
    gateway = Gateway([{"raise": "connect"}, {"raise": "timeout"}, OK])
    health = RouterHealth()
    config = _config(breaker=BreakerPolicy(failure_threshold=2, reset_timeout=30, clock=clock))
    with LlmClient(config, transport=gateway.transport(), health=health) as client:
        for _ in range(2):
            with pytest.raises(RouterUnavailableError):
                client.health()
        with pytest.raises(CircuitOpenError):
            client.health()
        assert len(gateway.requests) == 2
        clock.now += 30
        assert client.health() == {"status": "ok"}
    assert health.to_dict()["consecutive_failures"] == 0


def test_router_health_semantics() -> None:
    clock = Clock()
    health = RouterHealth(clock=clock, secrets=["geheim"])
    assert not health.is_healthy()
    assert health.to_dict()["reachable"] is False
    health.record_success()
    assert health.is_healthy()
    for _ in range(3):
        health.record_failure("Fehler geheim http://x.test/y")
    record = health.to_dict()
    assert record["last_error_message"] == "Fehler <redacted> <url>"
    assert record["consecutive_failures"] == 3 and not health.is_healthy()
    health.record_success()
    clock.now += 60
    assert not health.is_healthy()
    assert health.to_dict()["last_success_age_s"] == 60
    assert RouterHealth.shared() is RouterHealth.shared()
