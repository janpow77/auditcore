"""Proportional control (guidance 7.10): examples 7.10.3.1 b, 7.10.3.2, 7.10.3.3, 7.10.3.4."""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_extrapolation import (
    INCONCLUSIVE,
    KOM_TABLES,
    NOT_MATERIAL,
    ExtrapolationInputError,
    SampleUnit,
    Stratum,
    assess,
    extension_factor,
    project,
)


def spread(total: float, square_sum: float, count: int, books: float) -> list[SampleUnit]:
    """``count`` units with book value ``books``: k values a, one b (Σ = total, Σ² = square_sum)."""
    for k in range(1, count):
        disc = 4 * k * k * total**2 - 4 * (k * k + k) * (total**2 - square_sum)
        if disc < 0:
            continue
        for a in (
            (2 * k * total + math.sqrt(disc)) / (2 * (k * k + k)),
            (2 * k * total - math.sqrt(disc)) / (2 * (k * k + k)),
        ):
            b = total - k * a
            if a >= 0 and b >= 0 and max(a, b) <= books:
                values = [a] * k + [b] + [0.0] * (count - k - 1)
                return [SampleUnit(f"s{i}", books, v) for i, v in enumerate(values)]
    raise AssertionError("keine Zerlegung")


def test_mus_exclusion_7_10_3_2() -> None:
    """90 %: 4 operations (12,706,417 €) excluded; 87 sampled, Σ E/BV = 1.026, s_r = 0.0832."""
    rates = spread(1.026, 86 * 0.0832**2 + 1.026**2 / 87, 87, 1.0)
    units = tuple(SampleUnit(u.id, 1_000_000.0, u.random_error * 1_000_000.0) for u in rates)
    top = tuple(
        SampleUnit(f"h{i}", 586_837_081 / 6, 7_616_805 / 3 if i < 3 else 0.0) for i in range(6)
    )
    stratum = Stratum(
        "Programm", 4_187_175_607, units, top, excluded_book_value=12_706_417, excluded_units=4
    )
    result = assess("mus.standard", [stratum], confidence_level=0.9, factor_profile=KOM_TABLES)
    ter = result.total_error_rate
    assert result.projection.projected_random_error == pytest.approx(50_225_817, abs=2)
    assert result.projection.precision == pytest.approx(53_015_513, abs=2)
    assert ter.upper_limit == pytest.approx(103_241_330, abs=3)
    assert ter.tolerable_error == pytest.approx(83_997_640, abs=1)
    assert ter.conclusion == INCONCLUSIVE


def test_conservative_exclusion_7_10_3_3() -> None:
    """Extension factor of the low-value stratum 2,832,370,231 / 2,824,751,647."""
    factor = extension_factor(2_832_370_231, 2_824_751_647)
    assert 30_881_485 * 1.077 * factor == pytest.approx(33_349_063, abs=2)
    assert 85_766_992 * factor == pytest.approx(85_998_313, abs=1)
    assert 7_843_574 + 30_881_485 * 1.077 * factor == pytest.approx(41_192_637, abs=2)


def _srs_stratum() -> Stratum:
    """7.10.3.4: 45 units, ΣE 378,906, s_e 28,199, ΣBV 23,424,898; top stratum 2 of 3 audited."""
    units = spread(378_906, 44 * 28_199**2 + 378_906**2 / 45, 45, 23_424_898 / 45)
    top = (SampleUnit("h1", 150_000_000, 469_301), SampleUnit("h2", 53_577_481, 0.0))
    return Stratum(
        "Programm",
        2_208_284_489,
        tuple(units),
        top,
        population_size=3_514,
        excluded_book_value=2_006_876_728 - 2_004_707_008,
        excluded_units=5,
        excluded_exhaustive_book_value=295_006_242 - 203_577_481,
        excluded_exhaustive_units=1,
    )


def test_srs_mean_per_unit_exclusion_7_10_3_4() -> None:
    result = assess(
        "srs.mean_per_unit", [_srs_stratum()], confidence_level=0.7, factor_profile=KOM_TABLES
    )
    assert result.projection.projected_random_error == pytest.approx(30_317_560.43, abs=0.05)
    assert result.projection.precision == pytest.approx(15_316_501.38, abs=5)
    ter = result.total_error_rate
    assert ter.book_value == 2_301_882_970
    assert ter.upper_limit == pytest.approx(45_634_061.81, abs=5)
    assert ter.conclusion == NOT_MATERIAL


