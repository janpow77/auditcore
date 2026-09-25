"""Differential comparison: original verdicts (fixtures) against the ``strict`` profile.

Writes ``docs/differences.md`` and ``tests/fixtures/differences.json``; the test
``test_differences.py`` recomputes the JSON and fails if the committed report is stale.

    python tools/difference_report.py
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auditcore_identifiers import CheckResult, check  # noqa: E402

Strict = Callable[[dict[str, Any]], CheckResult]
_VALUE = "value"


def _strict(kind: str, country: str | None = None) -> Strict:
    return lambda inputs: check(kind, inputs[_VALUE], country=country)


#: (fixture, function) -> (label, strict call, legacy verdict from the observed output)
COMPARISONS: dict[tuple[str, str], tuple[str, Strict]] = {
    ("flowinvoice", "validate_iban"): ("flowinvoice validate_iban", _strict("iban")),
    ("flowinvoice", "validate_bic"): ("flowinvoice validate_bic", _strict("bic")),
    ("flowinvoice", "validate_german_tax_id"):
        ("flowinvoice validate_german_tax_id", _strict("tax_number")),
    ("flowinvoice", "validate_german_vat_id"):
        ("flowinvoice validate_german_vat_id", _strict("vat_id", "DE")),
    ("flowinvoice", "validate_uk_vat_id"):
        ("flowinvoice validate_uk_vat_id", _strict("vat_id", "GB")),
    ("flowinvoice", "validate_eu_vat_id"): (
        "flowinvoice validate_eu_vat_id",
        lambda i: check("vat_id", i[_VALUE], country=i["country_code"])),
    ("flowinvoice", "_validate_iban"): ("Pipeline IbanChecksumRule", _strict("iban")),
    ("flowinvoice", "VatIdFormatRule.evaluate"): ("Pipeline VatIdFormatRule", _strict("vat_id")),
    ("internal", "invoicesynth.iban_valid"): ("invoicesynth iban_valid", _strict("iban")),
    ("internal", "invoicesynth.vat_id_valid"): ("invoicesynth vat_id_valid", _strict("vat_id")),
    ("internal", "documents.donut_vat_id_check"):
        ("documents vat_id_check (Donut)", _strict("vat_id")),
    ("internal", "documents.donut_iban"): ("documents validate_iban (Donut)", _strict("iban")),
    ("internal", "is_valid_lei"): ("flowworkshop is_valid_lei", _strict("lei")),
    ("internal", "entity_matching.check_lei"): ("entity_matching check_lei", _strict("lei")),
}


def legacy_verdict(case: dict[str, Any]) -> str:
    """VALID / INVALID / MISSING / EXCEPTION of the original call."""
    output, function = case["output"], case["function"]
    if case["exception"]:
        return f"EXCEPTION:{case['exception']}"
    if isinstance(output, dict) and "status" in output:
        return str(output["status"])
    if isinstance(output, dict):
        skipped = str(output["message"]).startswith("No VAT ID found")
        return "MISSING" if skipped else ("VALID" if output["outcome"] == "PASS" else "INVALID")
    if isinstance(output, list):
        return "VALID" if output[0] else "INVALID"
    if function == "documents.donut_vat_id_check":
        return "VALID" if output is None else "INVALID"
    return "VALID" if output else "INVALID"


def _strict_verdict(result: CheckResult) -> str:
    status = result.status.value
    return status if result.reason is None else f"{status}:{result.reason}"


def compute() -> list[dict[str, Any]]:
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    for fixture in ("flowinvoice", "internal"):
        path = ROOT / "tests" / "fixtures" / f"{fixture}_observed.json"
        for case in json.loads(path.read_text("utf-8"))["cases"]:
            comparison = COMPARISONS.get((fixture, case["function"]))
            if comparison is None:
                continue
            label, strict = comparison
            old, new = legacy_verdict(case), _strict_verdict(strict(case["inputs"]))
            if old == new.split(":")[0] or (old == "INVALID" and new.startswith("INVALID")):
                continue
            key = (label, old, new)
            row = rows.setdefault(key, {"comparison": label, "legacy": old, "strict": new,
                                        "count": 0, "example": case["inputs"]})
            row["count"] += 1
    return sorted(rows.values(), key=lambda r: (r["comparison"], r["legacy"], r["strict"]))


def markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Abweichungen: Originale gegenüber dem Profil `strict`",
        "",
        "Erzeugt mit `tools/difference_report.py` aus den ausgeführten Originalen",
        "(`tests/fixtures/*_observed.json`). Gezählt sind nur Fälle, in denen sich das",
        "Urteil ändert (gültig ↔ ungültig/fehlend); unterschiedliche Meldungen bei",
        "gleichem Urteil sind nicht aufgeführt. Die Legacy-Profile geben die linke Spalte",
        "exakt wieder (`tests/test_replay.py`). audit-portal ist hier nicht getrennt",
        "aufgeführt, weil seine Dateien dieselben Urteile liefern (Blob-gleich bzw.",
        "gleicher Regelteil, geprüft in `test_replay.py`).",
        "",
        "| Vergleich | Original | strict (Grund) | Fälle | Beispiel |",
        "|---|---|---|---:|---|",
    ]
    for row in rows:
        example = json.dumps(row["example"], ensure_ascii=True)
        lines.append(f"| {row['comparison']} | {row['legacy']} | {row['strict']} "
                     f"| {row['count']} | `{example}` |")
    return "\n".join(lines) + "\n"


def main() -> None:
    rows = compute()
    (ROOT / "tests" / "fixtures" / "differences.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ROOT / "docs" / "differences.md").write_text(markdown(rows), encoding="utf-8")


if __name__ == "__main__":
    main()
