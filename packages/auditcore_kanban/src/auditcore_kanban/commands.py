"""Pure card commands: each checks rights, validation, transitions and WIP and
returns the new board plus the changes (no I/O)."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace

from .card_fields import as_optional_str, parse_card_fields, with_fields
from .errors import JsonObject, KanbanError
from .events import Change
from .model import Board, Card, done_column, first_column
from .permissions import Action, authorize
from .rank import is_strictly_increasing, rank_between, spread_ranks
from .rules import check_capacity, check_move
from .validation import DEFAULT_LIMITS, Limits


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass(frozen=True)
class Context:
    """Who acts, when, with which inherited grants and limits."""

    actor: str
    now: str
    inherited: Mapping[str, str] | None = None
    limits: Limits = DEFAULT_LIMITS
    new_id: Callable[[], str] = _new_id


@dataclass(frozen=True)
class CommandResult:
    board: Board
    changes: tuple[Change, ...]
    card: Card | None = None
    warnings: tuple[str, ...] = ()
    changed_cards: tuple[Card, ...] = field(default=())


def require(board: Board, ctx: Context, action: Action) -> None:
    authorize(board, ctx.actor, action, ctx.inherited).raise_if_denied()


def bump(board: Board, ctx: Context, cards: tuple[Card, ...] | None = None) -> Board:
    """Next version of the board."""
    return replace(
        board,
        cards=board.cards if cards is None else cards,
        version=board.version + 1,
        updated_at=ctx.now,
    )


def get_card(board: Board, card_id: str) -> Card:
    card = board.card(card_id)
    if card is None:
        raise KanbanError("CARD_NOT_FOUND", "Karte nicht gefunden")
    return card


# -- placement ---------------------------------------------------------------


def resolve_slot(
    siblings: tuple[Card, ...],
    before_id: str | None = None,
    after_id: str | None = None,
    index: int | None = None,
) -> int:
    """Insert position among ``siblings`` (default: end; index is clamped)."""
    ids = [c.id for c in siblings]
    for anchor, offset in ((before_id, 0), (after_id, 1)):
        if anchor is not None:
            if anchor not in ids:
                raise KanbanError("INVALID_REQUEST", "Bezugskarte liegt nicht in der Zielspalte")
            return ids.index(anchor) + offset
    if index is None:
        return len(siblings)
    return max(0, min(index, len(siblings)))


def place(siblings: tuple[Card, ...], slot: int) -> tuple[str, dict[str, str]]:
    """Rank for a card at ``slot``; rebalances the column only if ranks collide."""
    ranks = [c.rank for c in siblings]
    if is_strictly_increasing(ranks):
        low = ranks[slot - 1] if slot > 0 else None
        high = ranks[slot] if slot < len(ranks) else None
        return rank_between(low, high), {}
    keys = spread_ranks(len(siblings) + 1)
    own = keys.pop(slot)
    return own, {card.id: key for card, key in zip(siblings, keys, strict=True)}


def _apply_ranks(cards: tuple[Card, ...], ranks: Mapping[str, str]) -> tuple[Card, ...]:
    return tuple(replace(c, rank=ranks[c.id]) if c.id in ranks else c for c in cards)


def _rebalanced(board: Board, ranks: Mapping[str, str]) -> tuple[Card, ...]:
    return tuple(c for c in board.cards if c.id in ranks)


# -- commands ----------------------------------------------------------------


def create_card(board: Board, ctx: Context, fields: Mapping[str, object]) -> CommandResult:
    """New card in ``column_id`` (default first column), appended unless a slot is given."""
    require(board, ctx, Action.CREATE_CARD)
    column_id = as_optional_str("column_id", fields.get("column_id")) or first_column(board).id
    capacity = check_capacity(board, column_id)
    capacity.raise_if_denied()
    values = parse_card_fields(fields, ctx.limits)
    if "title" not in values:
        raise KanbanError("VALIDATION_ERROR", "Titel darf nicht leer sein")
    card_id = as_optional_str("id", fields.get("id")) or ctx.new_id()
    if board.card(card_id) is not None:
        raise KanbanError("VALIDATION_ERROR", "Karten-ID existiert bereits")
    siblings = board.cards_in(column_id)
    slot = _slot_from(fields, siblings)
    rank, moved = place(siblings, slot)
    base = Card(card_id, column_id, rank, str(values["title"]),
                created_at=ctx.now, updated_at=ctx.now)
    card = with_fields(base, values)
    cards = _apply_ranks(board.cards, moved) + (card,)
    new_board = bump(board, ctx, cards)
    changes = (Change("card.created", card.id, {"column_id": column_id, "rank": rank}),)
    return CommandResult(new_board, changes + _rebalance_change(moved), card,
                         capacity.warnings, _rebalanced(new_board, moved))


def _slot_from(fields: Mapping[str, object], siblings: tuple[Card, ...]) -> int:
    index = fields.get("index")
    if index is not None and (isinstance(index, bool) or not isinstance(index, int)):
        raise KanbanError("INVALID_REQUEST", "Feld 'index' hat einen ungültigen Typ")
    return resolve_slot(
        siblings,
        before_id=as_optional_str("before_id", fields.get("before_id")),
        after_id=as_optional_str("after_id", fields.get("after_id")),
        index=index,
    )


def _rebalance_change(ranks: Mapping[str, str]) -> tuple[Change, ...]:
    if not ranks:
        return ()
    data: JsonObject = {"ranks": {k: v for k, v in ranks.items()}}
    return (Change("column.rebalanced", None, data),)


def move_card(
    board: Board,
    ctx: Context,
    card_id: str,
    column_id: str,
    *,
    before_id: str | None = None,
    after_id: str | None = None,
    index: int | None = None,
) -> CommandResult:
    """Move into ``column_id`` before/after a card or at ``index`` (default: end)."""
    require(board, ctx, Action.MOVE_CARD)
    card = get_card(board, card_id)
    decision = check_move(board, card, column_id)
    decision.raise_if_denied()
    siblings = tuple(c for c in board.cards_in(column_id) if c.id != card_id)
    slot = resolve_slot(siblings, before_id, after_id, index)
    rank, moved = place(siblings, slot)
    updated = replace(card, column_id=column_id, rank=rank, updated_at=ctx.now)
    cards = tuple(updated if c.id == card_id else c for c in _apply_ranks(board.cards, moved))
    new_board = bump(board, ctx, cards)
    data: JsonObject = {"from": card.column_id, "to": column_id, "rank": rank, "index": slot}
    changes = (Change("card.moved", card_id, data),) + _rebalance_change(moved)
    return CommandResult(new_board, changes, updated, decision.warnings,
                         _rebalanced(new_board, moved))


def update_card(
    board: Board, ctx: Context, card_id: str, fields: Mapping[str, object]
) -> CommandResult:
    """Change card fields; a different ``column_id`` moves the card to that column's end."""
    require(board, ctx, Action.EDIT_CARD)
    values = parse_card_fields(fields, ctx.limits)
    card = get_card(board, card_id)
    target = as_optional_str("column_id", fields.get("column_id"))
    base, prefix = board, None
    if target is not None and target != card.column_id:
        prefix = move_card(board, ctx, card_id, target)
        base = prefix.board
    updated = with_fields(replace(get_card(base, card_id), updated_at=ctx.now), values)
    cards = tuple(updated if c.id == card_id else c for c in base.cards)
    new_board = replace(base, cards=cards) if prefix else bump(base, ctx, cards)
    changes = prefix.changes if prefix else ()
    warnings = prefix.warnings if prefix else ()
    data: JsonObject = {"fields": [n for n in sorted(values)]}
    change = Change("card.updated", card_id, data)
    return CommandResult(new_board, changes + (change,), updated, warnings)


def delete_card(board: Board, ctx: Context, card_id: str) -> CommandResult:
    require(board, ctx, Action.DELETE_CARD)
    card = get_card(board, card_id)
    cards = tuple(c for c in board.cards if c.id != card_id)
    change = Change("card.deleted", card_id, {"column_id": card.column_id})
    return CommandResult(bump(board, ctx, cards), (change,), card)


def toggle_done(board: Board, ctx: Context, card_id: str) -> CommandResult:
    """Done column -> top of the first column; otherwise -> end of the done column."""
    card = get_card(board, card_id)
    done = done_column(board)
    if card.column_id == done.id:
        return move_card(board, ctx, card_id, first_column(board).id, index=0)
    return move_card(board, ctx, card_id, done.id)
