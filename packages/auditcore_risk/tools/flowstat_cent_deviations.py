"""Re-characterise BL_RF07/BL_RF10 of the 112 Flowstat frames after the switch to cents.

``tests/fixtures/flowstat_observed.json`` stays the recorded output of the
original ``_red_flags`` (float arithmetic). This tool evaluates every frame
with profile version 2026.10.1 (whole cents) and with the float
arithmetic of the source (``|projekt − kürzung − anerkannt| > 0.01`` on the
coerced amounts, missing = 0; concentration via correctly rounded float sums),
and writes every changed decision with its reason::

    python tools/flowstat_cent_deviations.py tests/fixtures/flowstat_cent_deviations.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from conftest import decode, fixture  # noqa: E402

from auditcore_risk import evaluate, load_profile  # noqa: E402
from auditcore_risk.base import amount_cents  # noqa: E402
from auditcore_risk.values import coerce_number  # noqa: E402

PROFILE = load_profile("audit_designer.flowstat_belegliste", "2026.10.1")
RF07, RF10 = "BL_RF07_ACCEPTED_MISMATCH", "BL_RF10_VENDOR_CONCENTRATION"
PARTS = ("projektbetrag", "kuerzungsbetrag", "anerkannter_betrag")


def _amount(row: dict[str, Any], name: str) -> float:
    number = coerce_number(row.get(name), name)
    return 0.0 if number is None else number


def legacy_rf07(row: dict[str, Any]) -> bool:
    """Float decision of the source: ``abs(projekt − kürzung − anerkannt) > 0.01``."""
    rest = _amount(row, PARTS[0]) - _amount(row, PARTS[1]) - _amount(row, PARTS[2])
    return bool(abs(rest) > 0.01)


def legacy_rf10(rows: list[dict[str, Any]]) -> bool:
    """Float decision of the source: share of the largest supplier ≥ 0.5."""
    sums: dict[object, list[float]] = {}
    total: list[float] = []
    for row in rows:
        number = coerce_number(row.get("projektbetrag"), "projektbetrag")
        raw = row.get("rechnungssteller")
        key = None if raw is None or raw != raw else raw
        sums.setdefault(key, [])
        if number is not None:
            sums[key].append(number)
            total.append(number)
    if not all(math.isfinite(v) for v in total) or not math.fsum(total) > 0:
        return False
    return max(math.fsum(v) for v in sums.values()) / math.fsum(total) >= 0.5


def _reason(row: dict[str, Any], new: bool | None) -> str:
    values = [_amount(row, name) for name in PARTS]
    if new is None:
        return (
            f"Betrag nicht endlich ({', '.join(map(repr, values))}); in ganzen Cent nicht "
            "prüfbar (Gleitkomma: Differenz NaN, daher kein Treffer)."
        )
    cents = [amount_cents(v) for v in values]
    difference = cents[0] - cents[1] - cents[2]  # type: ignore[operator]
    rest = values[0] - values[1] - values[2]
    return (
        f"Differenz {difference} Cent liegt innerhalb der Toleranz von 1 Cent; in "
        f"Gleitkomma ist der Betrag der Differenz {abs(rest)!r} > 0,01 "
        "(Darstellungsfehler der Binärzahl)."
    )


def _entry(case: dict[str, Any], index: int, old: bool, new: bool | None) -> dict[str, Any]:
    return {
        "frame": case["name"],
        "row": index,
        "rule": RF07,
        "old": old,
        "new": new,
        "values": {name: case["rows"][index].get(name) for name in PARTS},
        "reason": _reason(decode(case["rows"][index]), new),
    }


def deviations() -> dict[str, Any]:
    """All changed record decisions and RF10 decisions of the 112 frames."""
    found: list[dict[str, Any]] = []
    rf10_changed: list[str] = []
    for case in fixture("flowstat_observed.json")["cases"]:
        rows = [decode(r) for r in case["rows"]]
        result = evaluate(rows, PROFILE, columns=case["columns"])
        finding = next((d for d in result.dataset if d.code == RF10), None)
        if finding is not None and finding.triggered != legacy_rf10(rows):
            rf10_changed.append(case["name"])
        if RF07 in result.skipped:
            continue
        for index, record in enumerate(result.records):
            old, new = legacy_rf07(rows[index]), record.flags[RF07]
            if old != new:
                found.append(_entry(case, index, old, new))
    return {"rf07": found, "rf10_changed_frames": rf10_changed}


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = {
        "description": (
            "Geänderte Entscheidungen von BL_RF07/BL_RF10 gegenüber der aufgezeichneten "
            "Ausgabe (flowstat_observed.json) im Profil audit_designer.flowstat_belegliste "
            "2026.10.1 (ganze Cent, RK-C12); erzeugt mit tools/flowstat_cent_deviations.py."
        ),
        "profile": PROFILE.reference,
        **deviations(),
    }
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", "utf-8")


if __name__ == "__main__":
    main()
