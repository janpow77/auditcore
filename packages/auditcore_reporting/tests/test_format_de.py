"""``format_eur`` against the shared contract ``format-money`` (Python counterpart of formatEur)."""

from __future__ import annotations

import json
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from auditcore_reporting import format_eur
from auditcore_reporting.format_de import EMPTY_VALUE, NBSP, plain_decimal

CASES = Path(__file__).resolve().parents[3] / "contracts" / "common-cases"


def _decode(value: object) -> object:
    if isinstance(value, dict) and value.get("$nan") is True:
        return math.nan
    return value


def _contract() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = CASES / "format-money.json"
    if not path.is_file():  # installed sdist without the repository contracts
        return [], {}
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    decisions = json.loads((CASES / "decisions.json").read_text(encoding="utf-8"))["decisions"]
    return [c for c in cases if "python" in c.get("languages", ["python"])], decisions


CONTRACT, DECISIONS = _contract()


@pytest.mark.parametrize("case", CONTRACT, ids=[c["id"] for c in CONTRACT])
def test_contract_format_money(case: dict[str, Any]) -> None:
    expected = case["expect"]["value"]
    if isinstance(expected, dict):
        expected = DECISIONS[expected["$decision"]]
    assert format_eur(_decode(case["input"]["value"])) == expected


@pytest.mark.skipif(not CONTRACT, reason="contracts/common-cases not available")
def test_contract_is_complete_and_empty_value_matches() -> None:
    assert len(CONTRACT) >= 10
    assert DECISIONS["empty_value"] == EMPTY_VALUE
    assert DECISIONS["money_rounding"] == "half-up"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1.005, "1,01"),  # shortest decimal "1.005", like String(1.005) in JavaScript
        (2.675, "2,68"),
        (-0.125, "-0,13"),
        (-0.001, "0,00"),  # no negative zero
        (Decimal("999.995"), "1.000,00"),
        ("+12", "12,00"),
        (" 0001.5 ", "1,50"),
        (1e21, "1.000.000.000.000.000.000.000,00"),
        (1e-7, "0,00"),
        (123, "123,00"),
        (1234567, "1.234.567,00"),
    ],
)
def test_edge_cases(value: object, expected: str) -> None:
    assert format_eur(value) == f"{expected}{NBSP}€"


@pytest.mark.parametrize(
    "value", [None, "", "  ", "1,5", "1.234,50", "1e3", "abc", True, math.inf, Decimal("NaN"), []]
)
def test_empty_and_invalid_give_the_empty_value(value: object) -> None:
    assert format_eur(value) == "—"
    assert format_eur(value, empty="") == ""


def test_digits() -> None:
    assert format_eur(1234.5, digits=0) == f"1.235{NBSP}€"
    assert format_eur(0.12345, digits=4) == f"0,1235{NBSP}€"
    with pytest.raises(ValueError, match="digits"):
        format_eur(1, digits=-1)


def test_too_many_digits_for_the_decimal_context() -> None:
    assert format_eur("1" * 40) == "—"


@given(st.integers(min_value=-(10**15), max_value=10**15))
def test_cents_round_trip(cents: int) -> None:
    text = format_eur(Decimal(cents) / 100)
    number = text.removesuffix(f"{NBSP}€").replace(".", "").replace(",", ".")
    assert Decimal(number) == Decimal(cents) / 100
    assert plain_decimal(number) == Decimal(cents) / 100
