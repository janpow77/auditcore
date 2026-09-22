"""Applicable framework T-38: pure formatting cannot bypass protected persistence."""

import ast
from pathlib import Path

import auditcore_reporting


def test_reporting_uses_only_its_own_api_and_standard_library():
    """Verify the complete installed Python module set has no infrastructure imports."""
    package = Path(auditcore_reporting.__file__).parent
    allowed = {"__future__", "re", "typing", "auditcore_reporting"}
    observed = set()
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                observed.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                observed.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__"}
    assert observed <= allowed
