"""Worked examples of EGESIF_16-0014-01 recalculated with the guidance-based planning.

Each test states the printed result; misprints and rounding of the guidance
are named where the recalculation differs (see docs/leitfaden-umfang.md).
"""

from __future__ import annotations

import math

import pytest

from auditcore_sampling.guidance import (
    DIFFERENCE,
    GUIDANCE_STATUS,
    KOM_TABLES,
    SRS,
    StratumInput,
    equal_probability_size,
    error_rate_sd,
    error_rates,
    error_sd,
    high_value_split,
    mus_conservative_size,
    mus_standard_size,
    mus_stratified_size,
    nonstatistical_minimum,
    stratified_equal_probability_size,
)


def sizes(plan: object) -> dict[str, int]:
    return {row.name: row.sample_size for row in plan.strata}  # type: ignore[attr-defined]


def test_srs_6_1_1_6() -> None:
    """N 3.852, BV 46.501.186 €, σ_e 518 €, 80 %, AE 1,24 % → n ≈ 53 (52,39 aufgerundet)."""
    plan = equal_probability_size(
        SRS,
        population_size=3852,
        book_value=46_501_186,
        error_sd=518,
        confidence_level=0.80,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.0124,
    )
    assert plan.sample_size == 53
    assert plan.raw_size == pytest.approx(52.3905, abs=1e-4)
    assert plan.inputs["tolerable_error"] == pytest.approx(930_024, abs=1)
    assert plan.inputs["anticipated_error"] == pytest.approx(576_615, abs=1)
    assert plan.status == GUIDANCE_STATUS


def test_srs_stratified_6_1_2_6() -> None:
    """n ≈ 121 (+ 5 Hochwert) = 126; Aufteilung 90 / 31 / 5.

    Unstimmigkeit: N₁ + N₂ = 3.582 + 1.225 = 4.807, der Leitfaden rechnet aber
    mit N = 4.802 (Gesamtzahl ohne die 5 Hochwertvorhaben) und erhält
    σ_w² = 24.737.134; mit N = 4.807 sind es 24.711.404. Druckfehler: die Formel
    für n zeigt √24.734,134. Alle Varianten ergeben n = 121 (120,17 / 120,16 /
    120,30 aufgerundet).
    """
    plan = stratified_equal_probability_size(
        SRS,
        strata=[
            StratumInput("Programm 1", 3582, 43_226_801, 444),
            StratumInput("Programm 2", 1225, 1_348_417_361, 9818),
            StratumInput("Hochwert", 5, 4_891_156, exhaustive=True),
        ],
        book_value=1_396_535_319,
        confidence_level=0.80,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.018,
    )
    assert plan.inputs["weighted_variance"] == pytest.approx(24_711_404, abs=1)
    assert plan.inputs["population_size"] == 4807
    assert math.ceil(plan.raw_size) == 121
    assert plan.sample_size == 126
    assert sizes(plan) == {"Programm 1": 90, "Programm 2": 31, "Hochwert": 5}
    assert plan.method == "guidance.srs_stratified"


def test_difference_6_2_1_6() -> None:
    """N 3.852, BV 4.199.882.024 €, σ_e 168.397 €, 60 %, AE 0,7 % → n ≈ 101."""
    plan = equal_probability_size(
        DIFFERENCE,
        population_size=3852,
        book_value=4_199_882_024,
        error_sd=168_397,
        confidence_level=0.60,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.007,
    )
    assert plan.sample_size == 101
    assert plan.inputs["z"] == 0.842


def test_difference_stratified_6_2_2_6() -> None:
    """σ_w² 32.092.103.451, n ≈ 51, Aufteilung 16 / 35, Hochwert 5.

    Druckfehler: die Formel für n setzt z = 0,845 ein; mit 0,845 wären es 52
    (51,11), das gedruckte Ergebnis 51 gehört zu z = 0,842 (50,75). Der
    Leitfaden prüft danach 60 Vorhaben, weil die Vorstichprobe von 20 in
    Schicht 1 vollständig verwendet wird; geplant sind 16 + 35 + 5 = 56.
    """
    plan = stratified_equal_probability_size(
        DIFFERENCE,
        strata=[
            StratumInput("Programm 1", 1520, 3_023_598_442, 21_312),
            StratumInput("Programm 2", 3347, 2_832_769_525, 215_546),
            StratumInput("Hochwert", 5, 584_359_223, exhaustive=True),
        ],
        book_value=6_440_727_190,
        confidence_level=0.60,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.004,
    )
    assert plan.inputs["weighted_variance"] == pytest.approx(32_092_103_451, abs=1)
    assert plan.raw_size == pytest.approx(50.75, abs=0.01)
    assert sizes(plan) == {"Programm 1": 16, "Programm 2": 35, "Hochwert": 5}
    assert plan.sample_size == 56


