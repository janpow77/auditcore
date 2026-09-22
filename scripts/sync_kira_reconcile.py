"""Read back one repository's uncertain KIRA writes, without remote mutations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sync_inventory import repository_documents

from auditcore.tools.common import write_json
from auditcore.tools.consolidator.inventory import JsonInventory
from auditcore.tools.consolidator.providers.knowledge import KiraKnowledgeStore


def main() -> None:
    """Recover exact inventory acknowledgements without repeating timed-out POSTs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="Exact owner/repository from the local inventory")
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path(".auditcore/kira-reconciliation.json"))
    args = parser.parse_args()
    inventory = JsonInventory()
    repositories = [r for r in inventory.load("repositories") if r["repository"] == args.repository]
    if len(repositories) != 1:
        parser.error("Repository must occur exactly once in the inventory")
    symbols = [s for s in inventory.load("symbols") if s["repository"] == args.repository]
    sys.path.insert(0, str(Path.home() / "Projekte/graphify-kira/src"))
    from graphify_kira.config import Config

    config = Config.resolve()
    store = KiraKnowledgeStore(
        config.kira_url,
        config.api_key,
        Path(".auditcore/kira-ledgers") / (args.repository.replace("/", "__") + ".json"),
    )
    result = {
        "repository": args.repository,
        "remote_mutations": 0,
        **store.reconcile(repository_documents(repositories[0], symbols), args.max_pages),
    }
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
