"""Framework T-38: stdlib-only runtime, no global random state, no I/O."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_sampling


def test_runtime_imports_and_calls() -> None:
    package = Path(auditcore_sampling.__file__).parent
    allowed = {
        "__future__",
        "bisect",
        "collections",
        "dataclasses",
        "math",
        "random",
        "types",
        "typing",
    }
    observed: set[str] = set()
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                observed.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                observed.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id not in {"open", "eval", "exec", "__import__", "print"}
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    # module-level random functions would use the global state
                    assert not (func.value.id == "random" and func.attr != "Random"), path.name
    assert observed <= allowed, observed - allowed
