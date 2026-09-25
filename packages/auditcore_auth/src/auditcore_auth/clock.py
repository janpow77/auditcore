"""Timezone-aware clock handling.

Every timestamp inside auditcore_auth is an aware ``datetime`` in UTC. A clock
is any zero-argument callable returning such a value; tests inject a fixed one.
"""

from __future__ import annotations

from calendar import timegm
from collections.abc import Callable
from datetime import UTC, datetime

from .errors import ConfigurationError

Clock = Callable[[], datetime]


def system_clock() -> datetime:
    """Return the current time as an aware UTC datetime."""
    return datetime.now(UTC)


def fixed_clock(instant: datetime) -> Clock:
    """Return a clock that always answers ``instant`` (for tests and replays)."""
    aware = require_aware(instant)
    return lambda: aware


def require_aware(value: datetime) -> datetime:
    """Reject naive datetimes and normalise aware ones to UTC."""
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ConfigurationError("Zeitstempel ohne Zeitzone sind nicht zulässig")
    return value.astimezone(UTC)


def to_epoch(value: datetime) -> int:
    """Whole seconds since the epoch, truncating microseconds like PyJWT and python-jose."""
    return timegm(require_aware(value).utctimetuple())


def from_epoch(seconds: int | float) -> datetime:
    """Aware UTC datetime for a NumericDate claim."""
    return datetime.fromtimestamp(seconds, UTC)
