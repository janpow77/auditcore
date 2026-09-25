"""The library against the executed original (tests/fixtures/legacy_kanban_observed.json).

Same decision where the contract is the same; deliberate changes are pinned
here with their observed legacy value and explained in docs/behavior-changes.md.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest
from conftest import FIXTURES, NOW

from auditcore_kanban import (
    Board,
    Column,
    Context,
    KanbanError,
    Share,
    authorize,
    check_revoke,
    check_share,
    configure_columns,
    create_card,
    delete_card,
    move_card,
    update_card,
    validate_columns,
)
from auditcore_kanban.permissions import Action
from auditcore_kanban.validation import (
    normalize_due,
    validate_description,
    validate_tags,
    validate_title,
)

DATA = json.loads((FIXTURES / "legacy_kanban_observed.json").read_text(encoding="utf-8"))
CASES = {c["name"]: c for c in DATA["observations"]}


def by_kind(kind: str) -> list[dict[str, Any]]:
    return [c for c in DATA["observations"] if c["kind"] == kind]


def outcome(fn: Callable[[], object]) -> tuple[int, str | None]:
    try:
        fn()
    except KanbanError as error:
        return 400 if error.status in (400, 422) else error.status, error.message
    return 200, None


def test_source_binding() -> None:
    assert DATA["source"]["commit"] == "2c726f3c1481775cd34aeaa83f87137d6ab12ffe"
    assert {f["git_blob"] for f in DATA["source"]["files"]} == {
        "ccdb57dd3677b36fb4212c5347c2cfcd0096cabe", "b2ecd79398c77c13b450331642074840d535ca6c"}
    assert DATA["cases"] == len(DATA["observations"]) == 77


@pytest.mark.parametrize("item", by_kind("task_payload"), ids=lambda c: c["name"])
def test_task_payload_validation_matches(item: dict[str, Any]) -> None:
    payload = item["input"]

    def run() -> None:
        if "title" in payload:
            validate_title(payload["title"])
        if "description" in payload:
            validate_description(payload["description"])
        if "tags" in payload:
            validate_tags(payload["tags"])

    observed = item["observed"]
    assert outcome(run) == (observed["status"], observed.get("detail"))


@pytest.mark.parametrize("item", by_kind("columns"), ids=lambda c: c["name"])
def test_column_validation_matches(item: dict[str, Any]) -> None:
    columns = [Column(c["id"], c["label"]) for c in item["input"]]
    observed = item["observed"]
    assert outcome(lambda: validate_columns(columns)) == (observed["status"],
                                                          observed.get("detail"))
    if observed["status"] == 200:
        checked = validate_columns(columns)
        assert [(c.id, c.label) for c in checked] == [(c["id"], c["label"])
                                                      for c in observed["result"]]


#: Deliberate change: an empty deadline on create clears instead of failing (B4).
DUE_CHANGED = {"deadline '' clear=False"}


@pytest.mark.parametrize("item", by_kind("deadline"), ids=lambda c: c["name"])
def test_deadline_parsing(item: dict[str, Any]) -> None:
    observed = item["observed"]
    value = item["input"]["value"]
    status, _ = outcome(lambda: normalize_due(value))
    if item["name"] in DUE_CHANGED:
        assert observed["status"] == 400 and status == 200
        return
    assert status == observed["status"]
    if status == 200 and value:
        assert normalize_due(value) is not None
        assert str(observed["result"]).startswith(value[:10])


# -- ordering --------------------------------------------------------------------


def legacy_board() -> Board:
    ctx = Context("1", NOW, new_id=iter("ABCX").__next__)
    board = Board("p", "Board", "1", version=1)
    for title, column in (("A", "offen"), ("B", "offen"), ("C", "offen"), ("X", "in_arbeit")):
        board = create_card(board, ctx, {"title": title, "column_id": column}).board
    return board


def titles(board: Board) -> dict[str, list[str]]:
    return {c.id: [x.title for x in board.cards_in(c.id)] for c in board.columns
            if board.cards_in(c.id)}


def observed_titles(name: str) -> dict[str, list[str]]:
    columns = CASES[name]["observed"]["columns"]
    return {k: [t for t, _ in v] for k, v in columns.items()}


CTX = Context("1", NOW, new_id=lambda: "D")
SAME: dict[str, Callable[[Board], Board]] = {
    "create three": lambda b: b,
    "move C to position 1": lambda b: move_card(b, CTX, "C", "offen", index=0).board,
    "move A to position 0": lambda b: move_card(b, CTX, "A", "offen", index=max(1, 0) - 1).board,
    "move A to position -5": lambda b: move_card(b, CTX, "A", "offen", index=-5).board,
    "move A to position 99": lambda b: move_card(b, CTX, "A", "offen", index=98).board,
    "move B to in_arbeit 1": lambda b: move_card(b, CTX, "B", "in_arbeit", index=0).board,
    "move B to in_arbeit 2": lambda b: move_card(b, CTX, "B", "in_arbeit", index=1).board,
    "update status without position":
        lambda b: update_card(b, CTX, "C", {"column_id": "in_arbeit"}).board,
    "update status and position": lambda b: move_card(b, CTX, "C", "in_arbeit", index=0).board,
    "update clear deadline": lambda b: update_card(b, CTX, "C", {"due": ""}).board,
    "update badge empty": lambda b: update_card(b, CTX, "C", {"badge": ""}).board,
    "delete middle": lambda b: delete_card(b, CTX, "B").board,
    "create ignores position": lambda b: create_card(b, CTX, {"title": "D"}).board,
}


@pytest.mark.parametrize("name", sorted(SAME))
def test_ordering_matches(name: str) -> None:
    assert titles(SAME[name](legacy_board())) == observed_titles(name)


def test_update_position_tie_is_a_deliberate_change() -> None:
    """Original: position=1 on update ties with A and sorts after it (created earlier)."""
    for name in ("update position 1 same column", "update position 0"):
        assert observed_titles(name)["offen"] == ["A", "C", "B"]
    moved = move_card(legacy_board(), CTX, "C", "offen", index=0).board
    assert titles(moved)["offen"] == ["C", "A", "B"]


@pytest.mark.parametrize(("name", "code"), [
    ("move A to unknown status", "UNKNOWN_COLUMN"),
    ("update invalid priority", "VALIDATION_ERROR"),
    ("create invalid status", "UNKNOWN_COLUMN"),
])
def test_rejections_match(name: str, code: str) -> None:
    assert CASES[name]["observed"]["response"]["status"] == 400
    board = legacy_board()
    run = {
        "move A to unknown status": lambda: move_card(board, CTX, "A", "gibt_es_nicht"),
        "update invalid priority": lambda: update_card(board, CTX, "C", {"priority": "dringend"}),
        "create invalid status": lambda: create_card(board, CTX, {"title": "D",
                                                                  "column_id": "nope"}),
    }[name]
    with pytest.raises(KanbanError) as error:
        run()
    assert error.value.code == code and error.value.status == 400


def test_empty_deadline_on_create_is_a_deliberate_change() -> None:
    assert CASES["create empty deadline"]["observed"]["response"]["status"] == 400
    card = create_card(legacy_board(), CTX, {"title": "D", "due": ""}).card
    assert card is not None and card.due is None


# -- settings ------------------------------------------------------------------------


def test_removed_columns_move_to_first_column_but_are_appended() -> None:
    """Original interleaves by old position (A, X, B, Y); the library appends (A, B, X, Y)."""
    assert observed_titles("settings remove in_arbeit")["offen"] == ["A", "X", "B", "Y"]
    assert observed_titles("settings remove offen")["in_arbeit"] == ["A", "X", "B", "Y"]
    ctx = Context("1", NOW, new_id=iter("ABXY").__next__)
    board = Board("p", "Board", "1", version=1)
    for title, column in (("A", "offen"), ("B", "offen"), ("X", "in_arbeit"), ("Y", "in_arbeit")):
        board = create_card(board, ctx, {"title": title, "column_id": column}).board
    removed = configure_columns(board, ctx, (Column("offen", "Offen"),
                                             Column("erledigt", "Erledigt"))).board
    assert titles(removed)["offen"] == ["A", "B", "X", "Y"]
    first_removed = configure_columns(board, ctx, (Column("in_arbeit", "In Arbeit"),
                                                   Column("erledigt", "Erledigt"))).board
    assert titles(first_removed)["in_arbeit"] == ["X", "Y", "A", "B"]


def test_default_columns() -> None:
    observed = CASES["settings default columns"]["observed"]["result"]["columns"]
    assert [(c.id, c.label, c.color) for c in Board("p", "t", "1").columns] == [
        (c["id"], c["label"], c["color"]) for c in observed]


# -- access and sharing -------------------------------------------------------------------

ROLES_BOARD = Board("p", "Board", "1", shares=(Share("2", "edit"), Share("3", "read")))
INHERITED = {"4": "edit", "5": "read", "3": "edit"}
STATUS = {"OK": 200, "FORBIDDEN": 403, "NOT_VISIBLE": 404}


@pytest.mark.parametrize("item", by_kind("access"), ids=lambda c: c["name"])
def test_access_matches(item: dict[str, Any]) -> None:
    user = str(item["input"]["user"])
    observed = item["observed"]

    def status(action: Action) -> int:
        return STATUS[authorize(ROLES_BOARD, user, action, INHERITED).code]

    assert status(Action.READ) == observed["read"]
    assert status(Action.CREATE_CARD) == observed["write"]
    owner_only = status(Action.SHARE)
    if user == "1" or observed["read"] == 404:
        assert owner_only == observed["owner_only"]
    else:  # deliberate: visible non-owners get 403 instead of 404
        assert (observed["owner_only"], owner_only) == (404, 403)


SHARE_CODES = {"owner shares read": "OK", "owner shares write": "INVALID_PERMISSION",
               "owner shares self": "SELF_SHARE", "editor shares": "FORBIDDEN",
               "upsert existing": "OK"}


@pytest.mark.parametrize("name", sorted(SHARE_CODES))
def test_share_decisions(name: str) -> None:
    actor, target, permission = CASES[f"share {name}"]["input"]
    decision = check_share(ROLES_BOARD, str(actor), str(target), permission)
    assert decision.code == SHARE_CODES[name]
    observed = CASES[f"share {name}"]["observed"]
    if decision.code in ("INVALID_PERMISSION", "SELF_SHARE"):
        assert (observed["status"], observed["detail"]) == (400, decision.message)
    elif decision.allowed:
        assert observed["status"] == 200
    else:
        assert observed["status"] == 404  # deliberate: 403 for visible non-owners


@pytest.mark.parametrize("item", by_kind("revoke"), ids=lambda c: c["name"])
def test_revoke_matches(item: dict[str, Any]) -> None:
    actor, target = item["input"]
    decision = check_revoke(ROLES_BOARD, str(actor), str(target))
    observed = item["observed"]
    expected = {"OK": 200, "FORBIDDEN": 403, "SHARE_NOT_FOUND": 404}[decision.code]
    assert observed["status"] == expected
    if not decision.allowed:
        assert observed["detail"] == decision.message


def test_write_permission_is_rejected_like_the_backend() -> None:
    """The original share dialog sends 'write'; the backend rejects it (bug in the original)."""
    assert CASES["share owner shares write"]["observed"]["status"] == 400
    assert CASES["update share write"]["observed"]["status"] == 400
    assert not check_share(ROLES_BOARD, "1", "9", "write").allowed
