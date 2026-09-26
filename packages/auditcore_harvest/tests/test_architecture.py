"""Runtime modules use only the standard library, the own package and auditcore_common.

No app bindings; ``auditcore_common`` is the shared stdlib-only helper package
(safe XML parsing, canonical hashing) and pulls in defusedxml only via the extra.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import auditcore_harvest

FORBIDDEN_CALLS = {"eval", "exec", "__import__", "open"}


def test_runtime_imports_are_stdlib_or_common_only() -> None:
    package = Path(auditcore_harvest.__file__).parent
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            for name in names:
                root = name.split(".")[0]
                assert root in stdlib or root in {"auditcore_harvest", "auditcore_common"}, (
                    f"{path.name}: {name}"
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALLS, f"{path.name}: {node.func.id}"


def test_no_database_orm_or_tenant_concepts() -> None:
    package = Path(auditcore_harvest.__file__).parent
    for path in package.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for word in ("sqlalchemy", "session.commit", "mandant", "tenant_id", "celery", "redis"):
            assert word not in text, f"{path.name}: {word}"
