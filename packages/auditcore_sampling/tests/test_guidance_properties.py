"""Invariants of the guidance-based planning (Hypothesis)."""

from __future__ import annotations

import math

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from auditcore_sampling.guidance import (
    EXACT,
    KOM_TABLES,
    RF_TABLE,
    SRS,
    Z_TABLE,
    StratumInput,
    equal_probability_size,
    high_value_split,
    mus_conservative_size,
    mus_standard_size,
    reliability_factor,
    stratified_equal_probability_size,
    z_value,
)
from auditcore_sampling.guidance.plan import largest_remainder

book = st.floats(min_value=1e4, max_value=1e10, allow_nan=False)
rate = st.floats(min_value=0.0, max_value=0.015, allow_nan=False)
levels = st.sampled_from(sorted(Z_TABLE))


@given(st.integers(0, 500), st.lists(st.floats(0.01, 1e6), min_size=1, max_size=12))
def test_largest_remainder_sums_to_total_and_stays_within_one(
    total: int, weights: list[float]
) -> None:
    shares = largest_remainder(total, weights)
    assert sum(shares) == total
    exact = [total * w / math.fsum(weights) for w in weights]
    assert all(abs(s - x) < 1 for s, x in zip(shares, exact, strict=True))


@given(st.integers(30, 50_000), book, st.floats(1.0, 1e6), levels, rate, st.booleans())
def test_srs_size_is_between_one_and_n(
    units: int, value: float, sd: float, level: float, expected: float, fpc: bool
) -> None:
    plan = equal_probability_size(
        SRS,
        population_size=units,
        book_value=value,
        error_sd=sd,
        confidence_level=level,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=expected,
        finite_population_correction=fpc,
    )
    assert 1 <= plan.sample_size <= units
    assert plan.sample_size >= min(units, math.floor(plan.raw_size))


@given(book, st.floats(0.001, 2.0), rate, rate)
def test_mus_size_grows_with_anticipated_error(
    value: float, sd: float, low: float, high: float
) -> None:
    low, high = sorted((low, high))
    sizes = [
        mus_standard_size(
            book_value=value,
            error_rate_sd=sd,
            confidence_level=0.9,
            factor_profile=KOM_TABLES,
            anticipated_error_rate=r,
        ).raw_size
        for r in (low, high)
    ]
    assert sizes[0] <= sizes[1]


@given(
    book, st.floats(0.0, 0.01), st.sampled_from(sorted(RF_TABLE)), st.sampled_from(sorted(RF_TABLE))
)
def test_conservative_size_grows_with_confidence(
    value: float, expected: float, a: float, b: float
) -> None:
    low, high = sorted((a, b))
    assume(0.02 - expected * 1.9 > 0)
    sizes = [
        mus_conservative_size(
            book_value=value,
            confidence_level=level,
            factor_profile=KOM_TABLES,
            anticipated_error_rate=0.0,
        ).sample_size
        for level in (low, high)
    ]
    assert sizes[0] <= sizes[1]


@given(st.sampled_from(sorted(Z_TABLE)))
def test_exact_z_matches_table_3_to_three_places(level: float) -> None:
    assert abs(z_value(level, EXACT) - Z_TABLE[level]) < 0.0015


@given(st.sampled_from(sorted(RF_TABLE)))
def test_exact_rf_matches_table_4_to_two_places(level: float) -> None:
    """Table 4 rounds −ln(1 − CL) up at 90 %, 70 % and 50 % (2,3026 → 2,31)."""
    assert abs(reliability_factor(level, EXACT) - RF_TABLE[level]) < 0.011


@settings(max_examples=60)
@given(st.lists(st.floats(1.0, 1e7), min_size=2, max_size=300), st.integers(1, 120))
def test_high_value_split_leaves_no_unit_above_the_interval(values: list[float], n: int) -> None:
    split = high_value_split(values, n)  # k units above BV/k' < n: always room left
    rest = [v for i, v in enumerate(values) if i not in split.exhaustive]
    assert all(v <= split.interval * (1 + 1e-12) for v in rest)
    assert split.sampling_size == n - len(split.exhaustive)
    assert math.isclose(split.sampling_book_value, math.fsum(rest))


@given(
    st.lists(st.tuples(st.integers(5, 5000), st.floats(1.0, 1e5)), min_size=1, max_size=6),
    book,
    rate,
)
def test_stratified_allocation_respects_strata(
    rows: list[tuple[int, float]], value: float, expected: float
) -> None:
    strata = [StratumInput(f"S{i}", n, None, sd) for i, (n, sd) in enumerate(rows)]
    plan = stratified_equal_probability_size(
        SRS,
        strata=strata,
        book_value=value,
        confidence_level=0.8,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=expected,
    )
    assert all(row.sample_size <= (row.population_size or 0) for row in plan.strata)
    assert plan.sample_size == sum(row.sample_size for row in plan.strata)