def test_srs_ratio_exclusion_7_10_3_4() -> None:
    stratum = _srs_stratum()
    result = assess("srs.ratio", [stratum], confidence_level=0.7, factor_profile=KOM_TABLES)
    assert result.projection.projected_random_error == pytest.approx(33_142_008.96, abs=0.05)
    reduced = project(
        "srs.ratio",
        [
            Stratum(
                "P",
                stratum.book_value,
                stratum.units,
                stratum.exhaustive_units,
                population_size=3514,
            )
        ],
        confidence_level=0.7,
        factor_profile=KOM_TABLES,
    )
    assert reduced.precision is not None
    # SE for the reduced population (N = 3,512), extended by 2,006,876,728 / 2,004,707,008 = 1.0011
    assert result.projection.precision == pytest.approx(
        reduced.precision * 2_006_876_728 / 2_004_707_008
    )


def test_pps_replacement_of_a_high_value_unit_7_10_3_1_b() -> None:
    """7 of 8 high-value operations audited (error 420), 23 sampled with Σ E/BV = 0.52."""
    units = tuple(SampleUnit(f"s{i}", 1_000_000.0, 1_000_000.0 * 0.52 / 23) for i in range(23))
    top = tuple(SampleUnit(f"h{i}", 1_697_136_654 / 7, 60.0) for i in range(7))
    stratum = Stratum(
        "Programm",
        4_199_882_024 - 290_309_600,
        units,
        top,
        population_size=3_851,
        excluded_exhaustive_book_value=290_309_600,
        excluded_exhaustive_units=1,
    )
    result = assess("nonstatistical.pps", [stratum])
    assert result.projection.projected_random_error == pytest.approx(50_020_779, abs=1)
    assert result.total_error_rate.book_value == 4_199_882_024


def test_exclusion_inputs() -> None:
    with pytest.raises(ExtrapolationInputError, match="7.10.3.1 b"):
        project(
            "nonstatistical.pps",
            [Stratum("S", 1000.0, (SampleUnit("a", 10.0),), excluded_exhaustive_book_value=5.0)],
        )
    with pytest.raises(ExtrapolationInputError, match="nicht negativ"):
        project(
            "nonstatistical.pps",
            [Stratum("S", 1000.0, (SampleUnit("a", 10.0),), excluded_book_value=-1.0)],
        )
    with pytest.raises(ExtrapolationInputError, match="mindestens so groß"):
        extension_factor(1.0, 2.0)


@settings(max_examples=100, deadline=None)
@given(
    st.floats(1.0, 1e6), st.integers(1, 500), st.lists(st.floats(0.0, 1.0), min_size=3, max_size=12)
)
def test_mean_per_unit_extension_equals_direct_projection(
    excluded: float, excluded_units: int, shares: list[float]
) -> None:
    """Footnotes 69/70: extending by N_orig/N_red equals projecting with the original N."""
    units = tuple(SampleUnit(f"u{i}", 100.0, 100.0 * share) for i, share in enumerate(shares))
    reduced = Stratum(
        "S",
        1e6,
        units,
        population_size=1000,
        excluded_book_value=excluded,
        excluded_units=excluded_units,
    )
    direct = Stratum("S", 1e6 + excluded, units, population_size=1000 + excluded_units)
    one = project("srs.mean_per_unit", [reduced], confidence_level=0.8, factor_profile=KOM_TABLES)
    two = project("srs.mean_per_unit", [direct], confidence_level=0.8, factor_profile=KOM_TABLES)
    assert one.projected_random_error == pytest.approx(two.projected_random_error)
    assert one.precision == pytest.approx(two.precision)
    plain = project(
        "srs.mean_per_unit",
        [Stratum("S", 1e6, units, population_size=1000)],
        confidence_level=0.8,
        factor_profile=KOM_TABLES,
    )
    assert one.projected_random_error >= plain.projected_random_error - 1e-9
