"""Shared parsing and JSON helpers behind the source profiles (structure of 0.1.1)."""

from __future__ import annotations

import math
from datetime import date
from decimal import Decimal

from auditcore_funding_sources import (
    _jsonsafe,
    _parsing,
    deminimis,
    deminimis_inventory,
    designer,
    flowsearch,
    workshop,
    workshop_state_aid,
)


def test_separators_follow_the_variant() -> None:
    assert _parsing.normalize_separators("1.234.567", dot_thousands=True) == "1234567"
    assert _parsing.normalize_separators("1.234.567", dot_thousands=False) == "1.234.567"
    assert _parsing.normalize_separators("1.200.000,50", dot_thousands=False) == "1200000.50"
    assert _parsing.normalize_separators("1,200,000", dot_thousands=False) == "1200000"
    assert _parsing.normalize_separators("12,5", dot_thousands=False) == "12.5"


def test_grammars_keep_their_differences() -> None:
    assert designer.parse_betrag("1.234.567") == Decimal("1234567")
    assert workshop.parse_amount("1.234.567") is None
    assert designer.parse_betrag("weniger als 5.000 EUR") == Decimal("5000")
    assert designer.state_aid_parse_amount("weniger als 5.000") is None
    assert designer.state_aid_parse_amount("1 bis 2,5") == Decimal("2.5")
    assert workshop.parse_amount("1 bis 2,5") is None
    assert workshop.parse_amount("1 to 2,5") == Decimal("2.5")
    assert designer.parse_betrag("–") is None
    assert workshop.parse_amount("–") is None


def test_sa_reference_and_legal_tokens_are_shared() -> None:
    assert designer.detect_sa_reference is workshop.detect_sa_reference
    assert _parsing.detect_sa_reference("Beihilfe SA.12345/2021") == (
        "SA.12345/2021",
        "https://competition-cases.ec.europa.eu/cases/SA.12345/2021",
    )
    assert _parsing.drop_legal_tokens("muster gmbh co", {"gmbh"}, {"co"}, drop_filler=True) == (
        "muster"
    )


def test_modules_re_export_their_former_names() -> None:
    assert workshop.parse_amount is workshop_state_aid.parse_amount
    assert workshop.PROFILE_ID == workshop_state_aid.PROFILE_ID
    assert deminimis.record_hash is deminimis_inventory.record_hash
    assert deminimis.Reconciliation is deminimis_inventory.Reconciliation


def test_json_safe_copies() -> None:
    value = {1: [Decimal("1.5"), date(2024, 1, 2), math.nan, ("a",)], "b": None}
    assert _jsonsafe.json_safe(value) == {"1": ["1.5", "2024-01-02", None, ["a"]], "b": None}
    assert _jsonsafe.json_safe_mapping({"x": Decimal("2")}) == {"x": "2"}


def test_harvest_values_of_a_workshop_row() -> None:
    row = {
        "_row_number": 3,
        "beneficiary_name": "Müller GmbH",
        "cost_total_raw": "1.000,00",
        "project_start_raw": "01.02.2024",
    }
    values = workshop.harvest_values(row)
    assert list(values)[: len(workshop.HARVEST_TEXT_FIELDS)] == list(workshop.HARVEST_TEXT_FIELDS)
    assert values["cost_total"] == Decimal("1000.00")
    assert values["project_start"] == date(2024, 2, 1)
    assert values["beneficiary_name_normalized"] == "mueller gmbh"
    assert values["source_row_number"] == 3


def test_read_items_chooses_csv_by_url_or_note() -> None:
    content = b"Name;Betrag\nA;1\n"
    mapping = {"delimiter": ";"}
    assert flowsearch.read_items(content, "https://x/list.csv", {}, mapping) == [
        {"Name": "A", "Betrag": "1"}
    ]
    assert flowsearch.read_items(content, "https://x/list", {"notes": "CSV statt XLSX"}, mapping)
