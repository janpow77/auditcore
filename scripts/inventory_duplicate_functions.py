"""Inventory structurally duplicated functions across the auditcore domain packages.

Every function body below ``packages/*/src`` is normalised on the AST level:
docstrings, decorators, annotations and the function name are removed and all
locally bound identifiers (parameters, assignment/loop/comprehension targets,
exception names) are renamed in order of first appearance.  Free names
(imports, globals, builtins), attribute names and constants stay, because they
carry the behaviour.  The result is hashed (exact duplicates) and compared by
token similarity (near duplicates, ``difflib`` ratio >= threshold).

The output is JSON; ``docs/quality/duplikate.md`` is written from it by hand
review (variants must be described concretely, which no script can do).

Usage::

    python scripts/inventory_duplicate_functions.py --root . --output inventory.json
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

_TOKEN = re.compile(r"\w+|[^\w\s]")
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


@dataclass(frozen=True)
class Function:
    """One measured function body."""

    package: str
    path: str
    line: int
    name: str
    statements: int
    nodes: int
    digest: str
    tokens: tuple[str, ...]


class _Canonicaliser(ast.NodeTransformer):
    """Rename locally bound identifiers to v0, v1, ... in order of appearance."""

    def __init__(self, bound: set[str]) -> None:
        self.bound = bound
        self.mapping: dict[str, str] = {}

    def _rename(self, name: str) -> str:
        if name not in self.bound:
            return name
        return self.mapping.setdefault(name, f"v{len(self.mapping)}")

    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = self._rename(node.id)
        return node

    def visit_arg(self, node: ast.arg) -> ast.AST:
        node.arg = self._rename(node.arg)
        node.annotation = None
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        if node.name:
            node.name = self._rename(node.name)
        self.generic_visit(node)
        return node

    def visit_keyword(self, node: ast.keyword) -> ast.AST:
        self.generic_visit(node)
        return node


def _bound_names(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names = {arg.arg for arg in ast.walk(function.args) if isinstance(arg, ast.arg)}
    for node in ast.walk(function):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
    return names


def _strip(body: list[ast.stmt]) -> list[ast.stmt]:
    first = body[0] if body else None
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return body[1:]
    return body


def normalise(function: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, int, int]:
    """Return the canonical dump of a function, its statement and its node count."""
    clone = copy.deepcopy(function)
    clone.name = "_"
    clone.decorator_list = []
    clone.returns = None
    clone.body = _strip(clone.body) or [ast.Pass()]
    for node in ast.walk(clone):
        if isinstance(node, _FUNCTIONS) and node is not clone:
            node.body = _strip(node.body) or [ast.Pass()]
        if isinstance(node, ast.AnnAssign):
            node.annotation = ast.Constant(None)
    clone = _Canonicaliser(_bound_names(clone)).visit(clone)
    statements = sum(isinstance(node, ast.stmt) for node in ast.walk(clone)) - 1
    body = "\n".join(ast.dump(stmt, annotate_fields=False) for stmt in clone.body)
    arguments = ast.dump(clone.args, annotate_fields=False)
    nodes = sum(1 for stmt in clone.body for _ in ast.walk(stmt))
    return f"{arguments}\n{body}", statements, nodes


def iter_functions(root: Path) -> Iterator[Function]:
    """Yield every function of every domain package source tree."""
    for source in sorted(root.glob("packages/auditcore_*/src")):
        package = source.parent.name
        for path in sorted(source.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, _FUNCTIONS):
                    dump, statements, nodes = normalise(node)
                    yield Function(
                        package=package,
                        path=path.relative_to(root).as_posix(),
                        line=node.lineno,
                        name=node.name,
                        statements=statements,
                        nodes=nodes,
                        digest=hashlib.sha256(dump.encode()).hexdigest()[:16],
                        tokens=tuple(_TOKEN.findall(dump)),
                    )


def _shingles(tokens: tuple[str, ...], size: int = 5) -> set[tuple[str, ...]]:
    return {tokens[i : i + size] for i in range(max(1, len(tokens) - size + 1))}


def near_pairs(
    functions: list[Function], threshold: float, min_nodes: int
) -> list[tuple[int, int, float]]:
    """Cross-package pairs with a token similarity of at least ``threshold``."""
    candidates = [i for i, f in enumerate(functions) if f.nodes >= min_nodes]
    shingles = {i: _shingles(functions[i].tokens) for i in candidates}
    index: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for i in candidates:
        for shingle in shingles[i]:
            index[shingle].append(i)
    pairs = []
    for i in candidates:
        shared: dict[int, int] = defaultdict(int)
        for shingle in shingles[i]:
            for j in index[shingle]:
                if j > i and functions[j].package != functions[i].package:
                    shared[j] += 1
        for j, count in shared.items():
            union = len(shingles[i]) + len(shingles[j]) - count
            if count / union < 0.4 or functions[i].digest == functions[j].digest:
                continue
            ratio = SequenceMatcher(
                None, functions[i].tokens, functions[j].tokens, autojunk=False
            ).ratio()
            if ratio >= threshold:
                pairs.append((i, j, round(ratio, 3)))
    return pairs


def _clusters(size: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    parent = list(range(size))

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for left, right in edges:
        parent[find(left)] = find(right)
    groups: dict[int, list[int]] = defaultdict(list)
    for left, right in edges:
        groups[find(left)].extend((left, right))
    return [sorted(set(group)) for group in groups.values()]


def _describe(function: Function) -> dict[str, object]:
    return {
        "package": function.package,
        "path": function.path,
        "line": function.line,
        "name": function.name,
        "statements": function.statements,
        "nodes": function.nodes,
        "digest": function.digest,
    }


def _same_name(functions: list[Function], min_nodes: int) -> list[dict[str, object]]:
    """Public or private helpers with the same name in several packages (review aid)."""
    by_name: dict[str, list[Function]] = defaultdict(list)
    for function in functions:
        if function.nodes >= min_nodes and not function.name.startswith("__"):
            by_name[function.name].append(function)
    rows = []
    for name, members in sorted(by_name.items()):
        if len({m.package for m in members}) < 2:
            continue
        first = members[0]
        rows.append(
            {
                "name": name,
                "members": [_describe(m) for m in members],
                "ratio_to_first": [
                    round(SequenceMatcher(None, first.tokens, m.tokens, autojunk=False).ratio(), 3)
                    for m in members
                ],
            }
        )
    return rows


def inventory(root: Path, threshold: float, min_nodes: int) -> dict[str, object]:
    """Build the machine-readable duplicate inventory."""
    functions = list(iter_functions(root))
    by_digest: dict[str, list[int]] = defaultdict(list)
    for i, function in enumerate(functions):
        by_digest[function.digest].append(i)
    exact = [
        members
        for members in by_digest.values()
        if len({functions[i].package for i in members}) > 1
        and functions[members[0]].nodes >= min_nodes
    ]
    pairs = near_pairs(functions, threshold, min_nodes)
    exact_edges = [(g[0], other) for g in exact for other in g[1:]]
    clusters = _clusters(len(functions), exact_edges + [(i, j) for i, j, _ in pairs])
    ratios = {(i, j): r for i, j, r in pairs}
    groups = []
    for members in sorted(clusters, key=lambda g: (functions[g[0]].name, functions[g[0]].path)):
        digests = {functions[i].digest for i in members}
        groups.append(
            {
                "kind": "identical" if len(digests) == 1 else "variants",
                "packages": sorted({functions[i].package for i in members}),
                "members": [_describe(functions[i]) for i in members],
                "similarities": [
                    {"left": functions[i].path + ":" + str(functions[i].line),
                     "right": functions[j].path + ":" + str(functions[j].line),
                     "ratio": r}
                    for (i, j), r in sorted(ratios.items())
                    if i in members and j in members
                ],
            }
        )
    return {
        "functions_measured": len(functions),
        "threshold": threshold,
        "min_nodes": min_nodes,
        "groups": groups,
        "same_name": _same_name(functions, min_nodes),
    }


def main() -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--min-nodes", type=int, default=12)
    args = parser.parse_args()
    result = inventory(args.root.resolve(), args.threshold, args.min_nodes)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"{result['functions_measured']} functions, {len(result['groups'])} groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
