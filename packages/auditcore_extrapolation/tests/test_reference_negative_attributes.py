"""Negative units (4.6), discovery and stop-or-go sampling (7.9.6), groups over periods."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_extrapolation import (
    KOM_TABLES,
    DeclaredUnit,
    ExtrapolationInputError,
    NegativeCheck,
    Period,
    SampleUnit,
    Stratum,
    assess_groups_over_periods,
    evaluate_discovery,
    evaluate_stop_or_go,
    review_negative_units,
    split_population,
    upper_deviation_limit,
)

UNITS = (
    DeclaredUnit("X", 100_000),
    DeclaredUnit("Y", 25_000, current_corrections=700, previous_corrections=4_300),
    DeclaredUnit("Z", 10_000, previous_corrections=15_000),
)


def test_negative_units_example_4_6() -> None:
    """X 100,000; Y 25,000 − 700 (current) − 4,300 (earlier); Z 10,000 − 15,000: net 115,000."""
    first = split_population(UNITS, 1)
    assert dict(first.positive) == {"X": 100_000, "Y": 20_000}
    assert dict(first.negative) == {"Z": -5_000}
    assert first.net_declared == 115_000 and len(first.notes) == 2
    third = split_population(UNITS, 3)
    assert dict(third.positive) == {"X": 100_000, "Y": 24_300, "Z": 10_000}
    assert dict(third.negative) == {"Y": -4_300, "Z": -15_000}
    second = split_population(UNITS, 2)
    assert dict(second.positive)["Y"] == 25_000 and dict(second.negative)["Y"] == -5_000
    for split in (first, second, third):
        assert split.positive_total + split.negative_total == pytest.approx(split.net_declared)


def test_negative_units_inputs_and_review() -> None:
    with pytest.raises(ExtrapolationInputError, match="Variante"):
        split_population(UNITS, 4)
    with pytest.raises(ExtrapolationInputError, match="≥ 0"):
        split_population([DeclaredUnit("A", -1.0)], 2)
    review = review_negative_units(
        [NegativeCheck("Z", 12_000, 15_000), NegativeCheck("Y", 700, 700)]
    )
    assert review.disclose and review.shortfalls == (("Z", 3_000),)


@settings(max_examples=150, deadline=None)
@given(
    st.lists(
        st.tuples(st.floats(0, 1e6), st.floats(0, 1e5), st.floats(0, 1e5)), min_size=1, max_size=20
    ),
    st.sampled_from((1, 2, 3)),
)
def test_split_reconciles_with_the_net_declared(
    rows: list[tuple[float, float, float]], approach: int
) -> None:
    units = [DeclaredUnit(f"u{i}", a, b, c) for i, (a, b, c) in enumerate(rows)]
    split = split_population(units, approach)
    assert split.positive_total + split.negative_total == pytest.approx(
        split.net_declared, abs=1e-6
    )
    assert all(a > 0 for _, a in split.positive) and all(a < 0 for _, a in split.negative)


@pytest.mark.parametrize(("deviations", "size"), [(0, 59), (1, 93), (2, 124)])
def test_exact_upper_limit_matches_the_attribute_sampling_table(deviations: int, size: int) -> None:
    """Classic table values (5 % tolerable, 95 %): n = 59, 93, 124 for 0, 1, 2 deviations."""
    assert upper_deviation_limit(deviations, size, 0.95) <= 0.05
    assert upper_deviation_limit(deviations, size - 1, 0.95) > 0.05


def test_discovery_and_stop_or_go() -> None:
    clean = evaluate_discovery(0, 59, confidence_level=0.95, critical_rate=0.05)
    assert clean.conclusion == "criterion_met"
    assert (
        evaluate_discovery(1, 59, confidence_level=0.95, critical_rate=0.05).conclusion
        == "deviation_found"
    )
    assert evaluate_discovery(0, 20, confidence_level=0.95, critical_rate=0.05).conclusion == "go"
    assert (
        evaluate_stop_or_go(1, 93, confidence_level=0.95, tolerable_rate=0.05).conclusion == "stop"
    )
    assert evaluate_stop_or_go(2, 93, confidence_level=0.95, tolerable_rate=0.05).conclusion == "go"
    with pytest.raises(ExtrapolationInputError):
        evaluate_stop_or_go(1, 10, confidence_level=0.95, tolerable_rate=1.5)


@settings(max_examples=100, deadline=None)
@given(st.integers(1, 400), st.data(), st.sampled_from((0.8, 0.9, 0.95)))
def test_upper_limit_is_monotone(size: int, data: st.DataObject, level: float) -> None:
    k = data.draw(st.integers(0, size - 1))
    upper = upper_deviation_limit(k, size, level)
    assert k / size <= upper <= 1
    assert upper_deviation_limit(k + 1, size, level) >= upper
    assert upper_deviation_limit(k, size, min(level + 0.04, 0.99)) >= upper


def _stratum(name: str, errors: tuple[float, ...]) -> Stratum:
    units = tuple(SampleUnit(f"{name}{i}", 1_000.0, e) for i, e in enumerate(errors))
    return Stratum(name, 200_000.0, units)


def test_groups_over_periods_6_3_4_and_7_8() -> None:
    """Programmes as strata in each semester; per programme over both semesters."""
    periods = [
        Period("H1", (_stratum("P1", (10, 0, 0, 5)), _stratum("P2", (0, 0, 2)))),
        Period("H2", (_stratum("P1", (0, 20, 0)), _stratum("P2", (3, 0, 0, 0)))),
    ]
    labels = {(p.name, s.name): s.name for p in periods for s in p.strata}
    result = assess_groups_over_periods(
        "mus.standard", periods, labels, confidence_level=0.9, factor_profile=KOM_TABLES
    )
    parts = sum(g.assessment.projection.projected_random_error for g in result.groups)
    assert result.overall.projection.projected_random_error == pytest.approx(parts)
    assert [g.name for g in result.groups] == ["P1", "P2"]
    assert result.groups[0].observations == 7
    with pytest.raises(ExtrapolationInputError, match="ohne Programm"):
        assess_groups_over_periods(
            "mus.standard", periods, {}, confidence_level=0.9, factor_profile=KOM_TABLES
        )
