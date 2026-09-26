"""Standard library only (web: Starlette/FastAPI, auditcore_common), module size, provenance."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import auditcore_identifiers

PACKAGE = Path(auditcore_identifiers.__file__).parent
SOURCES = {
    ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
    ("janpow77/audit-portal", "d8eefa426826bdecb67036774f3128ae05e7d0d0"),
    ("janpow77/flowworkshop", "a05bb2143bd96d5e981f9462f05b965e1658be36"),
    ("janpow77/auditcore", "99788a18c28bf683ada62bb3ab9d4aeb36f2c5b2"),
}


WEB_FRAMEWORKS = {"starlette", "fastapi"}
#: The web layer also uses the stdlib-only REST helpers of ``auditcore_common``.
WEB_IMPORTS = WEB_FRAMEWORKS | {"auditcore_common"}


def test_only_standard_library_imports() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__", "auditcore_identifiers"}
    for path in PACKAGE.rglob("*.py"):
        allowed = stdlib | (WEB_IMPORTS if path.parent.name == "web" else set())
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(a.name.split(".")[0] in allowed for a in node.names), path.name
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert (node.module or "").split(".")[0] in allowed, path.name
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}, path.name


def test_module_size() -> None:
    for path in PACKAGE.rglob("*.py"):
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 400, path.name


def test_provenance_copies_match_and_carry_the_rights_block() -> None:
    packaged = json.loads((PACKAGE / "provenance.json").read_text(encoding="utf-8"))
    top = PACKAGE.parents[1] / "provenance.json"
    if top.is_file():
        assert json.loads(top.read_text(encoding="utf-8")) == packaged
    authorization = packaged["rights"]["authorization"]
    assert authorization["status"] == "USER_AUTHORIZED_MIT"
    assert authorization["date"] == "2026-09-22"
    assert {(s["repository"], s["commit"]) for s in packaged["sources"]} == SOURCES
    assert packaged["version"] == auditcore_identifiers.__version__
