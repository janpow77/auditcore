"""Status lifecycle of ZVG notices as pure, database-free functions.

Characterized by running the original ``Ingest.mark_seen``,
``Ingest.close_vanished`` and ``Ingest.upsert`` of
``janpow77/versteigerung@e4ad7af`` against a throwaway PostgreSQL database
migrated with the original Alembic migrations (fixture ``lifecycle``).

Statuses: ``erfasst`` and ``terminiert`` are open; ``abgehalten`` and
``aufgehoben`` are closed. The consumer keeps persistence, transactions and
the SQL; this module only decides the transitions:

* :func:`mark_seen` — every case whose file number is in the complete result
  list of its court gets ``last_seen_at = now``; an empty list changes nothing.
* :func:`close_vanished` — open, not deleted cases of the court whose
  ``last_seen_at`` is strictly older than ``now - grace_days`` are closed:
  ``abgehalten`` if they have a past date and no date at or after ``now``,
  otherwise ``aufgehoben``; ``closed_at = now``. Cases never seen
  (``last_seen_at is None``) stay untouched.
* :func:`reappear` — a case listed again (the original upsert) becomes
  ``terminiert`` if its new date is at or after ``now``, else ``erfasst``;
  ``closed_at`` is cleared, ``last_seen_at = now`` and the dates are replaced.

Only the result list of a court that was loaded successfully may be passed;
the original runs the lifecycle only after a successful listing.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

OPEN = frozenset({"erfasst", "terminiert"})
CLOSED = frozenset({"abgehalten", "aufgehoben"})
STATUSES = OPEN | CLOSED


@dataclass(frozen=True)
class CaseState:
    """Lifecycle-relevant state of one auction case of one court."""

    file_number: str
    status: str
    last_seen_at: datetime | None
    closed_at: datetime | None = None
    deleted: bool = False
    dates: tuple[datetime, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"Unbekannter Status {self.status!r}.")
        for moment in (self.last_seen_at, self.closed_at, *self.dates):
            if moment is not None and moment.tzinfo is None:
                raise ValueError("Zeitangaben müssen eine Zeitzone tragen.")


def _aware(now: datetime) -> datetime:
    if now.tzinfo is None:
        raise ValueError("Zeitangaben müssen eine Zeitzone tragen.")
    return now


def mark_seen(
    cases: Iterable[CaseState], listed_file_numbers: Iterable[str], now: datetime
) -> list[CaseState]:
    """Bump ``last_seen_at`` of every listed case (deleted or closed ones included)."""
    now = _aware(now)
    listed = {n for n in listed_file_numbers if n}
    out = []
    for case in cases:
        out.append(replace(case, last_seen_at=now) if case.file_number in listed else case)
    return out


def closing_status(case: CaseState, now: datetime) -> str:
    """``abgehalten`` if only past dates exist, otherwise ``aufgehoben``."""
    past = any(d < now for d in case.dates)
    upcoming = any(d >= now for d in case.dates)
    return "abgehalten" if past and not upcoming else "aufgehoben"


def close_vanished(
    cases: Iterable[CaseState], now: datetime, grace_days: int = 3
) -> tuple[list[CaseState], int]:
    """Close vanished open cases after the grace period; returns cases and count."""
    now = _aware(now)
    if isinstance(grace_days, bool) or not isinstance(grace_days, int) or grace_days < 0:
        raise ValueError("grace_days muss eine ganze Zahl ≥ 0 sein.")
    limit = now - timedelta(days=grace_days)
    out: list[CaseState] = []
    closed = 0
    for case in cases:
        if (
            not case.deleted
            and case.status in OPEN
            and case.last_seen_at is not None
            and case.last_seen_at < limit
        ):
            out.append(replace(case, status=closing_status(case, now), closed_at=now))
            closed += 1
        else:
            out.append(case)
    return out, closed


def status_for_date(termin: datetime | None, now: datetime) -> str:
    """Open status of a listed notice: ``terminiert`` for a date at or after ``now``."""
    now = _aware(now)
    return "terminiert" if (termin is not None and termin >= now) else "erfasst"


def reappear(case: CaseState, termin: datetime | None, now: datetime) -> CaseState:
    """Original upsert of a listed case: reopen, set last seen, replace the dates."""
    now = _aware(now)
    return replace(
        case,
        status=status_for_date(termin, now),
        last_seen_at=now,
        closed_at=None,
        dates=() if termin is None else (termin,),
    )


__all__ = [
    "CLOSED",
    "OPEN",
    "STATUSES",
    "CaseState",
    "close_vanished",
    "closing_status",
    "mark_seen",
    "reappear",
    "status_for_date",
]
