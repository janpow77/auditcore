"""Repository inventory, analysis and planning CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from auditcore.tools.common import emit, run
from auditcore.tools.consolidator.analysis import analyze_repository, detect_candidates
from auditcore.tools.consolidator.inventory import GlobalInventory, JsonInventory
from auditcore.tools.consolidator.models import WorkflowMode
from auditcore.tools.consolidator.providers.github import GitHubProvider
from auditcore.tools.consolidator.providers.graph import GraphifyProvider
from auditcore.tools.consolidator.providers.knowledge import KiraKnowledgeStore
from auditcore.tools.consolidator.workflow import ConsolidationWorkflow


def inventory_documents(store: JsonInventory) -> list[dict[str, Any]]:
    """Build structured per-repository knowledge with SHA provenance and consumers."""
    symbols, dependencies = store.load("symbols"), store.load("dependencies")
    documents = []
    for repository in store.load("repositories"):
        name = repository["repository"]
        records = [s for s in symbols if s["repository"] == name]
        documents.append(
            {
                "type": "REPOSITORY",
                "repository": name,
                "branch": repository["default_branch"],
                "commit_sha": repository["commit_sha"],
                "path": "",
                "symbol": "",
                "classification": "OBSERVED",
                "metadata": repository,
                "symbol_count": len(records),
                "dependencies": sorted(
                    {
                        d.get("dependency", d.get("target", ""))
                        for d in dependencies
                        if d["repository"] == name
                    }
                ),
            }
        )
        for symbol in records:
            # Raw source and docstrings are deliberately not transmitted.
            documents.append(
                {
                    **{k: v for k, v in symbol.items() if k != "docstring_summary"},
                    "type": "SYMBOL",
                    "branch": repository["default_branch"],
                }
            )
    return documents


def main(argv: list[str] | None = None) -> int:
    """Run discovery, inventory, comparison and plan generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=Path(".auditcore"))
    sub = parser.add_subparsers(dest="command", required=True)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("--global", action="store_true", dest="global_scope")
    inventory.add_argument("--update", action="store_true")
    sub.add_parser("libraries")
    analyse = sub.add_parser("analyse")
    analyse.add_argument("repository", type=Path)
    analyse.add_argument("--with-auditcore", action="store_true")
    migrate = sub.add_parser("migrate")
    migrate.add_argument("symbol")
    migrate.add_argument("--dry-run", action="store_true")
    sub.add_parser("status")
    kira = sub.add_parser("kira")
    kira.add_argument("action", choices=["sync", "search"])
    kira.add_argument("query", nargs="?", default="shared audit domain logic")
    graph = sub.add_parser("graphify")
    graph.add_argument("repository", type=Path)
    args = parser.parse_args(argv)
    store = JsonInventory(args.state_dir / "inventory")
    provider = GitHubProvider(args.state_dir / "repositories")
    knowledge = KiraKnowledgeStore(ledger=args.state_dir / "kira-ledger.json")
    try:
        if args.command == "inventory":
            result = GlobalInventory(provider, store).scan_authenticated_account(update=args.update)
        elif args.command == "libraries":
            result = {"candidates": detect_candidates(store.load("symbols"))}
        elif args.command == "analyse":
            revision = run(["git", "rev-parse", "HEAD"], args.repository).strip()
            result = analyze_repository(args.repository, args.repository.name, revision)
            if args.with_auditcore:
                result["reuse_candidates"] = store.load("candidates")
        elif args.command == "migrate":
            result = ConsolidationWorkflow(provider, store, knowledge).run(
                args.symbol.split(":")[0], WorkflowMode.REPO_AUDITCORE, args.dry_run
            )
        elif args.command == "kira":
            result = (
                knowledge.sync(inventory_documents(store))
                if args.action == "sync"
                else knowledge.search(args.query)
            )
            store.save("kira_status", result)
        elif args.command == "graphify":
            result = GraphifyProvider(args.state_dir / "graphify").analyze(args.repository)
            store.save("graphify_status", result)
        else:
            result = {
                "inventory": store.load("inventory_metadata"),
                "kira": store.load("kira_status"),
                "plans": store.load("plans"),
            }
        emit(result)
        return 1 if result.get("status") in {"FAIL", "PARTIAL"} else 0
    except (OSError, ValueError, RuntimeError) as exc:
        emit({"status": "NOT_EXECUTED", "reason": type(exc).__name__})
        return 2
