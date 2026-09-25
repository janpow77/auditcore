"""Generates src/validation/catalogRows.ts from the rule catalogue of auditcore_bpmn.

Usage (repository root, auditcore_bpmn importable):
    python packages-js/bpmn-flowaudit/scripts/generate_rule_catalog.py
"""

from __future__ import annotations

import json
from pathlib import Path

from auditcore_bpmn.validation.messages import MESSAGES

TARGET = Path(__file__).resolve().parents[1] / "src" / "validation" / "catalogRows.ts"
HEADER = """/**
 * Rule catalogue rows (id, severity, group, de, en) – generated from
 * `auditcore_bpmn.validation.messages` by `scripts/generate_rule_catalog.py`.
 * Do not edit by hand.
 */

export type CatalogRow = [string, string, string, string, string]

export const ROWS: CatalogRow[] = [
"""


def main() -> None:
    rows = [
        "  " + json.dumps([m.id, m.severity, m.group, m.de, m.en], ensure_ascii=False) + ","
        for m in sorted(MESSAGES.values(), key=lambda m: m.id)
    ]
    TARGET.write_text(HEADER + "\n".join(rows) + "\n]\n", encoding="utf-8")


if __name__ == "__main__":
    main()
