"""Search, filters, deadline state and grouping of records by a property."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import TypeVar

from .model import Board, Card

T = TypeVar("T")

DUE_SOON_DAYS = 3
DUE_STATES: tuple[str, ...] = ("none", "overdue", "due_soon", "later")


def parse_due_date(due: str | None) -> date | None:
    """Date part of an ISO date or date-time string; None if missing or invalid."""
    if not due:
        return None
    try:
        return date.fromisoformat(due[:10])
    except ValueError:
        return None


def deadline_state(due: str | None, today: date) -> str:
    """``none``, ``overdue``, ``due_soon`` (≤ 3 days) or ``later`` (WorkspaceTaskCard)."""
    due_date = parse_due_date(due)
    if due_date is None:
        return "none"
    days = (due_date - today).days
    if days < 0:
        return "overdue"
    if days <= DUE_SOON_DAYS:
        return "due_soon"
    return "later"


@dataclass(frozen=True)
class CardFilter:
    """All given criteria must hold; an empty criterion matches everything."""

    query: str = ""
    priorities: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()
    assignees: frozenset[str] = frozenset()
    columns: frozenset[str] = frozenset()
    due_states: frozenset[str] = frozenset()


def matches_query(card: Card, query: str) -> bool:
    """Case-insensitive substring search in title, description, tags and badge."""
    needle = query.strip().lower()
    if not needle:
        return True
    haystacks = [card.title, card.description, card.badge or "", *card.tags]
    return any(needle in text.lower() for text in haystacks)


def _intersects(values: Sequence[str], wanted: frozenset[str]) -> bool:
    return not wanted or any(v in wanted for v in values)


def matches(card: Card, criteria: CardFilter, today: date) -> bool:
    """True if ``card`` satisfies every criterion."""
    checks = (
        matches_query(card, criteria.query),
        not criteria.priorities or card.priority in criteria.priorities,
        _intersects(card.tags, criteria.tags),
        _intersects(card.assignees, criteria.assignees),
        not criteria.columns or card.column_id in criteria.columns,
        not criteria.due_states or deadline_state(card.due, today) in criteria.due_states,
    )
    return all(checks)


def filter_cards(board: Board, criteria: CardFilter, today: date) -> tuple[Card, ...]:
    """Matching cards in board order (columns, then rank)."""
    return tuple(c for c in board.ordered_cards() if matches(c, criteria, today))


def group_by_value(
    items: Sequence[T], key: Callable[[T], str | None], options: Sequence[str]
) -> list[tuple[str, list[T]]]:
    """Group items into one bucket per option (useDbKanban).

    Items with an empty or unknown value go into a leading ``""`` bucket that
    only exists when it is not empty.
    """
    buckets: list[tuple[str, list[T]]] = [(o, [i for i in items if key(i) == o]) for o in options]
    unassigned = [i for i in items if (key(i) or "") not in options]
    if unassigned:
        buckets.insert(0, ("", unassigned))
    return buckets
