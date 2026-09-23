"""Framework T-38: the installed runtime is stdlib-only and cannot bypass the consumer.

Optional renderers may import their third-party dependency only lazily inside
a function, so importing the package never requires openpyxl or WeasyPrint.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import auditcore_dataprotection

PACKAGE = Path(auditcore_dataprotection.__file__).parent
OPTIONAL = {"excel.py": {"openpyxl", "auditcore_reporting"}, "pdf.py": {"weasyprint"}}
FORBIDDEN_CALLS = {"open", "eval", "exec", "compile", "__import__"}
FORBIDDEN_MODULES = {
    "subprocess",
    "socket",
    "http",
    "urllib",
    "ftplib",
    "smtplib",
    "sqlite3",
    "pickle",
    "marshal",
    "shelve",
    "ctypes",
    "multiprocessing",
    "asyncio",
    "os",
    "shutil",
    "tempfile",
}


def _root(name: str | None) -> str:
    return (name or "").split(".")[0]


def test_runtime_imports_are_stdlib_or_own_package() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    modules = sorted(PACKAGE.rglob("*.py"))
    assert {p.name for p in modules} >= {
        "calculation.py",
        "rules.py",
        "legacy.py",
        "register.py",
        "assessment.py",
        "memory.py",
        "model.py",
        "ports.py",
    }
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        allowed_lazy = OPTIONAL.get(path.name, set())
        top_level = {id(n) for n in tree.body}
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [_root(a.name) for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = ["auditcore_dataprotection"] if node.level else [_root(node.module)]
            for name in names:
                if name == "auditcore_dataprotection":
                    continue
                if name in allowed_lazy:
                    assert id(node) not in top_level, f"{path.name}: {name} must be lazy"
                    continue
                assert name in stdlib, f"{path.name} imports {name}"
                assert name not in FORBIDDEN_MODULES, f"{path.name} imports {name}"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALLS, f"{path.name} calls {node.func.id}"


def test_profiles_are_packaged_data_not_code() -> None:
    profiles = PACKAGE / "profiles"
    assert sorted(p.name for p in profiles.glob("*.json")) == [
        "regulierung.dsgvo-2026.09.1.json",
        "regulierung.dsgvo-2026.10.1.json",
        "regulierung.hdsig_ji-2026.09.1.json",
        "regulierung.hdsig_ji-2026.10.1.json",
    ]


def test_import_does_not_load_optional_renderers() -> None:
    for name in ("openpyxl", "weasyprint", "auditcore_reporting", "sqlalchemy", "fastapi"):
        before = name in sys.modules
        import auditcore_dataprotection.assessment  # noqa: F401
        import auditcore_dataprotection.calculation  # noqa: F401
        import auditcore_dataprotection.memory  # noqa: F401
        import auditcore_dataprotection.register  # noqa: F401

        assert (name in sys.modules) == before
