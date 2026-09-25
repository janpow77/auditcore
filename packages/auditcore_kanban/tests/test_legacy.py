from __future__ import annotations

from auditcore_kanban import export_board_columns, export_workspace_tasks, import_workspace
from auditcore_kanban.rank import is_strictly_increasing

PAGE = {"id": "p1", "notebook_id": "nb", "title": "Board", "icon": "🔍", "owner_user_id": 1,
        "is_pinned": True, "board_columns": None, "created_at": "2026-01-01T00:00:00"}


def _task(tid: str, status: str, position: int, created: str, **extra: object) -> dict[str, object]:
    return {"id": tid, "title": tid, "status": status, "position": position,
            "created_at": created, "priority": "mittel", "tags": ["a"], **extra}


def test_import_orders_by_position_then_created_at() -> None:
    tasks = [_task("c", "offen", 2, "2026-01-03"), _task("a", "offen", 1, "2026-01-02"),
             _task("b", "offen", 1, "2026-01-01"), _task("x", "erledigt", 1, "2026-01-01",
                                                          deadline="2026-02-01T00:00:00",
                                                          card_color="", badge="VP-1",
                                                          checklist=[{"text": "t", "done": True}],
                                                          generated_prompt="p", file_count=2),
             _task("z", "archiv", 1, "2026-01-01")]
    shares = [{"shared_with_user_id": 2, "permission": "write", "shared_by_user_id": 1}]
    board = import_workspace(PAGE, tasks, shares)
    assert board.owner_id == "1" and board.pinned and board.icon == "🔍"
    assert [c.id for c in board.columns] == ["offen", "in_arbeit", "erledigt"]
    assert [c.id for c in board.cards_in("offen")] == ["b", "a", "c", "z"]
    assert is_strictly_increasing([c.rank for c in board.cards_in("offen")][:3])
    z = board.card("z")
    x = board.card("x")
    assert z is not None and z.extra["legacy_status"] == "archiv"
    assert x is not None and x.color is None and x.badge == "VP-1" and x.checklist[0].done
    assert x.extra["generated_prompt"] == "p" and x.due == "2026-02-01T00:00:00"
    assert board.shares[0].permission == "edit" and board.shares[0].user_id == "2"


def test_export_roundtrip_positions() -> None:
    page = {**PAGE, "board_columns": [{"id": "todo", "label": "To-Do", "color": "#3b82f6"}]}
    board = import_workspace(page, [_task("a", "todo", 5, "1"), _task("b", "todo", 9, "2")])
    rows = export_workspace_tasks(board)
    assert [(r["id"], r["status"], r["position"]) for r in rows] == [("a", "todo", 1),
                                                                    ("b", "todo", 2)]
    assert export_board_columns(board) == [{"id": "todo", "label": "To-Do", "color": "#3b82f6"}]
