"""Runtime modules: standard library, own package and auditcore_harvest only."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_price_sources

ALLOWED = {
    "__future__",
    "base64",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "hashlib",
    "json",
    "typing",
    "urllib",
    "auditcore_harvest",
    "auditcore_price_sources",
}
FORBIDDEN_CALLS = {"open", "eval", "exec", "__import__", "compile", "print"}


def _modules() -> list[Path]:
    return sorted(Path(auditcore_price_sources.__file__).parent.glob("*.py"))


def test_imports_are_restricted() -> None:
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = ["auditcore_price_sources"] if node.level else [node.module or ""]
            else:
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    assert node.func.id not in FORBIDDEN_CALLS, (path.name, node.func.id)
                continue
            for name in names:
                assert name.split(".")[0] in ALLOWED, (path.name, name)
                if name.startswith("urllib"):
                    # only URL encoding; no network access from the library
                    assert name == "urllib.parse", (path.name, name)


def test_no_network_database_or_logging_after_import() -> None:
    code = (
        "import sys, auditcore_price_sources; "
        "bad = {'socket', 'ssl', 'http.client', 'urllib.request', 'sqlalchemy', 'httpx', "
        "'logging', 'auditcore'} & set(sys.modules); assert not bad, bad"
    )
    subprocess.run([sys.executable, "-I", "-c", code], check=True)
