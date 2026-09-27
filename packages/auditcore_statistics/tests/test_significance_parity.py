"""Chi-square test and z per digit reproduce flowinvoice's executed Benford analyzers.

Fixture: ``tools/capture_flowinvoice_significance.py`` (63 synthetic cases).
flowinvoice rounds χ², p and observed shares to four decimals and states the
critical value with three; the comparison uses exactly these output formats.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from auditcore_statistics import benford_test, chi_square_test, digit_z_test

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "flowinvoice_significance_observed.json").read_text()
)
CASES = FIXTURE["cases"]


def decode(value: Any) -> Any:
    if isinstance(value, dict) and "$decimal" in value:
        return Decimal(value["$decimal"])
    if isinstance(value, dict) and value.get("$float") == "nan":
        return float("nan")
    return value


def measures(case: dict[str, Any]) -> tuple[Any, Any, Any]:
    result = benford_test([decode(v) for v in case["amounts"]], digits=1)
    chi = chi_square_test(result, "first", significance_level=0.05)
    z = digit_z_test(result, "first", continuity_correction=False, z_critical=2.576)
    return result, chi, z


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_chi_square_equals_the_current_flowinvoice_analyzer(case: dict[str, Any]) -> None:
    current = case["current"]
    result, chi, _ = measures(case)
    assert result.analysed == current["sample_size"]
    observed = {str(r.digit): round(r.observed_share, 4) for r in result.rows}
    assert observed == current["observed_distribution"]
    assert round(chi.critical_value or 0, 3) == current["critical_value"] == 15.507
    if not current["sample_size_sufficient"]:  # minimum of 50 values is flowinvoice's own rule
        assert current["chi_square_statistic"] == 0.0 and current["p_value"] == 1.0
        return
    assert round(chi.chi2_statistic, 4) == current["chi_square_statistic"]
    assert round(chi.p_value, 4) == current["p_value"]
    assert chi.degrees_of_freedom == current["degrees_of_freedom"] == 8
    assert chi.significance_level == current["significance_level"]
    assert chi.rejects == current["is_anomalous"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_digit_z_equals_the_flowinvoice_source_test(case: dict[str, Any]) -> None:
    source = case["original_exact"]
    result, chi, z = measures(case)
    assert result.analysed == source["sample_size"]
    if not source["sample_size_sufficient"]:
        assert source["anomalous_digits"] == []
        return
    assert list(z.exceeding_digits or ()) == source["anomalous_digits"]
    assert round(chi.chi2_statistic, 4) == source["chi_square_statistic"]
    observed = {str(r.digit): round(r.observed_share, 4) for r in z.rows}
    assert observed == source["observed_distribution"]


def test_rounded_source_table_marks_the_same_digits_on_these_cases() -> None:
    same = [
        c["original_exact"]["anomalous_digits"] == c["original_rounded"]["anomalous_digits"]
        for c in CASES
    ]
    assert all(same)
    assert sum(bool(c["original_exact"]["anomalous_digits"]) for c in CASES) >= 30


def test_fixture_scope() -> None:
    revisions = FIXTURE["source"]["revisions"]
    assert revisions["current"]["commit"].startswith("06c06a8")
    assert revisions["original"]["commit"].startswith("fb2d185")
    assert len(CASES) == 63
