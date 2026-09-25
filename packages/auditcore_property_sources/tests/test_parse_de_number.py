"""``zvg.parse_de_number`` follows the shared contract ``parse-number`` (mode ``de``, PS-C10)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from auditcore_property_sources import zvg

CONTRACT = Path(__file__).resolve().parents[3] / "contracts/common-cases/parse-number.json"


def _de_cases() -> list[dict[str, Any]]:
    if not CONTRACT.is_file():  # installed sdist without the repository contracts
        return []
    cases = json.loads(CONTRACT.read_text(encoding="utf-8"))["cases"]
    return [c for c in cases if c["input"]["mode"] == "de"]


DE_CASES = _de_cases()


@pytest.mark.parametrize("case", DE_CASES, ids=[c["id"] for c in DE_CASES])
def test_contract_mode_de(case: dict[str, Any]) -> None:
    result = zvg.parse_de_number(case["input"]["text"])
    if case["expect"].get("invalid"):
        assert result is None
    else:
        assert result == float(Decimal(case["expect"]["value"]))


def test_contract_cases_present() -> None:
    if CONTRACT.is_file():
        assert len(DE_CASES) >= 60


#: Differences to the characterized original (docs/behavior-changes.md, PS-C10).
CHANGED = [
    ("1234,56", 123.0, 1234.56),
    ("2015", 201.0, 2015.0),
    ("ca. 120,5 m²", 120.5, None),
    ("1.234", 1234.0, None),
    ("1.5", 1.0, None),
    ("-3,2", 3.2, -3.2),
    ("85,555", 85.55, None),
]
UNCHANGED = [
    ("945,80", 945.8),
    ("1.234,5", 1234.5),
    ("12.345.678,99", 12345678.99),
    ("keine Angabe", None),
]


@pytest.mark.parametrize(("text", "legacy", "new"), CHANGED)
def test_documented_differences(text: str, legacy: float | None, new: float | None) -> None:
    assert zvg.legacy_parse_de_number(text) == legacy
    assert zvg.parse_de_number(text) == new


@pytest.mark.parametrize(("text", "value"), UNCHANGED)
def test_unchanged_results(text: str, value: float | None) -> None:
    assert zvg.legacy_parse_de_number(text) == value
    assert zvg.parse_de_number(text) == value


def test_living_area_from_detail_text() -> None:
    notice = zvg.ZvgNotice(zvg_id="1", land="he", court_id="X")
    zvg._apply_facts(notice, "Wohnfläche ca. 1234,56 m², Baujahr 1999", 2026)
    assert (notice.living_area_sqm, notice.build_year) == (1234.56, 1999)
    ambiguous = zvg.ZvgNotice(zvg_id="2", land="he", court_id="X")
    zvg._apply_facts(ambiguous, "Wohnfläche 85,555 m²", 2026)
    assert ambiguous.living_area_sqm is None
