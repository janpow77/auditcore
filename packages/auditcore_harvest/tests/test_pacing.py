"""0.1.5: shared pacing, ``Retry-After`` parsing and the pure retry decision."""

from __future__ import annotations

import random
import threading
from datetime import UTC, datetime, timedelta

import pytest

from auditcore_harvest import (
    AuthError,
    MemoryRateLimitStore,
    RateLimitError,
    RateLimitStore,
    Response,
    RetryPolicy,
    SharedRateLimit,
    TransportError,
    parse_retry_after,
    raise_for_status,
)
from auditcore_harvest.memory import ClockSleeper, FixedClock

NOW = datetime(2026, 10, 21, 7, 28, tzinfo=UTC)


@pytest.mark.parametrize(
    ("value", "now", "expected"),
    [
        ("120", None, 120.0),
        (" 7 ", None, 7.0),
        ("0", None, 0.0),
        (None, None, None),
        ("", NOW, None),
        ("-5", NOW, None),
        ("1.5", NOW, None),
        ("bald", NOW, None),
        ("Wed, 21 Oct 2026 07:30:00 GMT", None, None),
        ("Wed, 21 Oct 2026 07:30:00 GMT", NOW, 120.0),
        ("Wed, 21 Oct 2026 07:00:00 GMT", NOW, 0.0),
    ],
)
def test_parse_retry_after(value: str | None, now: datetime | None, expected: float | None) -> None:
    assert parse_retry_after(value, now) == expected


def test_raise_for_status_keeps_seconds_only() -> None:
    with pytest.raises(RateLimitError) as caught:
        raise_for_status(Response(429, b"", {"retry-after": "30"}))
    assert caught.value.retry_after == 30.0
    with pytest.raises(RateLimitError) as dated:
        raise_for_status(Response(429, b"", {"Retry-After": "Wed, 21 Oct 2026 07:30:00 GMT"}))
    assert dated.value.retry_after is None


def test_memory_store_is_a_rate_limit_store() -> None:
    assert isinstance(MemoryRateLimitStore(), RateLimitStore)


def test_store_hands_out_consecutive_slots_and_respects_max_wait() -> None:
    store = MemoryRateLimitStore()
    assert store.reserve("quelle", 5.0, 100.0, 60.0) == 0.0
    assert store.reserve("quelle", 5.0, 100.0, 60.0) == 5.0
    assert store.reserve("quelle", 5.0, 101.0, 60.0) == 9.0
    assert store.reserve("andere", 5.0, 101.0, 60.0) == 0.0
    assert store.reserve("quelle", 5.0, 101.0, 8.0) is None
    # Nothing was reserved by the refused call.
    assert store.reserve("quelle", 5.0, 101.0, 60.0) == 14.0


def test_defer_only_moves_forward() -> None:
    store = MemoryRateLimitStore()
    store.defer("quelle", 200.0)
    store.defer("quelle", 150.0)
    assert store.reserve("quelle", 1.0, 100.0, 500.0) == 100.0


def test_store_is_safe_under_threads() -> None:
    store = MemoryRateLimitStore()
    waits: list[float] = []
    lock = threading.Lock()

    def take() -> None:
        wait = store.reserve("quelle", 1.0, 0.0, 1000.0)
        assert wait is not None
        with lock:
            waits.append(wait)

    threads = [threading.Thread(target=take) for _ in range(50)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(waits) == [float(i) for i in range(50)]


def test_shared_rate_limit_waits_pauses_and_gives_up() -> None:
    clock = FixedClock()
    sleeper = ClockSleeper(clock)
    store = MemoryRateLimitStore()
    first = SharedRateLimit("quelle", 2.0, store, max_wait=30.0)
    second = SharedRateLimit("quelle", 2.0, store, max_wait=30.0)
    assert first.wait(clock, sleeper) and second.wait(clock, sleeper)
    assert sleeper.sleeps == [2.0]
    first.pause(clock, 60.0)
    assert second.wait(clock, sleeper) is False
    assert sleeper.sleeps == [2.0]
    clock.elapsed += 45.0
    assert second.wait(clock, sleeper) is True
    assert sleeper.sleeps[-1] == pytest.approx(15.0)


def test_should_retry_matches_delay() -> None:
    policy = RetryPolicy(max_attempts=3, max_retry_after=60.0)
    errors = [
        TransportError("x"),
        TransportError("x", retryable=False),
        AuthError("x"),
        RateLimitError("x"),
        RateLimitError("x", retry_after=30.0),
        RateLimitError("x", retry_after=61.0),
    ]
    for error in errors:
        for attempt in range(0, 5):
            delay = policy.delay(attempt, error, random.Random(1))
            assert policy.should_retry(attempt, error) is (delay is not None)


def test_backoff_is_delay_without_jitter() -> None:
    policy = RetryPolicy(base_delay=60.0, max_delay=600.0, jitter=0.0)
    error = TransportError("x")
    for attempt in range(1, 3):
        assert policy.backoff(attempt) == policy.delay(attempt, error, random.Random(0))
    assert [policy.backoff(n) for n in (1, 2, 3, 4, 5)] == [60.0, 120.0, 240.0, 480.0, 600.0]
    assert timedelta(seconds=policy.backoff(5)) == timedelta(minutes=10)
