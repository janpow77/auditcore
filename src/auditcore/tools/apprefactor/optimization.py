"""Measured, reversible technical optimization operations."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import time
import tomllib
import tracemalloc
from collections.abc import Callable
from pathlib import Path
from typing import Any

from auditcore.exceptions import MigrationBlocked
from auditcore.tools.apprefactor.engine import source_digest, verify
from auditcore.tools.common import write_json
from auditcore.tools.quality.scanners import python_sources


def annotate_function(source: str, symbol: str, annotations: dict[str, str]) -> str:
    """Add explicitly supplied annotations while retaining the function implementation."""
    tree = ast.parse(source)
    node = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == symbol), None)
    if node is None:
        raise ValueError("Function not found")
    for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
        if arg.arg in annotations:
            arg.annotation = ast.parse(annotations[arg.arg], mode="eval").body
    if "return" in annotations:
        node.returns = ast.parse(annotations["return"], mode="eval").body
    lines = source.splitlines(keepends=True)
    lines[node.lineno - 1 : node.end_lineno] = [ast.unparse(node) + "\n"]
    return "".join(lines)


def edit_dependencies(path: Path, remove: list[str], add: list[str]) -> str:
    """Edit declared requirements without executing package managers or touching locks."""
    source = path.read_text()

    def name(requirement: str) -> str:
        """Normalize distribution names while ignoring version and extra constraints."""
        return re.split(r"[\s<>=!~\[;@]", requirement, maxsplit=1)[0].lower().replace("_", "-")

    removed = {name(item) for item in remove}
    if path.name == "pyproject.toml":
        parsed = tomllib.loads(source)
        original = parsed.get("project", {}).get("dependencies", [])
        dependencies = [d for d in original if name(d) not in removed] + add
        match = re.search(r"(?ms)^\[project\]\s*\n(.*?)(?=^\[|\Z)", source)
        if not match:
            raise MigrationBlocked("PEP 621 project table required for dependency edit")
        section = match.group(0)
        declaration = re.search(r"(?m)^dependencies\s*=\s*\[", section)
        replacement = "dependencies = " + json.dumps(dependencies)
        if declaration:
            depth, quote, escaped, comment = 1, "", False, False
            end = declaration.end()
            while end < len(section) and depth:
                char = section[end]
                if comment:
                    comment = char != "\n"
                elif quote:
                    if escaped:
                        escaped = False
                    elif char == "\\" and quote == '"':
                        escaped = True
                    elif char == quote:
                        quote = ""
                elif char in {"'", '"'}:
                    quote = char
                elif char == "#":
                    comment = True
                elif char == "[":
                    depth += 1
                elif char == "]":
                    depth -= 1
                end += 1
            if depth:
                raise MigrationBlocked("Unterminated dependency array")
            section = section[: declaration.start()] + replacement + section[end:]
        else:
            section += replacement + "\n"
        result = source[: match.start()] + section + source[match.end() :]
        if tomllib.loads(result)["project"]["dependencies"] != dependencies:
            raise MigrationBlocked("Dependency edit did not round-trip")
        return result
    if path.name.startswith("requirements") and path.suffix == ".txt":
        retained = [line for line in source.splitlines() if name(line.strip()) not in removed]
        return "\n".join(retained + add) + "\n"
    raise MigrationBlocked("Unsupported manifest; supply a reviewed patch including lockfile")


def safe_import_cleanup(root: Path, commands: dict[str, list[str]]) -> dict[str, Any]:
    """Apply Ruff import ordering only after baseline tests, and roll back on any regression."""
    before = verify(root, commands)
    if before["status"] != "PASS":
        raise MigrationBlocked("Optimization baseline verification incomplete")
    sources = python_sources(root)
    try:
        result = subprocess.run(
            ["ruff", "check", "--select", "I", "--fix", str(root)],
            cwd=root,
            capture_output=True,
            timeout=120,
            check=False,
        )
        if result.returncode:
            raise MigrationBlocked("Import cleanup failed")
        after = verify(root, commands)
        if after["status"] != "PASS":
            raise MigrationBlocked("Optimization regression")
        report = {
            "status": "OPTIMIZED",
            "kind": "import_order",
            "before": before,
            "after": after,
            "source_digest": source_digest(root),
            "changed_files": [
                name for name, text in sources.items() if (root / name).read_text() != text
            ],
        }
        write_json(root / ".auditcore/optimization-result.json", report)
        return report
    except BaseException:
        for name, text in sources.items():
            (root / name).write_text(text)
        raise


def benchmark(
    function: Callable[..., Any], args: tuple[Any, ...], repeat: int = 10
) -> dict[str, Any]:
    """Measure elapsed time, peak Python allocation and observed result."""
    if repeat < 1:
        raise ValueError("Repeat must be positive")
    tracemalloc.start()
    start = time.perf_counter()
    try:
        values = [function(*args) for _ in range(repeat)]
        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    if any(value != values[0] for value in values):
        raise MigrationBlocked("Nondeterministic benchmark results")
    return {
        "seconds_per_call": elapsed / repeat,
        "peak_bytes": peak,
        "repeat": repeat,
        "result": values[0],
    }


def cleanup_legacy(
    root: Path,
    relative_path: str,
    symbol: str,
    active_consumers: list[str],
    commands: dict[str, list[str]],
    *,
    consumer_scope_verified: bool = False,
) -> dict[str, Any]:
    """Remove a deprecated wrapper only after verified consumer migration and fresh tests."""
    from auditcore.tools.common import safe_path

    if active_consumers or not consumer_scope_verified:
        raise MigrationBlocked("Active or unknown consumers prevent legacy cleanup")
    evidence_path = root / ".auditcore/refactor-result.json"
    if not evidence_path.exists():
        raise MigrationBlocked("A verified migration is required before cleanup")
    evidence = json.loads(evidence_path.read_text())
    if evidence.get("status") != "VERIFIED" or evidence.get("source_digest") != source_digest(root):
        raise MigrationBlocked("Migration verification is stale")
    path = safe_path(root, relative_path)
    source = path.read_text()
    tree = ast.parse(source)
    node = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == symbol), None)
    if node is None or "Deprecated compatibility wrapper" not in (ast.get_docstring(node) or ""):
        raise MigrationBlocked("Only a verified compatibility wrapper may be cleaned up")
    for filename, text in python_sources(root).items():
        check_tree = ast.parse(text)
        for item in ast.walk(check_tree):
            if filename == relative_path and node.lineno <= getattr(item, "lineno", 0) <= (
                node.end_lineno or node.lineno
            ):
                continue
            if (
                isinstance(item, ast.Name)
                and item.id == symbol
                or isinstance(item, ast.Attribute)
                and item.attr == symbol
                or isinstance(item, ast.alias)
                and item.name == symbol
            ):
                raise MigrationBlocked("A local consumer still references the legacy symbol")
            if isinstance(item, ast.Call) and ast.unparse(item.func) in {
                "__import__",
                "importlib.import_module",
                "getattr",
            }:
                raise MigrationBlocked("Dynamic consumers require manual resolution")
    before = verify(root, commands)
    if before["status"] != "PASS":
        raise MigrationBlocked("Cleanup baseline verification incomplete")
    lines = source.splitlines(keepends=True)
    del lines[node.lineno - 1 : node.end_lineno]
    try:
        path.write_text("".join(lines))
        after = verify(root, commands)
        if after["status"] != "PASS":
            raise MigrationBlocked("Cleanup regression")
        result = {
            "status": "VERIFIED",
            "removed_legacy_symbols": [symbol],
            "path": relative_path,
            "before": before,
            "after": after,
        }
        write_json(root / ".auditcore/cleanup-result.json", result)
        return result
    except BaseException:
        path.write_text(source)
        raise
