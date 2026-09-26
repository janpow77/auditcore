"""Runtime modules: standard library and own package only; no I/O, network or logging."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_price_analysis

ALLOWED = {
    "__future__",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "hashlib",
    "importlib",
    "json",
    "re",
    "typing",
    "auditcore_common",
    "auditcore_price_analysis",
}
FORBIDDEN_CALLS = {"open", "eval", "exec", "__import__", "compile", "print"}


def _modules() -> list[Path]:
    return sorted(Path(auditcore_price_analysis.__file__).parent.glob("*.py"))


def test_imports_are_restricted_to_stdlib_computation() -> None:
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = (
                    ["auditcore_price_analysis"]
                    if node.level
                    else [(node.module or "").split(".")[0]]
                )
            else:
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    assert node.func.id not in FORBIDDEN_CALLS, (path.name, node.func.id)
                continue
            for name in names:
                assert name in ALLOWED, (path.name, name)


def test_no_float_in_new_contract_results() -> None:
    for name in ("calculation.py", "comparison.py", "selection.py", "tariff.py"):
        source = (Path(auditcore_price_analysis.__file__).parent / name).read_text(encoding="utf-8")
        assert "float(" not in source, name


def test_import_has_no_side_effects_on_foreign_modules() -> None:
    code = (
        "import sys, auditcore_price_analysis; "
        "assert not {'auditcore', 'auditcore_harvest', 'sqlalchemy', 'httpx', 'socket', 'logging'} "
        "& set(sys.modules), sorted(sys.modules)"
    )
    subprocess.run([sys.executable, "-I", "-c", code], check=True)
