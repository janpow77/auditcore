"""Planning (auditcore_sampling.guidance) → sample → projection (this package) fit together.

The sample sizes of EGESIF_16-0014-01 are chosen so that the precision of
the later projection does not exceed the planned margin:

* equal probability and MUS standard: n = (… σ / (TE − AE))², hence a
  sample that shows the planned standard deviation gives
  SE = (TE − AE) × √(n_raw / n) ≤ TE − AE; without errors SE = 0;
* MUS conservative: n = BV × RF / (TE − AE × EF), hence a sample without
  errors gives the upper limit BP = BV × RF / n ≤ TE − AE × EF ≤ TE.

Both packages share the factor profiles; the tables and the high-value
separation are compared here, the only place where both are installed
(``auditcore_sampling`` is a development dependency of this package, never
the other way round).
"""

from __future__ import annotations

import math
import random

from auditcore_sampling import draw_start, simple_random, systematic_mus
from auditcore_sampling import guidance as planning
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from auditcore_extrapolation import (
    INCONCLUSIVE,
    KOM_TABLES,
    NOT_MATERIAL,
    SampleUnit,
    Stratum,
    assess,
    split_top_stratum,
    z_value,
)
from auditcore_extrapolation.factors import RF_ZERO_TABLE, Z_TABLE


def test_factor_tables_are_identical() -> None:
    assert dict(planning.Z_TABLE) == dict(Z_TABLE)
    assert dict(planning.RF_TABLE) == dict(RF_ZERO_TABLE)
    for level in (0.6, 0.8, 0.9, 0.95):
        assert planning.z_value(level, "exact") == z_value(level, "exact")


@settings(max_examples=60)
@given(st.lists(st.floats(1.0, 1e7), min_size=2, max_size=200), st.integers(1, 80))
def test_high_value_separation_agrees(values: list[float], n: int) -> None:
    ours = planning.high_value_split(values, n)
    theirs = split_top_stratum(values, n)
    assert ours.exhaustive == theirs.exhaustive
    assert ours.sampling_size == theirs.sampling_size
    assert math.isclose(ours.interval, theirs.interval)


def _errors_with_sd(count: int, sd: float) -> list[float]:
    """Non-negative errors whose sample standard deviation is exactly ``sd``."""
    base = [float(i % 2) for i in range(count)]
    mean = sum(base) / count
    spread = math.sqrt(sum((b - mean) ** 2 for b in base) / (count - 1))
    return [b * sd / spread for b in base]


def _margin(plan: planning.GuidancePlan) -> float:
    return float(plan.inputs["tolerable_error"]) - float(plan.inputs["anticipated_error"])  # type: ignore[arg-type]


@settings(max_examples=40, deadline=None)
@given(
    st.integers(500, 6000),
    st.floats(10.0, 800.0),
    st.sampled_from([0.6, 0.7, 0.8, 0.9, 0.95]),
    st.floats(0.0, 0.012),
    st.sampled_from(["srs", "difference"]),
)
def test_equal_probability_precision_matches_the_plan(
    units: int, sd: float, level: float, expected: float, kind: str
) -> None:
    value = units * 20_000.0
    plan = planning.equal_probability_size(
        f"guidance.{kind}",
        population_size=units,
        book_value=value,
        error_sd=sd,
        confidence_level=level,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=expected,
    )
    assume(2 <= plan.sample_size < units)
    chosen = simple_random(random.Random(plan.sample_size), range(units), plan.sample_size)
    errors = _errors_with_sd(len(chosen), sd)
    sample = tuple(SampleUnit(f"V{i}", 20_000.0, e) for i, e in zip(chosen, errors, strict=True))
    method = "srs.mean_per_unit" if kind == "srs" else "difference"
    result = assess(
        method,
        [Stratum("P", value, sample, population_size=units)],
        confidence_level=level,
        factor_profile=KOM_TABLES,
    )
    margin = _margin(plan)
    precision = result.projection.precision or 0.0
    assert precision <= margin * (1 + 1e-9)
    assert math.isclose(
        precision, margin * math.sqrt(plan.raw_size / plan.sample_size), rel_tol=1e-9
    )
    zero = tuple(SampleUnit(u.id, u.book_value) for u in sample)
    clean = assess(
        method,
        [Stratum("P", value, zero, population_size=units)],
        confidence_level=level,
        factor_profile=KOM_TABLES,
    )
    assert clean.projection.precision == 0.0
    assert clean.total_error_rate.conclusion == NOT_MATERIAL


