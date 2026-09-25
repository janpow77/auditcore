"""F-09/T-38: runtime modules use only the standard library and declared optional extras."""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import auditcore_procurement

PACKAGE = Path(auditcore_procurement.__file__).parent
OPTIONAL = {"lxml": "company_sources.py", "auditcore_harvest": "sources.py"}


def _imports(path: Path) -> tuple[set[str], set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    top, nested = set(), set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            top.add((node.module or "").split(".")[0])
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            nested.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            nested.add((node.module or "").split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "eval", "exec", "__import__", "print"}, path.name
    return top, nested - top


def test_runtime_imports_are_stdlib_or_declared_extras() -> None:
    for path in PACKAGE.rglob("*.py"):
        top, lazy = _imports(path)
        for name in top | lazy:
            if name in OPTIONAL:
                if OPTIONAL[name] == "company_sources.py":
                    assert name in lazy and path.name == "company_sources.py", path
                else:
                    assert path.name == OPTIONAL[name], path
                continue
            own = {"auditcore_procurement", "auditcore_common"}
            assert name in sys.stdlib_module_names or name in own, (path, name)
        assert not (
            {"logging", "socket", "subprocess", "urllib", "http", "httpx", "requests"}
            & (top | lazy)
        ), path


def test_core_import_needs_no_optional_dependency() -> None:
    for module in ("records", "ted", "prechecks", "company_sources"):
        importlib.import_module(f"auditcore_procurement.{module}")
