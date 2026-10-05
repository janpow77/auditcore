"""Der Kern bleibt ohne Plattform, Frameworks und Drittpakete importierbar."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

SOURCE = Path(__file__).parents[1] / "src"
FORBIDDEN_DATA = {".mdb", ".accdb", ".xlsx", ".xlsm", ".docx", ".docm", ".bak", ".csv"}


def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {entry.name.split(".")[0] for entry in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.add((node.module or "").split(".")[0])
    return names


def test_core_imports_only_stdlib_and_itself() -> None:
    allowed = set(sys.stdlib_module_names) | {"auditcore_officebank", "__future__"}
    for path in SOURCE.rglob("*.py"):
        foreign = _imports(path) - allowed
        assert not foreign, f"{path.name} importiert Nicht-Standardbibliothek: {sorted(foreign)}"


def test_package_data_has_no_office_files_or_addresses() -> None:
    files = [p for p in SOURCE.rglob("*") if p.is_file()]
    assert not [p.name for p in files if p.suffix.lower() in FORBIDDEN_DATA]
    email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    for path in files:
        if path.suffix in {".py", ".json", ".md", ".ps1"}:
            found = email.findall(path.read_text(encoding="utf-8"))
            assert all(addr.endswith(".invalid") for addr in found), path.name
