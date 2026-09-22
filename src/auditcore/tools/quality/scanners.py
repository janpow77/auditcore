"""Deterministic scanners; findings never contain matched secret values."""

from __future__ import annotations

import ast
import ipaddress
import re
from pathlib import Path

from auditcore.models import CheckResult, CheckStatus

SECRET_PATTERNS = (
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b",
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
    r"(?i)\bBearer\s+[A-Za-z0-9_.-]{20,}",
    r"""(?i)\b(?:password|passwd|api_key|access_token|secret|token)["']?\s*[:=]\s*["'][^"'\n]{8,}["']""",
    r"\bsk-[A-Za-z0-9_-]{24,}\b",
)
PRIVACY_PATTERNS = (
    r"\b[\w.-]+@(?:[\w-]+\.)+[A-Za-z]{2,}\b",
    r"\b(?:[\w-]+\.)+(?:local|internal)\b",
    r"\blocalhost\b",
    r"\\\\[\w.-]+\\",
    r"[A-Za-z]:\\[^\s]+",
    r"/(?:home|Users)/[^/\s]+",
    r"https?://[^/\s]+(?:\.internal|\.local)",
)


def scan_sensitive(text: str, path: str = "") -> list[CheckResult]:
    """Find secrets and privacy indicators without echoing their contents."""
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        if any(re.search(pattern, line) for pattern in SECRET_PATTERNS):
            findings.append(
                CheckResult(
                    "AC-SEC-001",
                    CheckStatus.FAIL,
                    "Potential credential; value redacted",
                    path,
                    number,
                )
            )
        privacy = any(re.search(pattern, line) for pattern in PRIVACY_PATTERNS)
        for token in re.findall(r"[0-9a-fA-F:.]{3,}", line):
            try:
                ipaddress.ip_address(token)
                privacy = True
            except ValueError:
                continue
        if privacy:
            findings.append(
                CheckResult(
                    "AC-OSS-001",
                    CheckStatus.REVIEW_REQUIRED,
                    "Potential internal or personal identifier; review required",
                    path,
                    number,
                )
            )
    return findings


def import_names(tree: ast.AST) -> list[tuple[str, int]]:
    """Return AST imports, including explicit imported members."""
    result: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result.append((node.module or "", node.lineno))
            result.extend(
                (f"{node.module or ''}.{alias.name}", node.lineno) for alias in node.names
            )
    return result


def api_snapshot(sources: dict[str, str]) -> dict[str, dict[str, str]]:
    """Capture public modules, classes, methods, signatures and explicit raises."""
    snapshot: dict[str, dict[str, str]] = {}
    for path, text in sorted(sources.items()):
        tree = ast.parse(text)
        module = path.removesuffix(".py").replace("/", ".").removesuffix(".__init__")
        snapshot[module] = {"kind": "module"}

        def visit(nodes: list[ast.stmt], prefix: str) -> None:
            """Capture visible declarations recursively under their qualified name."""
            for node in nodes:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name.startswith("_"):
                        continue
                    name = f"{prefix}.{node.name}"
                    if isinstance(node, ast.ClassDef):
                        attributes = [
                            ast.unparse(n) for n in node.body if isinstance(n, ast.AnnAssign)
                        ]
                        snapshot[name] = {
                            "kind": "class",
                            "fields": "\n".join(attributes),
                            "bases": ",".join(ast.unparse(b) for b in node.bases),
                        }
                        visit(node.body, name)
                    else:
                        raises = sorted(
                            {
                                ast.unparse(n.exc.func if isinstance(n.exc, ast.Call) else n.exc)
                                for n in ast.walk(node)
                                if isinstance(n, ast.Raise) and n.exc
                            }
                        )
                        snapshot[name] = {
                            "kind": "async_function"
                            if isinstance(node, ast.AsyncFunctionDef)
                            else "function",
                            "signature": ast.unparse(node.args),
                            "returns": ast.unparse(node.returns) if node.returns else "UNKNOWN",
                            "raises": ",".join(raises),
                        }

        visit(tree.body, module)
    return snapshot