def test_mus_standard_6_3_1_7() -> None:
    """σ_r 0,085, 90 %, AE 0,4 % → n ≈ 77; Schwellenwert BV/n.

    Druckfehler: der Leitfaden druckt den Schwellenwert 54.593.922 €; BV/77
    ist 54.543.922 €.
    """
    plan = mus_standard_size(
        book_value=4_199_882_024,
        error_rate_sd=0.085,
        confidence_level=0.90,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.004,
    )
    assert plan.sample_size == 77
    assert plan.raw_size == pytest.approx(76.37, abs=0.01)
    assert round(plan.interval or 0) == 54_543_922


def test_mus_high_value_iteration_6_3_1_7() -> None:
    """8 Vorhaben über dem Schwellenwert, 786.837.081 €; SI = 3.413.044.943 / 69 = 49.464.419 €."""
    top = [
        120_000_000.0,
        115_000_000.0,
        110_000_000.0,
        105_000_000.0,
        95_000_000.0,
        90_000_000.0,
        80_000_000.0,
        71_837_081.0,
    ]
    rest_value = 4_199_882_024 - 786_837_081
    rest = [rest_value / 3844] * 3844
    split = high_value_split(top + rest, 77)
    assert split.exhaustive == tuple(range(8))
    assert split.sampling_size == 69
    assert round(split.interval) == 49_464_419
    assert split.rounds == 1


def test_mus_stratified_6_3_2_7() -> None:
    """σ_rw² 0,004425, n ≈ 148.

    Abweichung: Der Leitfaden teilt 89 / 59 auf (n₁ = 88,33 aufgerundet); die
    Bibliothek rundet nach dem größten Rest wie in 6.1.2.6 (90,26 → 90) und
    erhält 88 / 60. Der Leitfaden schreibt die Proportion vor, nicht die Rundung.
    """
    plan = mus_stratified_size(
        strata=[
            StratumInput("Programm 1", book_value=2_506_626_292, sd=math.sqrt(0.000045)),
            StratumInput("Programm 2", book_value=1_693_255_732, sd=math.sqrt(0.010909)),
        ],
        confidence_level=0.90,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.011,
    )
    assert plan.inputs["weighted_variance"] == pytest.approx(0.004425, abs=5e-7)
    assert plan.sample_size == 148
    assert sizes(plan) == {"Programm 1": 88, "Programm 2": 60}


def test_mus_conservative_6_3_5_7() -> None:
    """RF 2,31, EF 1,5, AE 0,2 % → n ≈ 136, SI = 30.881.485 €."""
    plan = mus_conservative_size(
        book_value=4_199_882_024,
        confidence_level=0.90,
        factor_profile=KOM_TABLES,
        anticipated_error_rate=0.002,
    )
    assert plan.sample_size == 136
    assert (plan.inputs["reliability_factor"], plan.inputs["expansion_factor"]) == (2.31, 1.5)
    assert round(plan.interval or 0) == 30_881_485


def test_pilot_sd_and_error_rates_6_3_1_7() -> None:
    """Fehlerquoten über dem Schwellenwert: E_i / (BV/n) mit n = 50 (0,0491 und 0,0371)."""
    rates = error_rates(
        [4_122_399.0, 3_118_456.0, 0.0],
        [142_151_692.0, 103_948_529.0, 1_000_000.0],
        population_book_value=4_199_882_024,
        pilot_sample_size=50,
    )
    assert [round(r, 4) for r in rates] == [0.0491, 0.0371, 0.0]
    assert error_sd([1.0, 2.0, 3.0, 4.0]) == pytest.approx(math.sqrt(5 / 3))
    assert error_rate_sd(
        [1.0, 3.0], [10.0, 10.0], population_book_value=100.0, pilot_sample_size=2
    ) == pytest.approx(math.sqrt(0.02))


def test_nonstatistical_art_79_2_cpr_2021() -> None:
    """Weniger als 300 Einheiten, mindestens 10 % zufällig: 187 Einheiten → 19."""
    plan = nonstatistical_minimum("cpr_2021_art79_2", population_size=187)
    assert plan.sample_size == 19
    with pytest.raises(ValueError, match="weniger als 300"):
        nonstatistical_minimum("cpr_2021_art79_2", population_size=300)


def test_nonstatistical_art_127_1_and_table_6() -> None:
    """2014–2020: 5 % der Vorhaben, 10 % der Ausgaben; Tabelle 6 Kategorie 3: 10–15 %."""
    plan = nonstatistical_minimum(
        "cpr_2013_art127_1",
        population_size=120,
        book_value=1_000_000,
        assurance_level="works_partially",
    )
    assert plan.sample_size == 6
    assert plan.inputs["min_expenditure"] == 100_000
    assert plan.inputs["recommended_units"] == [12, 18]
    assert plan.inputs["recommended_expenditure_shares"] == [0.10, 0.20]
