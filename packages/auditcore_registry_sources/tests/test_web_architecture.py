"""The review API core stays framework-free; Starlette/FastAPI only in their adapters."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_registry_sources.web as web

WEB = Path(web.__file__).parent
CORE_ALLOWED = {
    "__future__",
    "collections",
    "dataclasses",
    "datetime",
    "hashlib",
    "itertools",
    "threading",
    "typing",
    "uuid",
    "auditcore_registry_sources",
    "auditcore_entity_matching",
}
ADAPTER_ONLY = {"http.py": {"starlette", "inspect", "json"}, "fastapi_router.py": {"fastapi"}}


def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(
                "auditcore_registry_sources" if node.level else (node.module or "").split(".")[0]
            )
    return names


def test_modules_import_only_what_they_may() -> None:
    for path in sorted(WEB.glob("*.py")):
        allowed = CORE_ALLOWED | ADAPTER_ONLY.get(path.name, set())
        assert _imports(path) <= allowed, (path.name, _imports(path) - allowed)


def test_modules_stay_small() -> None:
    for path in WEB.glob("*.py"):
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 400, path.name


def test_core_import_does_not_load_web_frameworks() -> None:
    code = (
        "import sys, auditcore_registry_sources.web as w; "
        "assert w.ScreeningReviewService; "
        "print(sorted(m for m in ('starlette', 'fastapi') if m in sys.modules))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]"
