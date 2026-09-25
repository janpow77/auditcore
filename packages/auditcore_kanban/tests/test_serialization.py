from __future__ import annotations

import json
from dataclasses import replace

import pytest

from auditcore_kanban import (
    SCHEMA_VERSION,
    Board,
    KanbanError,
    TransitionPolicy,
    board_from_json,
    board_schema,
    board_to_json,
    dumps,
    loads,
)
from auditcore_kanban.model import Attachment, CardLink, ChecklistItem, Label


def _rich(board: Board) -> Board:
    card = replace(board.cards[0], checklist=(ChecklistItem("x", True),),
                   links=(CardLink("notebook-page", "p1", "Seite"),),
                   attachments=(Attachment("f1", "a.pdf", "application/pdf", 12),),
                   extra={"generated_prompt": "p", "n": [1, {"a": None}]}, due="2026-10-01")
    policy = TransitionPolicy(allowed=frozenset({("offen", "erledigt")}),
                              locked_columns=frozenset({"in_arbeit"}),
                              fixed_order_columns=frozenset({"erledigt"}))
    return replace(board, cards=(card,) + board.cards[1:], transitions=policy, wip_mode="warn",
                   labels=(Label("l1", "Wichtig"),), extra={"k": "v"})


def test_roundtrip(board: Board) -> None:
    rich = _rich(board)
    again = loads(dumps(rich))
    assert board_to_json(again) == board_to_json(rich)
    assert again.transitions == rich.transitions and again.wip_mode == "warn"


def test_document_shape_matches_schema(board: Board) -> None:
    document = board_to_json(_rich(board))
    schema = board_schema()
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert set(document) == set(properties)
    assert document["schema_version"] == SCHEMA_VERSION
    defs = schema["$defs"]
    assert isinstance(defs, dict)
    card_props = defs["card"]["properties"]  # type: ignore[index,call-overload]
    cards = document["cards"]
    assert isinstance(cards, list) and isinstance(cards[0], dict)
    assert set(cards[0]) == set(card_props)
    transitions = document["transitions"]
    assert transitions == {"mode": "restricted", "allowed": [["offen", "erledigt"]],
                           "locked_columns": ["in_arbeit"],
                           "fixed_order_columns": ["erledigt"]}


def test_schema_validates_with_jsonschema_if_available(board: Board) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(board_to_json(_rich(board)), board_schema())


def test_free_mode_ignores_allowed(board: Board) -> None:
    document = board_to_json(board)
    document["transitions"] = {"mode": "free", "allowed": [["a", "b"]]}
    assert board_from_json(document).transitions.allowed is None


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(schema_version="x/2"), lambda d: d.update(columns=[]),
    lambda d: d.update(title=3), lambda d: d.update(version=True),
    lambda d: d.update(wip_mode="soft"), lambda d: d.update(transitions={"mode": "x"}),
    lambda d: d.update(transitions={"mode": "restricted", "allowed": [["a"]]}),
    lambda d: d["cards"][0].update(tags="x"), lambda d: d["cards"][0].update(extra=[1]),
    lambda d: d.update(cards={}),
])
def test_invalid_documents(board: Board, mutate: object) -> None:
    document = json.loads(json.dumps(board_to_json(board)))
    mutate(document)  # type: ignore[operator]
    with pytest.raises(KanbanError) as error:
        board_from_json(document)
    assert error.value.code == "INVALID_DOCUMENT"


def test_loads_rejects_bad_json() -> None:
    with pytest.raises(KanbanError, match="INVALID_DOCUMENT"):
        loads("{")
    with pytest.raises(KanbanError, match="INVALID_DOCUMENT"):
        board_from_json([])
