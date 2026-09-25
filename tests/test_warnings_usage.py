"""`warnings` is allowed in runtime code only for DeprecationWarning aliases.

Decision of 2026-09-25 (docs/quality/code-quality.md): the architecture tests of
the packages admit the standard module ``warnings`` so that renamed public names
can keep an alias that warns. Any other use (filters, other categories,
``from warnings import …``) stays forbidden and is caught here for all packages
and the platform at once.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _runtime_modules() -> list[Path]:
    roots = [ROOT / "src" / "auditcore", *sorted((ROOT / "packages").glob("auditcore_*/src"))]
    return [path for root in roots for path in sorted(root.rglob("*.py"))]


def _category(call: ast.Call) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == "category":
            return keyword.value
    return call.args[1] if len(call.args) > 1 else None


def violations(source: str) -> list[str]:
    """Return the offending uses of the ``warnings`` module in ``source``."""
    tree = ast.parse(source)
    found: list[str] = []
    imported = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "warnings":
            found.append(f"{node.lineno}: from warnings import …")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "warnings":
                    imported = True
                    if alias.asname:
                        found.append(f"{node.lineno}: import warnings as {alias.asname}")
    if not imported:
        return found
    calls = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "warnings"
        ):
            continue
        if node.attr != "warn" or id(node) not in calls:
            found.append(f"{node.lineno}: warnings.{node.attr}")
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "warnings"
            and node.func.attr == "warn"
        ):
            category = _category(node)
            if not (isinstance(category, ast.Name) and category.id == "DeprecationWarning"):
                found.append(f"{node.lineno}: warnings.warn without DeprecationWarning")
    return found


def test_runtime_code_uses_warnings_only_for_deprecation() -> None:
    offending = {
        str(path.relative_to(ROOT)): hits
        for path in _runtime_modules()
        if (hits := violations(path.read_text(encoding="utf-8")))
    }
    assert offending == {}


def test_deprecation_alias_passes() -> None:
    source = "import warnings\nwarnings.warn('alt', DeprecationWarning, stacklevel=2)\n"
    assert violations(source) == []
    keyword = "import warnings\nwarnings.warn('alt', category=DeprecationWarning)\n"
    assert violations(keyword) == []


@pytest.mark.parametrize(
    "source",
    [
        "import warnings\nwarnings.warn('x')\n",
        "import warnings\nwarnings.warn('x', UserWarning)\n",
        "import warnings\nwarnings.simplefilter('ignore')\n",
        "import warnings\nwith warnings.catch_warnings():\n    pass\n",
        "import warnings\nwarn = warnings.warn\n",
        "from warnings import warn\n",
        "import warnings as w\n",
    ],
)
def test_other_uses_fail(source: str) -> None:
    assert violations(source)


def test_unrelated_names_called_warnings_are_ignored() -> None:
    assert violations("warnings = ()\nresult.warnings.append('x')\n") == []
