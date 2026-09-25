"""Movement rules: column transitions, locked columns, fixed order and WIP limits."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ALLOWED, Decision, deny
from .model import Board, Card


@dataclass(frozen=True)
class WipState:
    column_id: str
    count: int
    limit: int | None

    @property
    def full(self) -> bool:
        return self.limit is not None and self.count >= self.limit

    @property
    def over(self) -> bool:
        return self.limit is not None and self.count > self.limit


def column_load(board: Board, column_id: str, exclude_card_id: str | None = None) -> int:
    """Number of cards in a column, not counting the card being moved."""
    return sum(1 for c in board.cards if c.column_id == column_id and c.id != exclude_card_id)


def wip_states(board: Board) -> tuple[WipState, ...]:
    """Current load against the limit for every column."""
    return tuple(
        WipState(col.id, column_load(board, col.id), col.wip_limit) for col in board.columns
    )


def check_capacity(board: Board, column_id: str, exclude_card_id: str | None = None) -> Decision:
    """Can one more card enter ``column_id``? Warn mode allows it with a warning."""
    column = board.column(column_id)
    if column is None:
        return deny("UNKNOWN_COLUMN", f"Unbekannte Spalte '{column_id}'")
    if column.wip_limit is None:
        return ALLOWED
    if column_load(board, column_id, exclude_card_id) < column.wip_limit:
        return ALLOWED
    if board.wip_mode == "warn":
        return Decision(True, warnings=("WIP_LIMIT_REACHED",))
    return deny(
        "WIP_LIMIT_REACHED",
        f"WIP-Limit der Spalte „{column.label}“ ({column.wip_limit}) ist erreicht",
    )


def check_transition(board: Board, source: str, target: str) -> Decision:
    """Column change rule without capacity (``source == target`` is a reorder)."""
    policy = board.transitions
    if board.column(target) is None:
        return deny("UNKNOWN_COLUMN", f"Unbekannte Spalte '{target}'")
    if source == target:
        if source in policy.fixed_order_columns:
            return deny("ORDER_FIXED", "Die Reihenfolge dieser Spalte ist fest")
        return ALLOWED
    if source in policy.locked_columns:
        return deny("COLUMN_LOCKED", "Karten dieser Spalte können nicht verschoben werden")
    if policy.allowed is not None and (source, target) not in policy.allowed:
        message = f"Übergang von '{source}' nach '{target}' ist nicht erlaubt"
        return deny("TRANSITION_NOT_ALLOWED", message)
    return ALLOWED


def check_move(board: Board, card: Card, target: str) -> Decision:
    """Full rule set for moving ``card`` into ``target`` (transition, then WIP)."""
    decision = check_transition(board, card.column_id, target)
    if not decision.allowed or card.column_id == target:
        return decision
    return check_capacity(board, target, exclude_card_id=card.id)


def movable_targets(board: Board, card: Card) -> tuple[str, ...]:
    """Columns the card may currently be moved into (keyboard/menu helpers)."""
    return tuple(
        col.id
        for col in board.columns
        if col.id != card.column_id and check_move(board, card, col.id).allowed
    )
