"""F-09/T-38: runtime modules use the standard library, their own package and
``auditcore_entity_matching`` at top level; pandas, rapidfuzz and
auditcore_procurement are imported lazily inside functions only."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_risk

ALLOWED = {
    "__future__",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "hashlib",
    "importlib",
    "json",
    "math",
    "numbers",
    "re",
    "string",
    "types",
    "typing",
    "warnings",  # only for DeprecationWarning aliases (docs/quality/code-quality.md)
    "auditcore_risk",
}
LAZY = {"pandas", "rapidfuzz", "auditcore_procurement", "auditcore_entity_matching"}


def test_runtime_imports_and_calls() -> None:
    package = Path(auditcore_risk.__file__).parent
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        nested = {
            id(n) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) for n in ast.walk(f)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                if getattr(node, "level", 0):
                    continue
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                roots = {n.split(".")[0] for n in names}
                if id(node) in nested:
                    assert roots <= LAZY | ALLOWED, (path.name, roots)
                else:
                    assert roots <= ALLOWED, (path.name, roots)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__", "print"}


def test_import_loads_no_optional_dependency() -> None:
    code = (
        "import sys, auditcore_risk; "
        "loaded = {'pandas', 'rapidfuzz', 'numpy', 'auditcore_procurement'} & set(sys.modules); "
        "assert not loaded, loaded"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_evaluation_without_pandas_needs_only_the_core() -> None:
    code = (
        "import sys; sys.modules['pandas'] = None; import auditcore_risk as r; "
        "p = r.load_profile('audit_designer.flowstat_belegliste', '1254591156d3'); "
        "e = r.evaluate([{'projektbetrag': 5000.0}], p); "
        "assert e.summary[0]['count'] == 1"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
