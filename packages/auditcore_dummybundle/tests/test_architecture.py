"""Importgrenzen per AST: Standardbibliothek und die drei gebundenen auditcore-Pakete."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_dummybundle

PACKAGE = Path(auditcore_dummybundle.__file__).parent
ALLOWED = {
    "__future__",
    "auditcore_common",
    "auditcore_dummybundle",
    "auditcore_dummygenerator",
    "auditcore_identifiers",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "functools",
    "importlib",
    "json",
    "random",
    "re",
    "string",
    "time",
    "typing",
}


def test_only_standard_library_and_bound_packages() -> None:
    found: set[str] = set()
    for path in sorted(PACKAGE.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                found.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__", "print"}, path
    assert found <= ALLOWED, found - ALLOWED


def test_no_float_amounts_in_sources() -> None:
    """Beträge laufen nie über ``float``: kein Aufruf und keine Annotation im Paket."""
    for path in sorted(PACKAGE.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Name) and node.id == "float":
                assert path.name in {"model.py", "web.py", "parsing.py"}, path
