"""F-09/T-38: runtime modules use only the standard library, their own package and
``auditcore_common``."""

import ast
from pathlib import Path

import auditcore_entity_matching

ALLOWED = {
    "__future__",
    "collections",
    "dataclasses",
    "functools",
    "hashlib",
    "importlib",
    "json",
    "re",
    "types",
    "typing",
    "unicodedata",
    "warnings",  # only for DeprecationWarning aliases (docs/quality/code-quality.md)
    "auditcore_entity_matching",
    "auditcore_common",
}


def test_runtime_imports_and_calls() -> None:
    package = Path(auditcore_entity_matching.__file__).parent
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        lazy = {
            id(n)
            for f in ast.walk(tree)
            if isinstance(f, ast.FunctionDef) and f.name == "_rapidfuzz"
            for n in ast.walk(f)
        }
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                if getattr(node, "level", 0):
                    continue
                roots = {n.split(".")[0] for n in names}
                if id(node) in lazy:
                    assert roots == {"rapidfuzz"}
                else:
                    assert roots <= ALLOWED, (path.name, roots)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__", "print"}


def test_import_does_not_load_rapidfuzz() -> None:
    import subprocess
    import sys

    code = "import sys, auditcore_entity_matching; assert 'rapidfuzz' not in sys.modules"
    subprocess.run([sys.executable, "-c", code], check=True)
