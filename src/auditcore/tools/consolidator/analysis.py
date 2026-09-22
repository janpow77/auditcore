"""Local AST inventory and conservative cross-repository candidate detection."""

from __future__ import annotations

import ast
import copy
import json
from collections import defaultdict
from importlib.resources import files
from pathlib import Path
from typing import Any

from auditcore.tools.common import digest
from auditcore.tools.consolidator.models import LibraryCandidate, SymbolRecord
from auditcore.tools.quality.scanners import import_names, python_sources

DOMAINS = {
    "documents": ("document", "pdf", "docx", "text", "extract", "parser"),
    "reporting": ("report", "export", "bericht", "render"),
    "risk": ("risk", "risiko", "score"),
    "sampling": ("sample", "sampling", "stichprob"),
    "procurement": ("procurement", "vergabe", "tender"),
    "validation": ("valid", "check", "pruef", "parse"),
    "anonymization": ("anonym", "redact", "pseudonym"),
}


def domain(name: str) -> str:
    """Classify names as heuristic domains, not authoritative business meaning."""
    return next(
        (
            category
            for category, words in DOMAINS.items()
            if any(word in name.lower() for word in words)
        ),
        "utils",
    )


class _Normalize(ast.NodeTransformer):
    def __init__(self, shape: bool) -> None:
        self.shape = shape

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        """Normalize only function names and docstrings for structural comparison."""
        node.name = "FUNCTION"
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body = node.body[1:]
        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """Retain literal types when comparing shapes and values for exact matches."""
        if self.shape:
            return ast.copy_location(ast.Constant(value=type(node.value).__name__), node)
        return node


def analyze_sources(
    sources: dict[str, str],
    repository: str,
    commit: str,
) -> tuple[list[SymbolRecord], list[dict[str, str]], list[str]]:
    """Extract symbols and imports without importing or executing repository code."""
    symbols = []
    edges = []
    errors = []
    policy = load_policy("human_decisions")
    security_words = policy["security_boundaries"]
    for path, source in sorted(sources.items()):
        try:
            tree = ast.parse(source)
        except SyntaxError:
            errors.append(f"{path}: invalid Python syntax")
            continue
        module = path.removesuffix(".py").replace("/", ".").removesuffix(".__init__")
        imports = sorted({name for name, _ in import_names(tree)})
        for name in imports:
            edges.append(
                {
                    "repository": repository,
                    "source": module,
                    "target": name,
                    "kind": "import",
                    "commit_sha": commit,
                    "path": path,
                }
            )
        framework = [
            x for x in imports if x.split(".")[0] in {"fastapi", "flask", "django", "starlette"}
        ]
        database = [
            x
            for x in imports
            if x.split(".")[0] in {"sqlalchemy", "psycopg", "asyncpg", "sqlite3", "pymongo"}
        ]

        def visit(
            nodes: list[ast.stmt],
            parent: str = "",
            *,
            source: str = source,
            path: str = path,
            module: str = module,
            imports: list[str] = imports,
            framework: list[str] = framework,
            database: list[str] = database,
        ) -> None:
            """Collect scoped symbol observations and conservative static call edges."""
            for node in nodes:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = f"{parent}.{node.name}" if parent else node.name
                    if isinstance(node, ast.ClassDef):
                        bases = [ast.unparse(b) for b in node.bases]
                        decorators = [ast.unparse(d) for d in node.decorator_list]
                        kind = "class"
                        for marker, category in (
                            ("Enum", "enum"),
                            ("Protocol", "protocol"),
                            ("BaseModel", "pydantic_model"),
                            ("dataclass", "dataclass"),
                        ):
                            if any(marker in b for b in bases + decorators):
                                kind = category
                        signature = ", ".join(bases)
                    else:
                        kind = "method" if parent else "function"
                        signature = ast.unparse(node.args)
                    callees = sorted(
                        {ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)}
                    )
                    source_node = ast.get_source_segment(source, node) or ""
                    normalized = _Normalize(False).visit(copy.deepcopy(node))
                    shape = _Normalize(True).visit(copy.deepcopy(node))
                    constants = sorted(
                        {
                            repr(n.value)
                            for n in ast.walk(node)
                            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                        }
                    )
                    symbols.append(
                        SymbolRecord(
                            repository,
                            path,
                            module,
                            name,
                            kind,
                            signature,
                            (ast.get_docstring(node) or "").split("\n")[0][:200],
                            imports,
                            [],
                            callees,
                            framework,
                            database,
                            domain(f"{module}.{name}"),
                            commit,
                            node.lineno,
                            node.end_lineno or node.lineno,
                            digest(ast.dump(normalized)),
                            digest(ast.dump(shape)),
                            constants,
                            any(word in source_node.lower() for word in security_words),
                        )
                    )
                    for callee in callees:
                        edges.append(
                            {
                                "repository": repository,
                                "source": f"{module}.{name}",
                                "target": callee,
                                "kind": "call",
                                "commit_sha": commit,
                                "path": path,
                            }
                        )
                    if isinstance(node, ast.ClassDef):
                        visit(node.body, name)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            symbols.append(
                                SymbolRecord(
                                    repository,
                                    path,
                                    module,
                                    target.id,
                                    "constant",
                                    "",
                                    "",
                                    imports,
                                    [],
                                    [],
                                    framework,
                                    database,
                                    domain(module),
                                    commit,
                                    node.lineno,
                                    node.end_lineno or node.lineno,
                                    digest(ast.dump(node)),
                                    digest(ast.dump(node)),
                                    [],
                                    False,
                                )
                            )

        visit(tree.body)
    by_short: dict[str, list[SymbolRecord]] = defaultdict(list)
    for symbol in symbols:
        by_short[symbol.symbol.split(".")[-1]].append(symbol)
    for symbol in symbols:
        for callee in symbol.callees:
            matches = by_short.get(callee.split(".")[-1], [])
            if len(matches) == 1:
                matches[0].callers.append(f"{symbol.module}.{symbol.symbol}")
    return symbols, edges, errors


