"""Run policies of the engine: bounded retry, request pacing and cooperative cancellation."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

from .errors import HarvestError, RateLimitError
from .ports import Clock, Sleeper


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded exponential backoff with jitter; honours ``Retry-After`` up to a limit.

    A ``Retry-After`` above ``max_retry_after`` ends the retries (default). With
    ``retry_after_cap`` set, a too long ``Retry-After`` is shortened to the cap
    instead and the attempt is retried; ``max_attempts`` and the run deadline
    still bound the run.
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: float = 0.1
    max_retry_after: float = 300.0
    retry_after_cap: float | None = None

    def delay(self, attempt: int, error: HarvestError, rng: random.Random) -> float | None:
        """Seconds to wait before the next attempt, or ``None`` to give up."""
        if attempt >= self.max_attempts or not error.retryable:
            return None
        if isinstance(error, RateLimitError) and error.retry_after is not None:
            wanted = max(0.0, float(error.retry_after))
            if self.retry_after_cap is not None:
                return min(wanted, max(0.0, self.retry_after_cap))
            if wanted > self.max_retry_after:
                return None
            return wanted
        backoff = min(self.max_delay, self.base_delay * (2.0 ** (attempt - 1)))
        return backoff * (1.0 + self.jitter * rng.random())


@dataclass
class RateLimit:
    """Minimum interval between two requests of a run."""

    min_interval_seconds: float = 0.0
    _last: float | None = field(default=None, init=False, repr=False)

    def pending(self, clock: Clock) -> float:
        """Seconds still to wait before the next request (``0.0`` if none)."""
        if self._last is None:
            return 0.0
        return max(0.0, self.min_interval_seconds - (clock.monotonic() - self._last))

    def mark(self, clock: Clock) -> None:
        """Remember that a request starts now."""
        self._last = clock.monotonic()

    def wait(self, clock: Clock, sleeper: Sleeper) -> None:
        """Sleep until the interval has passed."""
        remaining = self.pending(clock)
        if remaining > 0:
            sleeper.sleep(remaining)
        self.mark(clock)


@dataclass
class CancelToken:
    """Cooperative cancellation checked between pages and attempts.

    The asynchronous engine also registers a callback with :meth:`on_cancel`
    so that :meth:`cancel` aborts a request in progress. ``cancel`` may be
    called from another thread; callbacks must be thread-safe.
    """

    cancelled: bool = False
    _callbacks: list[Callable[[], None]] = field(
        default_factory=list, init=False, repr=False, compare=False
    )

    def cancel(self) -> None:
        """Request cancellation and notify registered callbacks."""
        self.cancelled = True
        for callback in list(self._callbacks):
            callback()

    def on_cancel(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register ``callback``; returns a function that removes it again."""
        self._callbacks.append(callback)

        def remove() -> None:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return remove
