from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from auditcore_invoicesynth.formats import (
    AMOUNT_STYLES,
    CURRENCY_STYLES,
    DATE_STYLES,
    format_amount,
    format_date,
    format_money,
    format_rate,
    parse_date,
    parse_money,
    parse_rate,
)


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        ("de_grouped", "1.234.567,89"),
        ("de_plain", "1234567,89"),
        ("de_space", "1 234 567,89"),
        ("en_grouped", "1,234,567.89"),
    ],
)
def test_amount_styles(style: str, expected: str) -> None:
    assert format_amount(Decimal("1234567.885"), style) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize("value", ["0.01", "5.10", "999.99", "1000.00", "21718.74", "1234567.80"])
def test_money_round_trip(value: str) -> None:
    for style in AMOUNT_STYLES:
        for currency in CURRENCY_STYLES:
            text = format_money(Decimal(value), style, currency)
            assert parse_money(text) == Decimal(value), text


def test_ambiguous_and_invalid_amounts() -> None:
    assert parse_money("1.234") is None
    assert parse_money("abc") is None
    assert parse_money("12,5") is None
    assert parse_money("1.234,56 €") == Decimal("1234.56")
    assert parse_money("-5,00") == Decimal("-5.00")


def test_dates_round_trip_including_austrian_january() -> None:
    day = date(2026, 1, 5)
    assert format_date(day, "de_long", country="AT") == "5. Jänner 2026"
    assert format_date(day, "de_short") == "5.1.26"
    for style in DATE_STYLES:
        for country in ("DE", "AT"):
            assert parse_date(format_date(day, style, country=country)) == "2026-01-05"
    assert parse_date("31.02.2026") is None
    assert parse_date("gestern") is None


def test_rates() -> None:
    assert [format_rate(Decimal(19), variant=v) for v in range(3)] == ["19 %", "19%", "19,0 %"]
    assert format_rate(Decimal(10)) == "10 %"
    for text in ("19 %", "19%", "19,0 %", "10 %"):
        assert parse_rate(text) in {Decimal(19), Decimal(10)}
    assert str(parse_rate("10 %")) == "10"
    assert parse_rate("x") is None
