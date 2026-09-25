"""Access model as pure logic: who may read, move, edit, configure and share a board.

Roles follow audit_designer: ``owner``, ``edit``, ``read``. A user without a
role does not see the board at all (``NOT_VISIBLE``, REST 404 like the
original); a visible user lacking the right gets ``FORBIDDEN`` (403).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from .errors import ALLOWED, Decision, deny
from .model import PERMISSIONS, Board


class Action(StrEnum):
    READ = "read"
    CREATE_CARD = "create_card"
    EDIT_CARD = "edit_card"
    MOVE_CARD = "move_card"
    DELETE_CARD = "delete_card"
    RENAME = "rename"
    CONFIGURE = "configure"
    SHARE = "share"
    DELETE_BOARD = "delete_board"
    PIN = "pin"


_CARD_WORK = frozenset(
    {Action.READ, Action.CREATE_CARD, Action.EDIT_CARD, Action.MOVE_CARD, Action.DELETE_CARD}
)

#: Declarative role table; ``configure``, ``share``, ``delete_board``, ``pin`` are owner-only.
ROLE_ACTIONS: Mapping[str, frozenset[Action]] = {
    "owner": frozenset(Action),
    "edit": _CARD_WORK | {Action.RENAME},
    "read": frozenset({Action.READ}),
}


def role_of(board: Board, user_id: str, inherited: Mapping[str, str] | None = None) -> str | None:
    """Role of ``user_id``: owner, the board's own share, else an inherited grant.

    ``inherited`` maps user ids to a permission granted on a container (the
    notebook in audit_designer). A board share takes precedence over it, as in
    ``get_accessible_page_or_404``.
    """
    if user_id == board.owner_id:
        return "owner"
    share = board.share_for(user_id)
    if share is not None:
        return share.permission
    if inherited is not None:
        return inherited.get(user_id)
    return None


def allowed_actions(role: str | None) -> frozenset[Action]:
    """Actions of a role (empty for no or an unknown role)."""
    if role is None:
        return frozenset()
    return ROLE_ACTIONS.get(role, frozenset())


def authorize(
    board: Board, user_id: str, action: Action, inherited: Mapping[str, str] | None = None
) -> Decision:
    """Decision for one action of one user on one board."""
    role = role_of(board, user_id, inherited)
    if role not in ROLE_ACTIONS:
        return deny("NOT_VISIBLE", "Board nicht gefunden")
    if action in allowed_actions(role):
        return ALLOWED
    if role == "read":
        return deny("FORBIDDEN", "Nur Lesezugriff auf dieses Board")
    return deny("FORBIDDEN", "Nur der Eigentümer darf das")


def check_share(board: Board, actor: str, target_user: str, permission: str) -> Decision:
    """Owner-only sharing with a valid permission and never with oneself."""
    decision = authorize(board, actor, Action.SHARE)
    if not decision.allowed:
        return decision
    if permission not in PERMISSIONS:
        return deny(
            "INVALID_PERMISSION",
            f"Ungültige Berechtigung. Erlaubt: {sorted(PERMISSIONS)}",
        )
    if target_user == actor or target_user == board.owner_id:
        return deny("SELF_SHARE", "Kann nicht mit sich selbst geteilt werden")
    return ALLOWED


def check_revoke(board: Board, actor: str, target_user: str) -> Decision:
    """Owner revokes every share; a recipient may remove their own share."""
    if board.share_for(target_user) is None:
        return deny("SHARE_NOT_FOUND", "Freigabe nicht gefunden")
    if actor == board.owner_id or actor == target_user:
        return ALLOWED
    return deny("FORBIDDEN", "Keine Berechtigung")
