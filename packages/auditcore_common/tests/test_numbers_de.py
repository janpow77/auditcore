"""``numbers_de`` against the shared contract ``parse-number`` and the decisions."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from auditcore_common.numbers_de import (
    AMOUNT_FRACTION_DIGITS,
    HINT_MESSAGES,
    ParsedNumber,
    parse_de_number,
    parse_number,
    parse_number_result,
)

CASES = Path(__file__).resolve().parents[3] / "contracts" / "common-cases"


def _contract() -> list[dict[str, Any]]:
    path = CASES / "parse-number.json"
    if not path.is_file():  # installed sdist without the repository contracts
        return []
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    return [c for c in cases if "python" in c.get("languages", ["python"])]


CONTRACT = _contract()


@pytest.mark.skipif(not CONTRACT, reason="contracts/common-cases not available")
def test_amount_limit_is_the_recorded_decision() -> None:
    decisions = json.loads((CASES / "decisions.json").read_text(encoding="utf-8"))
    assert decisions["decisions"]["amount_max_fraction_digits_de"] == AMOUNT_FRACTION_DIGITS
    assert decisions["decisions"]["ambiguous_single_dot_de"] == "invalid"


@pytest.mark.parametrize("case", CONTRACT, ids=[c["id"] for c in CONTRACT])
def test_contract_parse_number(case: dict[str, Any]) -> None:
    result = parse_number_result(case["input"]["text"], case["input"]["mode"])
    expect = case["expect"]
    if expect.get("invalid"):
        assert result.value is None and result.hint is not None
        if "hint" in expect:
            assert result.hint == expect["hint"]
    else:
        assert result == ParsedNumber(Decimal(expect["value"]))


def test_contract_is_complete() -> None:
    if CASES.is_dir():
        assert len(CONTRACT) >= 80


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1234,56", Decimal("1234.56")),
        ("1.234,56 €", Decimal("1234.56")),
        ("945,80", Decimal("945.80")),
        ("2015", Decimal(2015)),
    ],
)
def test_parse_de_number(text: str, expected: Decimal) -> None:
    assert parse_de_number(text) == expected
    assert parse_number(text) == expected


@pytest.mark.parametrize(
    ("text", "mode", "limit", "expected"),
    [
        ("1,234", "de", None, Decimal("1.234")),
        ("0,3456", "de", None, Decimal("0.3456")),
        ("1.234,567", "de", None, Decimal("1234.567")),
        ("0.345", "auto", AMOUNT_FRACTION_DIGITS, Decimal("0.345")),
        ("1234.567", "auto", AMOUNT_FRACTION_DIGITS, Decimal("1234.567")),
        ("0,3456", "auto", AMOUNT_FRACTION_DIGITS, Decimal("0.3456")),
        ("-0,00", "de", AMOUNT_FRACTION_DIGITS, Decimal("0.00")),
    ],
)
def test_limits_and_unambiguous_imports(
    text: str, mode: str, limit: int | None, expected: Decimal
) -> None:
    result = parse_number(text, mode, max_fraction_digits=limit)  # type: ignore[arg-type]
    assert result == expected and str(result) == str(expected)


@pytest.mark.parametrize(
    ("value", "hint"),
    [
        (None, "ungültig"),
        (12, "ungültig"),
        ("1.5", "mehrdeutig"),
        ("1.234", "mehrdeutig"),
        (" € ", "leer"),
        ("12x", "ungültig"),
    ],
)
def test_hints_and_messages(value: object, hint: str) -> None:
    result = parse_number_result(value)
    assert not result.ok and result.hint == hint
    assert result.message == HINT_MESSAGES[hint]


def test_value_has_no_hint_and_unknown_mode_fails() -> None:
    result = parse_number_result("1,5")
    assert result.ok and result.hint is None and result.message is None
    with pytest.raises(ValueError, match="Unknown notation"):
        parse_number_result("1", "fr")  # type: ignore[arg-type]
