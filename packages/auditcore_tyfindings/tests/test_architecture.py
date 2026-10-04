"""Importgrenzen per AST: nur Standardbibliothek und auditcore_common."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_tyfindings

PAKET = Path(auditcore_tyfindings.__file__).parent
ERLAUBT = {
    "__future__",
    "auditcore_common",
    "collections",
    "dataclasses",
    "functools",
    "types",
    "typing",
}


def test_nur_standardbibliothek_und_common() -> None:
    gefunden: set[str] = set()
    for pfad in sorted(PAKET.rglob("*.py")):
        for knoten in ast.walk(ast.parse(pfad.read_text(encoding="utf-8"))):
            if isinstance(knoten, ast.Import):
                gefunden.update(a.name.split(".")[0] for a in knoten.names)
            elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0:
                gefunden.add((knoten.module or "").split(".")[0])
            elif isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name):
                assert knoten.func.id not in {"open", "eval", "exec", "__import__", "print"}, pfad
    assert gefunden <= ERLAUBT, gefunden - ERLAUBT
