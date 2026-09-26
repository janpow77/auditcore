"""Invariants of projection, TER and RER (property-based, Hypothesis)."""

from __future__ import annotations

import math
import random as random_module
from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from auditcore_extrapolation import (
    EXACT,
    KOM_TABLES,
    ResidualInputs,
    SampleUnit,
    Stratum,
    assess,
    poisson_factor,
    project,
    residual_error_rate,
    split_top_stratum,
    stratified_precision,
)

SETTINGS = settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@st.composite
def units(draw: st.DrawFn, minimum: int = 3, maximum: int = 25) -> tuple[SampleUnit, ...]:
    """Audited units with book values 1–1e6 and random errors ≤ book value."""
    count = draw(st.integers(minimum, maximum))
    result = []
    for index in range(count):
        book = draw(st.floats(1.0, 1e6))
        share = draw(st.one_of(st.just(0.0), st.floats(0.0, 1.0)))
        result.append(SampleUnit(f"u{index}", book, book * share))
    return tuple(result)


def equal_stratum(sample: tuple[SampleUnit, ...], extra: int = 50) -> Stratum:
    books = math.fsum(u.book_value for u in sample)
    return Stratum("S", books * 10, sample, population_size=len(sample) + extra)


STATISTICAL = ("srs.mean_per_unit", "srs.ratio", "difference")


@SETTINGS
@given(units(), st.sampled_from(STATISTICAL), st.sampled_from((0.6, 0.7, 0.8, 0.9, 0.95)))
def test_upper_limit_is_at_least_ter_and_ter_at_least_projection(
    sample: tuple[SampleUnit, ...], method: str, level: float
) -> None:
    result = assess(
        method, [equal_stratum(sample)], confidence_level=level, factor_profile=KOM_TABLES
    )
    ter = result.total_error_rate
    assert ter.total_error >= result.projection.projected_random_error - 1e-9
    assert ter.upper_limit is not None and ter.upper_limit >= ter.total_error - 1e-9
    assert ter.rate == pytest.approx(ter.total_error / ter.book_value)


@SETTINGS
@given(units(), st.sampled_from(STATISTICAL + ("mus.standard",)), st.randoms())
def test_order_of_units_does_not_matter(
    sample: tuple[SampleUnit, ...], method: str, random: random_module.Random
) -> None:
    shuffled = list(sample)
    random.shuffle(shuffled)
    first = project(
        method, [equal_stratum(sample)], confidence_level=0.8, factor_profile=KOM_TABLES
    )
    second = project(
        method, [equal_stratum(tuple(shuffled))], confidence_level=0.8, factor_profile=KOM_TABLES
    )
    assert second.projected_random_error == pytest.approx(first.projected_random_error)
    assert second.precision == pytest.approx(first.precision)


@SETTINGS
@given(units(), st.sampled_from(STATISTICAL + ("mus.standard",)))
def test_clean_sample_projects_zero(sample: tuple[SampleUnit, ...], method: str) -> None:
    clean = tuple(SampleUnit(u.id, u.book_value) for u in sample)
    result = assess(method, [equal_stratum(clean)], confidence_level=0.9, factor_profile=KOM_TABLES)
    assert result.projection.projected_random_error == 0
    assert result.projection.precision == 0
    assert result.total_error_rate.conclusion == "not_material"


@SETTINGS
@given(units(), units())
def test_stratified_precision_with_one_stratum_is_the_simple_formula(
    left: tuple[SampleUnit, ...], right: tuple[SampleUnit, ...]
) -> None:
    single = stratified_precision(1.282, [(100.0, 5.0, 10)])
    assert single == pytest.approx(100 * 1.282 * 5 / math.sqrt(10))
    a = Stratum("A", 1e7, left, population_size=len(left) + 40)
    b = Stratum(
        "B",
        2e7,
        tuple(SampleUnit("b" + u.id, u.book_value, u.random_error) for u in right),
        population_size=len(right) + 60,
    )
    both = project("srs.mean_per_unit", [a, b], confidence_level=0.8, factor_profile=KOM_TABLES)
    alone_a = project("srs.mean_per_unit", [a], confidence_level=0.8, factor_profile=KOM_TABLES)
    alone_b = project("srs.mean_per_unit", [b], confidence_level=0.8, factor_profile=KOM_TABLES)
    assert both.projected_random_error == pytest.approx(
        alone_a.projected_random_error + alone_b.projected_random_error
    )


