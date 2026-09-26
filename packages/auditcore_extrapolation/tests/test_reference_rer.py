"""Reference cases: the examples of the RER template CPRE_23-0013-01 Annex 3.

Sheets "Examples" (A, B, C.1, C.2) and "Negative units example", recomputed
with the template formulas; expected values are the cell results of the
workbook (exact decimals).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from auditcore_extrapolation import (
    ExtrapolationInputError,
    ResidualInputs,
    residual_error_rate,
)


def test_example_a_individual_corrections_bring_rer_below_2_percent() -> None:
    result = residual_error_rate(
        ResidualInputs(Decimal(1000), Decimal("0.022"), financial_corrections=Decimal("2.1"))
    )
    assert result.population == 1000
    assert result.amount_at_risk == Decimal("22.000")
    assert result.certifiable == Decimal("997.9")
    assert result.residual_amount == Decimal("19.900")
    assert result.rate is not None and float(result.rate) == pytest.approx(19.9 / 997.9)
    assert result.rate_rounded == Decimal("0.0199")
    assert not result.exceeds_materiality
    assert result.extrapolated_correction is None and result.rate_after_correction is None
    assert result.to_dict()["not_applicable"] == "NA RTER not exceeding 2%"


def test_example_b_extrapolated_correction_needed() -> None:
    result = residual_error_rate(
        ResidualInputs(Decimal(1000), Decimal("0.025"), financial_corrections=Decimal("2.1"))
    )
    assert result.residual_amount == Decimal("22.900")
    assert result.rate_rounded == Decimal("0.0229")
    assert result.exceeds_materiality
    correction = (Decimal("22.9") - Decimal("0.02") * Decimal("997.9")) / Decimal("0.98")
    assert result.extrapolated_correction == correction
    assert result.rate_after_correction == pytest.approx(Decimal("0.02"), abs=Decimal("1e-20"))


def test_example_c1_ongoing_assessment_outside_sample() -> None:
    result = residual_error_rate(
        ResidualInputs(1000, Decimal("0.022"), ongoing_assessment=50, financial_corrections=2)
    )
    assert result.population == 950
    assert result.amount_at_risk == Decimal("20.900")
    assert result.certifiable == 948
    assert result.rate_rounded == Decimal("0.0199")
    assert not result.exceeds_materiality


def test_example_c2_ongoing_assessment_partially_within_sample() -> None:
    result = residual_error_rate(
        ResidualInputs(
            1000, Decimal("0.022"), ongoing_assessment=50, financial_corrections=Decimal("0.5")
        )
    )
    assert result.certifiable == Decimal("949.5")
    assert result.residual_amount == Decimal("20.400")
    assert result.rate_rounded == Decimal("0.0215")
    assert result.extrapolated_correction == pytest.approx(Decimal("1.438775510204081632653"))
    assert result.rate_after_correction == pytest.approx(Decimal("0.02"), abs=Decimal("1e-20"))


def test_negative_units_example() -> None:
    """E1 = 50 (ongoing assessment), E2 = 100 + 250 (other negative amounts), H = 2."""
    result = residual_error_rate(
        ResidualInputs(
            1000,
            Decimal("0.022"),
            ongoing_assessment=50,
            other_negative_amounts=350,
            financial_corrections=2,
        )
    )
    assert result.population == 600
    assert result.amount_at_risk == Decimal("13.200")
    assert result.certifiable == 598
    assert result.residual_amount == Decimal("11.200")
    assert not result.exceeds_materiality


def test_rate_is_a_share_not_a_percentage() -> None:
    with pytest.raises(ExtrapolationInputError, match="0.022"):
        residual_error_rate(ResidualInputs(1000, Decimal("2.2")))


def test_zero_certifiable_amount_follows_iferror() -> None:
    result = residual_error_rate(ResidualInputs(10, Decimal("0.5"), financial_corrections=10))
    assert result.rate is None and not result.exceeds_materiality
    assert any("IFERROR" in note for note in result.notes)


def test_float_inputs_are_read_by_their_decimal_repr() -> None:
    result = residual_error_rate(ResidualInputs(1000.0, 0.025, financial_corrections=2.1))
    assert result.residual_amount == Decimal("22.9000")
    assert result.exceeds_materiality