@settings(max_examples=40, deadline=None)
@given(
    st.floats(0.01, 0.3),
    st.sampled_from([0.6, 0.8, 0.9]),
    st.floats(0.0, 0.012),
    st.integers(0, 2**31),
)
def test_mus_standard_precision_matches_the_plan(
    rate_sd: float, level: float, expected: float, seed: int
) -> None:
    units, each = 20_000, 50_000.0
    value = units * each
    plan = planning.mus_standard_size(
        book_value=value,
        error_rate_sd=rate_sd,
        confidence_level=level,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=expected,
    )
    assume(2 <= plan.sample_size < units)
    amounts = [each] * units
    interval = value / plan.sample_size
    drawn = systematic_mus(
        amounts,
        sample_size=plan.sample_size,
        interval=interval,
        start=draw_start(random.Random(seed), interval),
        variant="portal",
    )
    rates = [min(r, 1.0) for r in _errors_with_sd(len(drawn.positions), rate_sd)]
    assume(len(drawn.positions) == plan.sample_size and max(rates) < 1.0)
    sample = tuple(
        SampleUnit(f"V{i}", each, each * r) for i, r in zip(drawn.positions, rates, strict=True)
    )
    result = assess(
        "mus.standard",
        [Stratum("P", value, sample)],
        confidence_level=level,
        factor_profile=KOM_TABLES,
    )
    margin = _margin(plan)
    precision = result.projection.precision or 0.0
    assert precision <= margin * (1 + 1e-9)
    assert math.isclose(
        precision, margin * math.sqrt(plan.raw_size / plan.sample_size), rel_tol=1e-9
    )


@settings(max_examples=60, deadline=None)
@given(st.floats(1e6, 1e10), st.sampled_from([0.6, 0.7, 0.8, 0.9, 0.95]), st.floats(0.0, 0.009))
def test_mus_conservative_without_errors_reaches_the_planned_precision(
    value: float, level: float, expected: float
) -> None:
    plan = planning.mus_conservative_size(
        book_value=value,
        confidence_level=level,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=expected,
    )
    ef = float(plan.inputs["expansion_factor"])  # type: ignore[arg-type]
    margin = float(plan.inputs["tolerable_error"]) - float(plan.inputs["anticipated_error"]) * ef  # type: ignore[arg-type]
    sample = tuple(SampleUnit(f"V{i}", 1.0) for i in range(3))
    result = assess(
        "mus.conservative",
        [Stratum("P", value, sample)],
        confidence_level=level,
        factor_profile=KOM_TABLES,
        sample_size=plan.sample_size,
    )
    upper = result.total_error_rate.upper_limit or 0.0
    assert upper <= margin * (1 + 1e-9) <= float(plan.inputs["tolerable_error"]) * (1 + 1e-9)  # type: ignore[arg-type]
    assert math.isclose(upper, margin * plan.raw_size / plan.sample_size, rel_tol=1e-9)
    # ULE = TE only if n_raw is a whole number (e.g. 46,0): then 4.12 says "inconclusive".
    tolerable = result.total_error_rate.tolerable_error
    assert result.total_error_rate.conclusion == (
        NOT_MATERIAL if upper < tolerable else INCONCLUSIVE
    )


def test_guidance_example_6_3_5_7_end_to_end() -> None:
    """n = 136 planned; without errors BP = 30.881.485 × 2,31 = 71.336.231 € < TE."""
    plan = planning.mus_conservative_size(
        book_value=4_199_882_024,
        confidence_level=0.9,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.002,
    )
    result = assess(
        "mus.conservative",
        [Stratum("P", 4_199_882_024, (SampleUnit("V1", 10_173_875.0),))],
        confidence_level=0.9,
        factor_profile=KOM_TABLES,
        sample_size=plan.sample_size,
    )
    assert round(result.projection.precision or 0) == 71_336_231
