"""Zielwerte der Hochrechnung (Version 0.3.0), unabhängig nachgerechnet.

Die Erwartungen stehen als Rechenweg mit ``math`` im Test, nicht aus dem
Rechenkern übernommen. Synthetische Fälle E2, E4, E5, E8, E10, E11, E13 und R3
aus der Prüfung vom 23.11.2026. z = 1,645 (90 %, Profil ``kom_2017_tables``);
t-Quantile mit SciPy 1.x gegengerechnet (``scipy.stats.t.ppf``).
"""

from __future__ import annotations

import math
from decimal import Decimal

import pytest

from auditcore_extrapolation import (
    INCONCLUSIVE,
    KOM_TABLES,
    MINIMUM_SAMPLE_UNITS,
    ExtrapolationInputError,
    ResidualInputs,
    SampleUnit,
    Stratum,
    assess,
    general_stratified_precision,
    incremental_allowances,
    is_proportional,
    project,
    residual_error_rate,
    stratified_precision,
)
from auditcore_extrapolation._student_t import t_quantile

Z90 = 1.645


def _units(prefix: str, book: float, errors: list[float]) -> tuple[SampleUnit, ...]:
    return tuple(SampleUnit(f"{prefix}{i}", book, e) for i, e in enumerate(errors, 1))


def _variance(errors: list[float]) -> float:
    mean = math.fsum(errors) / len(errors)
    return math.fsum((e - mean) ** 2 for e in errors) / (len(errors) - 1)


ERRORS_A = [0.0, 400.0, 0.0, 2000.0, 0.0]


@pytest.mark.parametrize(
    ("probability", "df", "expected"),
    [(0.95, 1, 6.313752), (0.95, 9, 1.833113), (0.95, 29, 1.699127), (0.975, 29, 2.045230)],
)
def test_t_quantiles_match_scipy(probability: float, df: int, expected: float) -> None:
    assert t_quantile(probability, df) == pytest.approx(expected, abs=1e-6)


@pytest.mark.parametrize(("probability", "df"), [(0.5, 3), (1.0, 3), (0.9, 0), (0.9, True)])
def test_t_quantile_rejects_invalid_input(probability: float, df: int) -> None:
    with pytest.raises(ValueError):
        t_quantile(probability, df)


def test_e13_non_proportional_allocation_uses_the_general_formula() -> None:
    """E13: A (N 1 000, n 5, Fehler 0/400/0/2 000/0), B (N 200, n 25, fehlerfrei).

    s_A² = 752 000; SE = z · √(N_A² s_A² / n_A) = 1,645 · 1 000 · √(752 000 / 5)
    = 637 955 €; EE = 1 000 · 480 = 480 000 €; ULE 1 117 955 € > TE 900 000 €
    (2 % von 45 Mio. €) → nicht schlüssig. Die Formel aus Anhang II hätte bei
    dieser Aufteilung 285 302 € und „nicht wesentlich“ ergeben.
    """
    var_a = _variance(ERRORS_A)
    assert var_a == 752_000
    expected_se = Z90 * 1000 * math.sqrt(var_a / 5)
    assert round(expected_se) == 637_955
    a = Stratum("A", 40_000_000, _units("a", 40_000, ERRORS_A), population_size=1000)
    b = Stratum("B", 5_000_000, _units("b", 25_000, [0.0] * 25), population_size=200)
    result = assess("srs.mean_per_unit", [a, b], confidence_level=0.9, factor_profile=KOM_TABLES)
    ter = result.total_error_rate
    assert result.projection.projected_random_error == pytest.approx(480_000)
    assert result.projection.precision == pytest.approx(expected_se)
    assert ter.upper_limit == pytest.approx(480_000 + expected_se)
    assert ter.tolerable_error == pytest.approx(900_000)
    assert ter.conclusion == INCONCLUSIVE
    assert any("nicht proportional" in w for w in result.projection.warnings)
    annex = stratified_precision(Z90, [(1000, math.sqrt(var_a), 5), (200, 0.0, 25)])
    assert round(annex) == 285_302


