import ast
from pathlib import Path


def test_domain_does_not_import_platform_or_web_frameworks():
    forbidden = {"fastapi", "flask", "django", "sqlalchemy", "auditcore"}
    for path in Path(__file__).parents[1].joinpath("src").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {entry.name.split(".")[0] for entry in node.names} & forbidden
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden
