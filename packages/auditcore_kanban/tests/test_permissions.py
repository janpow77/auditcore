from __future__ import annotations

import pytest

from auditcore_kanban import (
    ROLE_ACTIONS,
    Action,
    Board,
    authorize,
    check_revoke,
    check_share,
    role_of,
)


@pytest.mark.parametrize(("user", "role"), [("u1", "owner"), ("u2", "edit"), ("u3", "read"),
                                            ("u9", None)])
def test_roles(board: Board, user: str, role: str | None) -> None:
    assert role_of(board, user) == role


def test_board_share_beats_inherited_grant(board: Board) -> None:
    inherited = {"u3": "edit", "u4": "read"}
    assert role_of(board, "u3", inherited) == "read"
    assert role_of(board, "u4", inherited) == "read"


@pytest.mark.parametrize(("user", "action", "code"), [
    ("u1", Action.SHARE, "OK"), ("u2", Action.MOVE_CARD, "OK"), ("u2", Action.RENAME, "OK"),
    ("u2", Action.CONFIGURE, "FORBIDDEN"), ("u3", Action.READ, "OK"),
    ("u3", Action.EDIT_CARD, "FORBIDDEN"), ("u9", Action.READ, "NOT_VISIBLE"),
])
def test_authorize(board: Board, user: str, action: Action, code: str) -> None:
    assert authorize(board, user, action).code == code


def test_role_table_is_monotonic() -> None:
    assert ROLE_ACTIONS["read"] < ROLE_ACTIONS["edit"] < ROLE_ACTIONS["owner"]


@pytest.mark.parametrize(("actor", "target", "permission", "code"), [
    ("u1", "u5", "read", "OK"), ("u1", "u5", "write", "INVALID_PERMISSION"),
    ("u1", "u1", "edit", "SELF_SHARE"), ("u2", "u5", "read", "FORBIDDEN"),
    ("u9", "u5", "read", "NOT_VISIBLE"),
])
def test_check_share(board: Board, actor: str, target: str, permission: str, code: str) -> None:
    assert check_share(board, actor, target, permission).code == code


@pytest.mark.parametrize(("actor", "target", "code"), [
    ("u1", "u2", "OK"), ("u3", "u3", "OK"), ("u2", "u3", "FORBIDDEN"),
    ("u1", "u7", "SHARE_NOT_FOUND"),
])
def test_check_revoke(board: Board, actor: str, target: str, code: str) -> None:
    assert check_revoke(board, actor, target).code == code
