"""Invariants of multi-period, sub-sample, group and confidence evaluations (Hypothesis)."""

from __future__ import annotations

import math

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from auditcore_extrapolation import (
    INCONCLUSIVE,
    KOM_TABLES,
    Group,
    Period,
    SampleUnit,
    Stratum,
    SubSample,
    assess,
    assess_groups,
    evaluate_attributes,
    project,
    project_periods,
    project_subsample,
    recalculate_confidence,
)

SETTINGS = settings(max_examples=120, deadline=None, suppress_health_check=[HealthCheck.too_slow])
METHODS = ("srs.mean_per_unit", "srs.ratio", "difference", "mus.standard")
NON_STATISTICAL = ("nonstatistical.mean_per_unit", "nonstatistical.ratio", "nonstatistical.pps")


@st.composite
def strata(draw: st.DrawFn, prefix: str) -> Stratum:
    """A stratum with 3–15 audited units, errors ≤ book values, BV ≥ 5 × sample."""
    count = draw(st.integers(3, 15))
    units = []
    for index in range(count):
        book = draw(st.floats(10.0, 1e6))
        share = draw(st.one_of(st.just(0.0), st.floats(0.0, 1.0)))
        units.append(SampleUnit(f"{prefix}{index}", book, book * share))
    sample_book = math.fsum(u.book_value for u in units)
    factor = draw(st.floats(5.0, 50.0))
    return Stratum(prefix, sample_book * factor, tuple(units), population_size=count * 20)


def _level(method_id: str) -> tuple[float | None, str | None]:
    return (None, None) if method_id in NON_STATISTICAL else (0.8, KOM_TABLES)


@SETTINGS
@given(strata("a"), strata("b"), st.sampled_from(METHODS + NON_STATISTICAL))
def test_periods_add_projections_and_squared_precisions(
    first: Stratum, second: Stratum, method_id: str
) -> None:
    level, profile = _level(method_id)
    both = project_periods(
        method_id,
        [Period("H1", (first,)), Period("H2", (second,))],
        confidence_level=level,
        factor_profile=profile,
    )
    one = project(method_id, [first], confidence_level=level, factor_profile=profile)
    two = project(method_id, [second], confidence_level=level, factor_profile=profile)
    total = one.projected_random_error + two.projected_random_error
    assert both.projected_random_error == pytest.approx(total)
    if one.precision is None or two.precision is None or both.precision is None:
        assert both.precision is None
    else:
        assert both.precision == pytest.approx(math.hypot(one.precision, two.precision))
        assert both.precision >= max(one.precision, two.precision) - 1e-9
    assert {s.period for s in both.strata} == {"H1", "H2"}


@SETTINGS
@given(strata("a"), strata("b"))
def test_two_period_mus_equals_mus_stratified_by_period(first: Stratum, second: Stratum) -> None:
    """6.3.3.4/6.3.3.5 equal the stratified formulas 6.3.2.4/6.3.2.5 with periods as strata."""
    periods = project_periods(
        "mus.standard",
        [Period("H1", (first,)), Period("H2", (second,))],
        confidence_level=0.9,
        factor_profile=KOM_TABLES,
    )
    stratified = project(
        "mus.standard", [first, second], confidence_level=0.9, factor_profile=KOM_TABLES
    )
    assert periods.projected_random_error == pytest.approx(stratified.projected_random_error)
    assert periods.precision == pytest.approx(stratified.precision)


@SETTINGS
@given(strata("a"), strata("b"), st.sampled_from(METHODS))
def test_order_of_periods_does_not_matter(first: Stratum, second: Stratum, method_id: str) -> None:
    forward = project_periods(
        method_id,
        [Period("H1", (first,)), Period("H2", (second,))],
        confidence_level=0.7,
        factor_profile=KOM_TABLES,
    )
    backward = project_periods(
        method_id,
        [Period("H2", (second,)), Period("H1", (first,))],
        confidence_level=0.7,
        factor_profile=KOM_TABLES,
    )
    assert backward.projected_random_error == pytest.approx(forward.projected_random_error)
    assert backward.precision == pytest.approx(forward.precision)


