"""Unit-level projections: guidance examples rebuilt from synthetic units.

The guidance does not reproduce its sample tables. The samples below are
constructed so that their sums and standard deviations equal the printed
aggregates; the full pipeline (validation, projection, TER, conclusion) must
then reproduce the printed results.
"""

from __future__ import annotations

import math

import pytest

from auditcore_extrapolation import (
    INCONCLUSIVE,
    KOM_TABLES,
    NOT_MATERIAL,
    SampleUnit,
    Stratum,
    assess,
)


def two_values(total: float, square_sum: float) -> tuple[float, float]:
    """x, y with x + y = total and x² + y² = square_sum."""
    half = total / 2
    spread = math.sqrt(square_sum / 2 - half**2)
    return half + spread, half - spread


def three_values(total: float, square_sum: float) -> tuple[float, float, float]:
    """x, x, z with 2x + z = total and 2x² + z² = square_sum (smaller root)."""
    root = math.sqrt(16 * total**2 - 24 * (total**2 - square_sum))
    x = (4 * total - root) / 12
    return x, x, total - 2 * x


def test_srs_example_from_units() -> None:
    """6.1.1.6 with 53 units: ΣE = 7,797, s_e = 758, ΣBV_i = 661,580."""
    n, total, sd = 53, 7797.0, 758.0
    big, small = two_values(total, (n - 1) * sd**2 + total**2 / n)
    errors = [big, small] + [0.0] * (n - 2)
    books = [20_000.0, 20_000.0] + [(661_580.0 - 40_000.0) / (n - 2)] * (n - 2)
    units = tuple(
        SampleUnit(f"o{i}", b, e) for i, (b, e) in enumerate(zip(books, errors, strict=True))
    )
    stratum = Stratum("Programm", 46_501_186.0, units, population_size=3852)
    mpu = assess("srs.mean_per_unit", [stratum], confidence_level=0.8, factor_profile=KOM_TABLES)
    assert mpu.projection.projected_random_error == pytest.approx(3852 * total / n)
    assert mpu.projection.precision == pytest.approx(514_169, abs=1)
    ratio = assess("srs.ratio", [stratum], confidence_level=0.8, factor_profile=KOM_TABLES)
    assert ratio.projection.projected_random_error == pytest.approx(46_501_186 * total / 661_580)
    assert mpu.total_error_rate.conclusion == INCONCLUSIVE
    assert "estimator_check" in mpu.projection.extra


def mus_example() -> Stratum:
    """6.3.1.7: 8 high-value units, 69 sampled units with Σ taintings 1.096, s_r 0.09."""
    n = 69
    taints = three_values(1.096, (n - 1) * 0.09**2 + 1.096**2 / n)
    sampled = tuple(
        SampleUnit(f"s{i}", 1_000_000.0, 1_000_000.0 * (taints[i] if i < 3 else 0.0))
        for i in range(n)
    )
    errors = [4_000_000.0, 3_000_000.0, 616_805.0] + [0.0] * 5
    exhaustive = tuple(SampleUnit(f"e{i}", 786_837_081.0 / 8, errors[i]) for i in range(8))
    return Stratum("Programm", 4_199_882_024.0, sampled, exhaustive)


def test_mus_standard_example_from_units() -> None:
    result = assess(
        "mus.standard", [mus_example()], confidence_level=0.9, factor_profile=KOM_TABLES
    )
    projection, ter = result.projection, result.total_error_rate
    assert projection.projected_random_error == pytest.approx(61_829_809, abs=1)
    assert projection.precision == pytest.approx(60_831_129, abs=1)
    assert ter.upper_limit == pytest.approx(122_660_937, abs=2)
    assert ter.tolerable_error == pytest.approx(83_997_640, abs=1)
    assert ter.conclusion == INCONCLUSIVE
    assert projection.strata[0].exhaustive_error == pytest.approx(7_616_805)


def test_mus_ratio_without_systemic_errors_equals_standard() -> None:
    standard = assess(
        "mus.standard", [mus_example()], confidence_level=0.9, factor_profile=KOM_TABLES
    ).projection
    ratio = assess(
        "mus.ratio", [mus_example()], confidence_level=0.9, factor_profile=KOM_TABLES
    ).projection
    assert ratio.projected_random_error == pytest.approx(standard.projected_random_error)
    assert ratio.precision == pytest.approx(standard.precision)


def test_nonstatistical_pps_example_from_units() -> None:
    """6.4.7: 36 units, 4 high-value units (error 80,028), 4 sampled, Σ taintings 0.0272."""
    exhaustive = tuple(
        SampleUnit(f"h{i}", 12_411_965.0 / 4, e) for i, e in enumerate((50_000.0, 30_028.0, 0, 0))
    )
    sampled = tuple(
        SampleUnit(f"s{i}", 500_000.0, 500_000.0 * t) for i, t in enumerate((0.02, 0.0072, 0, 0))
    )
    stratum = Stratum("alle", 22_031_228.0, sampled, exhaustive, population_size=36)
    result = assess("nonstatistical.pps", [stratum])
    assert result.projection.projected_random_error == pytest.approx(145_439, abs=1)
    assert result.projection.precision is None
    assert result.total_error_rate.upper_limit is None
    assert result.total_error_rate.conclusion == NOT_MATERIAL
    assert result.projection.extra["coverage"] == {
        "population_units": 36,
        "audited_units": 8,
        "coverage": 8 / 36,
    }
    assert result.projection.warnings == ()
