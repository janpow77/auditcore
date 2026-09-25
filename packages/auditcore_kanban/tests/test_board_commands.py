from __future__ import annotations

from dataclasses import replace

import pytest
from conftest import ctx, order

from auditcore_kanban import (
    Board,
    Column,
    KanbanError,
    TransitionPolicy,
    configure_columns,
    create_board,
    respread_column,
    revoke_share,
    share_board,
    template,
    update_board,
)


def test_create_board_with_template() -> None:
    chosen = template("cockpit-auftraege")
    assert chosen is not None
    result = create_board(ctx("u7"), "b9", "Aufträge", board_template=chosen)
    board = result.board
    assert board.owner_id == "u7" and board.version == 1
    assert [c.id for c in board.columns] == ["eingang", "geplant", "laeuft", "rueckfrage",
                                             "fertig"]
    assert board.transitions.locked_columns == frozenset({"laeuft"})
    with pytest.raises(KanbanError):
        create_board(ctx(), "b9", "   ")


def test_update_board_rights(board: Board) -> None:
    renamed = update_board(board, ctx("u2"), title=" Neu ")
    assert renamed.board.title == "Neu"
    with pytest.raises(KanbanError, match="FORBIDDEN"):
        update_board(board, ctx("u2"), pinned=True)
    pinned = update_board(board, ctx(), pinned=True, archived=True, icon="🔍")
    assert pinned.board.pinned and pinned.board.archived and pinned.board.icon == "🔍"
    assert pinned.changes[0].data["fields"] == ["archived", "icon", "pinned"]


def test_configure_moves_cards_of_removed_columns_to_first_column_end(board: Board) -> None:
    policy = TransitionPolicy(allowed=frozenset({("offen", "in_arbeit"), ("offen", "erledigt")}),
                              locked_columns=frozenset({"in_arbeit"}))
    staged = replace(board, transitions=policy)
    result = configure_columns(staged, ctx(), (Column(" offen ", " Offen "),
                                               Column("erledigt", "Erledigt")))
    assert [c.id for c in result.board.columns] == ["offen", "erledigt"]
    assert order(result.board, "offen") == ["a", "b", "c"]
    assert result.board.transitions.allowed == frozenset({("offen", "erledigt")})
    assert result.board.transitions.locked_columns == frozenset()
    assert result.changes[0].data == {"removed": ["in_arbeit"], "moved_cards": ["c"]}


def test_configure_is_owner_only_and_validated(board: Board) -> None:
    with pytest.raises(KanbanError, match="FORBIDDEN"):
        configure_columns(board, ctx("u2"), board.columns)
    with pytest.raises(KanbanError, match="Mindestens eine Spalte"):
        configure_columns(board, ctx(), ())


def test_share_upsert_and_revoke(board: Board) -> None:
    created = share_board(board, ctx(), "u5", "read")
    assert created.changes[0].kind == "share.created"
    updated = share_board(created.board, ctx(), "u5", "edit")
    assert updated.changes[0].kind == "share.updated"
    assert [s.permission for s in updated.board.shares if s.user_id == "u5"] == ["edit"]
    revoked = revoke_share(updated.board, ctx("u5"), "u5")
    assert revoked.board.share_for("u5") is None
    with pytest.raises(KanbanError, match="FORBIDDEN"):
        revoke_share(board, ctx("u2"), "u3")


def test_respread_column(board: Board) -> None:
    result = respread_column(board, ctx(), "offen")
    assert order(result.board, "offen") == ["a", "b"]
    with pytest.raises(KanbanError, match="UNKNOWN_COLUMN"):
        respread_column(board, ctx(), "nope")
