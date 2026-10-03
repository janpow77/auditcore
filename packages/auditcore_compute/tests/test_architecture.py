"""Import boundaries and determinism rules, checked on the source (AST)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import auditcore_compute

PACKAGE = Path(auditcore_compute.__file__).parent
ALLOWED = {
    "__future__",
    "collections",
    "contextlib",
    "contextvars",
    "dataclasses",
    "datetime",
    "decimal",
    "fractions",
    "hashlib",
    "importlib",
    "logging",
    "math",
    "numpy",
    "os",
    "pathlib",
    "threading",
    "types",
    "typing",
}


@pytest.fixture(autouse=True)
def engine_path() -> str:
    """Static checks run once (overrides the parametrised conftest fixture)."""
    return "static"


def _trees() -> list[tuple[Path, ast.Module]]:
    return [(p, ast.parse(p.read_text(encoding="utf-8"))) for p in sorted(PACKAGE.glob("*.py"))]


def test_imports_only_standard_library_and_numpy() -> None:
    observed: set[str] = set()
    for path, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                observed.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                observed.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "__import__", "print"}, path
    # Numba is optional: it is only loaded through importlib in _engine.
    assert observed <= ALLOWED, observed - ALLOWED


def _accelerate_options(function: ast.FunctionDef) -> dict[str, ast.expr] | None:
    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "accelerate":
            return {}
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "accelerate"
        ):
            return {k.arg or "": k.value for k in decorator.keywords}
    return None


def _kernels() -> list[tuple[str, ast.FunctionDef, dict[str, ast.expr]]]:
    found = []
    for path, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                options = _accelerate_options(node)
                if options is not None:
                    found.append((f"{path.name}:{node.name}", node, options))
    return found


def test_no_kernel_requests_fastmath() -> None:
    kernels = _kernels()
    assert len(kernels) >= 10
    for name, _node, options in kernels:
        assert "fastmath" not in options, name


def test_parallel_kernels_are_element_wise() -> None:
    """``parallel=True`` only where no scalar is accumulated (no parallel reductions)."""
    for name, node, options in _kernels():
        flag = options.get("parallel")
        if not (isinstance(flag, ast.Constant) and flag.value is True):
            continue
        loops = [n for n in ast.walk(node) if isinstance(n, ast.For)]
        assert loops and all(
            isinstance(loop.iter, ast.Call)
            and isinstance(loop.iter.func, ast.Name)
            and loop.iter.func.id == "prange"
            for loop in loops
        ), name
        for statement in ast.walk(node):
            if isinstance(statement, ast.AugAssign):
                assert not isinstance(statement.target, ast.Name), name
