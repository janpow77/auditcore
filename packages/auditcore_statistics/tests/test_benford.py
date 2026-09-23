"""Corrected contract of benford_test next to the legacy results (ST-C ids)."""

from __future__ import annotations

import json
import math
from decimal import Decimal
from pathlib import Path

import pytest

from auditcore_statistics import (
    METHOD,
    StatisticsInputError,
    benford_test,
    expected_share,
    legacy_run_benford,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "flowstat_benford_observed.json").read_text()
)
CASES = {c["name"]: c for c in FIXTURE["cases"]}


def test_expected_shares_sum_to_one() -> None:
    assert math.isclose(sum(expected_share(d) for d in range(1, 10)), 1.0)
    assert math.isclose(sum(expected_share(d) for d in range(10, 100)), 1.0)


def test_first_digit_matches_legacy_on_regular_data() -> None:
    values = CASES["lognormal-1"]["values"]
    result = benford_test(values, digits=1)
    legacy = CASES["lognormal-1"]["output"]
    assert [r.observed_count for r in result.rows] == [
        row["observed_count"] for row in legacy["rows"]
    ]
    assert round(result.chi2_statistic, 4) == legacy["meta"]["chi2_statistic"]
    assert round(result.p_value, 4) == legacy["meta"]["p_value"]
    assert result.method == METHOD and result.to_dict()["library"].endswith("0.1.0")


def test_st_c01_two_digit_analysis_does_not_crash_on_short_values() -> None:
    values = CASES["integers-2"]["values"]
    with pytest.raises(ValueError, match="sum of the observed"):
        legacy_run_benford(values, dtype="int", digit=2, column="betrag")
    excluded = benford_test(values, digits=2, short_values="exclude")
    padded = benford_test(values, digits=2, short_values="pad")
    assert excluded.short_excluded > 0 and excluded.analysed + excluded.short_excluded == 400
    assert padded.short_excluded == 0 and padded.analysed == 400
    assert sum(r.observed_count for r in excluded.rows) == excluded.analysed


def test_st_c01_short_value_rule_must_be_explicit() -> None:
    with pytest.raises(StatisticsInputError, match="short_values"):
        benford_test([12, 34], digits=2)
    with pytest.raises(StatisticsInputError):
        benford_test([12, 34], digits=1, short_values="pad")


def test_st_c02_integer_and_float_forms_give_the_same_digits() -> None:
    ints = [1, 2, 3, 5, 9, 12, 15, 99, 100, 7]
    floats = [float(v) for v in ints]
    legacy_int = legacy_run_benford(ints, dtype="int", digit=1, column="x")
    legacy_float = legacy_run_benford(floats, dtype="float", digit=1, column="x")
    assert legacy_int["rows"] == legacy_float["rows"]  # first digit agrees in the source
    with pytest.raises(ValueError):
        legacy_run_benford(ints, dtype="int", digit=2, column="x")
    legacy_two = legacy_run_benford(floats, dtype="float", digit=2, column="x")
    assert {r["digit"] for r in legacy_two["rows"] if r["observed_count"]} >= {"50", "70"}
    a = benford_test(ints, digits=2, short_values="exclude")
    b = benford_test(floats, digits=2, short_values="exclude")
    assert a == b and a.short_excluded == 7  # 1, 2, 3, 5, 7, 9 and 100


def test_st_c03_scientific_notation_and_small_values_use_exact_digits() -> None:
    result = benford_test(
        [1e-05, 2.5e-07, 1.5e20, 3.14e16, 12.5, 0.05], digits=2, short_values="exclude"
    )
    counts = {r.digit: r.observed_count for r in result.rows if r.observed_count}
    assert counts == {25: 1, 15: 1, 31: 1, 12: 1}
    assert result.short_excluded == 2
    assert benford_test([Decimal("0.0042"), 42], digits=1).rows[3].observed_count == 2


def test_st_c04_booleans_strings_and_infinities_are_rejected() -> None:
    for bad in ([True, 2.0], ["123"], [math.inf], [Decimal("NaN")]):
        with pytest.raises(StatisticsInputError):
            benford_test(bad, digits=1)  # type: ignore[arg-type]


def test_st_c05_exclusions_are_reported() -> None:
    result = benford_test([None, math.nan, 0, 0.0, -9, 47, 3.3], digits=1)
    assert (result.missing, result.zero, result.negative_absolute, result.analysed) == (2, 2, 1, 3)
    with pytest.raises(StatisticsInputError, match="Keine auswertbaren"):
        benford_test([0, None], digits=1)
    with pytest.raises(StatisticsInputError):
        benford_test([1], digits=3)
    with pytest.raises(StatisticsInputError):
        benford_test([1], digits=True)  # type: ignore[arg-type]


def test_st_c06_no_judgement_without_explicit_level() -> None:
    legacy = CASES["integers-1"]["output"]["meta"]
    assert legacy["significant"] is True  # source fixes alpha = 0.05 silently
    values = CASES["integers-1"]["values"]
    assert benford_test(values, digits=1).deviates_at_level is None
    assert benford_test(values, digits=1, significance_level=0.05).deviates_at_level is True
    with pytest.raises(StatisticsInputError):
        benford_test(values, digits=1, significance_level=1.5)


def test_result_is_serialisable_and_input_is_not_mutated() -> None:
    values = [123, 456.0, None]
    before = list(values)
    data = benford_test(values, digits=1).to_dict()
    assert values == before
    assert json.loads(json.dumps(data))["excluded"] == {"missing": 1, "zero": 0, "short": 0}
    assert math.isclose(sum(r["observed_share"] for r in data["rows"]), 1.0)