@SETTINGS
@given(strata("x"), st.sampled_from(("ratio", "pps", "mean_per_unit")))
def test_fully_audited_subsample_returns_the_found_error(stratum: Stratum, estimator: str) -> None:
    """A sub-sample covering the whole unit projects exactly the errors found (7.6.3)."""
    book = math.fsum(u.book_value for u in stratum.units)
    full = Stratum("Belege", book, stratum.units, population_size=len(stratum.units))
    result = project_subsample(SubSample("V", estimator, (full,)))
    found = math.fsum(u.random_error for u in stratum.units)
    if estimator != "pps":  # PPS weights by BV_s/n_s, exact only for equal book values
        assert result.projected_error == pytest.approx(found)
    assert result.coverage == pytest.approx(1.0)


@SETTINGS
@given(strata("x"))
def test_subsample_ratio_projects_the_sample_error_rate(stratum: Stratum) -> None:
    result = project_subsample(SubSample("V", "ratio", (stratum,)))
    rate = math.fsum(u.random_error for u in stratum.units) / math.fsum(
        u.book_value for u in stratum.units
    )
    assert result.error_rate == pytest.approx(rate)
    assert 0 <= result.projected_error <= result.book_value * (1 + 1e-12)


@SETTINGS
@given(
    strata("a"), strata("b"), st.sampled_from(("srs.mean_per_unit", "srs.ratio", "mus.standard"))
)
def test_groups_add_up_to_the_group_of_programmes(
    first: Stratum, second: Stratum, method_id: str
) -> None:
    """Top-down projection (7.8.1) equals the sum of the programme projections."""
    result = assess_groups(
        method_id,
        [Group("P1", (first,)), Group("P2", (second,))],
        confidence_level=0.8,
        factor_profile=KOM_TABLES,
    )
    parts = sum(g.assessment.projection.projected_random_error for g in result.groups)
    assert result.overall.projection.projected_random_error == pytest.approx(parts)
    assert all(
        g.observations == len(s.units) for g, s in zip(result.groups, (first, second), strict=True)
    )


@SETTINGS
@given(strata("a"), st.sampled_from(METHODS), st.sampled_from((0.7, 0.8, 0.9, 0.95)))
def test_recalculated_level_makes_the_upper_limit_equal_the_threshold(
    stratum: Stratum, method_id: str, level: float
) -> None:
    result = assess(method_id, [stratum], confidence_level=level, factor_profile=KOM_TABLES)
    ter = result.total_error_rate
    recalculation = recalculate_confidence(result.projection, ter, required_level=0.6)
    if ter.conclusion != INCONCLUSIVE:
        assert not recalculation.applicable
        return
    assert recalculation.applicable and recalculation.confidence_level is not None
    z, z_star = recalculation.coefficient, recalculation.recalculated_coefficient
    assert z is not None and z_star is not None and result.projection.precision is not None
    upper = ter.total_error + result.projection.precision * z_star / z
    assert upper == pytest.approx(ter.tolerable_error, rel=1e-9, abs=1e-6)
    assert recalculation.confidence_level < level + 1e-9
    assert recalculation.supports_not_material == (recalculation.confidence_level >= 0.6)


@SETTINGS
@given(st.integers(1, 2000), st.data(), st.sampled_from((0.6, 0.8, 0.9, 0.95)))
def test_attribute_upper_limit_is_at_least_the_rate(
    size: int, data: st.DataObject, level: float
) -> None:
    deviations = data.draw(st.integers(0, size))
    result = evaluate_attributes(
        deviations, size, confidence_level=level, factor_profile=KOM_TABLES, tolerable_rate=0.1
    )
    assert result.upper_limit >= result.rate
    if deviations in (0, size):
        assert result.precision == 0