def architecture(
    tree: ast.AST,
    path: str,
    forbidden: list[str],
    core: bool,
) -> list[CheckResult]:
    """Check core dependency direction without scanning comments as imports."""
    if not core:
        return []
    result = []
    frameworks = {"fastapi", "flask", "django", "starlette"}
    infrastructure = {
        "sqlalchemy",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "requests",
        "httpx",
        "sqlite3",
        "urllib.request",
        "auditcore.tools",
    } | set(forbidden)
    imports = import_names(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and ast.unparse(node.func) in {"__import__", "importlib.import_module"}
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            imports.append((node.args[0].value, node.lineno))
        if (
            isinstance(node, ast.ImportFrom)
            and node.level
            and (node.module or "").startswith("tools")
        ):
            imports.append(("auditcore." + (node.module or ""), node.lineno))
    for name, line in imports:
        for code, banned in (("AC-ARCH-001", frameworks), ("AC-ARCH-002", infrastructure)):
            if any(name == item or name.startswith(item + ".") for item in banned):
                result.append(
                    CheckResult(
                        code, CheckStatus.FAIL, f"Forbidden core import: {name}", path, line
                    )
                )
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.level
            and any(alias.name == "tools" for alias in node.names)
        ):
            result.append(
                CheckResult(
                    "AC-ARCH-002",
                    CheckStatus.FAIL,
                    "Core imports relative tools namespace",
                    path,
                    node.lineno,
                )
            )
    return result


def documentation_complexity(
    tree: ast.AST, path: str, *, detailed: bool = False, bilingual: bool = False
) -> list[CheckResult]:
    """Check public documentation, annotations and structural complexity."""
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not node.name.startswith("_") and not ast.get_docstring(node):
            results.append(
                CheckResult(
                    "AC-DOC-001",
                    CheckStatus.WARNING,
                    "Public API lacks a docstring",
                    path,
                    node.lineno,
                )
            )
        if isinstance(node, ast.ClassDef):
            continue
        args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
        doc = ast.get_docstring(node) or ""
        if detailed and not node.name.startswith("_"):
            undocumented = [
                a.arg for a in args if a.arg not in {"self", "cls"} and a.arg not in doc
            ]
            if (
                undocumented
                or node.returns
                and ast.unparse(node.returns) != "None"
                and ("Returns" not in doc and "Rückgabe" not in doc)
                or any(isinstance(n, ast.Raise) for n in ast.walk(node))
                and ("Raises" not in doc and "Exceptions" not in doc)
            ):
                results.append(
                    CheckResult(
                        "AC-DOC-001",
                        CheckStatus.WARNING,
                        "Incomplete parameter/return/exception documentation",
                        path,
                        node.lineno,
                    )
                )
        if (
            bilingual
            and not node.name.startswith("_")
            and not all(t in doc for t in ("DE:", "EN:"))
        ):
            results.append(
                CheckResult(
                    "AC-DOC-001",
                    CheckStatus.WARNING,
                    "Public documentation needs DE: and EN: sections",
                    path,
                    node.lineno,
                )
            )
        if not node.name.startswith("_") and (
            not node.returns or any(not a.annotation for a in args if a.arg not in {"self", "cls"})
        ):
            results.append(
                CheckResult(
                    "AC-TYPE-001",
                    CheckStatus.WARNING,
                    "Public signature lacks annotations",
                    path,
                    node.lineno,
                )
            )
        complexity = 1 + sum(
            isinstance(
                n, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.IfExp, ast.comprehension)
            )
            for n in ast.walk(node)
        )
        depth = _depth(node)
        if (
            (node.end_lineno or node.lineno) - node.lineno > 100
            or len(args) > 10
            or (complexity > 20 or depth > 8)
        ):
            results.append(
                CheckResult(
                    "AC-COMP-001",
                    CheckStatus.WARNING,
                    f"Complexity={complexity}, nesting={depth}, args={len(args)}",
                    path,
                    node.lineno,
                )
            )
    return results


def _depth(node: ast.AST) -> int:
    return int(isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With))) + max(
        (_depth(child) for child in ast.iter_child_nodes(node)), default=0
    )


def python_sources(root: Path, exclude: list[str] | None = None) -> dict[str, str]:
    """Read Python sources, excluding dependency environments and generated outputs."""
    excluded = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".auditcore",
        "build",
        "dist",
        "__pycache__",
    }
    result = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if (
            path.is_symlink()
            or excluded.intersection(relative.parts)
            or any(relative.match(pattern) for pattern in (exclude or []))
        ):
            continue
        result[relative.as_posix()] = path.read_text(encoding="utf-8-sig")
    return result


def text_resources(root: Path, exclude: list[str] | None = None) -> dict[str, str]:
    """Read shipped text resources for secret scanning and exact wheel/source binding."""
    suffixes = {
        ".json",
        ".toml",
        ".yaml",
        ".yml",
        ".ini",
        ".cfg",
        ".env",
        ".txt",
        ".md",
        ".rst",
        ".tmpl",
        ".typed",
    }
    excluded = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".auditcore",
        "build",
        "dist",
        "__pycache__",
    }
    resources = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if (
            path.is_symlink()
            or not path.is_file()
            or excluded.intersection(relative.parts)
            or any(relative.match(pattern) for pattern in (exclude or []))
        ):
            continue
        if path.suffix in suffixes or path.name.startswith(".env"):
            resources[relative.as_posix()] = path.read_text(encoding="utf-8-sig")
    return resources
