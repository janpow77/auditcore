"""Laufzeitmodule nutzen nur Standardbibliothek und eigenes Paket; Extras nur verzögert."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_bpmn

PACKAGE = Path(auditcore_bpmn.__file__).parent
ALLOWED = {
    "__future__",
    "collections",
    "csv",
    "dataclasses",
    "datetime",
    "hashlib",
    "importlib",
    "io",
    "json",
    "os",
    "pathlib",
    "re",
    "tempfile",
    "types",
    "typing",
    "xml",
    "auditcore_bpmn",
}
LAZY = {"defusedxml", "openpyxl", "reportlab"}
EXTRA_MODULES = {"legal.py": {"auditcore_legal_sources"}}


def _imports(tree: ast.AST) -> list[tuple[set[str], bool]]:
    nested = {id(n) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) for n in ast.walk(f)}
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom) and not getattr(node, "level", 0):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            result.append(({n.split(".")[0] for n in names}, id(node) in nested))
    return result


def test_runtime_imports() -> None:
    for path in PACKAGE.rglob("*.py"):
        allowed_top = ALLOWED | EXTRA_MODULES.get(path.name, set())
        for roots, lazy in _imports(ast.parse(path.read_text(encoding="utf-8"))):
            assert roots <= (allowed_top | LAZY if lazy else allowed_top), (path.name, roots)


def test_no_forbidden_calls_or_names() -> None:
    forbidden_text = ("hmwvw", "wibank", "hessen")
    for path in PACKAGE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__", "print", "open"}, path.name
        assert not any(word in text.lower() for word in forbidden_text), path.name


def test_import_loads_no_optional_dependency() -> None:
    code = (
        "import sys, auditcore_bpmn, auditcore_bpmn.legacy, auditcore_bpmn.reports;"
        "print(sorted(m for m in ('openpyxl','reportlab','auditcore_legal_sources','pandas') if m in sys.modules))"
    )
    assert (
        subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.strip() == "[]"
    )


def test_public_api_is_curated() -> None:
    assert auditcore_bpmn.__version__ == "0.1.2"
    for name in auditcore_bpmn.__all__:
        assert hasattr(auditcore_bpmn, name), name
    assert "ValidationIssue" in auditcore_bpmn.__all__ and "AuditFinding" in auditcore_bpmn.__all__
