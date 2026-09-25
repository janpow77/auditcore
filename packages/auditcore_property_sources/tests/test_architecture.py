"""Framework T-38: parsers use only the standard library; auditcore_harvest only in adapters."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_property_sources

STDLIB = {
    "__future__",
    "collections",
    "copy",
    "dataclasses",
    "datetime",
    "functools",
    "html",
    "importlib",
    "json",
    "re",
    "typing",
    "unicodedata",
    "urllib",
}


def imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            found.add((node.module or "").split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "eval", "exec", "print", "__import__"}, path.name
    return found


def test_runtime_imports() -> None:
    package = Path(auditcore_property_sources.__file__).parent
    for path in package.glob("*.py"):
        allowed = STDLIB | ({"auditcore_harvest"} if path.name == "adapters.py" else set())
        allowed |= {"auditcore_common"} if path.name == "_zvg_text.py" else set()
        assert imports(path) <= allowed, (path.name, imports(path) - allowed)


def test_core_import_needs_no_harvest_and_no_network_modules() -> None:
    code = (
        "import sys, auditcore_property_sources.zvg, auditcore_property_sources.bienici; "
        "print(sorted(m for m in sys.modules if m.split('.')[0] in "
        "{'auditcore_harvest','socket','http','ssl'}))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]"
