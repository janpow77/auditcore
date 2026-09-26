"""Generate the Python/TypeScript parity fixtures (tests/fixtures/parity/*.json).

    python tools/build_parity_fixtures.py            # write
    python tools/build_parity_fixtures.py --check    # compare, exit 1 on drift

Every file is a JSON list of ``{"name", "input", "expected"}``; inputs are pure
JSON (boards in the ``auditcore_kanban.board/1`` shape). ``expected`` is what
this Python package decides; ``@auditcore/kanban-core`` must decide the same.
Format: docs/kanban/parity-fixtures.md.
"""

from __future__ import annotations

import json
import random
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from auditcore_kanban import (
    Action,
    Board,
    Card,
    CardFilter,
    Column,
    Context,
    KanbanError,
    TransitionPolicy,
    authorize,
    board_from_json,
    board_to_json,
    check_capacity,
    check_move,
    check_revoke,
    check_share,
    configure_columns,
    create_card,
    deadline_state,
    filter_cards,
    group_by_value,
    is_valid_rank,
    move_card,
    rank_between,
    role_of,
    spread_ranks,
    toggle_done,
)
from auditcore_kanban import validation as v
from auditcore_kanban.card_fields import parse_card_fields
from auditcore_kanban.serialization import columns_from_json

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "parity"
NOW = "2026-09-25T12:00:00+00:00"
Case = dict[str, Any]


def case(name: str, input_: Any, expected: Any) -> Case:
    return {"name": name, "input": input_, "expected": expected}


# -- boards ---------------------------------------------------------------------


def card(cid: str, column: str, rank: str, **fields: Any) -> Card:
    return Card(
        cid, column, rank, fields.pop("title", cid.upper()), created_at="2026-09-01", **fields
    )


def base_board(**changes: Any) -> Board:
    columns = (
        Column("offen", "Offen"),
        Column("in_arbeit", "In Arbeit", wip_limit=2),
        Column("erledigt", "Erledigt", "#10b981"),
    )
    cards = (
        card(
            "a",
            "offen",
            "V",
            title="Prüfbericht Entwurf",
            tags=("VP", "Bericht"),
            priority="hoch",
            due="2026-09-20",
            badge="VP-19",
            assignees=("u2",),
        ),
        card(
            "b",
            "offen",
            "k",
            title="Belegliste anfordern",
            description="Straße prüfen",
            due="2026-09-27",
        ),
        card(
            "c",
            "in_arbeit",
            "V",
            title="Vergabe prüfen",
            priority="niedrig",
            tags=("Vergabe",),
            due="2026-10-30",
        ),
        card("d", "erledigt", "V", title="Kick-off", assignees=("u3",)),
    )
    board = Board("b1", "Prüfung 2026", "u1", columns, cards, version=3)
    for key, value in changes.items():
        board = _replace(board, key, value)
    return board


def _replace(board: Board, key: str, value: Any) -> Board:
    from dataclasses import replace

    return replace(board, **{key: value})


def bj(board: Board) -> Any:
    return board_to_json(board)


# -- rank -----------------------------------------------------------------------


def _rank_result(a: str | None, b: str | None) -> Any:
    try:
        return rank_between(a, b)
    except ValueError as error:
        return {"error": "INVALID_RANK" if "invalid" in str(error) else "INVALID_RANK_ORDER"}


def rank_cases() -> list[Case]:
    pairs = [
        (None, None),
        (None, "V"),
        ("V", None),
        ("A", "B"),
        ("A", "C"),
        ("V", "V1"),
        ("0V", "1"),
        ("z", None),
        ("zz", None),
        (None, "01"),
        (None, "001"),
        ("a", "a1"),
        ("Az", "B"),
        ("y1", "z"),
        ("V", "V"),
        ("W", "V"),
        ("V0", None),
        ("", "V"),
        ("A!", None),
        ("V", "W"),
        ("V", "V01"),
    ]
    cases = [
        case(f"between {a!r} {b!r}", {"op": "between", "a": a, "b": b}, _rank_result(a, b))
        for a, b in pairs
    ]
    cases += [
        case(f"spread {n}", {"op": "spread", "count": n}, spread_ranks(n))
        for n in (0, 1, 2, 3, 5, 10, 61, 62, 100)
    ]
    cases += [
        case(f"valid {k!r}", {"op": "valid", "key": k}, is_valid_rank(k))
        for k in ("V", "V0", "", "0", "a1", "a-", "zzzz", "Ä")
    ]
    rng = random.Random(20260925)
    keys: list[str] = []
    steps: list[Any] = []
    for _ in range(60):
        slot = rng.randint(0, len(keys))
        low = keys[slot - 1] if slot > 0 else None
        high = keys[slot] if slot < len(keys) else None
        new = rank_between(low, high)
        keys.insert(slot, new)
        steps.append({"a": low, "b": high, "key": new})
    cases.append(case("random insert sequence", {"op": "sequence", "steps": steps}, keys))
    return cases


