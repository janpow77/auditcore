"""Shared builders for the auditcore_kanban tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from auditcore_kanban import Board, Card, Column, Context, Share

FIXTURES = Path(__file__).parent / "fixtures"
NOW = "2026-09-25T12:00:00+00:00"


def make_card(cid: str, column: str, rank: str, **fields: Any) -> Card:
    return Card(cid, column, rank, fields.pop("title", cid.upper()),
                created_at=fields.pop("created_at", "2026-09-01"), **fields)


def make_board(**changes: Any) -> Board:
    columns = (Column("offen", "Offen"), Column("in_arbeit", "In Arbeit", wip_limit=2),
               Column("erledigt", "Erledigt"))
    cards = (make_card("a", "offen", "V"), make_card("b", "offen", "k"),
             make_card("c", "in_arbeit", "V"), make_card("d", "erledigt", "V"))
    board = Board("b1", "Board", "u1", columns, cards,
                  shares=(Share("u2", "edit", "u1"), Share("u3", "read", "u1")), version=1)
    return replace(board, **changes)


def ctx(actor: str = "u1", **kwargs: Any) -> Context:
    counter = iter(range(1, 10_000))
    return Context(actor, NOW, new_id=lambda: f"n{next(counter)}", **kwargs)


def order(board: Board, column: str) -> list[str]:
    return [c.id for c in board.cards_in(column)]


@pytest.fixture
def board() -> Board:
    return make_board()
