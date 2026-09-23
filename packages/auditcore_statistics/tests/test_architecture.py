"""Framework T-38: the runtime uses only the standard library and its own package."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_statistics


def test_runtime_imports_are_standard_library_only() -> None:
    package = Path(auditcore_statistics.__file__).parent
    allowed = {"__future__", "math", "collections", "dataclasses", "decimal", "typing"}
    observed: set[str] = set()
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                observed.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                observed.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__", "print"}
    assert observed <= allowed, observed - allowed
