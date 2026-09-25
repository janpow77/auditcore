"""Boundaries: stdlib core, httpx only in the HTTP modules, no GPU hosts, no secrets."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import auditcore_llm_client

PACKAGE = Path(auditcore_llm_client.__file__).parent
HTTP_MODULES = {"transport.py", "sync_client.py", "async_client.py"}


def _imports(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.append(node.module or "")
    return names


def test_core_is_stdlib_and_httpx_is_confined() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for name in _imports(tree):
            root = name.split(".")[0]
            if root == "httpx":
                assert path.name in HTTP_MODULES, f"{path.name} imports httpx"
            else:
                assert root in stdlib or root == "auditcore_llm_client", f"{path.name}: {name}"
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}, path.name


def test_module_size() -> None:
    for path in PACKAGE.rglob("*.py"):
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 400, path.name


def test_no_hosts_ips_or_direct_gpu_paths_in_code() -> None:
    host = re.compile(r"https?://[A-Za-z0-9]|\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
    for path in PACKAGE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert not host.search(node.value), f"{path.name}: {node.value!r}"
        assert "11434" not in text.replace("DIRECT_OLLAMA_PORT = 11434", ""), path.name
        assert "ollama_fallback" not in text.lower(), path.name


def test_provenance_copies_match() -> None:
    packaged = json.loads((PACKAGE / "provenance.json").read_text(encoding="utf-8"))
    top = PACKAGE.parents[1] / "provenance.json"
    if top.is_file():
        assert json.loads(top.read_text(encoding="utf-8")) == packaged
    assert packaged["rights"]["authorization"]["status"] == "USER_AUTHORIZED_MIT"
    assert {(s["repository"], s["commit"]) for s in packaged["sources"]} == {
        ("janpow77/audit_designer", "ccd65245182982af3ef885a7a6d43583f4f72cbb"),
        ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
        ("janpow77/audit-portal", "d8eefa426826bdecb67036774f3128ae05e7d0d0"),
        ("janpow77/cockpit", "df203d4c33e786eb8a8ad3fe53b3b7eb9241d406"),
        ("janpow77/ai-router", "426cd78e86df9f822452af035b8d58a19f7aa820"),
        ("janpow77/flow-agent", "149e14be8952fddacb7601753dd2bf133fca51cb"),
    }
