"""``parse_decimal`` reads German number text (PA-C01) after the contract ``parse-number``."""

from __future__ import annotations

import copy
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from helpers import run_new
from replay import load_fixture

from auditcore_price_analysis import PriceAnalysisError, legacy_parse_decimal, parse_decimal

CONTRACT = Path(__file__).resolve().parents[3] / "contracts/common-cases/parse-number.json"
#: The package's own text format: plain point notation keeps its value (unchanged).
PLAIN = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)")


def _de_cases() -> list[dict[str, Any]]:
    if not CONTRACT.is_file():  # installed sdist without the repository contracts
        return []
    cases = json.loads(CONTRACT.read_text(encoding="utf-8"))["cases"]
    return [c for c in cases if c["input"]["mode"] == "de"]


DE_CASES = _de_cases()
GERMAN = [c for c in DE_CASES if not PLAIN.fullmatch(c["input"]["text"].strip())]
POINT = [c for c in DE_CASES if PLAIN.fullmatch(c["input"]["text"].strip())]


@pytest.mark.parametrize("case", GERMAN, ids=[c["id"] for c in GERMAN])
def test_contract_mode_de_for_german_text(case: dict[str, Any]) -> None:
    expect = case["expect"]
    if expect.get("invalid"):
        with pytest.raises(PriceAnalysisError) as error:
            parse_decimal(case["input"]["text"], field="x")
        wanted = "ambiguous_number" if expect.get("hint") == "mehrdeutig" else "invalid_number"
        assert error.value.code == wanted
    else:
        assert parse_decimal(case["input"]["text"], field="x") == Decimal(expect["value"])


#: Plain point text is the documented text format of this package, not mode ``de``.
POINT_TEXT = {"1.5", "1.234", "-1.234", "1.23"}


@pytest.mark.parametrize("case", POINT, ids=[c["id"] for c in POINT])
def test_plain_point_text_keeps_its_value(case: dict[str, Any]) -> None:
    text = case["input"]["text"]
    result = parse_decimal(text, field="x")
    assert result == legacy_parse_decimal(text, field="x") == Decimal(text.strip())
    if case["expect"].get("invalid"):
        assert text in POINT_TEXT  # the only contract cases with another meaning
    else:
        assert result == Decimal(case["expect"]["value"])


def test_contract_cases_split() -> None:
    if CONTRACT.is_file():
        assert len(GERMAN) >= 50 and {c["input"]["text"] for c in POINT} >= set(POINT_TEXT)


#: Before (0.1.1, now ``legacy_parse_decimal``) and after (0.1.2).
CHANGED = [
    ("1234,56", "invalid_number", Decimal("1234.56")),
    ("1.234,56", "invalid_number", Decimal("1234.56")),
    ("10,82", "invalid_number", Decimal("10.82")),
    ("-3,2 €", "invalid_number", Decimal("-3.2")),
    ("1.000.000", "invalid_number", Decimal(1000000)),
    ("1,234", "invalid_number", "ambiguous_number"),
    ("0,125", "invalid_number", "ambiguous_number"),
]


@pytest.mark.parametrize(("text", "legacy_code", "new"), CHANGED)
def test_documented_differences(text: str, legacy_code: str, new: Decimal | str) -> None:
    with pytest.raises(PriceAnalysisError) as error:
        legacy_parse_decimal(text, field="x")
    assert error.value.code == legacy_code
    if isinstance(new, Decimal):
        assert parse_decimal(text, field="x") == new
    else:
        with pytest.raises(PriceAnalysisError) as error:
            parse_decimal(text, field="x")
        assert error.value.code == new and "mehrdeutig" in str(error.value)


@pytest.mark.parametrize("value", [None, True, "1e3", "", float("inf"), Decimal("NaN")])
def test_legacy_and_new_share_the_other_rules(value: object) -> None:
    for parser in (parse_decimal, legacy_parse_decimal):
        with pytest.raises(PriceAnalysisError):
            parser(value, field="x")


def _to_point(value: Any) -> Any:
    if isinstance(value, str) and "," in value:
        return value.replace(",", ".")
    if isinstance(value, dict):
        return {k: _to_point(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_point(v) for v in value]
    return value


GERMAN_LEGACY = [
    c
    for c in load_fixture()["cases"]
    if c["id"]
    in {
        "nw-verbrauch-013",
        "nw-ungueltig-001",
        "wa-verbrauch-011",
        "wa-ungueltig-001",
        "wa-staffelform-025",
        "wa-staffelform-026",
    }
]


@pytest.mark.parametrize("case", GERMAN_LEGACY, ids=[c["id"] for c in GERMAN_LEGACY])
def test_german_calculator_input_equals_point_input(case: dict[str, Any]) -> None:
    point = copy.deepcopy(case)
    point["args"], point["kwargs"] = _to_point(case["args"]), _to_point(case["kwargs"])
    german, reference = run_new(case), run_new(point)
    assert german.total == reference.total and german.lines == reference.lines


def test_all_german_legacy_cases_found() -> None:
    assert len(GERMAN_LEGACY) == 6
