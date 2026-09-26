"""New contract against every observed legacy calculation.

Where both succeed, all rounded amounts, totals and the comparability flag are
identical; the only differences are the documented undefined ratios (PA-L08).
Every case where exactly one side fails is listed here with its contract
number from ``docs/behavior-changes.md``.
"""

from __future__ import annotations

from typing import Any

import pytest
from helpers import PROFILES, run_new
from replay import load_fixture

from auditcore_price_analysis import PriceAnalysisError

CASES = [c for c in load_fixture()["cases"] if c["function"] in PROFILES]

#: legacy computes a result, the new contract rejects the input (corrected behavior)
NEW_ERROR_LEGACY_OK = {
    "nw-verbrauch-009": ("missing_value", "PA-L01"),
    "nw-verbrauch-010": ("missing_value", "PA-L01"),
    "wa-verbrauch-009": ("missing_value", "PA-L01"),
    "wa-q3-004": ("missing_value", "PA-L01"),
    "wa-staffelform-015": ("missing_value", "PA-L03"),
    "wa-staffelform-016": ("missing_value", "PA-L03"),
    "wa-staffelform-017": ("missing_value", "PA-L03"),
    "wa-staffelform-018": ("missing_value", "PA-L03"),
    "wa-staffelform-039": ("invalid_tiers", "PA-L05"),
    "wa-staffelform-040": ("invalid_tiers", "PA-L05"),
    "wa-staffelform-041": ("invalid_tiers", "PA-L05"),
    "wa-staffelform-042": ("invalid_tiers", "PA-L05"),
    "wa-staffelform-043": ("invalid_tiers", "PA-L05"),
    "wa-staffelform-044": ("invalid_tiers", "PA-L05"),
    "wa-stichtag-004": ("invalid_date", "PA-L09"),
    "nw-umlage-005": ("negative", "PA-L14"),
    "nw-ungueltig-010": ("invalid_number", "PA-L15"),
    "nw-ungueltig-015": ("unknown_component", "PA-L16"),
}
#: legacy rejects, the new contract accepts an open last tier (PA-L04) or German text (PA-C01)
NEW_OK_LEGACY_ERROR = {
    "wa-staffelform-011": "PA-L04",
    "wa-staffelform-012": "PA-L04",
    "wa-staffelform-013": "PA-L04",
    "wa-staffelform-014": "PA-L04",
    "wa-staffelform-019": "PA-L04",
    "wa-staffelform-020": "PA-L04",
    # German decimal comma is read since 0.1.2 (PA-C01)
    "nw-verbrauch-013": "PA-C01",
    "nw-ungueltig-001": "PA-C01",
    "wa-verbrauch-011": "PA-C01",
    "wa-ungueltig-001": "PA-C01",
    "wa-staffelform-025": "PA-C01",
    "wa-staffelform-026": "PA-C01",
}


def _as_float(value: Any) -> float | None:
    return None if value is None else float(value)


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_new_contract_matches_or_is_documented(case: dict[str, Any]) -> None:
    try:
        result = run_new(case)
    except PriceAnalysisError as error:
        if "error" in case:
            return
        assert case["id"] in NEW_ERROR_LEGACY_OK, f"undokumentierte Abweichung: {error}"
        assert error.code == NEW_ERROR_LEGACY_OK[case["id"]][0]
        return
    if "error" in case:
        assert case["id"] in NEW_OK_LEGACY_ERROR, case["error"]
        return
    assert case["id"] not in NEW_ERROR_LEGACY_OK
    legacy = case["ok"]
    assert float(result.total_rounded) == legacy["jahreskosten"]
    for line in result.lines:
        if line.status != "nicht_anwendbar":
            assert _as_float(line.amount_rounded) in (legacy[line.line], None)
            if line.amount_rounded is None:
                assert legacy[line.line] == 0.0
    assert result.comparable == legacy["vergleichsfaehig"]
    assert list(result.missing_required) == legacy["fehlende_komponenten"]
    basis = result.consumption["kwh" if result.kind == "nahwaerme" else "m3"]
    if basis > 0:
        assert _as_float(result.mixed_price) == legacy[result.mixed_price_name]
    else:  # PA-L08: legacy reports 0 for an undefined average price
        assert result.mixed_price is None and legacy[result.mixed_price_name] == 0.0
    if "fixkostenanteil_pct" in legacy:
        if result.total > 0:
            assert _as_float(result.fixed_share_pct) == legacy["fixkostenanteil_pct"]
            assert _as_float(result.variable_share_pct) == legacy["variablekostenanteil_pct"]
        else:  # PA-L08: legacy reports 0 % / 100 % without any costs
            assert result.fixed_share_pct is None and result.variable_share_pct is None
            assert (legacy["fixkostenanteil_pct"], legacy["variablekostenanteil_pct"]) == (0, 100)


def test_every_documented_divergence_is_observed() -> None:
    ids = {c["id"] for c in CASES}
    assert set(NEW_ERROR_LEGACY_OK) <= ids and set(NEW_OK_LEGACY_ERROR) <= ids
