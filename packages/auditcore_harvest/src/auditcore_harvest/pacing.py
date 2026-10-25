"""Request pacing shared across processes and the ``Retry-After`` header.

:class:`~auditcore_harvest.policies.RateLimit` paces the requests of one run
in one process. Several workers fetching from the same host need one shared
schedule instead; the store behind it (a key-value server, a database row, a lock
file) is infrastructure and therefore a port, :class:`RateLimitStore`. The core ships
an in-memory store for tests and single-process consumers.

Times in the store are wall-clock seconds (``Clock.now().timestamp()``),
because monotonic clocks of different processes are not comparable.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from .ports import Clock, Sleeper


def parse_retry_after(value: str | None, now: datetime | None = None) -> float | None:
    """Seconds requested by a ``Retry-After`` header (RFC 9110, section 10.2.3).

    Accepts delay-seconds (``"120"``). An HTTP date (``"Wed, 21 Oct 2026
    07:28:00 GMT"``) is converted only when ``now`` is given, because the core
    owns no clock; a date in the past gives ``0.0``. Missing, negative or
    unreadable values give ``None``.
    """
    text = (value or "").strip()
    if not text:
        return None
    if text.isdigit():
        return float(text)
    if now is None:
        return None
    # Lazy: ``email.utils`` loads ``socket``; plain imports of the core stay without it.
    from email.utils import parsedate_to_datetime

    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, (when - now).total_seconds())


@runtime_checkable
class RateLimitStore(Protocol):
    """Shared schedule of request slots per key (for example a host name).

    Both operations must be atomic across all processes that share the store.
    """

    def reserve(self, key: str, interval: float, now: float, max_wait: float) -> float:
        """Reserve the next free slot of ``key`` if it starts within ``max_wait``.

        Always returns the seconds from ``now`` until the next free slot
        (``0.0`` when free now). A result ``<= max_wait`` means the slot is
        reserved and the next free slot moved to ``slot + interval``; a result
        ``> max_wait`` means nothing was reserved, and the value tells the
        caller how long to come back later (for example a task countdown
        instead of a blocked worker).
        """
        ...

    def defer(self, key: str, until: float) -> None:
        """Make sure no slot of ``key`` starts before ``until`` (never earlier)."""
        ...


@dataclass
class MemoryRateLimitStore:
    """Thread-safe in-memory :class:`RateLimitStore` for one process."""

    _next: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def reserve(self, key: str, interval: float, now: float, max_wait: float) -> float:
        """See :meth:`RateLimitStore.reserve`."""
        with self._lock:
            slot = max(now, self._next.get(key, now))
            if slot - now <= max_wait:
                self._next[key] = slot + max(0.0, interval)
            return slot - now

    def defer(self, key: str, until: float) -> None:
        """See :meth:`RateLimitStore.defer`."""
        with self._lock:
            self._next[key] = max(self._next.get(key, until), until)


@dataclass(frozen=True)
class SharedRateLimit:
    """Minimum interval between requests for one key, shared through a store.

    ``acquire`` blocks until the reserved slot starts and returns ``0.0``. A
    slot further away than ``max_wait`` is not reserved; ``acquire`` then
    returns the seconds until it would be free, without sleeping, and the
    caller decides (typically: reschedule the work with that countdown rather
    than keep a worker waiting). ``wait`` is the boolean short form.
    """

    key: str
    min_interval_seconds: float
    store: RateLimitStore
    max_wait: float = 300.0

    def acquire(self, clock: Clock, sleeper: Sleeper) -> float:
        """Sleep until the next slot and return ``0.0``; beyond ``max_wait`` return
        the seconds to come back later instead (nothing reserved, no sleep)."""
        remaining = self.store.reserve(
            self.key, self.min_interval_seconds, clock.now().timestamp(), self.max_wait
        )
        if remaining > self.max_wait:
            return remaining
        if remaining > 0:
            sleeper.sleep(remaining)
        return 0.0

    def wait(self, clock: Clock, sleeper: Sleeper) -> bool:
        """Sleep until the next slot; ``False`` if it is beyond ``max_wait``."""
        return self.acquire(clock, sleeper) == 0.0

    def pause(self, clock: Clock, seconds: float) -> None:
        """Hold back every process for ``seconds`` (for example after ``Retry-After``)."""
        self.store.defer(self.key, clock.now().timestamp() + max(0.0, seconds))
