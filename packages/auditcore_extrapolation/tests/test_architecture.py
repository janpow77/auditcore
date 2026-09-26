"""Standard-library-only core without I/O; the web layer is optional."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_extrapolation

ALLOWED = {
    "__future__",
    "collections",
    "dataclasses",
    "decimal",
    "math",
    "statistics",
    "types",
    "typing",
}


def test_core_imports_only_the_standard_library() -> None:
    package = Path(auditcore_extrapolation.__file__).parent
    observed: set[str] = set()
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                observed.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                observed.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__", "print"}, path
    assert observed <= ALLOWED, observed - ALLOWED


def test_every_public_formula_names_its_source() -> None:
    """Each public function documents the guidance section or template it implements."""
    markers = ("section", "Section", "Appendix", "Annex", "template", "guidance", "Art.")
    exempt = {"assess", "project", "evaluate", "split_top_stratum_for_plan", "residual_from_total"}
    for name in auditcore_extrapolation.__all__:
        obj = getattr(auditcore_extrapolation, name)
        if callable(obj) and not isinstance(obj, type) and name not in exempt:
            doc = obj.__doc__ or ""
            assert any(m in doc for m in markers), name
