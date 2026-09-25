"""Core only stdlib; Starlette/FastAPI only lazily inside the REST adapters."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import auditcore_kanban

PACKAGE = Path(auditcore_kanban.__file__).parent
ADAPTERS = {"asgi.py": {"starlette"}, "fastapi_router.py": {"fastapi"}}


def _imports(tree: ast.Module) -> list[tuple[ast.stmt, str]]:
    found: list[tuple[ast.stmt, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(node, a.name) for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            found.append((node, node.module or ""))
    return found


def test_imports() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        top_level = {id(n) for n in tree.body}
        for node, name in _imports(tree):
            root = name.split(".")[0]
            if root in ADAPTERS.get(path.name, set()):
                assert id(node) not in top_level, f"{path.name}: {root} only lazily"
            else:
                assert root in stdlib or root == "auditcore_kanban", f"{path.name}: {name}"
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}, path.name


def test_module_size() -> None:
    for path in PACKAGE.rglob("*.py"):
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 400, path.name


def test_provenance_copies_match_and_carry_the_rights_block() -> None:
    packaged = json.loads((PACKAGE / "provenance.json").read_text(encoding="utf-8"))
    top = PACKAGE.parents[1] / "provenance.json"
    if top.is_file():
        assert json.loads(top.read_text(encoding="utf-8")) == packaged
    authorization = packaged["rights"]["authorization"]
    assert authorization["status"] == "USER_AUTHORIZED_MIT"
    assert authorization["date"] == "2026-09-22"
    assert {(s["repository"], s["commit"]) for s in packaged["sources"]} == {
        ("janpow77/audit_designer", "2c726f3c1481775cd34aeaa83f87137d6ab12ffe"),
        ("janpow77/cockpit", "df203d4c33e786eb8a8ad3fe53b3b7eb9241d406"),
    }


def test_schema_is_packaged() -> None:
    assert (PACKAGE / "schemas" / "board.schema.json").is_file()
