"""Core is stdlib-only; bcrypt, argon2, PyJWT and FastAPI are imported lazily in adapters."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import auditcore_auth
from auditcore_auth import APP_PROFILES

PACKAGE = Path(auditcore_auth.__file__).parent
ADAPTERS = {
    "_hash_backends.py": {"bcrypt", "argon2"},
    "_jwt_backend.py": {"jwt"},
    "fastapi_bearer.py": {"fastapi"},
}
FORBIDDEN = {"jose", "passlib"}
SOURCES = {
    ("janpow77/audit_designer", "ccd65245182982af3ef885a7a6d43583f4f72cbb"),
    ("janpow77/flownavigator", "9dff858d3772e59533886dfbae70c672d574a1d4"),
    ("janpow77/flowsearch", "9ac5e0dd0c2b7363b5a077551e4fb7103f32c697"),
    ("janpow77/qaaudit", "c78be5c86454d457e5c66d0c65b5117a8528d462"),
    ("janpow77/versteigerung", "729f9a10bc5478bd724ef40c1f4cd572e5a3dada"),
    ("janpow77/regulierung", "ce76e48c8ad7f1cbe430948158a4e7001a02ba99"),
    ("janpow77/flowinvoice", "5d5d8c5aded2b7eee82c0813994e9efd549277b3"),
    ("janpow77/audit-portal", "72cc4b1a15fdcd5ee06ef8124d864904cc4e1312"),
    ("janpow77/flowlib", "aca2dc6aad25aea0720312dbcc6da00b0bcba330"),
}


def _imports(tree: ast.Module) -> list[tuple[ast.stmt, str]]:
    found: list[tuple[ast.stmt, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(node, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            found.append((node, node.module or ""))
    return found


def test_imports() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        top_level = {id(node) for node in tree.body}
        for node, name in _imports(tree):
            root = name.split(".")[0]
            assert root not in FORBIDDEN, f"{path.name}: {name}"
            if root in ADAPTERS.get(path.name, set()):
                assert id(node) not in top_level, f"{path.name}: {root} only lazily"
            else:
                assert root in stdlib or root == "auditcore_auth", f"{path.name}: {name}"
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}, path.name


def test_dynamic_imports_only_in_backend_adapters() -> None:
    for path in PACKAGE.rglob("*.py"):
        if "import_module(" in path.read_text(encoding="utf-8"):
            assert path.name in {"_hash_backends.py", "_jwt_backend.py"}, path.name


def test_importing_the_package_loads_no_backend() -> None:
    import subprocess

    code = ("import sys, auditcore_auth, auditcore_auth.fastapi_bearer; "
            "assert not {'bcrypt', 'argon2', 'jwt', 'fastapi'} & set(sys.modules), "
            "sorted(sys.modules)")
    subprocess.run([sys.executable, "-c", code], check=True)  # noqa: S603


def test_no_own_cryptography() -> None:
    """Only established libraries hash and sign; the core never touches hashlib/hmac.new."""
    for path in PACKAGE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "hashlib" not in text and "hmac.new" not in text, path.name


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
    assert sorted(packaged["app_profiles"]) == sorted(APP_PROFILES)