# -- rules ----------------------------------------------------------------------


def _policy_boards() -> dict[str, Board]:
    restricted = TransitionPolicy(
        allowed=frozenset({("offen", "in_arbeit"), ("in_arbeit", "erledigt")})
    )
    return {
        "free": base_board(),
        "restricted": base_board(transitions=restricted),
        "locked": base_board(transitions=TransitionPolicy(locked_columns=frozenset({"in_arbeit"}))),
        "fixed": base_board(transitions=TransitionPolicy(fixed_order_columns=frozenset({"offen"}))),
        "warn": base_board(wip_mode="warn"),
    }


def transition_cases() -> list[Case]:
    moves = [
        ("a", "offen"),
        ("a", "in_arbeit"),
        ("a", "erledigt"),
        ("c", "offen"),
        ("c", "erledigt"),
        ("d", "offen"),
        ("b", "gibt_es_nicht"),
    ]
    cases = []
    for name, board in _policy_boards().items():
        full = _replace(board, "cards", board.cards + (card("e", "in_arbeit", "k"),))
        for label, variant in ((name, board), (f"{name}+full", full)):
            for card_id, target in moves:
                subject = variant.card(card_id)
                assert subject is not None
                cases.append(
                    case(
                        f"{label}: {card_id}->{target}",
                        {"board": bj(variant), "card_id": card_id, "target": target},
                        check_move(variant, subject, target).to_json(),
                    )
                )
    return cases


def wip_cases() -> list[Case]:
    cases = []
    for name, board in (("block", base_board()), ("warn", base_board(wip_mode="warn"))):
        full = _replace(board, "cards", board.cards + (card("e", "in_arbeit", "k"),))
        for label, variant in ((name, board), (f"{name}+full", full)):
            for column, exclude in (
                ("in_arbeit", None),
                ("in_arbeit", "c"),
                ("offen", None),
                ("nope", None),
            ):
                cases.append(
                    case(
                        f"{label}: {column} without {exclude}",
                        {"board": bj(variant), "column_id": column, "exclude_card_id": exclude},
                        check_capacity(variant, column, exclude).to_json(),
                    )
                )
    return cases


def filter_cases() -> list[Case]:
    board = base_board()
    filters: list[tuple[str, dict[str, Any]]] = [
        ("empty", {}),
        ("query title", {"query": "prüf"}),
        ("query case", {"query": "VERGABE"}),
        ("query description umlaut", {"query": "STRASSE"}),
        ("query ß", {"query": "straße"}),
        ("query tag", {"query": "bericht"}),
        ("query badge", {"query": "vp-19"}),
        ("query spaces", {"query": "  kick  "}),
        ("priority", {"priorities": ["hoch", "niedrig"]}),
        ("tags", {"tags": ["Vergabe"]}),
        ("assignee", {"assignees": ["u3"]}),
        ("columns", {"columns": ["offen"]}),
        ("overdue", {"due_states": ["overdue"]}),
        ("due soon or none", {"due_states": ["due_soon", "none"]}),
        ("combined", {"query": "prüf", "priorities": ["hoch"]}),
    ]
    cases = []
    for name, raw in filters:
        criteria = CardFilter(
            query=raw.get("query", ""),
            **{
                k: frozenset(raw.get(k, []))
                for k in ("priorities", "tags", "assignees", "columns", "due_states")
            },
        )
        ids = [c.id for c in filter_cards(board, criteria, date(2026, 9, 25))]
        cases.append(case(name, {"board": bj(board), "filter": raw, "today": "2026-09-25"}, ids))
    return cases


