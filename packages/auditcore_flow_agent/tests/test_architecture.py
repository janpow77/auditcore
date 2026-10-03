"""Die Bibliothek bleibt ohne Plattform und Anwendungsframework importierbar."""

import ast
from pathlib import Path


def test_no_platform_or_application_imports():
    forbidden = {"auditcore", "fastapi", "flask", "django", "sqlalchemy", "torch"}
    for path in Path(__file__).parents[1].joinpath("src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert not {entry.name.split(".")[0] for entry in node.names} & forbidden
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden
