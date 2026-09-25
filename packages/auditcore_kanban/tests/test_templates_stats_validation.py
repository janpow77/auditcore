from __future__ import annotations

from dataclasses import replace

import pytest
from conftest import make_card

from auditcore_kanban import (
    TEMPLATES,
    Board,
    Column,
    KanbanError,
    board_stats,
    percent,
    validate_columns,
)
from auditcore_kanban.stats import checklist_progress
from auditcore_kanban.validation import Limits, normalize_due, validate_badge


def test_templates_are_valid_and_unique() -> None:
    assert [t.key for t in TEMPLATES][:7] == ["standard", "vorhabenpruefung", "sprint",
                                              "einfach", "systempruefung", "teamplanung",
                                              "jahresplanung"]
    for t in TEMPLATES:
        validate_columns(t.columns)
        assert t.to_json()["columns"]
    labels = {c.label for t in TEMPLATES for c in t.columns}
    assert "Prüfung" in labels and "Rückfrage / Freigabe" in labels


@pytest.mark.parametrize(("part", "total", "expected"), [(0, 0, 0), (1, 3, 33), (1, 2, 50),
                                                         (2, 3, 67), (1, 8, 13), (3, 3, 100)])
def test_percent_rounds_half_up(part: int, total: int, expected: int) -> None:
    assert percent(part, total) == expected


def test_board_stats(board: Board) -> None:
    stray = replace(board, cards=board.cards + (make_card("z", "weg", "V"),))
    stats = board_stats(stray)
    assert stats == {"total": 4, "by_column": {"offen": 2, "in_arbeit": 1, "erledigt": 1},
                     "done_column": "erledigt", "done": 1, "progress": 25}
    assert checklist_progress(1, 2) == {"done": 1, "total": 2, "percent": 50}


def test_limits_are_configurable() -> None:
    tight = Limits(columns_max=2)
    with pytest.raises(KanbanError, match="Maximal 2 Spalten"):
        validate_columns([Column(f"c{i}", "L") for i in range(3)], tight)
    with pytest.raises(KanbanError, match="WIP-Limit"):
        validate_columns([Column("a", "A", wip_limit=0)])


def test_due_and_badge() -> None:
    assert normalize_due("2026-09-30") == "2026-09-30"
    assert normalize_due("2026-09-30T10:00:00Z") == "2026-09-30T10:00:00+00:00"
    assert normalize_due("") is None
    assert validate_badge("") is None
    with pytest.raises(KanbanError, match="Badge ist zu lang"):
        validate_badge("B" * 21)
