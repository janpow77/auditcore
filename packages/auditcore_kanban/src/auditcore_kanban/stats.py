"""Counts per column and progress (done column, else last column – audit_designer)."""

from __future__ import annotations

from .errors import JsonObject, JsonValue
from .model import Board, done_column


def percent(part: int, total: int) -> int:
    """Rounded percentage, half up (same as JavaScript ``Math.round``)."""
    if total <= 0:
        return 0
    return (200 * part + total) // (2 * total)


def board_stats(board: Board) -> JsonObject:
    """``total``, ``by_column``, ``done`` and ``progress`` (0–100)."""
    by_column: dict[str, JsonValue] = {}
    for column in board.columns:
        by_column[column.id] = sum(1 for c in board.cards if c.column_id == column.id)
    known = sum(1 for c in board.cards if board.column(c.column_id) is not None)
    done_id = done_column(board).id
    done = sum(1 for c in board.cards if c.column_id == done_id)
    return {
        "total": known,
        "by_column": by_column,
        "done_column": done_id,
        "done": done,
        "progress": percent(done, known),
    }


def checklist_progress(done: int, total: int) -> JsonObject:
    """Checklist counter of a card."""
    return {"done": done, "total": total, "percent": percent(done, total)}
