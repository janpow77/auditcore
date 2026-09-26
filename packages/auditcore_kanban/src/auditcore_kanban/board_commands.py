"""Pure board-level commands: create, rename/pin, configure columns, share, revoke."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from .commands import CommandResult, Context, bump, require
from .errors import JsonObject, KanbanError
from .events import Change
from .model import Board, Card, Column, Share, TransitionPolicy
from .permissions import Action, check_revoke, check_share
from .rank import rank_between, spread_ranks
from .templates import BoardTemplate
from .validation import validate_board_title, validate_columns


def create_board(
    ctx: Context,
    board_id: str,
    title: str = "Neues Board",
    icon: str = "📋",
    board_template: BoardTemplate | None = None,
) -> CommandResult:
    """New board owned by the acting user (default columns unless a template is given)."""
    board = Board(
        id=board_id,
        title=validate_board_title(title, ctx.limits),
        owner_id=ctx.actor,
        icon=icon,
        version=1,
        created_at=ctx.now,
        updated_at=ctx.now,
    )
    if board_template is not None:
        board = replace(
            board,
            columns=validate_columns(board_template.columns, ctx.limits),
            transitions=board_template.transitions,
        )
    data: JsonObject = {"template": board_template.key if board_template else None}
    return CommandResult(board, (Change("board.created", None, data),))


def update_board(
    board: Board,
    ctx: Context,
    *,
    title: str | None = None,
    icon: str | None = None,
    pinned: bool | None = None,
    archived: bool | None = None,
) -> CommandResult:
    """Rename (owner, edit), pin/archive (owner only)."""
    changed: list[str] = []
    if title is not None or icon is not None:
        require(board, ctx, Action.RENAME)
        board = replace(
            board,
            title=board.title if title is None else validate_board_title(title, ctx.limits),
            icon=board.icon if icon is None else icon,
        )
        changed += [n for n, v in (("title", title), ("icon", icon)) if v is not None]
    if pinned is not None or archived is not None:
        require(board, ctx, Action.PIN)
        board = replace(
            board,
            pinned=board.pinned if pinned is None else pinned,
            archived=board.archived if archived is None else archived,
        )
        changed += [n for n, v in (("pinned", pinned), ("archived", archived)) if v is not None]
    names = sorted(changed)
    data: JsonObject = {"fields": [n for n in names]}
    return CommandResult(bump(board, ctx), (Change("board.updated", None, data),))


def _restricted_policy(policy: TransitionPolicy, ids: set[str]) -> TransitionPolicy:
    allowed = None
    if policy.allowed is not None:
        allowed = frozenset(p for p in policy.allowed if p[0] in ids and p[1] in ids)
    return replace(
        policy,
        allowed=allowed,
        locked_columns=frozenset(policy.locked_columns & ids),
        fixed_order_columns=frozenset(policy.fixed_order_columns & ids),
    )


def _rehome(board: Board, removed: set[str], target: str) -> tuple[tuple[Card, ...], list[str]]:
    """Cards of removed columns go to the end of ``target`` in their previous order."""
    orphans = [c for col in board.columns if col.id in removed for c in board.cards_in(col.id)]
    if not orphans:
        return board.cards, []
    last = board.cards_in(target)
    low = last[-1].rank if last else None
    ranks: list[str] = []
    for _ in orphans:
        low = rank_between(low, None)
        ranks.append(low)
    new = {c.id: replace(c, column_id=target, rank=r) for c, r in zip(orphans, ranks, strict=True)}
    return tuple(new.get(c.id, c) for c in board.cards), [c.id for c in orphans]


def configure_columns(
    board: Board,
    ctx: Context,
    columns: Sequence[Column],
    transitions: TransitionPolicy | None = None,
) -> CommandResult:
    """Replace the column set (owner only); cards of removed columns move to the first column."""
    require(board, ctx, Action.CONFIGURE)
    checked = validate_columns(columns, ctx.limits)
    ids = {c.id for c in checked}
    removed = {c.id for c in board.columns} - ids
    policy = _restricted_policy(transitions or board.transitions, ids)
    staged = replace(board, columns=checked, transitions=policy)
    cards, moved = _rehome(board, removed, checked[0].id)
    data: JsonObject = {"removed": [c for c in sorted(removed)], "moved_cards": [c for c in moved]}
    return CommandResult(bump(staged, ctx, cards), (Change("board.configured", None, data),))


def share_board(
    board: Board, ctx: Context, user_id: str, permission: str
) -> CommandResult:
    """Grant or update (upsert) a share; the owner is the only one who may share."""
    check_share(board, ctx.actor, user_id, permission).raise_if_denied()
    existing = board.share_for(user_id)
    if existing is not None:
        shares = tuple(
            replace(s, permission=permission) if s.user_id == user_id else s for s in board.shares
        )
        kind = "share.updated"
    else:
        shares = board.shares + (Share(user_id, permission, ctx.actor, ctx.now),)
        kind = "share.created"
    data: JsonObject = {"user_id": user_id, "permission": permission}
    return CommandResult(bump(replace(board, shares=shares), ctx), (Change(kind, None, data),))


def revoke_share(board: Board, ctx: Context, user_id: str) -> CommandResult:
    """Owner revokes any share, a recipient their own."""
    check_revoke(board, ctx.actor, user_id).raise_if_denied()
    shares = tuple(s for s in board.shares if s.user_id != user_id)
    data: JsonObject = {"user_id": user_id}
    return CommandResult(
        bump(replace(board, shares=shares), ctx), (Change("share.revoked", None, data),)
    )


def respread_column(board: Board, ctx: Context, column_id: str) -> CommandResult:
    """Replace the ranks of one column by evenly spaced keys (keeps the order)."""
    require(board, ctx, Action.MOVE_CARD)
    if board.column(column_id) is None:
        raise KanbanError("UNKNOWN_COLUMN", f"Unbekannte Spalte '{column_id}'")
    ordered = board.cards_in(column_id)
    ranks = dict(zip((c.id for c in ordered), spread_ranks(len(ordered)), strict=True))
    cards = tuple(replace(c, rank=ranks[c.id]) if c.id in ranks else c for c in board.cards)
    data: JsonObject = {"ranks": {k: v for k, v in ranks.items()}}
    return CommandResult(bump(board, ctx, cards), (Change("column.rebalanced", None, data),))
