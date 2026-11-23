"""EU thresholds of profile 2026.11.1 against target values quoted from the official texts.

The target value of every case is read from the verbatim excerpt below (the
last amount in it), not from a table of the library. Each excerpt was copied
from the official German text retrieved from the Cellar of the Publications
Office (CELEX number and article in the comment); the test also checks that it
stands in the wording the profile records for that CELEX number together with
the SHA-256 of the retrieved document.
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import date, timedelta
from decimal import Decimal
from importlib import resources
from pathlib import Path
from typing import Any

import pytest

import auditcore_procurement
from auditcore_procurement import prechecks
from auditcore_procurement.eu_regimes import RegimeError, parse_regimes

CURRENT = prechecks.load_profile("procurement.hvtg", "2026.11.1")
P24 = (date(2024, 1, 1), date(2025, 12, 31))
P26 = (date(2026, 1, 1), date(2027, 12, 31))

#: (regime, contract type, authority type, period, CELEX, verbatim excerpt)
QUOTED: list[tuple[str, str, str | None, tuple[date, date], str, str]] = [
    # 32023R2495 Art. 1 Nr. 1 Buchst. a (ändert Art. 4 Buchst. a RL 2014/24/EU)
    (
        "public_contracts", "works", None, P24, "32023R2495",
        "unter Buchstabe a wird der Betrag „5 382 000 EUR“ durch den Betrag „5 538 000 EUR“ "
        "ersetzt",
    ),
    # 32023R2495 Art. 1 Nr. 1 Buchst. b (Art. 4 Buchst. b RL 2014/24/EU)
    (
        "public_contracts", "supplies_services", "central", P24, "32023R2495",
        "unter Buchstabe b wird der Betrag „140 000 EUR“ durch den Betrag „143 000 EUR“ ersetzt",
    ),
    # 32023R2495 Art. 1 Nr. 1 Buchst. c (Art. 4 Buchst. c RL 2014/24/EU)
    (
        "public_contracts", "supplies_services", "sub_central", P24, "32023R2495",
        "unter Buchstabe c wird der Betrag „215 000 EUR“ durch den Betrag „221 000 EUR“ ersetzt",
    ),
    # 32025R2152 Art. 1 Nr. 1 Buchst. a (Art. 4 Buchst. a RL 2014/24/EU)
    (
        "public_contracts", "works", None, P26, "32025R2152",
        "Unter Buchstabe a wird der Betrag „5 538 000 EUR“ durch den Betrag „5 404 000 EUR“ "
        "ersetzt",
    ),
    # 32025R2152 Art. 1 Nr. 1 Buchst. b (Art. 4 Buchst. b RL 2014/24/EU)
    (
        "public_contracts", "supplies_services", "central", P26, "32025R2152",
        "unter Buchstabe b wird der Betrag „143 000 EUR“ durch den Betrag „140 000 EUR“ ersetzt",
    ),
    # 32025R2152 Art. 1 Nr. 1 Buchst. c (Art. 4 Buchst. c RL 2014/24/EU)
    (
        "public_contracts", "supplies_services", "sub_central", P26, "32025R2152",
        "unter Buchstabe c wird der Betrag „221 000 EUR“ durch den Betrag „216 000 EUR“ ersetzt",
    ),
    # 32023R2496 Art. 1 Nr. 1 (Art. 15 Buchst. a RL 2014/25/EU)
    (
        "utilities", "supplies_services", None, P24, "32023R2496",
        "Unter Buchstabe a wird der Betrag „431 000 EUR“ durch den Betrag „443 000 EUR“ ersetzt",
    ),
    # 32023R2496 Art. 1 Nr. 2 (Art. 15 Buchst. b RL 2014/25/EU)
    (
        "utilities", "works", None, P24, "32023R2496",
        "unter Buchstabe b wird der Betrag „5 382 000 EUR“ durch den Betrag „5 538 000 EUR“ "
        "ersetzt",
    ),
    # 32025R2150 Art. 1 Nr. 1 (Art. 15 Buchst. a RL 2014/25/EU)
    (
        "utilities", "supplies_services", None, P26, "32025R2150",
        "Unter Buchstabe a wird der Betrag „443 000 EUR“ durch den Betrag „432 000 EUR“ ersetzt",
    ),
    # 32025R2150 Art. 1 Nr. 2 (Art. 15 Buchst. b RL 2014/25/EU)
    (
        "utilities", "works", None, P26, "32025R2150",
        "unter Buchstabe b wird der Betrag „5 538 000 EUR“ durch den Betrag „5 404 000 EUR“ "
        "ersetzt",
    ),
    # 32023R2497 Art. 1 (Art. 8 Abs. 1 RL 2014/23/EU)
    (
        "concessions", "concession", None, P24, "32023R2497",
        "In Artikel 8 Absatz 1 der Richtlinie 2014/23/EU wird der Betrag „5 382 000 EUR“ durch "
        "den Betrag „5 538 000 EUR“ ersetzt.",
    ),
    # 32025R2151 Art. 1 (Art. 8 Abs. 1 RL 2014/23/EU)
    (
        "concessions", "concession", None, P26, "32025R2151",
        "In Artikel 8 Absatz 1 der Richtlinie 2014/23/EU wird der Betrag „5 538 000 EUR“ durch "
        "den Betrag „5 404 000 EUR“ ersetzt.",
    ),
    # 32023R2510 Art. 1 Nr. 1 und 2 (Art. 8 Buchst. a und b RL 2009/81/EG)
    (
        "defence", "supplies_services", None, P24, "32023R2510",
        "Unter Buchstabe a wird „431 000 EUR“ ersetzt durch „443 000 EUR“",
    ),
    (
        "defence", "works", None, P24, "32023R2510",
        "unter Buchstabe b wird „5 382 000 EUR“ ersetzt durch „5 538 000 EUR“",
    ),
    # 32025R2487 Art. 1 Nr. 1 und 2 (Art. 8 Buchst. a und b RL 2009/81/EG)
    (
        "defence", "supplies_services", None, P26, "32025R2487",
        "Unter Buchstabe a wird der Betrag „443 000 EUR“ durch den Betrag „432 000 EUR“ ersetzt",
    ),
    (
        "defence", "works", None, P26, "32025R2487",
        "unter Buchstabe b wird der Betrag „5 538 000 EUR“ durch den Betrag „5 404 000 EUR“ "
        "ersetzt",
    ),
]  # fmt: skip

#: Fixed values of the directives (no end date), CELEX of the directive, verbatim excerpt.
FIXED = [
    # 32014L0024 Art. 4 Buchst. d
    (
        "public_contracts",
        "32014L0024",
        "d) 750 000 EUR bei öffentlichen Dienstleistungsaufträgen betreffend soziale und "
        "andere besondere Dienstleistungen im Sinne von Anhang XIV.",
    ),
    # 32014L0025 Art. 15 Buchst. c
    (
        "utilities",
        "32014L0025",
        "c) 1 000 000 EUR bei Dienstleistungsaufträgen betreffend soziale und andere besondere "
        "Dienstleistungen, die in Anhang XVII aufgeführt sind.",
    ),
]
#: Art. 6 Abs. 1 RL 2014/24/EU and Art. 17 Abs. 1 RL 2014/25/EU: only the other points
#: are revised every two years.
NOT_REVISED = {
    "32014L0024": "Die Kommission überprüft die in Artikel 4 Buchstaben a, b und c genannten "
    "Schwellenwerte alle zwei Jahre",
    "32014L0025": "Die Kommission überprüft die in Artikel 15 Buchstaben a und b genannten "
    "Schwellenwerte alle zwei Jahre",
}


def _amount(excerpt: str) -> int:
    """Target value: the last amount of the excerpt, as printed in the Official Journal."""
    return int(re.findall(r"(\d{1,3}(?: \d{3})*) EUR", excerpt)[-1].replace(" ", ""))


def _quote(celex: str) -> str:
    assert CURRENT.eu_regimes is not None
    return CURRENT.eu_regimes.sources[celex]["quote"]


@pytest.mark.parametrize(("regime", "kind", "authority", "period", "celex", "excerpt"), QUOTED)
def test_threshold_equals_the_quoted_amount_on_both_ends_of_its_period(
    regime: str,
    kind: str,
    authority: str | None,
    period: tuple[date, date],
    celex: str,
    excerpt: str,
) -> None:
    assert excerpt in _quote(celex)
    target = _amount(excerpt)
    for day in period:
        found = auditcore_procurement.eu_regime_threshold(CURRENT, regime, kind, day, authority)
        assert (found.value, found.row.source) == (target, celex)
        below = auditcore_procurement.check_eu_threshold(
            CURRENT,
            Decimal(target) - Decimal("0.01"),
            regime=regime,
            contract_type=kind,
            authority_type=authority,
            reference_date=day,
        )
        assert below["above_threshold"] is False


@pytest.mark.parametrize(("regime", "celex", "excerpt"), FIXED)
def test_fixed_directive_value_holds_from_2016_without_end_date(
    regime: str, celex: str, excerpt: str
) -> None:
    assert excerpt in _quote(celex)
    assert NOT_REVISED[celex] in CURRENT.eu_regimes.sources[celex]["review_quote"]
    target = _amount(excerpt)
    for day in (date(2016, 4, 18), date(2027, 12, 31), date(2028, 1, 1), date(2099, 12, 31)):
        found = auditcore_procurement.eu_regime_threshold(CURRENT, regime, "social_services", day)
        assert found.value == target and found.row.valid_to is None
        assert found.to_dict()["valid_to"] is None and "Art. " in str(found.to_dict()["open_end"])
    for year in (2017, 2028, 2040):  # 2016 only from 18.04., so not the whole year
        result = auditcore_procurement.check_eu_threshold(
            CURRENT, Decimal(target), regime=regime, contract_type="social_services", year=year
        )
        assert result["status"] == "PASS" and result["above_threshold"] is True
    before = auditcore_procurement.check_eu_threshold(
        CURRENT,
        Decimal(target),
        regime=regime,
        contract_type="social_services",
        reference_date=date(2016, 4, 18) - timedelta(days=1),
    )
    assert before["status"] == "REVIEW_REQUIRED"


def test_revised_values_stay_not_recorded_from_2028() -> None:
    for regime, kind, authority in (
        ("public_contracts", "works", None),
        ("public_contracts", "supplies_services", "sub_central"),
        ("utilities", "supplies_services", None),
        ("concessions", "concession", None),
        ("defence", "works", None),
    ):
        result = auditcore_procurement.check_eu_threshold(
            CURRENT,
            Decimal("1"),
            regime=regime,
            contract_type=kind,
            authority_type=authority,
            reference_date=date(2028, 1, 1),
        )
        assert result["status"] == "REVIEW_REQUIRED", (regime, kind)


def test_catalogue_shows_open_end_and_dated_central_government_note() -> None:
    catalogue = auditcore_procurement.eu_catalogue(CURRENT)
    public = next(r for r in catalogue["regimes"] if r["id"] == "public_contracts")
    kinds = {c["id"]: c for c in public["contract_types"]}
    (row,) = kinds["social_services"]["thresholds"]
    assert row["valid_to"] is None and row["open_end"]
    central = next(a for a in kinds["supplies_services"]["authority_types"] if a["id"] == "central")
    assert "in der Fassung ab 01.07.2026" in central["note"]["de"]
    assert "13.10.2026" not in central["note"]["de"]
    assert "obersten Bundesbehörden" in central["note"]["de"]
    assert "ab 2028" in catalogue["not_entered"] and "ohne Enddatum" in catalogue["not_entered"]


def test_2026_10_1_keeps_its_end_date_for_pinned_consumers() -> None:
    released = prechecks.load_profile("procurement.hvtg", "2026.10.1")
    result = auditcore_procurement.check_eu_threshold(
        released, Decimal("1"), regime="utilities", contract_type="social_services", year=2028
    )
    assert result["status"] == "REVIEW_REQUIRED"


TOOLS = Path(__file__).resolve().parents[1] / "tools"


def _raw(version: str) -> bytes:
    return (
        resources.files("auditcore_procurement.profiles")
        .joinpath(f"procurement.hvtg-{version}.json")
        .read_bytes()
    )


def test_2026_11_1_is_reproducible_from_the_released_2026_10_1() -> None:
    spec = importlib.util.spec_from_file_location("open_end", TOOLS / "build_eu_regimes_2026_11.py")
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    built = builder.build(json.loads(_raw("2026.10.1")))
    assert (json.dumps(built, indent=1, ensure_ascii=False) + "\n").encode() == _raw("2026.11.1")
    assert prechecks.CURRENT_PROFILE == ("procurement.hvtg", builder.VERSION)


def _social_row(raw: dict[str, Any]) -> dict[str, Any]:
    public = raw["eu_regimes"]["regimes"][0]
    return next(c for c in public["contract_types"] if c["id"] == "social_services")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("no_reason", "'open_end' fehlt"),
        ("reason_with_end", "Zeitraum ist fehlerhaft"),
        ("missing_key", "'valid_to' fehlt"),
        ("row_after_open_end", "überschneiden"),
    ],
)
def test_open_end_needs_a_reason_and_must_be_the_last_row(change: str, message: str) -> None:
    raw = json.loads(_raw("2026.11.1"))
    kind = _social_row(raw)
    row = kind["thresholds"][0]
    if change == "no_reason":
        del row["open_end"]
    elif change == "reason_with_end":
        row["valid_to"] = "2027-12-31"
    elif change == "missing_key":
        del row["valid_to"]
    else:
        kind["thresholds"].append({**row, "valid_from": "2030-01-01"})
    with pytest.raises(RegimeError, match=message):
        parse_regimes(raw["eu_regimes"])
