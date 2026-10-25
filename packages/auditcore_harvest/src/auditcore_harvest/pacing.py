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

    def reserve(self, key: str, interval: float, now: float, max_wait: float) -> float | None:
        """Reserve the next free slot of ``key``.

        Returns the seconds until the slot starts (``0.0`` when free now) and
        moves the next free slot to ``slot + interval``. When the slot starts
        more than ``max_wait`` seconds after ``now``, nothing is reserved and
        ``None`` is returned.
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

    def reserve(self, key: str, interval: float, now: float, max_wait: float) -> float | None:
        """See :meth:`RateLimitStore.reserve`."""
        with self._lock:
            slot = max(now, self._next.get(key, now))
            if slot - now > max_wait:
                return None
            self._next[key] = slot + max(0.0, interval)
            return slot - now

    def defer(self, key: str, until: float) -> None:
        """See :meth:`RateLimitStore.defer`."""
        with self._lock:
            self._next[key] = max(self._next.get(key, until), until)


@dataclass(frozen=True)
class SharedRateLimit:
    """Minimum interval between requests for one key, shared through a store.

    ``wait`` blocks until the reserved slot starts. A slot further away than
    ``max_wait`` is not reserved; ``wait`` then returns ``False`` and the
    caller decides (typically: report a rate-limit error and retry later).
    """

    key: str
    min_interval_seconds: float
    store: RateLimitStore
    max_wait: float = 300.0

    def wait(self, clock: Clock, sleeper: Sleeper) -> bool:
        """Sleep until the next slot; ``False`` if it is beyond ``max_wait``."""
        remaining = self.store.reserve(
            self.key, self.min_interval_seconds, clock.now().timestamp(), self.max_wait
        )
        if remaining is None:
            return False
        if remaining > 0:
            sleeper.sleep(remaining)
        return True

    def pause(self, clock: Clock, seconds: float) -> None:
        """Hold back every process for ``seconds`` (for example after ``Retry-After``)."""
        self.store.defer(self.key, clock.now().timestamp() + max(0.0, seconds))
