"""F-09/T-38: Laufzeitmodule nutzen nur Standardbibliothek, eigenes Paket und auditcore_common.

Einzige Ausnahme ist ``nominatim`` (Extra ``[geocoder]``), das auf
``auditcore_harvest`` aufsetzt; der Paketimport lädt es nicht.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_geo

ALLOWED = {
    "__future__",
    "collections",
    "dataclasses",
    "enum",
    "io",
    "json",
    "math",
    "re",
    "struct",
    "typing",
    "urllib",
    "auditcore_geo",
    "auditcore_common",
}


def test_runtime_imports_and_calls() -> None:
    package = Path(auditcore_geo.__file__).parent
    for path in package.glob("*.py"):
        erlaubt = ALLOWED | ({"auditcore_harvest"} if path.name == "nominatim.py" else set())
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if getattr(node, "level", 0):
                    continue
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                assert {n.split(".")[0] for n in names} <= erlaubt, (path.name, names)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__", "print"}


def test_import_does_not_load_the_harvest_extra() -> None:
    code = (
        "import sys, auditcore_geo, auditcore_geo.legacy; "
        "assert 'auditcore_harvest' not in sys.modules; "
        "assert 'auditcore_geo.nominatim' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
