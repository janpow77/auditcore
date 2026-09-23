"""Runtime modules: stdlib, own package, entity_matching, harvest; optional extras lazily."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_registry_sources

ALLOWED = {
    "__future__",
    "collections",
    "csv",
    "dataclasses",
    "datetime",
    "difflib",
    "enum",
    "functools",
    "hashlib",
    "importlib",
    "io",
    "json",
    "re",
    "types",
    "typing",
    "xml",
    "auditcore_registry_sources",
    "auditcore_entity_matching",
    "auditcore_harvest",
}
OPTIONAL = {"rapidfuzz", "defusedxml", "bs4"}
FORBIDDEN_CALLS = {"open", "eval", "exec", "__import__", "compile"}
FORBIDDEN_MODULES = {
    "subprocess",
    "socket",
    "sqlalchemy",
    "requests",
    "httpx",
    "urllib",
    "os",
    "logging",
    "auditcore",
}


def _modules() -> list[Path]:
    return sorted(Path(auditcore_registry_sources.__file__).parent.glob("*.py"))


def test_imports_are_restricted_and_extras_are_lazy() -> None:
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        top_level = {id(n) for n in tree.body}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = (
                    ["auditcore_registry_sources"]
                    if node.level
                    else [(node.module or "").split(".")[0]]
                )
            else:
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    assert node.func.id not in FORBIDDEN_CALLS, path.name
                continue
            for name in names:
                assert name not in FORBIDDEN_MODULES, (path.name, name)
                if name in OPTIONAL:
                    assert id(node) not in top_level, (path.name, name)
                else:
                    assert name in ALLOWED, (path.name, name)


def test_xml_is_only_parsed_through_defusedxml() -> None:
    for path in _modules():
        text = path.read_text(encoding="utf-8")
        assert "ElementTree import fromstring" not in text.replace(
            "defusedxml.ElementTree import fromstring", ""
        ), path.name
        assert "ET.fromstring" not in text and "ElementTree.parse" not in text, path.name


def test_import_does_not_load_network_or_optional_libraries() -> None:
    code = (
        "import sys, auditcore_registry_sources; "
        "bad = {'rapidfuzz', 'defusedxml', 'bs4', 'httpx', 'socket', 'auditcore'}; "
        "bad &= set(sys.modules); "
        "assert not bad, bad"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
