"""Count functions duplicated across packages (metric ``duplicate_functions``).

Every function body is normalised on the AST level: docstring, decorators,
annotations and the name are dropped, locally bound identifiers are renamed
in order of appearance and string constants are replaced by a placeholder
(messages and resource names differ between otherwise equal copies). Free
names, attribute names and numbers stay because they carry the behaviour.

A function counts for its package when a function with the same normal form
exists in another measured package and the body has at least
``MIN_STATEMENTS`` statements and ``MIN_NODES`` AST nodes. The shared package
``auditcore_common`` is the canonical home of such helpers: its own functions
never count, a package copy of one of them does.
"""

from __future__ import annotations

import ast
import copy
import hashlib
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from auditcore.tools.quality.codegate_python import Finding, python_files

METRIC = "duplicate_functions"
MIN_STATEMENTS = 2
MIN_NODES = 25
CANONICAL_PACKAGE = "auditcore_common"
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


@dataclass(frozen=True)
class FunctionSite:
    """Location and normal-form digest of one function."""

    package: str
    path: str
    line: int
    name: str
    digest: str


class _Canonicaliser(ast.NodeTransformer):
    """Rename bound names to v0, v1, … and replace string constants."""

    def __init__(self, bound: set[str]) -> None:
        self.bound = bound
        self.mapping: dict[str, str] = {}

    def _rename(self, name: str) -> str:
        if name not in self.bound:
            return name
        return self.mapping.setdefault(name, f"v{len(self.mapping)}")

    def visit_Name(self, node: ast.Name) -> ast.AST:
        """Rename a bound name."""
        node.id = self._rename(node.id)
        return node

    def visit_arg(self, node: ast.arg) -> ast.AST:
        """Rename a parameter and drop its annotation."""
        node.arg = self._rename(node.arg)
        node.annotation = None
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        """Rename the exception name."""
        if node.name:
            node.name = self._rename(node.name)
        self.generic_visit(node)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Replace text and bytes constants by their type."""
        if isinstance(node.value, str | bytes):
            return ast.Constant(type(node.value).__name__)
        return node


def _bound_names(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names = {arg.arg for arg in ast.walk(function.args) if isinstance(arg, ast.arg)}
    for node in ast.walk(function):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
    return names


def _without_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    first = body[0] if body else None
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return body[1:] or [ast.Pass()]
    return body


def normal_form(function: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, int, int]:
    """Canonical dump, statement count and node count of a function body."""
    clone = copy.deepcopy(function)
    clone.name = "_"
    clone.decorator_list = []
    clone.returns = None
    for node in ast.walk(clone):
        if isinstance(node, _FUNCTIONS):
            node.body = _without_docstring(node.body)
        if isinstance(node, ast.AnnAssign):
            node.annotation = ast.Constant(None)
    clone = _Canonicaliser(_bound_names(clone)).visit(clone)
    statements = sum(isinstance(node, ast.stmt) for node in ast.walk(clone)) - 1
    nodes = sum(1 for stmt in clone.body for _ in ast.walk(stmt))
    body = "\n".join(ast.dump(stmt, annotate_fields=False) for stmt in clone.body)
    return f"{ast.dump(clone.args, annotate_fields=False)}\n{body}", statements, nodes


def function_sites(package: str, source: Path, root: Path) -> Iterator[FunctionSite]:
    """Every function of a source tree that is large enough to count."""
    for path in python_files(source):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, _FUNCTIONS):
                continue
            dump, statements, nodes = normal_form(node)
            if statements < MIN_STATEMENTS or nodes < MIN_NODES:
                continue
            digest = hashlib.sha256(dump.encode("utf-8")).hexdigest()
            relative = path.relative_to(root).as_posix()
            yield FunctionSite(package, relative, node.lineno, node.name, digest)


def duplicate_findings(sources: Iterable[tuple[str, Path]], root: Path) -> dict[str, list[Finding]]:
    """Findings per package for functions that also exist in another package."""
    by_digest: dict[str, list[FunctionSite]] = defaultdict(list)
    for package, source in sources:
        for site in function_sites(package, source, root):
            by_digest[site.digest].append(site)
    findings: dict[str, list[Finding]] = defaultdict(list)
    for sites in by_digest.values():
        if len({site.package for site in sites}) < 2:
            continue
        for site in sites:
            if site.package == CANONICAL_PACKAGE:
                continue
            others = sorted(f"{o.package}:{o.name}" for o in sites if o.package != site.package)
            detail = f"{site.name}: gleich mit {', '.join(others)}"
            findings[site.package].append(Finding(METRIC, site.path, site.line, detail))
    return findings
