"""Factor tables, conservative MUS on units, top-stratum separation, reuse of auditcore_sampling."""

from __future__ import annotations

from typing import cast

import pytest
from auditcore_sampling import MUS_POISSON, recommended_mus_size

from auditcore_extrapolation import (
    EXACT,
    KOM_TABLES,
    ExtrapolationInputError,
    SampleUnit,
    Stratum,
    assess,
    basic_reliability_factor,
    poisson_factor,
    reliability_factor,
    split_top_stratum,
    split_top_stratum_for_plan,
    z_value,
)
from auditcore_extrapolation import _rf_table as appendix3
from auditcore_extrapolation.factors import RF_ZERO_TABLE, Z_TABLE, poisson_cdf


def test_appendix3_equals_exact_poisson_limits_rounded() -> None:
    """All 510 printed factors are the exact Poisson limits to two decimals."""
    for errors, row in enumerate(appendix3.ROWS):
        for level, printed in zip(appendix3.LEVELS, row, strict=True):
            assert abs(poisson_factor(errors, level) - printed) <= 0.005 + 1e-12


def test_table4_rounds_up_where_appendix3_rounds() -> None:
    """Table 4 prints 2.31/1.21/0.70 where Appendix 3 prints 2.30/1.20/0.69."""
    assert basic_reliability_factor(0.90, KOM_TABLES) == 2.31
    assert reliability_factor(0, 0.90, KOM_TABLES) == 2.30
    for level, value in RF_ZERO_TABLE.items():
        assert abs(poisson_factor(0, level) - value) < 0.011


def test_z_table_is_the_two_sided_normal_quantile() -> None:
    for level, value in Z_TABLE.items():
        assert z_value(level, EXACT) == pytest.approx(value, abs=5e-4)


def test_basic_factors_agree_with_auditcore_sampling() -> None:
    """Reuse check: the MUS size method of auditcore_sampling uses the same RF(0)."""
    shared = set(MUS_POISSON.factors) & set(RF_ZERO_TABLE)
    assert shared == {0.50, 0.80, 0.90, 0.95, 0.99}
    for level in shared:
        assert basic_reliability_factor(level, KOM_TABLES) == MUS_POISSON.factors[level]


def test_exact_profile_accepts_any_level_tables_do_not() -> None:
    assert z_value(0.99, EXACT) == pytest.approx(2.5758, abs=1e-4)
    with pytest.raises(ExtrapolationInputError, match="Tabelle 3"):
        z_value(0.99, KOM_TABLES)
    with pytest.raises(ExtrapolationInputError, match="0 bis 50"):
        reliability_factor(51, 0.9, KOM_TABLES)
    assert reliability_factor(51, 0.9, EXACT) > reliability_factor(50, 0.9, KOM_TABLES)


def test_poisson_factor_solves_the_cdf() -> None:
    for errors in (0, 1, 5, 40):
        factor = poisson_factor(errors, 0.9)
        assert poisson_cdf(errors, factor) == pytest.approx(0.1, abs=1e-9)


def test_conservative_units_basic_precision_and_allowances() -> None:
    """SI = 100,000; taintings 0.5 and 0.1 (ordered), RF from Appendix 3 at 90 %."""
    units = (
        SampleUnit("low", 10_000.0, 1_000.0),
        SampleUnit("high", 20_000.0, 10_000.0),
        SampleUnit("clean", 30_000.0),
    )
    exhaustive = (SampleUnit("big", 150_000.0, 3_000.0),)
    stratum = Stratum("P", 1_000_000.0, units, exhaustive)
    result = assess(
        "mus.conservative",
        [stratum],
        confidence_level=0.9,
        factor_profile=KOM_TABLES,
        sample_size=10,
    )
    projection = result.projection
    assert projection.projected_random_error == pytest.approx(3_000 + 100_000 * 0.6)
    rows = cast(list[dict[str, object]], projection.extra["allowances"])
    assert [r["unit_id"] for r in rows] == ["high", "low"]
    first = (3.89 - 2.30 - 1) * 50_000
    second = (5.32 - 3.89 - 1) * 10_000
    assert projection.precision == pytest.approx(100_000 * 2.31 + first + second)
    assert projection.coefficient == 2.31


def test_split_top_stratum_iterates_until_no_unit_exceeds_the_interval() -> None:
    values = [500.0, 400.0, 90.0] + [10.0] * 20
    top = split_top_stratum(values, 10)
    assert top.cut_off == pytest.approx(119.0)
    # 500 and 400 exceed the cut-off; 90 exceeds the first interval 290 / 8
    assert top.exhaustive == (0, 1, 2)
    rest = [v for i, v in enumerate(values) if i not in top.exhaustive]
    assert all(v <= top.interval for v in rest)
    assert top.sampling_size == 7
    assert top.interval == pytest.approx(200.0 / 7)


def test_split_top_stratum_single_round() -> None:
    values = [100.0, 60.0] + [1.0] * 40
    top = split_top_stratum(values, 5)
    assert top.cut_off == pytest.approx(40.0)
    assert top.exhaustive == (0, 1)
    assert top.interval == pytest.approx(40.0 / 3)


def test_split_with_a_size_plan_of_auditcore_sampling() -> None:
    plan = recommended_mus_size(
        population_value=475_478.94,
        materiality=50_000.0,
        expected_error_rate=0.005,
        confidence_level=0.95,
    )
    values = [475_478.94 - 99 * 1000.0] + [1000.0] * 99
    top = split_top_stratum_for_plan(values, plan)
    assert plan.sample_size == 30
    assert top.exhaustive == (0,)
    assert top.sampling_size == 29
