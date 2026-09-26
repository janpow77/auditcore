"""Systemic and anomalous errors, TER composition and input validation."""

from __future__ import annotations

import pytest

from auditcore_extrapolation import (
    KOM_TABLES,
    MATERIAL,
    Assessment,
    ExtrapolationInputError,
    SampleUnit,
    Stratum,
    assess,
    project,
)


def sample(*units: SampleUnit, systemic: float = 0.0, size: int = 100) -> Stratum:
    return Stratum("S", 1_000_000.0, units, population_size=size, systemic_error=systemic)


BASE = (
    SampleUnit("a", 10_000.0, 500.0),
    SampleUnit("b", 20_000.0, 0.0),
    SampleUnit("c", 5_000.0, 250.0),
)


def run(stratum: Stratum, method: str = "srs.mean_per_unit") -> Assessment:
    return assess(method, [stratum], confidence_level=0.8, factor_profile=KOM_TABLES)


def test_anomalous_error_needs_a_reason() -> None:
    unit = SampleUnit("x", 1000.0, anomalous_error=100.0)
    with pytest.raises(ExtrapolationInputError, match="Begründung"):
        run(sample(*BASE, unit))


def test_uncorrected_anomalous_error_enters_ter_without_projection() -> None:
    plain = run(sample(*BASE, SampleUnit("x", 1000.0)))
    anomalous = run(
        sample(*BASE, SampleUnit("x", 1000.0, anomalous_error=100.0, anomalous_reason="Einzelfall"))
    )
    assert anomalous.projection.projected_random_error == plain.projection.projected_random_error
    ter = anomalous.total_error_rate
    assert ter.anomalous_uncorrected == 100.0
    assert ter.total_error == pytest.approx(plain.total_error_rate.total_error + 100.0)
    assert any("anomal" in w for w in anomalous.projection.warnings)


def test_corrected_anomalous_error_is_not_part_of_ter() -> None:
    unit = SampleUnit(
        "x", 1000.0, anomalous_error=100.0, anomalous_reason="Einzelfall", anomalous_corrected=True
    )
    result = run(sample(*BASE, unit)).total_error_rate
    assert result.anomalous_uncorrected == 0.0
    assert result.anomalous_corrected_excluded == 100.0
    assert any("Korrigierte anomale" in line for line in result.explanation)


def test_delimited_systemic_errors_are_added_not_projected() -> None:
    unit = SampleUnit("x", 1000.0, systemic_error=200.0)
    result = run(sample(*BASE, unit, systemic=5_000.0))
    assert result.total_error_rate.systemic_errors == 5_000.0
    plain = run(sample(*BASE, SampleUnit("x", 1000.0)))
    assert result.projection.projected_random_error == plain.projection.projected_random_error
    assert result.total_error_rate.total_error == pytest.approx(
        plain.total_error_rate.total_error + 5_000.0
    )


def test_systemic_errors_must_be_delimited() -> None:
    unit = SampleUnit("x", 1000.0, systemic_error=200.0)
    with pytest.raises(ExtrapolationInputError, match="zufällige Fehler"):
        run(sample(*BASE, unit))


def test_ratio_estimation_deducts_systemic_errors_from_book_values() -> None:
    """Appendix 1, 2.3: EE₂ = BV′ × ΣE / ΣBV′_i."""
    unit = SampleUnit("x", 1000.0, systemic_error=200.0)
    result = run(sample(*BASE, unit, systemic=50_000.0), "srs.ratio").projection
    expected = (1_000_000 - 50_000) * 750 / (36_000 - 200)
    assert result.projected_random_error == pytest.approx(expected)


def test_difference_estimation_reports_corrected_book_value() -> None:
    result = run(sample(*BASE), "difference").total_error_rate
    assert result.difference is not None
    corrected = result.book_value - result.total_error
    assert result.difference.corrected_book_value == pytest.approx(corrected)
    assert result.difference.lower_limit == pytest.approx(corrected - (result.precision or 0))
    assert result.difference.book_value_less_tolerable == pytest.approx(0.98 * result.book_value)


def test_high_error_is_material() -> None:
    heavy = tuple(SampleUnit(f"h{i}", 1000.0, 500.0) for i in range(5))
    assert run(sample(*heavy)).total_error_rate.conclusion == MATERIAL


@pytest.mark.parametrize(
    ("unit", "message"),
    [
        (SampleUnit("x", 0.0), "größer als 0"),
        (SampleUnit("x", 100.0, -1.0), "nicht negativ"),
        (SampleUnit("x", 100.0, 150.0), "übersteigen"),
        (SampleUnit("x", 100.0, anomalous_corrected=True), "korrigiert"),
    ],
)
def test_invalid_units_are_rejected(unit: SampleUnit, message: str) -> None:
    with pytest.raises(ExtrapolationInputError, match=message):
        run(sample(*BASE, unit))


def test_statistical_methods_need_level_and_profile() -> None:
    with pytest.raises(ExtrapolationInputError, match="Konfidenzniveau"):
        project("srs.ratio", [sample(*BASE)])
    with pytest.raises(ExtrapolationInputError, match="Faktorprofil"):
        project("srs.ratio", [sample(*BASE)], confidence_level=0.8, factor_profile="x")
    with pytest.raises(ExtrapolationInputError, match="Tabelle 3"):
        project("srs.ratio", [sample(*BASE)], confidence_level=0.85, factor_profile=KOM_TABLES)


def test_materiality_above_two_percent_is_rejected() -> None:
    with pytest.raises(ExtrapolationInputError, match="2 %"):
        assess(
            "srs.ratio",
            [sample(*BASE)],
            confidence_level=0.8,
            factor_profile=KOM_TABLES,
            materiality_rate=0.05,
        )


def test_population_size_is_required_for_equal_probability() -> None:
    stratum = Stratum("S", 1_000_000.0, BASE)
    with pytest.raises(ExtrapolationInputError, match="Anzahl der Einheiten"):
        run(stratum)


def test_unknown_method() -> None:
    with pytest.raises(ExtrapolationInputError, match="Unbekannte Methode"):
        project("mus.magic", [sample(*BASE)])


def test_nonstatistical_coverage_warnings() -> None:
    result = project("nonstatistical.ratio", [sample(*BASE, size=400)])
    assert result.precision is None
    assert any("300" in w for w in result.warnings)
    assert any("unter 10 %" in w for w in result.warnings)


def test_conservative_rejects_stratification_and_needs_sample_size() -> None:
    one = Stratum("A", 1_000_000.0, BASE)
    two = Stratum("B", 1_000_000.0, (SampleUnit("z", 1000.0),))
    with pytest.raises(ExtrapolationInputError, match="Schichtung"):
        project(
            "mus.conservative",
            [one, two],
            confidence_level=0.9,
            factor_profile=KOM_TABLES,
            sample_size=10,
        )
    with pytest.raises(ExtrapolationInputError, match="Stichprobenumfang"):
        project("mus.conservative", [one], confidence_level=0.9, factor_profile=KOM_TABLES)
