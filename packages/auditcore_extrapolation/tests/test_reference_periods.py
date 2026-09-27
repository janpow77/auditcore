"""Reference cases for samples in several periods (6.1.3, 6.2.3, 6.3.3, 6.3.4, 6.4.9, 7.3).

The statistical examples print only aggregates (sums, standard deviations);
several of them cannot be rebuilt from non-negative errors because the printed
standard deviation exceeds ΣE/√n (see docs/referenzfaelle.md). They are
recomputed from the printed aggregates with the library formulas. The
non-statistical examples of 6.4.9 run through the whole pipeline.
"""

from __future__ import annotations

import pytest

from auditcore_extrapolation import (
    KOM_TABLES,
    NOT_MATERIAL,
    Period,
    SampleUnit,
    Stratum,
    assess_periods,
    combined_precision,
    conclude,
    mean_per_unit_error,
    mus_precision,
    precision,
    ratio_error,
    tainting_projection,
    z_value,
)


def test_srs_two_periods_6_1_3_6() -> None:
    """60 %, N_1 = N_2 = 3,852, n_1 = 49, n_2 = 52."""
    z = z_value(0.6, KOM_TABLES)
    ee1 = mean_per_unit_error(3852, 199_185, 49) + mean_per_unit_error(3852, 374_790, 52)
    assert ee1 == pytest.approx(43_421_670, abs=1)
    ee2 = ratio_error(1_237_952_015, 199_185, 13_039_581) + ratio_error(
        2_961_930_008, 374_790, 34_323_574
    )
    # printed 51,252,484; the numerator of r2 is misprinted as 51,252,451
    assert ee2 == pytest.approx(51_252_484, abs=1)
    se1 = combined_precision([precision(3852, z, 69_815, 49), precision(3852, z, 59_489, 52)])
    se2 = combined_precision([precision(3852, z, 54_897, 49), precision(3852, z, 57_659, 52)])
    assert se1 == pytest.approx(41_980_051, abs=1)
    assert se2 == pytest.approx(36_325_544, abs=1)
    tolerable = 0.02 * (1_237_952_015 + 2_961_930_008)
    assert tolerable == pytest.approx(83_997_640, abs=1)
    assert ee2 + se2 == pytest.approx(87_578_028, abs=1)
    assert conclude(ee2, ee2 + se2, tolerable) == "inconclusive"


def test_difference_two_periods_6_2_3_6() -> None:
    """90 %: EE and SE belong to n_1 = 73 and n_2 = 47 (printed 142 and 68: misprint)."""
    z = z_value(0.9, KOM_TABLES)
    ee = mean_per_unit_error(3852, 577_230, 73) + mean_per_unit_error(3852, 588_336, 47)
    assert ee == pytest.approx(78_677_283, abs=1)
    book = 1_237_952_015 + 5_202_775_175
    assert book - ee == pytest.approx(6_362_049_907, abs=1)
    # the result belongs to s_e2 = 78,489 of the table (the formula prints 78,849)
    se = combined_precision([precision(3852, z, 52_815, 73), precision(3852, z, 78_489, 47)])
    assert se == pytest.approx(82_444_754, abs=1)
    assert book - ee - se == pytest.approx(6_279_605_153, abs=1)
    assert book * 0.98 == pytest.approx(6_311_912_646, abs=1)


def test_mus_two_periods_6_3_3_7() -> None:
    """60 %, exhaustive errors 19,240,855 and 9,340,755."""
    z = z_value(0.6, KOM_TABLES)
    ee_s = tainting_projection(936_162_740 / 34, 1.4256) + tainting_projection(
        2_546_691_025 / 96, 1.1875
    )
    assert ee_s == pytest.approx(70_754_790, abs=1)
    ee = 19_240_855 + 9_340_755 + ee_s
    assert ee == pytest.approx(99_336_400, abs=1)
    se = mus_precision(z, [(936_162_740, 34, 0.085), (2_546_691_025, 96, 0.29)])
    assert se == pytest.approx(64_499_188, abs=1)
    assert ee + se == pytest.approx(163_835_589, abs=1)
    tolerable = 0.02 * (1_827_930_259 + 2_961_930_008)
    assert tolerable == pytest.approx(95_797_205, abs=1)


