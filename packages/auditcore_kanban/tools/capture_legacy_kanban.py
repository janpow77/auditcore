"""Characterize the audit_designer workspace board backend by executing it.

    python -I tools/capture_legacy_kanban.py /path/to/audit_designer \
        tests/fixtures/legacy_kanban_observed.json

The original ``backend/app/api/vpai_notebook/workspace.py`` and
``backend/app/modules/vp_ai/utils/user_scoped.py`` are read with ``git show``
at the pinned commit (blob SHAs checked) and executed unchanged. FastAPI,
Pydantic and SQLAlchemy are replaced by minimal stubs and a small in-memory
fake ORM that supports exactly the query forms the two files use
(filter/order_by/all/first/scalar, ==, !=, in_, asc, func.max). No database,
no network. Output: observed inputs/outputs per case.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import types
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

COMMIT = "2c726f3c1481775cd34aeaa83f87137d6ab12ffe"
SOURCES = {
    "workspace": ("backend/app/api/vpai_notebook/workspace.py",
                  "ccdb57dd3677b36fb4212c5347c2cfcd0096cabe"),
    "user_scoped": ("backend/app/modules/vp_ai/utils/user_scoped.py",
                    "b2ecd79398c77c13b450331642074840d535ca6c"),
}


def git_source(repo: Path, path: str, blob: str) -> str:
    actual = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{COMMIT}:{path}"],
                            capture_output=True, text=True, check=True).stdout.strip()
    if actual != blob:
        raise SystemExit(f"blob mismatch for {path}: {actual} != {blob}")
    return subprocess.run(["git", "-C", str(repo), "show", f"{COMMIT}:{path}"],
                          capture_output=True, text=True, check=True).stdout


# -- fake ORM -------------------------------------------------------------------


def _norm(value: Any) -> Any:
    return str(value) if isinstance(value, uuid.UUID) else value


class Pred:
    def __init__(self, fn: Callable[[Any], bool]) -> None:
        self.fn = fn


class Order:
    def __init__(self, name: str, desc: bool = False) -> None:
        self.name, self.desc = name, desc


class Col:
    type = None

    def __set_name__(self, owner: type, name: str) -> None:
        self.name, self.model = name, owner

    def __get__(self, obj: Any, owner: type) -> Any:
        return self if obj is None else obj.__dict__.get(self.name)

    def __set__(self, obj: Any, value: Any) -> None:
        obj.__dict__[self.name] = value

    def __eq__(self, other: Any) -> Pred:  # type: ignore[override]
        return Pred(lambda row: _norm(getattr(row, self.name)) == _norm(other))

    def __ne__(self, other: Any) -> Pred:  # type: ignore[override]
        return Pred(lambda row: _norm(getattr(row, self.name)) != _norm(other))

    __hash__ = object.__hash__

    def in_(self, values: Any) -> Pred:
        wanted = {_norm(v) for v in values}
        return Pred(lambda row: _norm(getattr(row, self.name)) in wanted)

    def asc(self) -> Order:
        return Order(self.name)

    def desc(self) -> Order:
        return Order(self.name, True)


class Agg:
    def __init__(self, fn: str, col: Col) -> None:
        self.fn, self.col = fn, col


class Model:
    defaults: dict[str, Any] = {}

    def __init__(self, **kwargs: Any) -> None:
        for key, value in {**self.defaults, **kwargs}.items():
            setattr(self, key, value)

    def to_dict(self, **_options: Any) -> dict[str, Any]:
        return dict(self.__dict__)


def _model(name: str, fields: list[str], defaults: dict[str, Any] | None = None) -> type:
    namespace: dict[str, Any] = {f: Col() for f in fields}
    namespace["defaults"] = defaults or {}
    return type(name, (Model,), namespace)


VpaiPage = _model("VpaiPage", ["id", "notebook_id", "title", "page_type", "icon",
                               "owner_user_id", "created_by_id", "is_pinned", "is_archived",
                               "board_columns", "created_at", "updated_at"],
                  {"is_pinned": False, "is_archived": False, "board_columns": None})
VpaiWorkspaceTask = _model("VpaiWorkspaceTask", [
    "id", "page_id", "title", "description", "status", "priority", "position", "tags",
    "deadline", "card_color", "card_image", "badge", "checklist", "generated_prompt",
    "prompt_generated_at", "created_at", "updated_at"], {"checklist": []})
VpaiPageShare = _model("VpaiPageShare", ["id", "page_id", "shared_with_user_id",
                                         "shared_by_user_id", "permission", "created_at"])
VpaiNotebookShare = _model("VpaiNotebookShare", ["id", "notebook_id", "shared_with_user_id",
                                                 "permission"])
VpaiNotebook = _model("VpaiNotebook", ["id", "name", "owner_user_id", "created_by_id"])
VpaiFile = _model("VpaiFile", ["id", "task_id", "page_id"])
User = _model("User", ["id", "username", "full_name", "is_active", "storage_quota_mb"])


class Query:
    def __init__(self, session: FakeSession, target: Any, preds: list[Pred] | None = None,
                 orders: list[Order] | None = None) -> None:
        self.session, self.target = session, target
        self.preds, self.orders = preds or [], orders or []

    def _model(self) -> type:
        return self.target.col.model if isinstance(self.target, Agg) else self.target

    def filter(self, *preds: Pred) -> Query:
        return Query(self.session, self.target, self.preds + list(preds), self.orders)

    def order_by(self, *orders: Any) -> Query:
        converted = [o if isinstance(o, Order) else Order(o.name) for o in orders]
        return Query(self.session, self.target, self.preds, self.orders + converted)

    def all(self) -> list[Any]:
        rows = [r for r in self.session.rows(self._model()) if all(p.fn(r) for p in self.preds)]
        for order in reversed(self.orders):
            rows.sort(key=lambda r, o=order: getattr(r, o.name), reverse=order.desc)
        return rows

    def first(self) -> Any:
        rows = self.all()
        return rows[0] if rows else None

    def scalar(self) -> Any:
        values = [getattr(r, self.target.col.name) for r in self.all()]
        return max(values) if values else None


class FakeSession:
    def __init__(self) -> None:
        self.tables: dict[type, list[Any]] = {}
        self.tick = datetime(2026, 1, 1)

    def rows(self, model: type) -> list[Any]:
        return self.tables.setdefault(model, [])

    def query(self, target: Any) -> Query:
        return Query(self, target)

    def add(self, obj: Any) -> None:
        if getattr(obj, "created_at", None) is None:
            self.tick += timedelta(seconds=1)
            obj.created_at = self.tick
        table = self.rows(type(obj))
        if obj not in table:
            table.append(obj)

    def delete(self, obj: Any) -> None:
        self.rows(type(obj)).remove(obj)

    def commit(self) -> None: ...

    def flush(self) -> None: ...

    def refresh(self, obj: Any) -> None: ...


# -- stubs ----------------------------------------------------------------------


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = "") -> None:
        super().__init__(detail)
        self.status_code, self.detail = status_code, detail


class BaseModel:
    def __init__(self, **kwargs: Any) -> None:
        for name in self._fields():
            default = getattr(type(self), name, None)
            value = kwargs.get(name, default)
            setattr(self, name, list(value) if isinstance(value, list) else value)

    @classmethod
    def _fields(cls) -> list[str]:
        names: list[str] = []
        for klass in reversed(cls.__mro__):
            names += [n for n in getattr(klass, "__annotations__", {}) if n not in names]
        return names

    def model_dump(self) -> dict[str, Any]:
        return {n: getattr(self, n) for n in self._fields()}


class APIRouter:
    def __getattr__(self, _name: str) -> Callable[..., Any]:
        return lambda *a, **k: (lambda fn: fn)


def install_stubs(sources: dict[str, str]) -> types.ModuleType:
    def module(name: str, **attrs: Any) -> types.ModuleType:
        mod = types.ModuleType(name)
        mod.__dict__.update(attrs)
        sys.modules[name] = mod
        return mod

    module("fastapi", APIRouter=APIRouter, Depends=lambda *_a: None, HTTPException=HTTPException)
    module("pydantic", BaseModel=BaseModel)
    module("sqlalchemy", func=types.SimpleNamespace(max=lambda c: Agg("max", c),
                                                    count=lambda c: Agg("count", c)))
    module("sqlalchemy.orm", Session=object, Query=object)
    for name in ("app", "app.api", "app.core", "app.models", "app.modules", "app.modules.vp_ai",
                 "app.modules.vp_ai.utils", "app.api.vpai_notebook"):
        module(name)
    module("app.api.auth", get_current_user=None)
    module("app.core.database", get_db=None)
    module("app.models.user", User=User)
    module("app.models.vpai_notebook", VpaiPage=VpaiPage, VpaiWorkspaceTask=VpaiWorkspaceTask,
           VpaiPageShare=VpaiPageShare, VpaiNotebookShare=VpaiNotebookShare,
           VpaiNotebook=VpaiNotebook, VpaiFile=VpaiFile)
    scoped = module("app.modules.vp_ai.utils.user_scoped")
    exec(compile(sources["user_scoped"], "user_scoped.py", "exec"), scoped.__dict__)  # noqa: S102
    workspace = module("app.api.vpai_notebook.workspace")
    exec(compile(sources["workspace"], "workspace.py", "exec"), workspace.__dict__)  # noqa: S102
    return workspace


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from capture_legacy_cases import run_all

    repository, output = Path(sys.argv[1]), Path(sys.argv[2])
    texts = {k: git_source(repository, p, b) for k, (p, b) in SOURCES.items()}
    ws = install_stubs(texts)
    cases = run_all(ws, FakeSession, asyncio.run, HTTPException)
    document = {
        "source": {"repository": "janpow77/audit_designer", "commit": COMMIT,
                   "files": [{"path": p, "git_blob": b} for p, b in SOURCES.values()]},
        "tool": "tools/capture_legacy_kanban.py",
        "cases": len(cases),
        "observations": cases,
    }
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(cases)} cases -> {output}")
