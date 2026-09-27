"""Contract of the guidance-based planning: explicit choices, no silent defaults."""

from __future__ import annotations

import pytest

from auditcore_sampling import SamplingInputError
from auditcore_sampling.guidance import (
    EXACT,
    KOM_TABLES,
    SRS,
    StratumInput,
    equal_probability_size,
    error_sd,
    expansion_factor,
    high_value_split,
    mus_conservative_size,
    mus_standard_size,
    mus_stratified_size,
    nonstatistical_minimum,
    stratified_equal_probability_size,
    z_value,
)

BASE = {
    "population_size": 1000,
    "book_value": 1e7,
    "error_sd": 500.0,
    "confidence_level": 0.9,
    "factor_profile": KOM_TABLES,
    "anticipated_error_rate": 0.005,
}


def test_unknown_profile_level_and_method_are_rejected() -> None:
    with pytest.raises(SamplingInputError, match="Faktorprofil"):
        z_value(0.9, "tabelle")
    with pytest.raises(SamplingInputError, match="Tabelle 3"):
        z_value(0.99, KOM_TABLES)
    assert z_value(0.99, EXACT) == pytest.approx(2.5758, abs=1e-4)
    with pytest.raises(SamplingInputError, match="Tabelle 5"):
        expansion_factor(0.97)
    with pytest.raises(SamplingInputError, match="Unbekannte Methode"):
        equal_probability_size("guidance.mus_standard", **BASE)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"materiality_rate": 0.025}, "höchstens 2 %"),
        ({"anticipated_error_rate": 0.02}, "kleiner als die Wesentlichkeit"),
        ({"error_sd": 0.0}, "größer als 0"),
        ({"population_size": 0}, "ganze Zahl"),
        ({"book_value": float("nan")}, "endliche Zahl"),
        ({"confidence_level": True}, "Konfidenzniveau"),
    ],
)
def test_invalid_inputs(change: dict[str, object], message: str) -> None:
    with pytest.raises(SamplingInputError, match=message):
        equal_probability_size(SRS, **{**BASE, **change})  # type: ignore[arg-type]


def test_lower_materiality_is_allowed_and_warnings_are_given() -> None:
    plan = equal_probability_size(SRS, **{**BASE, "materiality_rate": 0.01})  # type: ignore[arg-type]
    assert plan.inputs["tolerable_error"] == 100_000
    small = equal_probability_size(SRS, **{**BASE, "error_sd": 20.0})  # type: ignore[arg-type]
    assert any("Faustregel" in w for w in small.warnings)
    big = equal_probability_size(SRS, **{**BASE, "error_sd": 5000.0})  # type: ignore[arg-type]
    assert big.sample_size == 1000 and any("Vollerhebung" in w for w in big.warnings)
    corrected = equal_probability_size(
        SRS,
        **{**BASE, "error_sd": 5000.0},
        finite_population_correction=True,  # type: ignore[arg-type]
    )
    assert corrected.sample_size < 1000


def test_conservative_margin_must_be_positive() -> None:
    with pytest.raises(SamplingInputError, match="EF"):
        mus_conservative_size(
            book_value=1e6,
            confidence_level=0.95,
            factor_profile=KOM_TABLES,
            anticipated_error_rate=0.0125,
        )
    plan = mus_conservative_size(
        book_value=1e6, confidence_level=0.95, factor_profile=KOM_TABLES, anticipated_error_rate=0.0
    )
    assert plan.inputs["expansion_factor"] == 1.0 and plan.sample_size == 150


def test_strata_contracts() -> None:
    with pytest.raises(SamplingInputError, match="eindeutigem Namen"):
        stratified_equal_probability_size(
            SRS,
            strata=[StratumInput("A", 10, sd=1.0), StratumInput("A", 10, sd=1.0)],
            book_value=1e6,
            confidence_level=0.8,
            factor_profile=KOM_TABLES,
            anticipated_error_rate=0.0,
        )
    with pytest.raises(SamplingInputError, match="Stichprobenschicht"):
        stratified_equal_probability_size(
            SRS,
            strata=[StratumInput("A", 10, exhaustive=True)],
            book_value=1e6,
            confidence_level=0.8,
            factor_profile=KOM_TABLES,
            anticipated_error_rate=0.0,
        )
    with pytest.raises(SamplingInputError, match="Hochwertgruppe"):
        mus_stratified_size(
            strata=[StratumInput("A", book_value=1.0, exhaustive=True)],
            confidence_level=0.9,
            factor_profile=KOM_TABLES,
            anticipated_error_rate=0.0,
        )


def test_minimum_three_per_stratum_is_applied_with_warning() -> None:
    plan = stratified_equal_probability_size(
        SRS,
        strata=[StratumInput("groß", 5000, sd=900.0), StratumInput("klein", 20, sd=900.0)],
        book_value=5e7,
        confidence_level=0.8,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.005,
    )
    rows = {r.name: r.sample_size for r in plan.strata}
    assert rows["klein"] >= 3 and any("Mindestens 3" in w for w in plan.warnings)


def test_mus_book_values_must_add_up_and_be_positive() -> None:
    with pytest.raises(SamplingInputError, match="ergeben"):
        mus_standard_size(
            book_value=100.0,
            error_rate_sd=0.1,
            confidence_level=0.9,
            factor_profile=KOM_TABLES,
            anticipated_error_rate=0.0,
            book_values=[50.0, 40.0],
        )
    with pytest.raises(SamplingInputError, match="größer als 0"):
        high_value_split([100.0, 0.0], 2)


def test_nonstatistical_contracts() -> None:
    with pytest.raises(SamplingInputError, match="Unbekannte Regel"):
        nonstatistical_minimum("art_79", population_size=10)
    with pytest.raises(SamplingInputError, match="book_value"):
        nonstatistical_minimum("cpr_2013_art127_1", population_size=10)
    with pytest.raises(SamplingInputError, match="Bewertungsstufe"):
        nonstatistical_minimum("cpr_2021_art79_2", population_size=10, assurance_level="works")
    assert nonstatistical_minimum("cpr_2021_art79_2", population_size=3).sample_size == 1
    big = nonstatistical_minimum("cpr_2021_art79_2", population_size=299)
    assert big.sample_size == 30 and any("150" in w for w in big.warnings)
    with pytest.raises(SamplingInputError, match="2 Werte"):
        error_sd([1.0])
