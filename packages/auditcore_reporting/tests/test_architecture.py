"""Applicable T-38: optional Office adapter remains separate from core and applications."""

import ast
import subprocess
import sys
from pathlib import Path

import auditcore_reporting


def test_reporting_dependency_boundary():
    package = Path(auditcore_reporting.__file__).parent
    for path in package.glob("*.py"):
        allowed = set(sys.stdlib_module_names) | {"__future__", "auditcore_reporting"}
        if path.name == "_excel.py":
            allowed.add("openpyxl")
        if path.name == "_ooxml.py":
            allowed.add("defusedxml")
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert {alias.name.split(".")[0] for alias in node.names} <= allowed
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] in allowed
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__"}


def test_core_import_and_formats_work_with_excel_import_forbidden():
    script = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname == "openpyxl" or fullname.startswith("openpyxl."):
            raise ModuleNotFoundError("optional dependency blocked", name="openpyxl")
sys.meta_path.insert(0, Block())
from auditcore_reporting import get_number_format, render_workbook, ExcelDependencyError
assert get_number_format("Betrag") == '#,##0.00 "EUR"'
try:
    render_workbook([])
except ExcelDependencyError:
    pass
else:
    raise AssertionError("Expected clear optional dependency error")
"""
    result = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
