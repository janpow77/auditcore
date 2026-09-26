"""Runtime code uses the standard library only; defusedxml is imported lazily in safe_xml."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import auditcore_common

PACKAGE = Path(auditcore_common.__file__).parent
LAZY = {"defusedxml": {"safe_xml.py"}}


def test_imports_are_standard_library_or_lazy() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        top_level = {id(node) for node in tree.body}
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            for name in names:
                root = name.split(".")[0]
                if root in LAZY:
                    assert path.name in LAZY[root], path.name
                    assert id(node) not in top_level, f"{path.name}: {root} nur verzögert"
                else:
                    assert root in stdlib or root == "auditcore_common", f"{path.name}: {name}"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__", "open", "print"}


def test_topic_modules_and_no_catch_all() -> None:
    modules = {path.stem for path in PACKAGE.glob("*.py")} - {"__init__"}
    assert modules == {
        "aio",
        "clock",
        "filenames",
        "frozen",
        "hashing",
        "html_text",
        "ids",
        "json_values",
        "numbers_de",
        "numeric",
        "optional",
        "profiles",
        "safe_xml",
        "text",
    }
    assert not {"utils", "helpers", "common", "misc"} & modules


def test_import_loads_no_optional_dependency() -> None:
    code = (
        "import sys, auditcore_common; "
        "from auditcore_common import aio, clock, filenames, frozen, hashing, html_text, ids, "
        "json_values, numbers_de, numeric, optional, profiles, safe_xml, text; "
        "assert 'defusedxml' not in sys.modules and 'numpy' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_provenance_copies_match() -> None:
    packaged = json.loads((PACKAGE / "provenance.json").read_text(encoding="utf-8"))
    top = PACKAGE.parents[1] / "provenance.json"
    if top.is_file():
        assert json.loads(top.read_text(encoding="utf-8")) == packaged
    assert packaged["version"] == auditcore_common.__version__
    assert packaged["rights"]["authorization"]["status"] == "USER_AUTHORIZED_MIT"
    assert {s["repository"] for s in packaged["sources"]} == {
        "janpow77/audit-portal",
        "janpow77/audit_designer",
        "janpow77/flowaudit",
        "janpow77/flowinvoice",
        "janpow77/regulierung",
        "janpow77/riskanalysis",
        "janpow77/versteigerung",
    }