def analyze_repository(root: Path, repository: str, commit: str) -> dict[str, Any]:
    """Return structural observations and parse failures."""
    sources = python_sources(root)
    symbols, dependencies, errors = analyze_sources(sources, repository, commit)
    return {
        "symbols": symbols,
        "dependencies": dependencies,
        "errors": errors,
        "python_files": len(sources),
        "scope": "Python AST; unresolved dynamic calls remain unknown",
    }


def load_policy(name: str) -> dict[str, Any]:
    """Load installed policy resources used by workflow decisions."""
    resource = files("auditcore.tools.consolidator").joinpath(f"policies/{name}.json")
    result: dict[str, Any] = json.loads(resource.read_text())
    return result


def load_prompt(name: str) -> dict[str, str]:
    """Load a versioned installed prompt with a content hash."""
    content = files("auditcore.tools.consolidator").joinpath(f"prompts/{name}.md").read_text()
    lines = content.splitlines()
    return {
        "name": name,
        "version": lines[2].split(":", 1)[1].strip(),
        "sha256": digest(content),
        "content": content,
    }


def detect_candidates(symbols: list[dict[str, Any]]) -> list[LibraryCandidate]:
    """Detect exact/structural duplicates; different constants require human review."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for symbol in symbols:
        if (
            symbol["symbol_type"] in {"function", "method"}
            and (symbol["end_line"] - symbol["line"] >= 3)
            and not symbol["symbol"].split(".")[-1].startswith("_")
        ):
            groups[symbol["shape_fingerprint"]].append(symbol)
    candidates = []
    for group in groups.values():
        repos = sorted({s["repository"] for s in group})
        if len(repos) < 2:
            continue
        identical = len({s["fingerprint"] for s in group}) == 1
        security = any(s["security_sensitive"] for s in group)
        conflict = "IDENTICAL" if identical else "SEMANTICALLY_DIFFERENT"
        decision = (
            "SECURITY_OR_POLICY_REVIEW_REQUIRED"
            if security
            else ("REVIEW_REQUIRED" if identical else "HUMAN_DECISION_REQUIRED")
        )
        candidates.append(
            LibraryCandidate(
                "auditcore." + group[0]["domain_category"],
                [{k: s[k] for k in ("repository", "path", "symbol", "commit_sha")} for s in group],
                repos,
                "AST_IDENTICAL" if identical else "STRUCTURAL_SIMILARITY",
                conflict,
                decision,
                repos,
                sorted(
                    {
                        d
                        for s in group
                        for d in s["framework_dependencies"] + s["database_dependencies"]
                    }
                ),
                [],
                "CHARACTERIZE" if identical and not security else "REVIEW_CONFLICT",
            )
        )
    return candidates


def choose_mode(task: str) -> str:
    """Choose conservative shared-core scope when intent is uncertain."""
    if any(word in task.lower() for word in ("global", "gesamt", "landscape")):
        return "GLOBAL"
    if any(word in task.lower() for word in ("ui", "frontend", "routing", "css")):
        return "REPO"
    return "REPO_AUDITCORE"
