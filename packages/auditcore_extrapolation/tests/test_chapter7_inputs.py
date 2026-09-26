"""Rejected inputs and non-applicable cases of the chapter 7 procedures."""

from __future__ import annotations

import pytest

from auditcore_extrapolation import (
    KOM_TABLES,
    SYSTEM_ASSESSMENT_LEVELS,
    ExtrapolationInputError,
    Group,
    Period,
    SampleUnit,
    Stratum,
    SubSample,
    assess,
    assess_groups,
    evaluate_attributes,
    project_periods,
    project_subsample,
    recalculate_confidence,
    system_confidence_level,
    unit_from_subsample,
)


def _stratum(name: str = "S", error: float = 100.0) -> Stratum:
    units = tuple(SampleUnit(f"{name}{i}", 1000.0, error if i == 0 else 0.0) for i in range(5))
    return Stratum(name, 100_000.0, units, population_size=100)


def test_periods_need_two_named_periods_and_a_multi_period_method() -> None:
    with pytest.raises(ExtrapolationInputError, match="mindestens zwei"):
        project_periods(
            "srs.mean_per_unit",
            [Period("H1", (_stratum(),))],
            confidence_level=0.8,
            factor_profile=KOM_TABLES,
        )
    with pytest.raises(ExtrapolationInputError, match="eindeutig"):
        project_periods(
            "srs.mean_per_unit",
            [Period("H", (_stratum(),)), Period("H", (_stratum(),))],
            confidence_level=0.8,
            factor_profile=KOM_TABLES,
        )
    for method_id in ("mus.conservative", "mus.ratio"):
        with pytest.raises(ExtrapolationInputError, match="Leitfaden"):
            project_periods(method_id, [Period("H1", (_stratum(),)), Period("H2", (_stratum(),))])


def test_period_errors_name_the_period() -> None:
    broken = Stratum("S", 100_000.0, (SampleUnit("x", 10.0, 1.0),))
    with pytest.raises(ExtrapolationInputError, match="Zeitraum 'H2'"):
        project_periods(
            "srs.mean_per_unit",
            [Period("H1", (_stratum(),)), Period("H2", (broken,))],
            confidence_level=0.8,
            factor_profile=KOM_TABLES,
        )


def test_same_unit_may_appear_in_both_periods() -> None:
    result = project_periods(
        "nonstatistical.ratio",
        [Period("H1", (_stratum(),)), Period("H2", (_stratum(),))],
        population_units=100,
    )
    coverage = result.extra["coverage"]
    assert isinstance(coverage, dict) and coverage["audited_units"] == 5


def test_subsample_rejects_unknown_estimator_and_non_random_errors() -> None:
    with pytest.raises(ExtrapolationInputError, match="Schätzer"):
        project_subsample(SubSample("V", "median", (_stratum(),)))
    systemic = Stratum("S", 10_000.0, (SampleUnit("a", 100.0, 0.0, 10.0),), systemic_error=10.0)
    with pytest.raises(ExtrapolationInputError, match="nur zufällige Fehler"):
        project_subsample(SubSample("V", "ratio", (systemic,)))
    with pytest.raises(ExtrapolationInputError, match="Kennung"):
        project_subsample(SubSample(" ", "ratio", (_stratum(),)))


def test_subsample_mean_per_unit_needs_n_and_error_cannot_exceed_book_value() -> None:
    no_size = Stratum("S", 10_000.0, (SampleUnit("a", 100.0, 10.0), SampleUnit("b", 100.0)))
    with pytest.raises(ExtrapolationInputError, match="Anzahl der Einheiten"):
        project_subsample(SubSample("V", "mean_per_unit", (no_size,)))
    # mean-per-unit: N × mean error can exceed the book value of the unit
    heavy = Stratum(
        "S",
        1_000.0,
        (SampleUnit("a", 100.0, 100.0), SampleUnit("b", 100.0, 100.0)),
        population_size=50,
    )
    with pytest.raises(ExtrapolationInputError, match="übersteigt den Buchwert"):
        project_subsample(SubSample("V", "mean_per_unit", (heavy,)))


def test_unit_from_subsample_keeps_systemic_and_anomalous_errors_on_the_unit() -> None:
    unit, result = unit_from_subsample(
        SubSample("V", "ratio", (_stratum(),)),
        systemic_error=50.0,
        anomalous_error=10.0,
        anomalous_reason="Einmaliger Fehler",
    )
    assert unit.random_error == result.projected_error == pytest.approx(2000.0)
    assert unit.systemic_error == 50.0 and unit.anomalous_error == 10.0


def test_groups_need_two_distinct_groups() -> None:
    with pytest.raises(ExtrapolationInputError, match="mindestens zwei"):
        assess_groups(
            "srs.mean_per_unit",
            [Group("P1", (_stratum(),))],
            confidence_level=0.8,
            factor_profile=KOM_TABLES,
        )
    with pytest.raises(ExtrapolationInputError, match="eindeutigen"):
        assess_groups(
            "srs.mean_per_unit",
            [Group("P", (_stratum("A"),)), Group("P", (_stratum("B"),))],
            confidence_level=0.8,
            factor_profile=KOM_TABLES,
        )


def test_groups_warn_below_thirty_observations() -> None:
    result = assess_groups(
        "srs.mean_per_unit",
        [Group("P1", (_stratum("A"),)), Group("P2", (_stratum("B"),))],
        confidence_level=0.8,
        factor_profile=KOM_TABLES,
    )
    assert all("30" in g.warnings[0] for g in result.groups)
    assert result.to_dict()["overall"]


def test_recalculation_not_applicable_cases() -> None:
    stratum = _stratum()
    nonstat = assess("nonstatistical.ratio", [stratum])
    assert not recalculate_confidence(nonstat.projection, nonstat.total_error_rate).applicable
    conservative = assess(
        "mus.conservative",
        [stratum],
        confidence_level=0.9,
        factor_profile=KOM_TABLES,
        sample_size=5,
    )
    reason = recalculate_confidence(conservative.projection, conservative.total_error_rate).reason
    assert reason is not None and "Konservativer" in reason
    with pytest.raises(ExtrapolationInputError):
        recalculate_confidence(nonstat.projection, nonstat.total_error_rate, required_level=1.5)


def test_system_assessment_table() -> None:
    assert [system_confidence_level(c) for c in (1, 2, 3, 4)] == [0.6, 0.7, 0.8, 0.9]
    assert dict(SYSTEM_ASSESSMENT_LEVELS)[4] == 0.9
    with pytest.raises(ExtrapolationInputError, match="Kategorie"):
        system_confidence_level(5)


def test_attribute_inputs() -> None:
    with pytest.raises(ExtrapolationInputError, match="Mehr Abweichungen"):
        evaluate_attributes(
            5, 4, confidence_level=0.9, factor_profile=KOM_TABLES, tolerable_rate=0.1
        )
    with pytest.raises(ExtrapolationInputError, match="tolerierbare"):
        evaluate_attributes(
            1, 40, confidence_level=0.9, factor_profile=KOM_TABLES, tolerable_rate=0
        )
    with pytest.raises(ExtrapolationInputError, match="Stichprobenumfang"):
        evaluate_attributes(
            0, 0, confidence_level=0.9, factor_profile=KOM_TABLES, tolerable_rate=0.1
        )
    result = evaluate_attributes(
        10, 40, confidence_level=0.9, factor_profile=KOM_TABLES, tolerable_rate=0.1
    )
    assert result.conclusion == "not_supported" and result.to_dict()["steps"]
