"""Conformity measures (MAD, z per digit, second digit) under a named profile."""

from __future__ import annotations

import math
import random

import pytest

from auditcore_statistics import StatisticsInputError, benford_test
from auditcore_statistics.conformity import NIGRINI_2012, PROFILES, assess, z_statistic


def _benford_values(count: int, seed: int = 7) -> list[float]:
    rng = random.Random(seed)
    return [round(10 ** rng.uniform(0, 6), 2) for _ in range(count)]


def test_profile_is_named_and_source_bound() -> None:
    assert list(PROFILES) == ["nigrini.2012"]
    data = NIGRINI_2012.to_dict()
    assert data["mad_bounds"]["first"] == [0.006, 0.012, 0.015]
    assert data["mad_bounds"]["first_two"] == [0.0012, 0.0018, 0.0022]
    assert data["mad_bounds"]["second"] == [0.008, 0.010, 0.012]
    assert "Nigrini" in data["source"] and "_interpret_benford_mad" in data["source"]
    assert data["z_critical"] == 1.96 and data["continuity_correction"] is True


def test_z_statistic_with_and_without_continuity_correction() -> None:
    n, expected = 1000, math.log10(2)
    raw = (0.35 - expected) / math.sqrt(expected * (1 - expected) / n)
    corrected = (0.35 - expected - 1 / (2 * n)) / math.sqrt(expected * (1 - expected) / n)
    assert z_statistic(0.35, expected, n, correction=False) == pytest.approx(raw)
    assert z_statistic(0.35, expected, n, correction=True) == pytest.approx(corrected)
    # the correction is skipped when it exceeds the absolute difference
    tiny = expected + 0.0001
    assert z_statistic(tiny, expected, n, correction=True) == pytest.approx(
        0.0001 / math.sqrt(expected * (1 - expected) / n)
    )


def test_first_digit_mad_equals_mean_absolute_deviation() -> None:
    result = benford_test(_benford_values(5000), digits=1)
    conformity = assess(result, "first", "nigrini.2012")
    mad = sum(abs(r.deviation) for r in result.rows) / 9
    assert conformity.mad == pytest.approx(mad)
    assert conformity.mad_level == 0 and conformity.mad_label == "Enge Übereinstimmung"
    assert conformity.chi2_statistic == pytest.approx(result.chi2_statistic)
    assert conformity.p_value == pytest.approx(result.p_value)


def test_uniform_first_digits_are_not_conforming_and_digits_exceed() -> None:
    values = [d * 10 + k for d in range(1, 10) for k in range(100)]
    conformity = assess(benford_test(values, digits=1), "first", "nigrini.2012")
    assert conformity.mad_level == 3 and conformity.mad_label == "Keine Übereinstimmung"
    assert 1 in conformity.exceeding_digits and 9 in conformity.exceeding_digits
    assert conformity.chi2_exceeds
    data = conformity.to_dict()
    assert data["exceeding_digits"] == list(conformity.exceeding_digits)
    assert data["rows"][0]["exceeds"] is True and data["rows"][0]["z"] > 1.96


def test_second_digit_aggregates_first_two_digit_groups() -> None:
    result = benford_test(_benford_values(4000), digits=2, short_values="exclude")
    conformity = assess(result, "second", "nigrini.2012")
    assert [r.digit for r in conformity.rows] == list(range(10))
    assert sum(r.observed_count for r in conformity.rows) == result.analysed
    assert sum(r.expected_share for r in conformity.rows) == pytest.approx(1.0)
    assert conformity.rows[0].expected_share == pytest.approx(0.11968, abs=1e-5)
    assert conformity.rows[9].expected_share == pytest.approx(0.08500, abs=1e-5)
    assert conformity.degrees_of_freedom == 9


def test_level_boundaries_use_strict_less_than() -> None:
    result = benford_test(_benford_values(3000), digits=2, short_values="exclude")
    conformity = assess(result, "first_two", "nigrini.2012")
    bounds = NIGRINI_2012.mad_bounds["first_two"]
    expected = next((i for i, b in enumerate(bounds) if conformity.mad < b), 3)
    assert conformity.mad_level == expected and conformity.degrees_of_freedom == 89


@pytest.mark.parametrize(
    ("digits", "test", "profile", "message"),
    [
        (1, "first_two", "nigrini.2012", "digits=2"),
        (2, "first", "nigrini.2012", "digits=1"),
        (1, "first", "unbekannt", "Bewertungsprofil"),
        (1, "third", "nigrini.2012", "Unbekannter Test"),
    ],
)
def test_invalid_combinations(digits: int, test: str, profile: str, message: str) -> None:
    short = "exclude" if digits == 2 else None
    result = benford_test([12, 34, 56], digits=digits, short_values=short)  # type: ignore[arg-type]
    with pytest.raises(StatisticsInputError, match=message):
        assess(result, test, profile)  # type: ignore[arg-type]
