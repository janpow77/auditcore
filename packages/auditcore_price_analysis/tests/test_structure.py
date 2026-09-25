"""Structure of the 0.1.1 refactoring: rule objects, number helpers and tier helpers."""

from __future__ import annotations

from decimal import Decimal

import pytest

from auditcore_price_analysis import PriceAnalysisError, _profile_model, parse_decimal, profiles


def test_profile_rule_objects_are_reexported_unchanged() -> None:
    for name in (
        "CalculationProfile",
        "ComparisonProfile",
        "ComponentRule",
        "ConsumptionRule",
        "MixedPriceRule",
        "TierRule",
    ):
        assert getattr(profiles, name) is getattr(_profile_model, name)
    assert set(profiles.__all__) >= {"load_calculation_profile", "standard_consumption"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("1.50"), Decimal("1.50")),
        (3, Decimal(3)),
        (0.1, Decimal("0.1")),
        (" 2.5 ", Decimal("2.5")),
    ],
)
def test_parse_decimal_types(value: object, expected: Decimal) -> None:
    assert parse_decimal(value, field="x") == expected


@pytest.mark.parametrize(
    ("value", "code"),
    [
        (None, "missing_value"),
        (True, "invalid_number"),
        ("1,5", "invalid_number"),
        ("1e3", "invalid_number"),
        ([1], "invalid_number"),
        (float("inf"), "invalid_number"),
    ],
)
def test_parse_decimal_rejections(value: object, code: str) -> None:
    with pytest.raises(PriceAnalysisError) as error:
        parse_decimal(value, field="x")
    assert error.value.code == code
