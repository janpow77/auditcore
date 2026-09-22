"""Local AST inventory and conservative cross-repository candidate detection."""

from __future__ import annotations

import ast
import copy
import json
import re
from collections import defaultdict
from importlib.resources import files
from pathlib import Path
from typing import Any

from auditcore.tools.common import digest
from auditcore.tools.consolidator.models import LibraryCandidate, SymbolRecord
from auditcore.tools.quality.scanners import import_names, python_sources

DOMAINS = {
    "privacy": ("anonym", "redact", "pseudonym"),
    "statistics": ("benford", "statistic", "statistik", "outlier", "variance", "quantile"),
    "sampling": ("sample", "sampling", "stichprob"),
    "procurement": ("procurement", "vergabe", "tender"),
    "risk": ("risk", "risiko"),
    "reporting": ("report", "bericht", "excel", "xlsx", "numberformat"),
    "documents": ("document", "pdf", "docx", "invoice", "rechnung"),
}


def domain(name: str) -> str:
    """Classify names as heuristic domains, not authoritative business meaning."""
    tokens = re.findall(r"[a-z]+", re.sub(r"([a-z])([A-Z])", r"\1_\2", name).lower())
    lower = name.lower()
    if any(
        marker in lower for marker in ("testdatagenerator", "dummy_generator", "synthetic_data")
    ) and any(marker in lower for marker in ("generate_", "apply_deviation")):
        return "dummygenerator"
    return next(
        (
            category
            for category, words in DOMAINS.items()
            if any(token.startswith(word) for token in tokens for word in words)
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


def candidate_exclusion(symbol: dict[str, Any]) -> str:
    """Explain conservative exclusions without deleting observations from the inventory."""
    path = Path(symbol["path"])
    parts = {part.lower() for part in path.parts}
    name = symbol["symbol"].split(".")[-1].lower()
    if (
        parts & {"test", "tests", "testing", "fixtures", "__pycache__"}
        or path.name.startswith("test_")
        or path.name.endswith("_test.py")
        or name.startswith("test_")
        or path.name == "conftest.py"
    ):
        return "TEST_OR_FIXTURE"
    if parts & {
        "alembic",
        "migrations",
        "migration",
        "generated",
        "_generated",
        "vendor",
        "vendored",
        "node_modules",
        ".venv",
        "venv",
        "site-packages",
        "build",
        "dist",
    }:
        return "MIGRATION_GENERATED_OR_VENDOR_CODE"
    if path.name.endswith(("_pb2.py", "_pb2_grpc.py")):
        return "GENERATED_CODE"
    if symbol.get("framework_dependencies") or symbol.get("database_dependencies"):
        return "FRAMEWORK_OR_DATABASE_COUPLING"
    if parts & {
        "routers",
        "routes",
        "endpoints",
        "middleware",
        "auth",
        "authentication",
        "authorization",
        "oauth",
        "database",
        "db",
    }:
        return "APPLICATION_INFRASTRUCTURE"
    if name in {
        "health",
        "healthcheck",
        "health_check",
        "startup",
        "shutdown",
        "authorize",
        "authenticate",
        "login",
        "logout",
        "run_migrations_online",
        "run_migrations_offline",
    } or any(name.startswith(prefix) for prefix in ("get_current_user", "require_permission")):
        return "APPLICATION_INFRASTRUCTURE"
    calls = " ".join(symbol.get("callees", [])).lower()
    if any(
        marker in calls
        for marker in (
            "httpx.",
            "requests.",
            "subprocess.",
            "session.query",
            "session.execute",
            "joblib.",
            "threadpoolexecutor",
            "processpoolexecutor",
        )
    ):
        return "INFRASTRUCTURE_CALLS"
    if (
        symbol["symbol_type"] not in {"function", "method"}
        or symbol["end_line"] - symbol["line"] < 3
        or name.startswith("_")
    ):
        return "NO_PUBLIC_NONTRIVIAL_FUNCTION"
    if domain(f"{symbol['path']}.{symbol['symbol']}") == "utils":
        return "DOMAIN_REVIEW_REQUIRED"
    return ""


def _origins(group: list[dict[str, Any]]) -> tuple[list[list[str]], list[dict[str, str]]]:
    """Group proven shared revisions and embedded copies; similarity alone is not ancestry."""
    repositories = sorted({s["repository"] for s in group})
    parent = {repository: repository for repository in repositories}
    evidence = []

    def root(repository: str) -> str:
        while parent[repository] != repository:
            repository = parent[repository]
        return repository

    for source in group:
        for other in group:
            if source["repository"] >= other["repository"]:
                continue
            revision = source["commit_sha"]
            reason = ""
            if re.fullmatch(r"[0-9a-f]{40}", revision) and revision == other["commit_sha"]:
                reason = "IDENTICAL_GIT_COMMIT"
            elif source["fingerprint"] == other["fingerprint"]:
                for original, embedded in ((source, other), (other, source)):
                    suffix = original["repository"].split("/")[-1] + "/" + original["path"]
                    if embedded["path"].endswith(suffix):
                        reason = "IDENTICAL_SYMBOL_AT_EMBEDDED_REPOSITORY_PATH"
            if reason:
                parent[root(other["repository"])] = root(source["repository"])
                item = {
                    "source": source["repository"],
                    "related": other["repository"],
                    "evidence": reason,
                    "source_path": source["path"],
                    "related_path": other["path"],
                }
                if item not in evidence:
                    evidence.append(item)
    groups: dict[str, list[str]] = defaultdict(list)
    for repository in repositories:
        groups[root(repository)].append(repository)
    return list(groups.values()), evidence


def detect_candidates(
    symbols: list[dict[str, Any]],
    repositories: list[dict[str, Any]] | None = None,
) -> list[LibraryCandidate]:
    """Propose domain distributions; code occurrences never prove independent consumers."""
    metadata = {r["repository"]: r for r in repositories or []}
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for symbol in symbols:
        if not candidate_exclusion(symbol):
            category = domain(f"{symbol['path']}.{symbol['symbol']}")
            groups[(category, symbol["shape_fingerprint"])].append(symbol)
    candidates = []
    for (category, _), group in groups.items():
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
        target = "auditcore_" + category
        origin_groups, origin_evidence = _origins(group)
        # An observed license identifier is evidence, not a compatibility clearance.
        licenses = {metadata.get(repo, {}).get("license", "UNKNOWN") for repo in repos}
        license_status = (
            "REVIEW_REQUIRED"
            if licenses & {"UNKNOWN", "NOASSERTION", "", None}
            else "COMPATIBILITY_REVIEW_REQUIRED"
        )
        candidates.append(
            LibraryCandidate(
                target,
                [{k: s[k] for k in ("repository", "path", "symbol", "commit_sha")} for s in group],
                repos,
                "AST_IDENTICAL" if identical else "STRUCTURAL_SIMILARITY",
                conflict,
                decision,
                [],
                sorted(
                    {
                        d
                        for s in group
                        for d in s["framework_dependencies"] + s["database_dependencies"]
                    }
                ),
                [],
                "CHARACTERIZE" if identical and not security else "REVIEW_CONFLICT",
                target_distribution=target,
                package_directory="packages/" + target,
                license_status=license_status,
                potential_consumers=repos,
                origin_groups=origin_groups,
                origin_evidence=origin_evidence,
                independent_origins_status=(
                    "SHARED_ORIGIN_OBSERVED" if origin_evidence else "UNKNOWN"
                ),
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
