"""Graphify integration and documented local AST fallback."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from auditcore.tools.common import read_json, run
from auditcore.tools.consolidator.analysis import analyze_repository


class GraphifyProvider:
    """Code-only structural extraction without external LLM processing."""

    def __init__(self, output: Path = Path(".auditcore/graphify")) -> None:
        self.output = output.resolve()

    def analyze(self, path: Path) -> dict[str, Any]:
        """Run Graphify or report nonexecution alongside local dependency evidence."""
        executable = shutil.which("graphify")
        fallback = analyze_repository(path, path.name, "WORKTREE")
        if not executable:
            return {
                "status": "NOT_EXECUTED",
                "reason": "Graphify not configured",
                "fallback": "LOCAL_AST",
                "dependencies": fallback["dependencies"],
            }
        output = self.output / path.name
        output.mkdir(parents=True, exist_ok=True)
        try:
            run(
                [
                    executable,
                    "extract",
                    str(path.resolve()),
                    "--code-only",
                    "--out",
                    str(output),
                    "--exclude",
                    "node_modules",
                    "--exclude",
                    ".venv",
                    "--exclude",
                    ".auditcore",
                    "--exclude",
                    "dist",
                    "--exclude",
                    "build",
                ],
                timeout=300,
            )
            graph = read_json(output / "graphify-out/graph.json")
            return {
                "status": "PASS",
                "graph_path": str(output / "graphify-out/graph.json"),
                "nodes": len(graph.get("nodes", [])),
                "edges": len(graph.get("links", graph.get("edges", []))),
                "fallback_dependencies": fallback["dependencies"],
            }
        except (RuntimeError, OSError, ValueError):
            return {
                "status": "NOT_EXECUTED",
                "reason": "Graphify extraction failed",
                "fallback": "LOCAL_AST",
                "dependencies": fallback["dependencies"],
            }