def test_mus_two_periods_stratified_6_3_4_7() -> None:
    """90 %, two programmes in two semesters; exhaustive error 13,768."""
    z = z_value(0.9, KOM_TABLES)
    parts = [
        (24_147_946, 27, 0.0823, 0.0868),
        (10_697_561, 13, 0.1145, 0.0696),
        (25_740_723, 18, 0.1345, 0.0737),
        (11_914_400, 8, 0.0934, 0.0401),
    ]
    ee_s = sum(tainting_projection(book / n, rates) for book, n, rates, _ in parts)
    assert ee_s == pytest.approx(499_268, abs=1)
    assert 13_768 + ee_s == pytest.approx(513_036, abs=1)
    se = mus_precision(z, [(book, n, sd) for book, n, _, sd in parts])
    # printed 1,062,778 uses the tainting sum 0.0823 instead of s_r = 0.0868 (misprint)
    misprinted = mus_precision(
        z, [(24_147_946, 27, 0.0823)] + [(b, n, s) for b, n, _, s in parts[1:]]
    )
    assert misprinted == pytest.approx(1_062_778, abs=1)
    assert se == pytest.approx(1_083_499, abs=1)
    tolerable = 0.02 * (42_610_732 + 49_211_269)
    assert tolerable == pytest.approx(1_836_440, abs=1)
    assert conclude(13_768 + ee_s, 13_768 + ee_s + se, tolerable) == NOT_MATERIAL


def test_mus_two_periods_enlarged_first_sample_7_3_2_2() -> None:
    """60 %: first semester enlarged to 57 sampled units (section 7.3.2)."""
    z = z_value(0.6, KOM_TABLES)
    first = 1_827_930_259 - 891_767_519 - 83_678_923
    ee = (
        28_581_610
        + tainting_projection(first / 57, 0.8391)
        + tainting_projection(2_546_691_025 / 107, 0.2875)
    )
    assert ee == pytest.approx(47_973_814, abs=1)
    se = mus_precision(z, [(first, 57, 0.059), (2_546_691_025, 107, 0.129)])
    assert se == pytest.approx(27_323_507, abs=1)
    assert ee + se == pytest.approx(75_297_320, abs=1)


def _equal(prefix: str, n: int, book: float, error: float) -> tuple[SampleUnit, ...]:
    return tuple(SampleUnit(f"{prefix}{i}", book / n, error / n) for i in range(n))


def test_nonstatistical_two_periods_equal_probability_6_4_9_1() -> None:
    """Ratio estimation with a high-value stratum in each semester."""
    first = Stratum(
        "Programm",
        19_930_259,
        _equal("a", 3, 1_150_398, 4_801),
        (SampleUnit("H1", 3_388_144, 127),),
        population_size=41,
    )
    second = Stratum(
        "Programm",
        40_378_264,
        _equal("b", 3, 1_200_987, 5_287),
        tuple(SampleUnit(f"H2-{i}", 6_756_739 / 3, 432_076 / 3) for i in range(3)),
        population_size=61,
    )
    result = assess_periods(
        "nonstatistical.ratio",
        [Period("1. Halbjahr", (first,)), Period("2. Halbjahr", (second,))],
        population_units=63,
    )
    ter = result.total_error_rate
    # printed 649,247.94 with BV_s2 = 33,621,524 (elsewhere 33,621,525)
    assert result.projection.projected_random_error == pytest.approx(649_247.94, abs=0.5)
    assert ter.tolerable_error == pytest.approx(1_206_170, abs=1)
    assert ter.conclusion == NOT_MATERIAL and ter.upper_limit is None
    periods = result.projection.extra["periods"]
    assert isinstance(periods, list) and len(periods) == 2


def test_nonstatistical_two_periods_pps_6_4_9_2() -> None:
    """PPS selection: 3 + 3 sampled units, 2 high-value operations in the second semester."""
    first = Stratum(
        "Programm",
        16_930_259,
        tuple(SampleUnit(f"a{i}", 2_000_000, 2_000_000 * 0.022) for i in range(3)),
        population_size=34,
    )
    second = Stratum(
        "Programm",
        49_378_264,
        tuple(SampleUnit(f"b{i}", 700_000, 700_000 * 0.0475 / 3) for i in range(3)),
        (SampleUnit("H1", 11_000_000, 30_000), SampleUnit("H2", 10_895_357, 26_823)),
        population_size=46,
    )
    result = assess_periods(
        "nonstatistical.pps",
        [Period("1. Halbjahr", (first,)), Period("2. Halbjahr", (second,))],
        population_units=48,
    )
    assert result.projection.projected_random_error == pytest.approx(864_435, abs=1)
    assert result.total_error_rate.tolerable_error == pytest.approx(1_326_170, abs=1)
    assert result.total_error_rate.conclusion == NOT_MATERIAL
