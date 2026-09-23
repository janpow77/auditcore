"""Derive the packaged precheck profile from the recorded ruleset of the executed original."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

VERSION = "2026.09.1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text())
    ruleset = fixture["ruleset"]
    tiers = {
        category: [
            {
                "tier": name,
                "max": rule["max"],
                "procedure": rule["procedure"],
                "min_bids": rule["min_bids"],
            }
            for name, rule in rules.items()
        ]
        for category, rules in ruleset["threshold_rules"].items()
    }
    profile = {
        "schema": "auditcore_procurement.precheck-profile/1",
        "id": "procurement.hvtg-legacy",
        "version": VERSION,
        "status": "SOURCE_CHARACTERIZED",
        "legal_status": (
            "Schwellen, Verfahrenszuordnung und Pflichtdokumente aus dem Regelwerk "
            "PROCUREMENT_HVTG der Quellanwendungen übernommen. Aktualität der Beträge "
            "(insbesondere der EU-Schwellenwerte) und die rechtliche Zuordnung sind nicht "
            "geprüft: HUMAN_DECISION_REQUIRED."
        ),
        "source": {
            "repositories": [
                {
                    "repository": f["repository"],
                    "commit": f["commit"],
                    "path": f["path"],
                    "git_blob": f["git_blob"],
                }
                for f in fixture["source"]["files"]
                if f["path"].endswith(("procurement_analyzer.py", "procurement_ruleset.py"))
            ],
            "rights": "USER_AUTHORIZED_MIT",
        },
        "construction_marker": "Bau",
        "tiers": tiers,
        "fallback_tier": "ABOVE_EU",
        "required_documents": ruleset["required_documents_by_procedure"],
        "bid_document_type": "ANGEBOT",
        "default_min_bids": 1,
        "value_deviation": {
            "warning_above_percent": 10,
            "fail_above_percent": 20,
            "fail_reference": "§ 132 GWB",
        },
    }
    args.output.write_text(json.dumps(profile, indent=1, ensure_ascii=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
