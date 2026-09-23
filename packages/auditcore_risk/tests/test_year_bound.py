"""RF02 with year-bound EU thresholds from auditcore_procurement (candidate profile).

The legacy profile keeps its static list; the candidate takes the EU threshold
of the record's year from ``procurement.hvtg 2026.09.2`` instead of copying it.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pytest

from auditcore_risk import InputError, evaluate, load_profile, profile_from_dict

LEGACY = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
YEAR = load_profile("riskanalysis.year_bound", "2026.09.1")


def row(amount: float, day: Any) -> dict[str, Any]:
    return {
        "bruttobetrag": amount,
        "Name": None,
        "zahlungsempfaenger": None,
        "rechnungsdatum_dt": day,
    }


def rf02(profile: Any, rows: list[dict[str, Any]], **kw: Any) -> list[bool | None]:
    return [r.flags["RF02"] for r in evaluate(rows, profile, **kw).records]


def test_legacy_221000_is_the_2024_2025_eu_threshold() -> None:
    from auditcore_procurement import prechecks

    hvtg = prechecks.load_profile("procurement.hvtg", "2026.09.2")
    period = prechecks.eu_period(hvtg, date(2025, 6, 30))
    value = prechecks.eu_threshold(hvtg, "supply_service", period, "sub_central").value
    assert value == 221000
    assert 221000.0 in LEGACY.rule("RF02").params["thresholds"]["static"]
    later = prechecks.eu_period(hvtg, date(2026, 1, 1))
    assert prechecks.eu_threshold(hvtg, "supply_service", later, "sub_central").value == 216000


def test_threshold_follows_the_record_year() -> None:
    rows = [
        row(200_000.0, date(2025, 12, 31)),  # [198.900; 221.000)
        row(216_500.0, date(2025, 12, 31)),
        row(216_500.0, date(2026, 1, 1)),  # ≥ 216.000 → no longer "knapp darunter"
        row(195_000.0, datetime(2026, 3, 1, 12, 0)),  # [194.400; 216.000)
        row(195_000.0, "2025-03-01"),
        row(24_500.0, None),  # static national limit decides without a date
    ]
    assert rf02(YEAR, rows) == [True, True, False, True, False, True]
    assert rf02(LEGACY, rows) == [True, True, True, False, False, True]


def test_missing_or_unverified_period_stays_undetermined() -> None:
    result = evaluate([row(200_000.0, None), row(200_000.0, date(2023, 5, 1))], YEAR)
    assert [r.flags["RF02"] for r in result.records] == [None, None]
    assert "Datum fehlt" in result.records[0].undetermined["RF02"]
    assert "kein belegter EU-Schwellenwert" in result.records[1].undetermined["RF02"]
    summary = {s["code"]: s for s in result.summary}["RF02"]
    assert summary["treffer"] == 0 and summary["unbestimmt"] == 2


def test_hit_names_the_threshold_source() -> None:
    hits = evaluate([row(200_000.0, date(2026, 5, 1))], YEAR).records[0].hits
    hit = next(h for h in hits if h.code == "RF02")
    match = hit.evidence["matches"][0]
    assert match["source"] == "procurement_eu"
    assert match["value"] == 216000 and match["valid_from"] == "2026-01-01"
    assert match["regulation"].startswith("Delegierte Verordnung (EU) 2025/2152")
    assert "jahresbezogene EU-Schwelle" in hit.reason


def test_reference_date_source_needs_an_explicit_key_date() -> None:
    data = _with_date_source("reference_date")
    profile = profile_from_dict(data)
    rows = [row(200_000.0, None)]
    with pytest.raises(InputError):
        evaluate(rows, profile)
    assert rf02(profile, rows, reference_date=date(2026, 7, 1)) == [True]
    assert rf02(profile, [row(216_500.0, None)], reference_date=date(2025, 7, 1)) == [True]


def test_invalid_record_date_is_an_input_error() -> None:
    with pytest.raises(InputError):
        evaluate([row(200_000.0, "31.12.2025")], YEAR)


def _with_date_source(source: str) -> dict[str, Any]:
    import json
    from pathlib import Path

    path = (
        Path(__file__).parents[1]
        / "src/auditcore_risk/profile_data"
        / "riskanalysis.year_bound-2026.09.1.json"
    )
    data: dict[str, Any] = json.loads(path.read_text())
    for rule in data["rules"]:
        if rule["code"] == "RF02":
            eu = rule["params"]["thresholds"]["procurement_eu"]
            eu["date_source"] = source
            eu.pop("date_field")
    return data
