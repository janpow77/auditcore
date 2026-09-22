"""Synchronize structured inventory in bounded KIRA documents, without raw source."""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from auditcore.tools.common import digest, write_json
from auditcore.tools.consolidator.inventory import JsonInventory
from auditcore.tools.consolidator.providers.knowledge import KiraKnowledgeStore


def main() -> None:
    """Resolve the existing local KIRA configuration without persisting credentials."""
    # Explicit local integration supplied by the machine's existing graphify-kira setup.
    sys.path.insert(0, str(Path.home() / "Projekte/graphify-kira/src"))
    from graphify_kira.config import Config

    config = Config.resolve()
    store = JsonInventory()
    knowledge = KiraKnowledgeStore(config.kira_url, config.api_key)
    symbols = store.load("symbols")
    repositories = store.load("repositories")
    selected = os.environ.get("AUDITCORE_SYNC_REPOSITORIES", "").split(",")
    if selected != [""]:
        repositories = [r for r in repositories if r["repository"] in selected]
    grouped = defaultdict(list)
    for symbol in symbols:
        grouped[symbol["repository"]].append(symbol)
    total = {
        "stored": 0,
        "unchanged": 0,
        "screening_blocked": 0,
        "failed": 0,
        "pending": 0,
        "repositories_processed": 0,
        "status": "RUNNING",
        "symbol_count": len(symbols),
    }

    def sync_repository(repository):
        name = repository["repository"]
        base = {
            "repository": name,
            "branch": repository["default_branch"],
            "commit_sha": repository["commit_sha"],
            "classification": "OBSERVED",
        }
        documents = [
            {
                **base,
                "type": "REPOSITORY",
                "path": "",
                "symbol": "",
                "metadata": repository,
                "symbol_count": len(grouped[name]),
            }
        ]
        # Batch symbol observations with full provenance and relationships. Shared module
        # imports repeat in the local inventory, but are stored once per module in KIRA.
        by_file = defaultdict(list)
        for symbol in grouped[name]:
            by_file[symbol["path"]].append(symbol)
        batch = []
        size = 0
        ordinal = 0
        for path, items in sorted(by_file.items()):
            for symbol in items:
                compact = {
                    k: v
                    for k, v in symbol.items()
                    if k
                    not in {
                        "repository",
                        "commit_sha",
                        "imports",
                        "docstring_summary",
                        "classification",
                        "test_coverage",
                        "last_change",
                    }
                }
                record = json.dumps(compact, ensure_ascii=False)
                if size + len(record) > 30000 and batch:
                    documents.append(
                        {
                            **base,
                            "type": "SYMBOL_CATALOG",
                            "path": "",
                            "symbol": f"batch-{ordinal:05d}",
                            "symbols": batch,
                        }
                    )
                    ordinal += 1
                    batch, size = [], 0
                if len(record) > 30000:
                    # Oversized observed symbols are retained locally and explicitly referenced.
                    compact = {
                        "path": path,
                        "symbol": symbol["symbol"],
                        "source_sha256": symbol["fingerprint"],
                        "details_status": "LOCAL_INVENTORY_ONLY",
                        "reason": "Oversized symbol record",
                    }
                    record = json.dumps(compact)
                batch.append(compact)
                size += len(record)
        if batch:
            documents.append(
                {
                    **base,
                    "type": "SYMBOL_CATALOG",
                    "path": "",
                    "symbol": f"batch-{ordinal:05d}",
                    "symbols": batch,
                }
            )
        project_store = KiraKnowledgeStore(
            config.kira_url,
            config.api_key,
            Path(".auditcore/kira-ledgers") / (name.replace("/", "__") + ".json"),
        )
        # Retain acknowledgements from interrupted sequential initialization.
        if not project_store.ledger.exists() and knowledge.ledger.exists():
            from auditcore.tools.common import read_json

            write_json(project_store.ledger, read_json(knowledge.ledger))
        result = project_store.sync(documents)
        return name, result

    repositories.sort(key=lambda item: len(grouped[item["repository"]]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(sync_repository, repository) for repository in repositories]
        for future in as_completed(futures):
            name, result = future.result()
            for key in ("stored", "unchanged", "screening_blocked", "failed", "pending"):
                total[key] += result.get(key, 0)
            total["repositories_processed"] += 1
            write_json(Path(".auditcore/kira-sync-progress.json"), total)
            print(json.dumps({"repository": name, **result}), flush=True)
    total["status"] = (
        "FAIL" if total["failed"] else ("REVIEW_REQUIRED" if total["screening_blocked"] else "PASS")
    )
    total["inventory_sha256"] = digest(Path(".auditcore/inventory/symbols.json").read_bytes())
    write_json(Path(".auditcore/kira-sync-result.json"), total)


if __name__ == "__main__":
    main()