@SETTINGS
@given(units())
def test_mus_ratio_without_systemic_errors_equals_standard(sample: tuple[SampleUnit, ...]) -> None:
    stratum = Stratum("S", math.fsum(u.book_value for u in sample) * 5, sample)
    standard = project("mus.standard", [stratum], confidence_level=0.9, factor_profile=EXACT)
    ratio = project("mus.ratio", [stratum], confidence_level=0.9, factor_profile=EXACT)
    assert ratio.projected_random_error == pytest.approx(standard.projected_random_error)
    assert ratio.precision == pytest.approx(standard.precision, abs=1e-6)


@SETTINGS
@given(units(1, 20), st.integers(1, 30))
def test_conservative_precision_is_at_least_the_basic_precision(
    sample: tuple[SampleUnit, ...], extra: int
) -> None:
    book = math.fsum(u.book_value for u in sample) * 3
    stratum = Stratum("S", book, sample)
    result = project(
        "mus.conservative",
        [stratum],
        confidence_level=0.9,
        factor_profile=KOM_TABLES,
        sample_size=len(sample) + extra,
    )
    basic = book / (len(sample) + extra) * 2.31
    assert result.precision is not None and result.precision >= basic - 1e-6


@SETTINGS
@given(st.integers(0, 60), st.floats(0.5, 0.995), st.floats(0.5, 0.995))
def test_poisson_factor_increases_with_errors_and_level(errors: int, a: float, b: float) -> None:
    low, high = sorted((a, b))
    assert poisson_factor(errors + 1, low) > poisson_factor(errors, low)
    assert poisson_factor(errors, high) >= poisson_factor(errors, low) - 1e-9


@SETTINGS
@given(
    st.lists(st.floats(0.01, 1e6), min_size=2, max_size=200),
    st.integers(1, 60),
)
def test_top_stratum_leaves_no_unit_above_the_interval(values: list[float], size: int) -> None:
    try:
        top = split_top_stratum(values, size)
    except Exception as exc:  # noqa: BLE001 - only the documented refusal is allowed
        assert "Stichprobenplätze" in str(exc)
        return
    rest = [v for i, v in enumerate(values) if i not in top.exhaustive]
    assert all(v <= top.interval * (1 + 1e-12) for v in rest)
    assert top.sampling_size == size - len(top.exhaustive)
    assert top.sampling_book_value == pytest.approx(math.fsum(rest))


RATES = st.decimals(Decimal("0"), Decimal("0.2"), places=4)
AMOUNTS = st.decimals(Decimal("0"), Decimal("1000"), places=2)


@SETTINGS
@given(RATES, AMOUNTS)
def test_rer_never_exceeds_ter_and_equals_it_without_corrections(
    ter: Decimal, corrections: Decimal
) -> None:
    plain = residual_error_rate(ResidualInputs(Decimal(100_000), ter))
    assert plain.rate == ter
    corrected = residual_error_rate(
        ResidualInputs(Decimal(100_000), ter, financial_corrections=corrections)
    )
    assert corrected.rate is not None and corrected.rate <= ter


@SETTINGS
@given(st.decimals(Decimal("0.021"), Decimal("0.5"), places=4), AMOUNTS)
def test_extrapolated_correction_brings_rer_to_materiality(
    ter: Decimal, corrections: Decimal
) -> None:
    result = residual_error_rate(
        ResidualInputs(Decimal(100_000), ter, financial_corrections=corrections)
    )
    if result.exceeds_materiality:
        assert result.rate_after_correction == pytest.approx(Decimal("0.02"), abs=Decimal("1e-20"))
    else:
        assert result.extrapolated_correction is None
