"""Synchronize repository coverage independently of optional detailed symbol batches."""

from __future__ import annotations

import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from auditcore.tools.common import write_json
from auditcore.tools.consolidator.inventory import JsonInventory
from auditcore.tools.consolidator.providers.knowledge import KiraKnowledgeStore


def main() -> None:
    """Reuse the configured local integration, recording every repository outcome."""
    sys.path.insert(0, str(Path.home() / "Projekte/graphify-kira/src"))
    from graphify_kira.config import Config

    config = Config.resolve()
    inventory = JsonInventory()
    repositories = inventory.load("repositories")
    counts = Counter(s["repository"] for s in inventory.load("symbols"))
    results = []

    def sync(repository):
        """Send the same bounded repository document used by detailed synchronization."""
        name = repository["repository"]
        document = {
            "repository": name,
            "branch": repository["default_branch"],
            "commit_sha": repository["commit_sha"],
            "classification": "OBSERVED",
            "type": "REPOSITORY",
            "path": "",
            "symbol": "",
            "metadata": repository,
            "symbol_count": counts[name],
        }
        knowledge = KiraKnowledgeStore(
            config.kira_url,
            config.api_key,
            Path(".auditcore/kira-ledgers") / (name.replace("/", "__") + ".json"),
        )
        return {"repository": name, **knowledge.sync([document])}

    with ThreadPoolExecutor(max_workers=2) as executor:
        for future in as_completed([executor.submit(sync, r) for r in repositories]):
            result = future.result()
            results.append(result)
            print(json.dumps(result), flush=True)
            write_json(Path(".auditcore/kira-catalog-progress.json"), results)
    write_json(
        Path(".auditcore/kira-catalog-result.json"),
        {
            "status": "PASS" if all(r["status"] == "PASS" for r in results) else "PARTIAL",
            "scope": (
                "Repository metadata and symbol counts; detailed symbol sync separately recorded"
            ),
            "repositories": len(results),
            "results": results,
        },
    )


if __name__ == "__main__":
    main()
