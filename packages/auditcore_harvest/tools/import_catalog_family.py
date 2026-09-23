"""Replace one family of the central catalogue with the entries maintained by its adapter package.

    python tools/import_catalog_family.py <repositories-dir> <family> <package-catalog.json> \
        [--replace ID ...]

Statuses are taken over unchanged (never raised). Every origin is verified
again against the clean checkouts (file exists, symbols occur, commit equals
the checkout HEAD); a mismatch is recorded as ``verified: false`` and the
import aborts, so no unverifiable origin enters the central catalogue.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

CATALOG = Path(__file__).parents[1] / "src" / "auditcore_harvest" / "catalogs" / "sources.json"


def verify(repositories: Path, origin: dict[str, Any]) -> bool:
    repo = str(origin["repository"]).split("/")[-1]
    checkout = repositories / f"janpow77__{repo}"
    head = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    file = checkout / str(origin["path"])
    if head != origin["commit"] or not file.is_file():
        return False
    text = file.read_text(encoding="utf-8", errors="replace")
    # ``Klasse.methode`` counts as found if the class and a def of the method exist.
    for symbol in origin.get("symbols", []):
        parts = str(symbol).split(".")
        if not re.search(rf"\b{re.escape(parts[0])}\b", text):
            return False
        if any(not re.search(rf"def {re.escape(part)}\b", text) for part in parts[1:]):
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repositories", type=Path)
    parser.add_argument("family")
    parser.add_argument("package_catalog", type=Path)
    parser.add_argument(
        "--replace", nargs="*", default=None, help="IDs to remove instead of the whole family"
    )
    parser.add_argument("--package-commit", required=True)
    args = parser.parse_args()
    central = json.loads(CATALOG.read_text(encoding="utf-8"))
    imported = json.loads(args.package_catalog.read_text(encoding="utf-8"))["sources"]
    failures = []
    for entry in imported:
        if entry["family"] != args.family:
            raise SystemExit(f"{entry['source_id']}: andere Familie {entry['family']}")
        for origin in entry["origins"]:
            origin["verified"] = verify(args.repositories, origin)
            if not origin["verified"]:
                failures.append((entry["source_id"], origin["path"]))
        entry["catalog_import"] = {
            "from": str(args.package_catalog.name),
            "package_commit": args.package_commit,
        }
    if failures:
        raise SystemExit(f"Nicht verifizierbare Herkunft: {failures}")
    remove = set(args.replace) if args.replace is not None else None
    before = len(central["sources"])
    kept = [
        s
        for s in central["sources"]
        if not (s["source_id"] in remove if remove is not None else s["family"] == args.family)
    ]
    central["sources"] = kept + imported
    CATALOG.write_text(json.dumps(central, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "removed": before - len(kept),
                "imported": len(imported),
                "total": len(central["sources"]),
            }
        )
    )


if __name__ == "__main__":
    main()
