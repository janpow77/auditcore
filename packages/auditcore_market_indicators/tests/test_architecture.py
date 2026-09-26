"""Framework T-38: the runtime uses only the standard library and the stdlib-only
``auditcore_common``; polars only lazily in the adapter."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_market_indicators

ALLOWED = {
    "__future__",
    "auditcore_common",
    "math",
    "collections",
    "dataclasses",
    "typing",
    "hashlib",
    "json",
    "importlib",
    "types",
}


def imports(path: Path) -> tuple[set[str], set[str]]:
    """(module-level imports, imports inside functions)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    top: set[str] = set()
    nested: set[str] = set()
    for node in ast.walk(tree):
        names: set[str] = set()
        if isinstance(node, ast.Import):
            names = {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names = {(node.module or "").split(".")[0]}
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "eval", "exec", "__import__", "print", "input"}
        if names:
            inside = any(
                isinstance(parent, ast.FunctionDef) and node in ast.walk(parent)
                for parent in ast.walk(tree)
            )
            (nested if inside else top).update(names)
    return top, nested


def test_runtime_imports_are_standard_library_only() -> None:
    package = Path(auditcore_market_indicators.__file__).parent
    for path in package.rglob("*.py"):
        top, nested = imports(path)
        if path.name == "polars_adapter.py":
            assert nested <= {"polars"}
            assert top <= ALLOWED | {"polars"}
            continue
        assert top <= ALLOWED, (path.name, top - ALLOWED)
        assert not nested, (path.name, nested)


def test_polars_is_only_imported_for_type_checking_or_inside_functions() -> None:
    source = (Path(auditcore_market_indicators.__file__).parent / "polars_adapter.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
            assert module != "polars"
        if isinstance(node, ast.If):
            assert ast.unparse(node.test) == "TYPE_CHECKING"


def test_core_import_does_not_load_polars() -> None:
    import subprocess
    import sys

    code = "import sys, auditcore_market_indicators; print('polars' in sys.modules)"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert result.stdout.strip() == "False", result.stderr
