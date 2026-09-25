from __future__ import annotations

from dataclasses import replace

import pytest
from conftest import ctx, make_board, make_card, order

from auditcore_kanban import (
    Board,
    KanbanError,
    TransitionPolicy,
    create_card,
    delete_card,
    move_card,
    toggle_done,
    update_card,
)
from auditcore_kanban.rank import is_strictly_increasing


def test_create_appends_and_bumps_version(board: Board) -> None:
    result = create_card(board, ctx(), {"title": "  Neu  ", "column_id": "offen", "tags": ["x"]})
    assert order(result.board, "offen") == ["a", "b", "n1"]
    assert result.card is not None and result.card.title == "Neu" and result.card.tags == ("x",)
    assert result.board.version == board.version + 1
    assert [c.kind for c in result.changes] == ["card.created"]


def test_create_defaults_to_first_column_and_slot(board: Board) -> None:
    result = create_card(board, ctx(), {"title": "Neu", "index": 0})
    assert order(result.board, "offen") == ["n1", "a", "b"]
    before = create_card(board, ctx(), {"title": "Neu", "before_id": "b"})
    assert order(before.board, "offen") == ["a", "n1", "b"]


@pytest.mark.parametrize(("fields", "code"), [
    ({}, "VALIDATION_ERROR"), ({"title": " "}, "VALIDATION_ERROR"),
    ({"title": "x", "priority": "dringend"}, "VALIDATION_ERROR"),
    ({"title": "x", "column_id": "nope"}, "UNKNOWN_COLUMN"),
    ({"title": "x", "tags": "VP"}, "INVALID_REQUEST"),
    ({"title": "x", "index": "1"}, "INVALID_REQUEST"),
    ({"title": "x", "id": "a"}, "VALIDATION_ERROR"),
    ({"title": "x", "before_id": "c"}, "INVALID_REQUEST"),
])
def test_create_rejects(board: Board, fields: dict[str, object], code: str) -> None:
    with pytest.raises(KanbanError) as error:
        create_card(board, ctx(), fields)
    assert error.value.code == code


def test_create_respects_wip_and_rights(board: Board) -> None:
    full = replace(board, cards=board.cards + (make_card("e", "in_arbeit", "k"),))
    with pytest.raises(KanbanError, match="WIP_LIMIT_REACHED"):
        create_card(full, ctx(), {"title": "x", "column_id": "in_arbeit"})
    with pytest.raises(KanbanError, match="FORBIDDEN"):
        create_card(board, ctx("u3"), {"title": "x"})
    with pytest.raises(KanbanError, match="NOT_VISIBLE"):
        create_card(board, ctx("u9"), {"title": "x"})


@pytest.mark.parametrize(("kwargs", "expected"), [
    ({"index": 0}, ["d", "a", "b"]), ({"index": -4}, ["d", "a", "b"]),
    ({"index": 99}, ["a", "b", "d"]), ({}, ["a", "b", "d"]),
    ({"before_id": "b"}, ["a", "d", "b"]), ({"after_id": "a"}, ["a", "d", "b"]),
])
def test_move_positions(board: Board, kwargs: dict[str, object], expected: list[str]) -> None:
    result = move_card(board, ctx("u2"), "d", "offen", **kwargs)  # type: ignore[arg-type]
    assert order(result.board, "offen") == expected
    assert order(result.board, "erledigt") == []
    assert result.changes[0].data["from"] == "erledigt"


def test_move_within_column_changes_only_one_rank(board: Board) -> None:
    result = move_card(board, ctx(), "b", "offen", index=0)
    assert order(result.board, "offen") == ["b", "a"]
    changed = {c.id for c in result.board.cards if c not in board.cards}
    assert changed == {"b"}


