"""Timezone-aware time."""

from __future__ import annotations

from datetime import UTC, datetime

NAIVE_MESSAGE = "Zeitangaben müssen eine Zeitzone tragen."


def utc_now() -> datetime:
    """Current time in UTC."""
    return datetime.now(UTC)


def require_aware(moment: datetime) -> datetime:
    """``moment`` unchanged; ``ValueError`` if it has no time zone."""
    if moment.tzinfo is None:
        raise ValueError(NAIVE_MESSAGE)
    return moment