STATUS = ["offen", "in Prüfung", "erledigt"]
RECORD_PROPERTIES: list[dict[str, Any]] = [
    {"id": "titel", "name": "Titel", "type": "text"},
    {"id": "status", "name": "Status", "type": "select", "options": STATUS},
    {"id": "fonds", "name": "Fonds", "type": "select", "options": ["EFRE", "ESF+", "JTF"]},
    {"id": "betrag", "name": "Betrag", "type": "number"},
]


def _row(rid: str, title: str, status: Any, fonds: Any, **cells: Any) -> dict[str, Any]:
    return {"id": rid, "cells": {"titel": title, "status": status, "fonds": fonds, **cells}}


RECORD_ROWS: list[dict[str, Any]] = [
    _row("r1", "Vorhaben A", "offen", "EFRE", betrag=1200),
    _row("r2", "Vorhaben B", "erledigt", "ESF+", betrag=80),
    _row("r3", "Vorhaben C", None, "EFRE", betrag=0),
    _row("r4", "Vorhaben D", "in Prüfung", "unbekannt"),
    _row("r5", "Vorhaben E", "", 7),
    _row("r6", "Vorhaben F", "offen", ["EFRE"]),
]


def _record_key(row: dict[str, Any], prop: str) -> str | None:
    value = row["cells"].get(prop)
    return str(value) if isinstance(value, (str, int)) and not isinstance(value, bool) else None


def _group_case(name: str, rows: list[dict[str, Any]], prop: str) -> Case:
    options = next(p["options"] for p in RECORD_PROPERTIES if p["id"] == prop)
    groups = group_by_value(rows, lambda r: _record_key(r, prop), options)
    table = {"properties": RECORD_PROPERTIES, "rows": rows}
    expected = [[value, [r["id"] for r in items]] for value, items in groups]
    return case(name, {"table": table, "group_by": prop}, expected)


def group_cases() -> list[Case]:
    """Datenbankansicht (useDbKanban): Gruppierung nach einer Auswahl-Eigenschaft."""
    complete = [r for r in RECORD_ROWS if r["cells"].get("status") in ("offen", "erledigt")]
    return [
        _group_case("status", RECORD_ROWS, "status"),
        _group_case("fonds unbekannt und kein Text", RECORD_ROWS, "fonds"),
        _group_case("ohne leere Spalte", complete, "status"),
    ]


def deadline_cases() -> list[Case]:
    values = [
        None,
        "",
        "2026-09-24",
        "2026-09-25",
        "2026-09-28",
        "2026-09-29",
        "2026-09-25T23:59:00",
        "2026-09-25T00:00:00Z",
        "kaputt",
        "2026-02-30",
    ]
    return [
        case(f"due {d!r}", {"due": d, "today": "2026-09-25"}, deadline_state(d, date(2026, 9, 25)))
        for d in values
    ]


# -- permissions ------------------------------------------------------------------


def permission_cases() -> list[Case]:
    from auditcore_kanban import Share

    board = base_board(cards=(), shares=(Share("u2", "edit", "u1"), Share("u3", "read", "u1")))
    cases = []
    inherited_sets: list[dict[str, str] | None] = [None, {"u4": "edit", "u3": "edit"}]
    for inherited in inherited_sets:
        for user in ("u1", "u2", "u3", "u4", "u9"):
            for action in Action:
                decision = authorize(board, user, action, inherited)
                cases.append(
                    case(
                        f"{user} {action.value} inherited={bool(inherited)}",
                        {
                            "op": "authorize",
                            "board": bj(board),
                            "user_id": user,
                            "action": action.value,
                            "inherited": inherited,
                        },
                        {"role": role_of(board, user, inherited), "decision": decision.to_json()},
                    )
                )
    for actor, target, permission in (
        ("u1", "u5", "read"),
        ("u1", "u5", "write"),
        ("u1", "u1", "edit"),
        ("u2", "u5", "read"),
        ("u9", "u5", "read"),
        ("u1", "u2", "read"),
    ):
        cases.append(
            case(
                f"share {actor}->{target} {permission}",
                {
                    "op": "share",
                    "board": bj(board),
                    "actor": actor,
                    "target_user": target,
                    "permission": permission,
                },
                check_share(board, actor, target, permission).to_json(),
            )
        )
    for actor, target in (("u1", "u2"), ("u3", "u3"), ("u2", "u3"), ("u1", "u7")):
        cases.append(
            case(
                f"revoke {actor}->{target}",
                {"op": "revoke", "board": bj(board), "actor": actor, "target_user": target},
                check_revoke(board, actor, target).to_json(),
            )
        )
    return cases