def test_move_rebalances_duplicate_ranks(board: Board) -> None:
    dup = replace(board, cards=tuple(replace(c, rank="V") for c in board.cards))
    result = move_card(dup, ctx(), "d", "offen", index=1)
    assert order(result.board, "offen") == ["a", "d", "b"]
    ranks = [c.rank for c in result.board.cards_in("offen")]
    assert is_strictly_increasing(ranks)
    assert {c.id for c in result.changed_cards} == {"a", "b"}
    assert [c.kind for c in result.changes] == ["card.moved", "column.rebalanced"]


def test_move_rules(board: Board) -> None:
    with pytest.raises(KanbanError, match="FORBIDDEN"):
        move_card(board, ctx("u3"), "a", "erledigt")
    locked = replace(board, transitions=TransitionPolicy(locked_columns=frozenset({"offen"})))
    with pytest.raises(KanbanError, match="COLUMN_LOCKED"):
        move_card(locked, ctx(), "a", "erledigt")
    with pytest.raises(KanbanError, match="CARD_NOT_FOUND"):
        move_card(board, ctx(), "zz", "erledigt")
    warn = replace(board, wip_mode="warn",
                   cards=board.cards + (make_card("e", "in_arbeit", "k"),))
    assert move_card(warn, ctx(), "a", "in_arbeit").warnings == ("WIP_LIMIT_REACHED",)


def test_update_fields_and_clear_semantics(board: Board) -> None:
    card = replace(board.cards[0], color="#fff", badge="VP-1", due="2026-10-01")
    staged = replace(board, cards=(card,) + board.cards[1:])
    result = update_card(staged, ctx("u2"), "a", {
        "title": "Neu", "color": "", "badge": "", "due": None, "priority": "hoch",
        "checklist": [{"text": "x", "done": True}],
        "links": [{"kind": "notebook-page", "target": "p1"}],
        "attachments": [{"id": "f", "filename": "a.pdf", "size": 3}],
        "extra": {"generated_prompt": "…"},
    })
    updated = result.card
    assert updated is not None
    assert (updated.title, updated.color, updated.badge, updated.due) == ("Neu", None, None, None)
    assert updated.checklist[0].done and updated.links[0].kind == "notebook-page"
    assert updated.attachments[0].size == 3 and updated.extra == {"generated_prompt": "…"}
    assert result.changes[-1].data["fields"] == sorted(
        ["title", "color", "badge", "due", "priority", "checklist", "links", "attachments",
         "extra"])


def test_update_with_column_moves_to_end(board: Board) -> None:
    result = update_card(board, ctx(), "a", {"column_id": "erledigt", "title": "T"})
    assert order(result.board, "erledigt") == ["d", "a"]
    assert result.board.version == board.version + 1
    assert [c.kind for c in result.changes] == ["card.moved", "card.updated"]


@pytest.mark.parametrize("fields", [
    {"checklist": [{"text": "x", "done": "ja"}]}, {"attachments": [{"id": "f",
                                                                   "filename": "a", "size": -1}]},
    {"extra": {"x": object()}}, {"links": "x"}, {"due": "30.09.2026"},
])
def test_update_rejects_bad_types(board: Board, fields: dict[str, object]) -> None:
    with pytest.raises(KanbanError):
        update_card(board, ctx(), "a", fields)


def test_delete_and_toggle_done(board: Board) -> None:
    deleted = delete_card(board, ctx("u2"), "b")
    assert order(deleted.board, "offen") == ["a"]
    done = toggle_done(board, ctx(), "a")
    assert order(done.board, "erledigt") == ["d", "a"]
    reopened = toggle_done(board, ctx(), "d")
    assert order(reopened.board, "offen") == ["d", "a", "b"]


def test_toggle_done_prefers_flagged_done_column() -> None:
    board = make_board()
    cols = (board.columns[0], replace(board.columns[1], done=True), board.columns[2])
    flagged = replace(board, columns=cols)
    assert order(toggle_done(flagged, ctx(), "a").board, "in_arbeit")[-1] == "a"
