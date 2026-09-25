"""Cases for tools/capture_legacy_kanban.py (executed against the original code)."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

PAGE = "11111111-1111-4111-8111-111111111111"
NOTEBOOK = "22222222-2222-4222-8222-222222222222"
OWNER, EDITOR, READER, NB_EDITOR, NB_READER, STRANGER, INACTIVE = 1, 2, 3, 4, 5, 6, 7


class Env:
    def __init__(self, ws: Any, session_type: type, run: Callable[..., Any], exc: type) -> None:
        self.ws, self.session_type, self.run, self.exc = ws, session_type, run, exc
        self.models = __import__("app.models.vpai_notebook", fromlist=["x"])
        self.user_model = __import__("app.models.user", fromlist=["x"]).User

    def fresh(self, columns: list[dict[str, str]] | None = None) -> Any:
        db = self.session_type()
        m = self.models
        for uid in (OWNER, EDITOR, READER, NB_EDITOR, NB_READER, STRANGER, INACTIVE):
            db.add(self.user_model(id=uid, username=f"u{uid}", full_name=None,
                                   is_active=uid != INACTIVE, storage_quota_mb=100))
        db.add(m.VpaiNotebook(id=uuid.UUID(NOTEBOOK), name="NB", owner_user_id=OWNER))
        db.add(m.VpaiPage(id=uuid.UUID(PAGE), notebook_id=uuid.UUID(NOTEBOOK), title="Board",
                          page_type="workspace", icon="📋", owner_user_id=OWNER,
                          board_columns=columns))
        for uid, perm in ((EDITOR, "edit"), (READER, "read")):
            db.add(m.VpaiPageShare(id=uuid.uuid4(), page_id=uuid.UUID(PAGE),
                                   shared_with_user_id=uid, shared_by_user_id=OWNER,
                                   permission=perm))
        for uid, perm in ((NB_EDITOR, "edit"), (NB_READER, "read"), (READER, "edit")):
            db.add(m.VpaiNotebookShare(id=uuid.uuid4(), notebook_id=uuid.UUID(NOTEBOOK),
                                       shared_with_user_id=uid, permission=perm))
        return db

    def user(self, db: Any, uid: int) -> Any:
        return next(u for u in db.rows(self.user_model) if u.id == uid)

    def call(self, db: Any, name: str, uid: int, **kwargs: Any) -> dict[str, Any]:
        endpoint = getattr(self.ws, name)
        try:
            result = self.run(endpoint(db=db, current_user=self.user(db, uid), **kwargs))
        except self.exc as error:
            return {"status": error.status_code, "detail": error.detail}
        return {"status": 200, "result": _plain(result)}

    def columns(self, db: Any) -> dict[str, list[list[Any]]]:
        tasks = db.rows(self.models.VpaiWorkspaceTask)
        out: dict[str, list[list[Any]]] = {}
        for t in sorted(tasks, key=lambda t: (t.position, t.created_at)):
            out.setdefault(t.status, []).append([t.title, t.position])
        return dict(sorted(out.items()))

    def create(self, db: Any, title: str, status: str = "offen", **extra: Any) -> str:
        req = self.ws.WorkspaceTaskCreate(title=title, status=status, **extra)
        result = self.call(db, "create_task", OWNER, page_id=PAGE, req=req)
        return str(result["result"]["id"]) if result["status"] == 200 else ""


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "to_dict"):
        return {"id": str(value.id), "status": value.status, "position": value.position,
                "title": value.title}
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _compact(response: Any) -> Any:
    """Status plus the stable task fields (ids are random UUIDs)."""
    if not isinstance(response, dict):
        return response
    result = response.get("result")
    if isinstance(result, dict) and "position" in result:
        keep = ("title", "status", "position", "deadline", "badge", "priority")
        result = {k: result.get(k) for k in keep}
    return {"status": response["status"], "result": result, "detail": response.get("detail")}


def _outcome(env: Env, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        return {"status": 200, "result": _plain(fn())}
    except env.exc as error:
        return {"status": error.status_code, "detail": error.detail}


def validation_cases(env: Env) -> list[dict[str, Any]]:
    ws = env.ws
    payloads: list[tuple[str, dict[str, Any]]] = [
        ("title empty", {"title": ""}), ("title spaces", {"title": "   "}),
        ("title 300", {"title": "x" * 300}), ("title 301", {"title": "x" * 301}),
        ("title 300 padded", {"title": "  " + "x" * 300 + "  "}),
        ("description 10000", {"description": "d" * 10000}),
        ("description 10001", {"description": "d" * 10001}),
        ("tags 20", {"tags": [f"t{i}" for i in range(20)]}),
        ("tags 21", {"tags": [f"t{i}" for i in range(21)]}),
        ("tag 80", {"tags": ["t" * 80]}), ("tag 81", {"tags": ["t" * 81]}),
    ]
    cases = [{"name": f"payload {n}", "kind": "task_payload", "input": p,
              "observed": _outcome(env, lambda p=p: ws._validate_task_payload(**p))}
             for n, p in payloads]

    def col(i: str, label: str = "L") -> dict[str, str]:
        return {"id": i, "label": label}

    column_sets = [
        ("columns 0", []), ("columns 1", [col("a")]),
        ("columns 10", [col(f"c{i}") for i in range(10)]),
        ("columns 11", [col(f"c{i}") for i in range(11)]),
        ("duplicate", [col("a"), col("a")]), ("duplicate after strip", [col(" a"), col("a")]),
        ("upper id", [col("A")]), ("leading dash", [col("-a")]), ("space", [col("a b")]),
        ("underscore start", [col("_a")]), ("50 chars", [col("a" * 50)]),
        ("51 chars", [col("a" * 51)]), ("mixed ok", [col("a_-9")]),
        ("empty label", [col("a", "  ")]), ("label 80", [col("a", "L" * 80)]),
        ("label 81", [col("a", "L" * 81)]), ("label stripped", [col(" a ", " Offen ")]),
    ]
    cases += [{"name": f"columns {n}", "kind": "columns", "input": c,
               "observed": _outcome(env, lambda c=c: ws._validate_board_columns(
                   [ws.BoardColumnDef(**x) for x in c]))}
              for n, c in column_sets]
    deadlines = [("2026-09-30", False), ("2026-09-30T10:00:00", False),
                 ("2026-09-30T10:00:00Z", False), ("30.09.2026", False), ("", False),
                 ("", True), (None, False)]
    cases += [{"name": f"deadline {d!r} clear={c}", "kind": "deadline",
               "input": {"value": d, "clear_empty": c},
               "observed": _outcome(env, lambda d=d, c=c: ws._parse_optional_deadline(
                   d, clear_empty=c))}
              for d, c in deadlines]
    return cases


def ordering_cases(env: Env) -> list[dict[str, Any]]:
    ws, cases = env.ws, []

    def flow(name: str, steps: Callable[[Any, dict[str, str]], Any]) -> None:
        db = env.fresh()
        ids = {t: env.create(db, t) for t in ("A", "B", "C")}
        ids["X"] = env.create(db, "X", status="in_arbeit")
        cases.append({"name": name, "kind": "ordering", "observed": {
            "response": _compact(steps(db, ids)), "columns": env.columns(db)}})

    def move(status: str, position: int, task: str) -> Callable[[Any, dict[str, str]], Any]:
        return lambda db, ids: env.call(db, "move_task", OWNER, page_id=PAGE, task_id=ids[task],
                                        req=ws.WorkspaceTaskMove(status=status, position=position))

    flow("create three", lambda db, ids: None)
    flow("move C to position 1", move("offen", 1, "C"))
    flow("move A to position 0", move("offen", 0, "A"))
    flow("move A to position -5", move("offen", -5, "A"))
    flow("move A to position 99", move("offen", 99, "A"))
    flow("move B to in_arbeit 1", move("in_arbeit", 1, "B"))
    flow("move B to in_arbeit 2", move("in_arbeit", 2, "B"))
    flow("move A to unknown status", move("gibt_es_nicht", 1, "A"))

    def update(fields: dict[str, Any], task: str = "C") -> Callable[[Any, dict[str, str]], Any]:
        return lambda db, ids: env.call(db, "update_task", OWNER, page_id=PAGE, task_id=ids[task],
                                        req=ws.WorkspaceTaskUpdate(**fields))

    flow("update status without position", update({"status": "in_arbeit"}))
    flow("update position 1 same column", update({"position": 1}))
    flow("update position 0", update({"position": 0}))
    flow("update status and position", update({"status": "in_arbeit", "position": 1}))
    flow("update invalid priority", update({"priority": "dringend"}))
    flow("update clear deadline", update({"deadline": ""}))
    flow("update badge empty", update({"badge": ""}))
    flow("delete middle", lambda db, ids: env.call(db, "delete_task", OWNER, page_id=PAGE,
                                                   task_id=ids["B"]))
    flow("create ignores position", lambda db, ids: env.call(
        db, "create_task", OWNER, page_id=PAGE,
        req=ws.WorkspaceTaskCreate(title="D", status="offen")))
    flow("create invalid status", lambda db, ids: env.call(
        db, "create_task", OWNER, page_id=PAGE,
        req=ws.WorkspaceTaskCreate(title="D", status="nope")))
    flow("create empty deadline", lambda db, ids: env.call(
        db, "create_task", OWNER, page_id=PAGE,
        req=ws.WorkspaceTaskCreate(title="D", deadline="")))
    return cases


def settings_cases(env: Env) -> list[dict[str, Any]]:
    ws, cases = env.ws, []
    for name, uid, columns in (
        ("remove in_arbeit", OWNER, [("offen", "Offen"), ("erledigt", "Erledigt")]),
        ("remove offen", OWNER, [("in_arbeit", "In Arbeit"), ("erledigt", "Erledigt")]),
        ("editor configures", EDITOR, [("offen", "Offen")]),
    ):
        db = env.fresh()
        for title, status in (("A", "offen"), ("B", "offen"), ("X", "in_arbeit"),
                              ("Y", "in_arbeit")):
            env.create(db, title, status=status)
        req = ws.BoardSettingsUpdate(columns=[ws.BoardColumnDef(id=i, label=lbl)
                                              for i, lbl in columns])
        response = env.call(db, "update_board_settings", uid, page_id=PAGE, req=req)
        cases.append({"name": f"settings {name}", "kind": "settings",
                      "input": {"user": uid, "columns": columns},
                      "observed": {"response": {"status": response["status"],
                                                "detail": response.get("detail")},
                                   "columns": env.columns(db)}})
    db = env.fresh()
    cases.append({"name": "settings default columns", "kind": "settings",
                  "observed": env.call(db, "get_board_settings", OWNER, page_id=PAGE)})
    return cases


def access_cases(env: Env) -> list[dict[str, Any]]:
    ws, cases = env.ws, []
    for uid in (OWNER, EDITOR, READER, NB_EDITOR, NB_READER, STRANGER):
        db = env.fresh()
        read = env.call(db, "list_tasks", uid, page_id=PAGE)
        write = env.call(db, "create_task", uid, page_id=PAGE,
                         req=ws.WorkspaceTaskCreate(title="T"))
        share = env.call(db, "list_shares", uid, page_id=PAGE)
        cases.append({"name": f"access user {uid}", "kind": "access", "input": {"user": uid},
                      "observed": {"read": read["status"], "write": write["status"],
                                   "write_detail": write.get("detail"),
                                   "owner_only": share["status"]}})
    return cases


def share_cases(env: Env) -> list[dict[str, Any]]:
    ws, cases = env.ws, []

    def share(uid: int, target: int, permission: str, db: Any | None = None) -> Any:
        db = db or env.fresh()
        return env.call(db, "share_page", uid, page_id=PAGE,
                        req=ws.ShareCreate(shared_with_user_id=target, permission=permission))

    for name, args in (("owner shares read", (OWNER, 5, "read")),
                       ("owner shares write", (OWNER, 5, "write")),
                       ("owner shares self", (OWNER, OWNER, "edit")),
                       ("unknown user", (OWNER, 99, "read")),
                       ("inactive user", (OWNER, INACTIVE, "read")),
                       ("editor shares", (EDITOR, 5, "read")),
                       ("upsert existing", (OWNER, EDITOR, "read"))):
        observed = share(*args)
        observed.get("result", {}).pop("id", None)
        cases.append({"name": f"share {name}", "kind": "share", "input": list(args),
                      "observed": observed})
    for name, actor, target in (("owner revokes", OWNER, EDITOR),
                                ("recipient revokes self", READER, READER),
                                ("other revokes", EDITOR, READER),
                                ("stranger revokes", STRANGER, READER)):
        db = env.fresh()
        shares = db.rows(env.models.VpaiPageShare)
        share_id = next(str(s.id) for s in shares if s.shared_with_user_id == target)
        observed = env.call(db, "revoke_share", actor, page_id=PAGE, share_id=share_id)
        cases.append({"name": f"revoke {name}", "kind": "revoke", "input": [actor, target],
                      "observed": observed})
    db = env.fresh()
    cases.append({"name": "revoke missing", "kind": "revoke", "input": [OWNER, None],
                  "observed": env.call(db, "revoke_share", OWNER, page_id=PAGE,
                                       share_id=str(uuid.uuid4()))})
    shares = db.rows(env.models.VpaiPageShare)
    cases.append({"name": "update share write", "kind": "share", "input": [OWNER, "write"],
                  "observed": env.call(db, "update_share", OWNER, page_id=PAGE,
                                       share_id=str(shares[0].id),
                                       req=ws.ShareCreate(shared_with_user_id=EDITOR,
                                                          permission="write"))})
    return cases


def run_all(ws: Any, session_type: type, run: Callable[..., Any], exc: type) -> list[Any]:
    env = Env(ws, session_type, run, exc)
    return (validation_cases(env) + ordering_cases(env) + settings_cases(env)
            + access_cases(env) + share_cases(env))
