"""Extract Python functions and normalise their bodies for duplicate detection.

Normalisation drops docstrings, decorators, annotations and the function name,
renames arguments and local names by position and masks long string constants.
Two functions with the same ``body_hash`` differ at most in names, types and
texts.
"""

from __future__ import annotations

import ast
import copy
import re
import sys
import textwrap
from functools import lru_cache

from auditcore.tools.helpers.model import PYTHON, FunctionInfo, SourceFile, short_hash

TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|'[^']*'|\S")
LONG_STRING = 40
STDLIB = frozenset(sys.stdlib_module_names)


class _Renamer(ast.NodeTransformer):
    """Rename arguments and assigned names to positional placeholders."""

    def __init__(self) -> None:
        self.names: dict[str, str] = {}

    def _name(self, name: str) -> str:
        return self.names.setdefault(name, f"v{len(self.names)}")

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.arg = self._name(node.arg)
        node.annotation = None
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if isinstance(node.ctx, ast.Store) or node.id in self.names:
            node.id = self._name(node.id)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        if isinstance(node.value, str) and len(node.value) > LONG_STRING:
            node.value = "S"
        return node


def _without_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    first = body[0] if body else None
    value = first.value if isinstance(first, ast.Expr) else None
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return body[1:]
    return body


def normalised(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return the normalised source of a function."""
    clone = copy.deepcopy(node)
    clone.body = _without_docstring(clone.body) or [ast.Pass()]
    clone.decorator_list = []
    clone.returns = None
    clone.name = "F"
    _Renamer().visit(clone)
    return ast.unparse(clone)


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _kind(parent: ast.AST | None) -> str:
    if isinstance(parent, ast.ClassDef):
        return "method"
    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return "nested"
    return "function"


def _qualified(node: ast.AST, parents: dict[ast.AST, ast.AST], name: str) -> str:
    parent = parents.get(node)
    return f"{parent.name}.{name}" if isinstance(parent, ast.ClassDef) else name


def module_prelude(tree: ast.Module, source: str) -> dict[str, str]:
    """Return stdlib imports, module-level assignments, functions and classes by bound name."""
    prelude: dict[str, str] = {}
    for statement in tree.body:
        segment = ast.get_source_segment(source, statement) or ""
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            module = statement.module if isinstance(statement, ast.ImportFrom) else None
            roots = [module or ""] if module else [alias.name for alias in statement.names]
            if statement_level(statement) == 0 and all(r.split(".")[0] in STDLIB for r in roots):
                for alias in statement.names:
                    prelude[(alias.asname or alias.name).split(".")[0]] = segment
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            prelude[statement.name] = segment
        else:
            name = _assigned_name(statement)
            if name:
                prelude[name] = segment
    return prelude


def _assigned_name(statement: ast.stmt) -> str:
    """Name bound by a simple module-level (annotated) assignment."""
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
        target: ast.expr = statement.targets[0]
    elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
        target = statement.target
    else:
        return ""
    return target.id if isinstance(target, ast.Name) else ""


def statement_level(statement: ast.Import | ast.ImportFrom) -> int:
    """Relative import level (0 for absolute imports)."""
    return statement.level if isinstance(statement, ast.ImportFrom) else 0


def _names(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


@lru_cache(maxsize=4096)
def _segment_names(segment: str) -> frozenset[str]:
    try:
        return frozenset(_names(ast.parse(textwrap.dedent(segment))))
    except SyntaxError:
        return frozenset()


def _needed(node: ast.AST, prelude: dict[str, str]) -> tuple[str, ...]:
    """Prelude segments the function needs, including those of needed assignments."""
    used = _names(node)
    selected: set[str] = set()
    pending = [name for name in used if name in prelude]
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        selected.add(name)
        extra = _segment_names(prelude[name])
        pending.extend(item for item in extra if item in prelude and item not in selected)
    ordered: list[str] = []
    for name, segment in prelude.items():
        if name in selected and segment not in ordered:
            ordered.append(segment)
    return tuple(ordered)


def _info(
    file: SourceFile,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[ast.AST, ast.AST],
    prelude: dict[str, str],
) -> FunctionInfo | None:
    kind = _kind(parents.get(node))
    if kind == "nested":
        return None
    try:
        text = normalised(node)
    except (ValueError, RecursionError):
        return None
    segment = ast.get_source_segment(file.text, node) or ""
    return FunctionInfo(
        language=PYTHON,
        path=file.path,
        name=_qualified(node, parents, node.name),
        kind=kind,
        line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        tokens=len(TOKEN.findall(text)),
        body_hash=short_hash(ast.dump(ast.parse(text)), 16),
        source=textwrap.dedent(segment),
        exported=not node.name.startswith("_"),
        params=len(node.args.args),
        prelude=_needed(node, prelude) if kind == "function" else (),
    )


def scan_python(file: SourceFile) -> list[FunctionInfo]:
    """Return top-level functions and methods of one Python file."""
    try:
        tree = ast.parse(file.text)
    except (SyntaxError, ValueError):
        return []
    parents = _parents(tree)
    prelude = module_prelude(tree, file.text)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info = _info(file, node, parents, prelude)
            if info is not None:
                found.append(info)
    return found
