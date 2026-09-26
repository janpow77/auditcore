from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from conftest import make_card

from auditcore_kanban import Board, CardFilter, deadline_state, filter_cards, group_by_value

TODAY = date(2026, 9, 25)


@pytest.mark.parametrize(("due", "state"), [
    (None, "none"), ("", "none"), ("kaputt", "none"), ("2026-09-24", "overdue"),
    ("2026-09-25", "due_soon"), ("2026-09-28", "due_soon"), ("2026-09-29", "later"),
    ("2026-09-25T23:59:00", "due_soon"),
])
def test_deadline_state(due: str | None, state: str) -> None:
    assert deadline_state(due, TODAY) == state


def _board(board: Board) -> Board:
    cards = (
        make_card("a", "offen", "V", title="Prüfbericht", tags=("VP",), priority="hoch",
                  badge="VP-19", assignees=("u2",), due="2026-09-20"),
        make_card("b", "offen", "k", title="Beleg", description="Straße prüfen"),
        make_card("c", "erledigt", "V", title="Kick-off", tags=("Team",)),
    )
    return replace(board, cards=cards)


@pytest.mark.parametrize(("criteria", "ids"), [
    (CardFilter(), ["a", "b", "c"]),
    (CardFilter(query="  PRÜF "), ["a", "b"]),
    (CardFilter(query="vp-19"), ["a"]),
    (CardFilter(query="team"), ["c"]),
    (CardFilter(query="strasse"), []),
    (CardFilter(priorities=frozenset({"hoch"})), ["a"]),
    (CardFilter(tags=frozenset({"Team"})), ["c"]),
    (CardFilter(assignees=frozenset({"u2"})), ["a"]),
    (CardFilter(columns=frozenset({"erledigt"})), ["c"]),
    (CardFilter(due_states=frozenset({"overdue"})), ["a"]),
])
def test_filter(board: Board, criteria: CardFilter, ids: list[str]) -> None:
    assert [c.id for c in filter_cards(_board(board), criteria, TODAY)] == ids


def test_group_by_value_puts_unassigned_first() -> None:
    rows = [{"s": "a"}, {"s": None}, {"s": "x"}, {"s": "b"}]
    groups = group_by_value(rows, lambda r: r["s"], ["a", "b"])
    assert [(k, len(v)) for k, v in groups] == [("", 2), ("a", 1), ("b", 1)]
    assert group_by_value([{"s": "a"}], lambda r: r["s"], ["a"]) == [("a", [{"s": "a"}])]