def test_e8_non_proportional_allocation_in_the_other_direction() -> None:
    """E8: A (N 1 000, n 5), B (N 20, n 5, Fehler 0/5 000/0/0/15 000).

    s_B² = 42 500 000; SE = 1,645 · √(1 000² · 752 000 / 5 + 20² · 42 500 000 / 5).
    """
    errors_b = [0.0, 5000.0, 0.0, 0.0, 15000.0]
    var_b = _variance(errors_b)
    assert var_b == 42_500_000
    expected = Z90 * math.sqrt(1000**2 * 752_000 / 5 + 20**2 * var_b / 5)
    a = Stratum("A", 10_000_000, _units("a", 10_000, ERRORS_A), population_size=1000)
    b = Stratum("B", 1_000_000, _units("b", 50_000, errors_b), population_size=20)
    result = project("srs.mean_per_unit", [a, b], confidence_level=0.9, factor_profile=KOM_TABLES)
    assert result.precision == pytest.approx(expected)
    assert result.projected_random_error == pytest.approx(1000 * 480 + 20 * 4000)


def test_proportional_allocation_keeps_the_annex_formula() -> None:
    """Bei n_h = n · N_h / N sind Anhang-II-Formel und allgemeine Formel gleich."""
    strata = [(1000.0, 30.0, 10), (500.0, 80.0, 5)]
    assert is_proportional(strata)
    assert stratified_precision(Z90, strata) == pytest.approx(
        general_stratified_precision(Z90, strata)
    )
    assert not is_proportional([(1000.0, 30.0, 5), (200.0, 0.0, 25)])


def test_e11_two_units_warn_and_report_the_t_comparison() -> None:
    """E11: n 2, N 200, Fehler 500/0. SE = 1,645 · 200 · 353,55 / √2 = 82 250 €.

    Vergleichswert mit t(1; 0,95) = 6,3138: 82 250 · 6,3138 / 1,645 = 315 688 €.
    """
    stratum = Stratum("A", 2_400_000, _units("u", 10_000, [500.0, 0.0]), population_size=200)
    result = assess("srs.mean_per_unit", [stratum], confidence_level=0.9, factor_profile=KOM_TABLES)
    projection = result.projection
    se = Z90 * 200 * math.sqrt(_variance([500.0, 0.0])) / math.sqrt(2)
    assert se == pytest.approx(82_250)
    assert projection.precision == pytest.approx(se)
    minimum = projection.extra["minimum_sample"]
    assert isinstance(minimum, dict)
    assert minimum["audited_units"] == 2 and minimum["minimum"] == MINIMUM_SAMPLE_UNITS == 30
    comparison = minimum["t_comparison"]
    assert comparison["degrees_of_freedom"] == 1
    assert comparison["precision_t"] == pytest.approx(se * 6.313752 / Z90, rel=1e-6)
    assert round(comparison["precision_t"]) == 315_688
    assert any("Art. 5 Abs. 5" in text for text in projection.limitations)
    assert any("Art. 5 Abs. 5" in w for w in projection.warnings)
    assert result.total_error_rate.limitations == projection.limitations
    assert any("Eingeschränkte Aussagekraft" in e for e in result.total_error_rate.explanation)


def test_e5_ten_units_t_comparison() -> None:
    """E5: n 10, N 200, Fehler 0/0/500/0/1 200/0/0/300/0/0.

    SE = 1,645 · 200 · s / √10 = 40 739 €; mit t(9) = 1,8331: 45 398 €.
    """
    errors = [0.0, 0.0, 500.0, 0.0, 1200.0, 0.0, 0.0, 300.0, 0.0, 0.0]
    stratum = Stratum("A", 2_400_000, _units("u", 10_000, errors), population_size=200)
    projection = project(
        "srs.mean_per_unit", [stratum], confidence_level=0.9, factor_profile=KOM_TABLES
    )
    se = Z90 * 200 * math.sqrt(_variance(errors)) / math.sqrt(10)
    assert round(se) == 40_739
    assert projection.precision == pytest.approx(se)
    comparison = projection.extra["minimum_sample"]["t_comparison"]  # type: ignore[index]
    assert round(comparison["precision_t"]) == 45_398


def test_thirty_units_have_no_minimum_warning() -> None:
    errors = [0.0] * 27 + [100.0, 300.0, 50.0]
    stratum = Stratum("A", 3_000_000, _units("u", 10_000, errors), population_size=300)
    projection = project(
        "srs.mean_per_unit", [stratum], confidence_level=0.9, factor_profile=KOM_TABLES
    )
    assert "minimum_sample" not in projection.extra
    assert projection.limitations == ()


