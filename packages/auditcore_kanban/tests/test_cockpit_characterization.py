"""cockpit template against the executed original rules (cockpit_rules_observed.json)."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from conftest import FIXTURES

from auditcore_kanban import Board, Card, check_move, column_for_status, template

DATA = json.loads((FIXTURES / "cockpit_rules_observed.json").read_text(encoding="utf-8"))
OBSERVED = DATA["observed"]


def cockpit_board() -> Board:
    chosen = template("cockpit-auftraege")
    assert chosen is not None
    return Board("c", "Aufträge", "u1", chosen.columns, transitions=chosen.transitions)


def test_source_binding() -> None:
    assert DATA["source"]["commit"] == "df203d4c33e786eb8a8ad3fe53b3b7eb9241d406"


@pytest.mark.parametrize("status", sorted(OBSERVED["spalteVon"]))
def test_status_to_column(status: str) -> None:
    column = column_for_status(cockpit_board(), status)
    assert column is not None and column.id == OBSERVED["spalteVon"][status]


@pytest.mark.parametrize("status", sorted(OBSERVED["darfVerschieben"]))
def test_user_moves_match_darf_verschieben(status: str) -> None:
    board = cockpit_board()
    column = column_for_status(board, status)
    assert column is not None
    card = Card("k", column.id, "V", "Auftrag")
    staged = replace(board, cards=(card,))
    for target, allowed in OBSERVED["darfVerschieben"][status].items():
        assert check_move(staged, card, target).allowed is allowed, (status, target)


def test_running_jobs_are_locked() -> None:
    assert "laeuft" in OBSERVED["source_lines"]["running_status_change"]
    assert "409" in OBSERVED["source_lines"]["running_status_change_error"]
    board = cockpit_board()
    card = Card("k", "laeuft", "V", "Auftrag")
    decision = check_move(replace(board, cards=(card,)), card, "fertig")
    assert decision.code == "COLUMN_LOCKED"
