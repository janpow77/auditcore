"""Strict sample-size contract next to the legacy results (SA-C ids)."""

from __future__ import annotations

import math

import pytest

from auditcore_sampling import (
    METHODS,
    SamplingInputError,
    __version__,
    legacy,
    mus_size,
    srs_size,
)


def test_both_mus_methods_are_named_and_neither_is_default() -> None:
    assert set(METHODS) == {
        "flowstat.mus_z_attribute",
        "portal.mus_poisson",
        "flowstat.srs_normal",
        "portal.srs_normal",
    }
    with pytest.raises(TypeError):
        mus_size(
            population_value=1.0,
            materiality=1.0,
            expected_error_rate=0.0,  # type: ignore[call-arg]
            confidence_level=0.95,
        )
    with pytest.raises(SamplingInputError, match="Zulässig"):
        mus_size(
            "flowstat.srs_normal",
            population_value=1.0,
            materiality=1.0,
            expected_error_rate=0.0,
            confidence_level=0.95,
        )


def test_sa_c01_method_conflict_is_visible() -> None:
    kwargs = dict(
        population_value=515_000.0,
        materiality=50_000.0,
        expected_error_rate=0.005,
        confidence_level=0.95,
    )
    z = mus_size("flowstat.mus_z_attribute", **kwargs)
    poisson = mus_size("portal.mus_poisson", **kwargs)
    assert z.sample_size == 1 and "abgelöst" in z.warnings[0]
    assert poisson.sample_size == math.ceil(3.0 * 515_000.0 / (50_000.0 - 515_000.0 * 0.005))
    assert (z.sample_size, z.interval) == legacy.flowstat_mus_size(**kwargs)
    assert (poisson.sample_size, poisson.interval) == legacy.portal_mus_size(**kwargs)


def test_sa_c02_undefined_confidence_level_is_rejected_not_defaulted() -> None:
    assert (
        legacy.flowstat_mus_size(1000.0, 10.0, 0.0, 0.975)[0]
        == legacy.flowstat_mus_size(1000.0, 10.0, 0.0, 0.95)[0]
    )
    with pytest.raises(SamplingInputError, match="kein Ersatzwert"):
        mus_size(
            "flowstat.mus_z_attribute",
            population_value=1000.0,
            materiality=10.0,
            expected_error_rate=0.0,
            confidence_level=0.975,
        )
    assert legacy.flowstat_srs_size(100, 0.5, 0.05) == legacy.flowstat_srs_size(100, 0.95, 0.05)
    with pytest.raises(SamplingInputError):
        srs_size(
            "flowstat.srs_normal", population_size=100, confidence_level=0.5, margin_of_error=0.05
        )
    assert srs_size(
        "portal.srs_normal", population_size=100, confidence_level=0.5, margin_of_error=0.05
    ).sample_size == legacy.portal_srs_size(100, 0.5, 0.05)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(population_value=-1.0, materiality=1.0, expected_error_rate=0.0),
        dict(population_value=1.0, materiality=0.0, expected_error_rate=0.0),
        dict(population_value=1.0, materiality=1.0, expected_error_rate=1.0),
        dict(population_value=1.0, materiality=1.0, expected_error_rate=-0.1),
        dict(population_value=math.nan, materiality=1.0, expected_error_rate=0.0),
        dict(population_value=True, materiality=1.0, expected_error_rate=0.0),
    ],
)
def test_sa_c03_invalid_mus_inputs(kwargs: dict[str, float]) -> None:
    for method_id in ("flowstat.mus_z_attribute", "portal.mus_poisson"):
        with pytest.raises(SamplingInputError):
            mus_size(method_id, confidence_level=0.95, **kwargs)


def test_zero_population_and_precision_floor() -> None:
    zero = mus_size(
        "portal.mus_poisson",
        population_value=0.0,
        materiality=1.0,
        expected_error_rate=0.0,
        confidence_level=0.95,
    )
    assert (zero.sample_size, zero.interval) == (0, 0.0) and zero.warnings
    with pytest.raises(ZeroDivisionError):
        legacy.flowstat_mus_size(0.0, 1.0, 0.0, 0.95)  # Python floats in the source
    assert legacy.flowstat_mus_size(0.0, 1.0, 0.0, 0.95, numpy_scalars=True) == (0, 0)
    floor = mus_size(
        "portal.mus_poisson",
        population_value=1_000_000.0,
        materiality=1000.0,
        expected_error_rate=0.01,
        confidence_level=0.95,
    )
    assert floor.sample_size == 6000 and "50 %" in floor.warnings[0]


def test_srs_contract() -> None:
    plan = srs_size(
        "flowstat.srs_normal", population_size=10, confidence_level=0.95, margin_of_error=0.05
    )
    assert plan.sample_size == 10 == legacy.flowstat_srs_size(10, 0.95, 0.05)
    none = srs_size(
        "portal.srs_normal",
        population_size=1,
        confidence_level=0.95,
        margin_of_error=0.05,
        expected_proportion=0.0,
    )
    assert none.sample_size == 0 and none.warnings
    with pytest.raises(ZeroDivisionError):
        legacy.flowstat_srs_size(1, 0.95, 0.05, 0.0)
    for bad in (
        dict(population_size=0),
        dict(population_size=5, margin_of_error=0.0),
        dict(population_size=5, expected_proportion=1.5),
        dict(population_size=5.0),
    ):
        arguments = {"population_size": 5, "confidence_level": 0.95, "margin_of_error": 0.05, **bad}
        with pytest.raises(SamplingInputError):
            srs_size("flowstat.srs_normal", **arguments)  # type: ignore[arg-type]


def test_plans_carry_method_inputs_and_library() -> None:
    data = mus_size(
        "portal.mus_poisson",
        population_value=100.0,
        materiality=10.0,
        expected_error_rate=0.0,
        confidence_level=0.9,
    ).to_dict()
    assert data["library"] == f"auditcore_sampling {__version__}"
    assert data["method"] == "portal.mus_poisson" and data["inputs"]["factor"] == 2.31


def test_decision_2026_09_23_poisson_is_recommended_flowstat_superseded() -> None:
    from auditcore_sampling import (
        MUS_DECISION,
        MUS_POISSON,
        MUS_Z_ATTRIBUTE,
        RECOMMENDED_MUS_METHOD,
        recommended_mus_method,
        recommended_mus_size,
    )

    assert RECOMMENDED_MUS_METHOD == "portal.mus_poisson" == recommended_mus_method().id
    assert MUS_POISSON.status == "RECOMMENDED" and MUS_Z_ATTRIBUTE.status == "SUPERSEDED"
    assert MUS_DECISION["decided_on"] == "2026-09-23" and MUS_DECISION["statement"] == "mus 30"
    plan = recommended_mus_size(
        population_value=475_478.94,
        materiality=50_000.0,
        expected_error_rate=0.005,
        confidence_level=0.95,
    )
    assert plan.sample_size == 30 and plan.method == "portal.mus_poisson"
    larger = recommended_mus_size(
        population_value=515_000.0,
        materiality=50_000.0,
        expected_error_rate=0.005,
        confidence_level=0.95,
    )
    assert larger.sample_size == 33
    assert plan == mus_size(
        "portal.mus_poisson",
        population_value=475_478.94,
        materiality=50_000.0,
        expected_error_rate=0.005,
        confidence_level=0.95,
    )
    # the superseded method stays callable and unchanged for replay
    assert (
        mus_size(
            "flowstat.mus_z_attribute",
            population_value=515_000.0,
            materiality=50_000.0,
            expected_error_rate=0.005,
            confidence_level=0.95,
        ).sample_size
        == 1
    )