def test_e2_mus_standard_without_errors_uses_the_basic_precision() -> None:
    """E2: 30 Einheiten ohne Fehler, BV 2 Mio. €. SI = 2 000 000 / 30 = 66 666,67 €;
    SE = SI × RF(0) = 66 666,67 × 2,31 = 154 000 € > TE 40 000 € → nicht schlüssig
    (vorher SE 0, ULE 0, „nicht wesentlich“)."""
    units = tuple(SampleUnit(f"u{i}", 10_000 + i * 1000) for i in range(1, 31))
    stratum = Stratum("A", 2_000_000, units)
    result = assess("mus.standard", [stratum], confidence_level=0.9, factor_profile=KOM_TABLES)
    projection = result.projection
    assert projection.projected_random_error == 0
    assert projection.precision == pytest.approx(2_000_000 / 30 * 2.31)
    assert round(projection.precision or 0) == 154_000
    zero = projection.extra["zero_errors"]
    assert isinstance(zero, dict) and zero["standard_precision"] == 0
    assert result.total_error_rate.upper_limit == pytest.approx(154_000)
    assert result.total_error_rate.conclusion == INCONCLUSIVE


def test_e4_conservative_allowances_use_one_basic_factor() -> None:
    """E4: n 50, BV 10 Mio. €, SI 200 000 €, Fehlerquoten 0,5 und 0,1.

    BP = 200 000 · 2,31 = 462 000; Zuschläge (3,89 − 2,31 − 1) · 200 000 · 0,5
    = 58 000 und (5,32 − 3,89 − 1) · 200 000 · 0,1 = 8 600 (RF(2) = 5,32 nach
    Tabelle 4 und Anhang 3); SE = 528 600 €. Vorher 529 600 € (erster Zuschlag
    mit RF(0) = 2,30: 59 000). Der Prüfbericht nannte 528 800 €; das setzt
    RF(2) = 5,33 voraus und ist um 200 € zu hoch.
    """
    rows = incremental_allowances([("u2", 0.5), ("u1", 0.1)], 200_000, 0.9, KOM_TABLES)
    assert [round(r.allowance) for r in rows] == [58_000, 8_600]
    units = [SampleUnit(f"u{i}", 30_000) for i in range(3, 51)]
    units[:0] = [SampleUnit("u1", 30_000, 3_000), SampleUnit("u2", 30_000, 15_000)]
    stratum = Stratum("A", 10_000_000, tuple(units))
    projection = project(
        "mus.conservative",
        [stratum],
        confidence_level=0.9,
        factor_profile=KOM_TABLES,
        sample_size=50,
    )
    assert projection.precision == pytest.approx(462_000 + 58_000 + 8_600)
    assert projection.projected_random_error == pytest.approx(200_000 * 0.6)


def test_e10_empty_stratum_message_names_the_stratum() -> None:
    a = Stratum("A", 2_400_000, _units("u", 10_000, [500.0, 0.0, 300.0]), population_size=200)
    b = Stratum("B", 100_000, (), population_size=10)
    with pytest.raises(
        ExtrapolationInputError, match="Schicht 'B': Mindestens eine geprüfte Einheit erforderlich"
    ):
        project("srs.mean_per_unit", [a, b], confidence_level=0.9, factor_profile=KOM_TABLES)


def test_r3_negative_residual_rate_is_stated_not_clamped() -> None:
    """R3: A 1 000, TER 1 %, H 15 → G 10, I 985, J = −5, K = −5 / 985 = −0,51 %."""
    result = residual_error_rate(
        ResidualInputs(Decimal(1000), Decimal("0.01"), financial_corrections=Decimal(15))
    )
    assert result.residual_amount == Decimal(-5)
    assert result.rate is not None and float(result.rate) == pytest.approx(-5 / 985)
    assert result.rate_rounded == Decimal("-0.0051")
    shown = result.to_dict()
    assert shown["residual_negative"] is True
    assert any("negativ" in note for note in result.notes)
    assert shown["not_applicable"] == (
        "Entfällt: Restfehlerquote nicht über der Signifikanzschwelle von 2 %."
    )