# -- validation -------------------------------------------------------------------


def _outcome(fn: Callable[[], Any]) -> Any:
    try:
        return {"ok": True, "value": fn()}
    except KanbanError as error:
        return {"ok": False, "code": error.code, "message": error.message}


def validation_cases() -> list[Case]:
    fields: list[tuple[str, dict[str, Any]]] = [
        ("title ok", {"title": "  Titel  "}),
        ("title empty", {"title": "   "}),
        ("title 300", {"title": "x" * 300}),
        ("title 301", {"title": "x" * 301}),
        ("description 10000", {"description": "d" * 10000}),
        ("description 10001", {"description": "d" * 10001}),
        ("tags 20", {"tags": [f"t{i}" for i in range(20)]}),
        ("tags 21", {"tags": [f"t{i}" for i in range(21)]}),
        ("tag 80", {"tags": ["t" * 80]}),
        ("tag 81", {"tags": ["t" * 81]}),
        ("priority ok", {"priority": "hoch"}),
        ("priority bad", {"priority": "dringend"}),
        ("due date", {"due": "2026-09-30"}),
        ("due z", {"due": "2026-09-30T10:00:00Z"}),
        ("due bad", {"due": "30.09.2026"}),
        ("due empty", {"due": ""}),
        ("badge 20", {"badge": "B" * 20}),
        ("badge 21", {"badge": "B" * 21}),
        ("badge empty", {"badge": ""}),
        ("color empty", {"color": ""}),
        ("tags wrong type", {"tags": "VP"}),
        ("checklist", {"checklist": [{"text": "a", "done": True}]}),
    ]
    cases = [
        case(
            name,
            {"op": "card_fields", "fields": raw},
            _outcome(lambda raw=raw: _jsonable(parse_card_fields(raw, v.DEFAULT_LIMITS))),
        )
        for name, raw in fields
    ]

    def col(i: str, label: str = "L", **extra: Any) -> dict[str, Any]:
        return {"id": i, "label": label, **extra}

    column_sets: list[tuple[str, list[dict[str, Any]]]] = [
        ("columns 0", []),
        ("columns 1", [col("a")]),
        ("columns 10", [col(f"c{i}") for i in range(10)]),
        ("columns 11", [col(f"c{i}") for i in range(11)]),
        ("duplicate", [col("a"), col("a")]),
        ("duplicate after strip", [col(" a"), col("a")]),
        ("upper id", [col("A")]),
        ("leading dash", [col("-a")]),
        ("space", [col("a b")]),
        ("underscore start", [col("_a")]),
        ("50 chars", [col("a" * 50)]),
        ("51 chars", [col("a" * 51)]),
        ("mixed ok", [col("a_-9")]),
        ("empty label", [col("a", "  ")]),
        ("label 80", [col("a", "L" * 80)]),
        ("label 81", [col("a", "L" * 81)]),
        ("wip 0", [col("a", wip_limit=0)]),
        ("wip 1", [col("a", wip_limit=1)]),
    ]
    cases += [
        case(
            name,
            {"op": "columns", "columns": raw},
            _outcome(
                lambda raw=raw: [
                    _jsonable_column(c) for c in v.validate_columns(columns_from_json(raw))
                ]
            ),
        )
        for name, raw in column_sets
    ]
    return cases


def _jsonable_column(column: Column) -> Any:
    from auditcore_kanban.serialization import column_to_json

    return column_to_json(column)


def _jsonable(values: dict[str, object]) -> Any:
    out: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, tuple):
            out[key] = [x.__dict__ if hasattr(x, "__dict__") else x for x in value]
        else:
            out[key] = value
    return out


# -- commands ---------------------------------------------------------------------


def _orders(board: Board) -> Any:
    return {col.id: [[c.id, c.rank] for c in board.cards_in(col.id)] for col in board.columns}


