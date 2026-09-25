"""Retries with exponential backoff and a thread-safe circuit breaker.

Legacy state: no app client retried; flowinvoice had a module-global circuit
breaker in its Ollama provider (3 failures, 180 s). Both are opt-in here with
the legacy numbers as defaults, so an unconfigured client behaves like the
legacy clients (one attempt, no breaker).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from auditcore_llm_client.errors import (
    AVAILABILITY_KINDS,
    CircuitOpenError,
    ErrorKind,
    LlmClientError,
)

Clock = Callable[[], float]

#: Status codes that are worth another attempt (overload/gateway errors).
RETRYABLE_STATUS = frozenset({429, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    """How often and how long to retry. ``max_attempts=1`` disables retries."""

    max_attempts: int = 1
    initial_delay: float = 0.5
    factor: float = 2.0
    max_delay: float = 8.0
    retry_status: frozenset[int] = RETRYABLE_STATUS
    retry_unreachable: bool = True
    retry_timeout: bool = False

    def __post_init__(self) -> None:
        if self.max_attempts < 1 or self.initial_delay < 0 or self.factor < 1:
            raise ValueError("Ungültige Wiederholungsstrategie.")

    def should_retry(self, error: LlmClientError, attempt: int) -> bool:
        """True if ``error`` after ``attempt`` (1-based) justifies another try."""
        if attempt >= self.max_attempts:
            return False
        if error.kind is ErrorKind.HTTP_STATUS:
            return error.status_code in self.retry_status
        if error.kind is ErrorKind.TIMEOUT:
            return self.retry_timeout
        return error.kind is ErrorKind.UNREACHABLE and self.retry_unreachable

    def delay(self, attempt: int, retry_after: float | None = None) -> float:
        """Backoff before attempt ``attempt + 1``; honours ``Retry-After`` up to ``max_delay``."""
        computed = min(self.max_delay, self.initial_delay * self.factor ** (attempt - 1))
        if retry_after is not None:
            computed = max(computed, min(retry_after, self.max_delay))
        return computed


@dataclass(frozen=True)
class BreakerPolicy:
    """Circuit breaker thresholds (legacy flowinvoice: 3 failures, 180 s)."""

    failure_threshold: int = 3
    reset_timeout: float = 180.0
    clock: Clock = field(default=time.monotonic, compare=False)


class BreakerState(StrEnum):
    """Circuit breaker state."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


def counts_as_outage(error: LlmClientError) -> bool:
    """Failures that open the breaker: unreachable, timeout, 5xx and 429."""
    if error.kind in AVAILABILITY_KINDS:
        return True
    status = error.status_code or 0
    return error.kind is ErrorKind.HTTP_STATUS and (status >= 500 or status == 429)


class CircuitBreaker:
    """Closed → open after ``failure_threshold`` outages; one trial after ``reset_timeout``."""

    def __init__(self, policy: BreakerPolicy | None = None) -> None:
        self.policy = policy or BreakerPolicy()
        self._lock = threading.Lock()
        self._failures = 0
        self._opened_at = 0.0
        self._state = BreakerState.CLOSED

    @property
    def state(self) -> BreakerState:
        """Current state (``OPEN`` turns into ``HALF_OPEN`` once the timeout elapsed)."""
        with self._lock:
            return self._current_state()

    def _current_state(self) -> BreakerState:
        if self._state is BreakerState.OPEN and self._elapsed() >= self.policy.reset_timeout:
            return BreakerState.HALF_OPEN
        return self._state

    def _elapsed(self) -> float:
        return self.policy.clock() - self._opened_at

    def before_call(self, endpoint: str) -> None:
        """Raise :class:`CircuitOpenError` while the breaker is open."""
        with self._lock:
            state = self._current_state()
            if state is BreakerState.OPEN:
                remaining = max(0.0, self.policy.reset_timeout - self._elapsed())
                raise CircuitOpenError(
                    "Circuit-Breaker offen: Gateway wird vorübergehend nicht angefragt.",
                    endpoint=endpoint,
                    retry_after=round(remaining, 3),
                )
            if state is BreakerState.HALF_OPEN:
                # Exactly one trial call; further calls wait for its outcome.
                self._state = BreakerState.OPEN
                self._opened_at = self.policy.clock()

    def record_success(self) -> None:
        """Close the breaker."""
        with self._lock:
            self._failures = 0
            self._state = BreakerState.CLOSED

    def record_failure(self, error: LlmClientError) -> None:
        """Count an outage; a client error (4xx) proves the gateway answers and closes it."""
        if not counts_as_outage(error):
            self.record_success()
            return
        with self._lock:
            self._failures += 1
            if self._failures >= self.policy.failure_threshold:
                self._state = BreakerState.OPEN
                self._opened_at = self.policy.clock()

    def snapshot(self) -> dict[str, str | int]:
        """State for health endpoints."""
        with self._lock:
            return {"state": self._current_state().value, "consecutive_failures": self._failures}
