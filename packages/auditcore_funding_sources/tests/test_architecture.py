"""Runtime modules: stdlib, own package, auditcore_harvest (adapters) and lazy openpyxl only."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_funding_sources

ALLOWED = {
    "__future__",
    "collections",
    "csv",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "functools",
    "hashlib",
    "importlib",
    "io",
    "json",
    "math",
    "re",
    "typing",
    "unicodedata",
    "warnings",  # only for DeprecationWarning aliases (docs/quality/code-quality.md)
    "zipfile",
    "auditcore_funding_sources",
}
OPTIONAL = {"openpyxl"}
FORBIDDEN_CALLS = {"open", "eval", "exec", "__import__", "compile"}
FORBIDDEN_MODULES = {
    "subprocess",
    "socket",
    "sqlalchemy",
    "requests",
    "httpx",
    "urllib",
    "os",
    "pandas",
    "logging",
}


def _modules() -> list[Path]:
    return sorted(Path(auditcore_funding_sources.__file__).parent.glob("*.py"))


def test_imports_are_restricted() -> None:
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        top_level = {id(n) for n in tree.body}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = (
                    ["auditcore_funding_sources"]
                    if node.level
                    else [(node.module or "").split(".")[0]]
                )
            else:
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    assert node.func.id not in FORBIDDEN_CALLS, path.name
                continue
            for name in names:
                assert name not in FORBIDDEN_MODULES, (path.name, name)
                if name == "auditcore_harvest":
                    assert path.name == "adapters.py", path.name
                elif name in OPTIONAL:
                    assert id(node) not in top_level, f"{path.name}: {name} must be imported lazily"
                else:
                    assert name in ALLOWED, (path.name, name)


def test_core_import_does_not_need_harvest_or_openpyxl() -> None:
    import subprocess
    import sys

    code = (
        "import sys; import auditcore_funding_sources.workshop, "
        "auditcore_funding_sources.cumulation, "
        "auditcore_funding_sources.deminimis, auditcore_funding_sources.snapshot; "
        "assert 'openpyxl' not in sys.modules and 'auditcore_harvest' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