def command_cases() -> list[Case]:
    board = base_board()
    ctx = Context("u1", NOW, new_id=lambda: "new")
    ops: list[tuple[str, dict[str, Any], Callable[[Board], Any]]] = [
        (
            "move to top",
            {"op": "move", "card_id": "b", "column_id": "offen", "index": 0},
            lambda b: move_card(b, ctx, "b", "offen", index=0),
        ),
        (
            "move before",
            {"op": "move", "card_id": "d", "column_id": "offen", "before_id": "b"},
            lambda b: move_card(b, ctx, "d", "offen", before_id="b"),
        ),
        (
            "move after",
            {"op": "move", "card_id": "d", "column_id": "offen", "after_id": "b"},
            lambda b: move_card(b, ctx, "d", "offen", after_id="b"),
        ),
        (
            "move end default",
            {"op": "move", "card_id": "a", "column_id": "erledigt"},
            lambda b: move_card(b, ctx, "a", "erledigt"),
        ),
        (
            "move index clamp",
            {"op": "move", "card_id": "a", "column_id": "erledigt", "index": 99},
            lambda b: move_card(b, ctx, "a", "erledigt", index=99),
        ),
        (
            "move negative",
            {"op": "move", "card_id": "d", "column_id": "offen", "index": -3},
            lambda b: move_card(b, ctx, "d", "offen", index=-3),
        ),
        ("toggle done", {"op": "toggle_done", "card_id": "a"}, lambda b: toggle_done(b, ctx, "a")),
        (
            "toggle reopen",
            {"op": "toggle_done", "card_id": "d"},
            lambda b: toggle_done(b, ctx, "d"),
        ),
        (
            "create end",
            {"op": "create", "fields": {"title": "Neu", "column_id": "offen"}},
            lambda b: create_card(b, ctx, {"title": "Neu", "column_id": "offen"}),
        ),
        (
            "create index",
            {"op": "create", "fields": {"title": "Neu", "index": 1}},
            lambda b: create_card(b, ctx, {"title": "Neu", "index": 1}),
        ),
        (
            "configure remove",
            {
                "op": "configure",
                "columns": [
                    {"id": "offen", "label": "Offen"},
                    {"id": "erledigt", "label": "Erledigt"},
                ],
            },
            lambda b: configure_columns(
                b, ctx, (Column("offen", "Offen"), Column("erledigt", "Erledigt"))
            ),
        ),
    ]
    dup = _replace(
        board,
        "cards",
        tuple(_replace_card(c, "V") if c.column_id == "offen" else c for c in board.cards),
    )
    cases = []
    for name, input_, fn in ops:
        result = fn(board)
        cases.append(
            case(
                name,
                {"board": bj(board), "actor": "u1", "now": NOW, "new_id": "new", **input_},
                {"orders": _orders(result.board), "version": result.board.version},
            )
        )
    rebalance = move_card(dup, ctx, "d", "offen", index=1)
    cases.append(
        case(
            "move with duplicate ranks rebalances",
            {
                "board": bj(dup),
                "actor": "u1",
                "now": NOW,
                "op": "move",
                "card_id": "d",
                "column_id": "offen",
                "index": 1,
            },
            {"orders": _orders(rebalance.board), "version": rebalance.board.version},
        )
    )
    return cases


def _replace_card(c: Card, rank: str) -> Card:
    from dataclasses import replace

    return replace(c, rank=rank)


BUILDERS: dict[str, Callable[[], list[Case]]] = {
    "rank": rank_cases,
    "transitions": transition_cases,
    "wip": wip_cases,
    "filter": filter_cases,
    "deadline": deadline_cases,
    "permissions": permission_cases,
    "validation": validation_cases,
    "commands": command_cases,
    "group": group_cases,
}


def render(name: str) -> str:
    return json.dumps(BUILDERS[name](), ensure_ascii=False, indent=1) + "\n"


def main() -> int:
    check = "--check" in sys.argv
    drift = []
    for name in BUILDERS:
        path = OUT / f"{name}.json"
        text = render(name)
        board_from_json(json.loads(json.dumps(bj(base_board()))))
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                drift.append(name)
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if drift:
        print("drift:", ", ".join(drift))
        return 1
    print("parity fixtures", "ok" if check else "written", f"({len(BUILDERS)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
