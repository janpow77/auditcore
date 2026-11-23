"""§ 106 Abs. 2 Nr. 1 GWB and § 3 VgV by reference date, against the quoted law.

Target wording and dates are quoted here from the law, independently of the
module tables:

- § 106 Abs. 2 Nr. 1 GWB, version until 30.06.2026 (buzer.de, a.F. bis
  01.07.2026, geändert durch Art. 1 G v. 12.05.2026 BGBl. 2026 I Nr. 137):
  „… ist von allen obersten Bundesbehörden sowie allen oberen Bundesbehörden und
  vergleichbaren Bundeseinrichtungen anzuwenden“; version from 01.07.2026
  (gesetze-im-internet.de): „… ist vom Bundeskanzleramt und den Bundesministerien
  anzuwenden“.
- § 3 Abs. 9 VgV (gesetze-im-internet.de, Fassung ab 14.02.2024): „… wenn der
  geschätzte Nettowert des betreffenden Loses bei Liefer- und Dienstleistungen
  unter 80 000 Euro und bei Bauleistungen unter 1 Million Euro liegt und die Summe
  der Nettowerte dieser Lose 20 Prozent des Gesamtwertes aller Lose nicht
  übersteigt.“ Until 13.02.2024 it referred to „Absatz 7 Satz 3“.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

import auditcore_procurement as ap
from auditcore_procurement import Lot

OLD_106 = (
    "von allen obersten Bundesbehörden sowie allen oberen Bundesbehörden und "
    "vergleichbaren Bundeseinrichtungen anzuwenden"
)
NEW_106 = "vom Bundeskanzleramt und den Bundesministerien anzuwenden"
LOT_SERVICES, LOT_WORKS = Decimal("80000"), Decimal("1000000")  # „unter 80 000 Euro“, „1 Million“


@pytest.mark.parametrize(
    ("on", "ending", "valid_to"),
    [
        (date(2016, 4, 18), OLD_106, "2026-06-30"),
        (date(2024, 3, 1), OLD_106, "2026-06-30"),
        (date(2026, 6, 30), OLD_106, "2026-06-30"),
        (date(2026, 7, 1), NEW_106, None),
        (date(2031, 1, 1), NEW_106, None),
    ],
)
def test_central_government_rule_follows_the_reference_date(
    on: date, ending: str, valid_to: str | None
) -> None:
    rule = ap.central_government_rule(on)
    view = rule.to_dict()
    assert rule.wording.endswith(ending)
    assert "für zentrale Regierungsbehörden ergebende Schwellenwert ist" in rule.wording
    assert view["valid_to"] == valid_to and view["provision"] == "§ 106 Abs. 2 Nr. 1 GWB"
    assert set(view) == {
        "provision",
        "version",
        "valid_from",
        "valid_to",
        "wording",
        "applies_to_de",
        "applies_to_en",
        "reference",
    }


def test_central_government_rule_names_the_amending_acts() -> None:
    old, new = (
        ap.central_government_rule(date(2020, 1, 1)),
        ap.central_government_rule(date(2026, 7, 1)),
    )
    assert "BGBl. I S. 203" in old.reference and old.valid_from == date(2016, 4, 18)
    assert "12.05.2026, BGBl. 2026 I Nr. 137" in new.reference
    assert new.applies_to_de == "das Bundeskanzleramt und die Bundesministerien"


def test_central_government_rule_before_2016_is_not_recorded() -> None:
    with pytest.raises(ap.ThresholdUnavailable, match="18.04.2016"):
        ap.central_government_rule(date(2016, 4, 17))


def _check(*lots: Lot, on: date | None = date(2026, 1, 1)) -> dict[str, object]:
    return ap.check_small_lots(list(lots), reference_date=on)


def test_lot_just_below_the_limit_qualifies_the_limit_itself_does_not() -> None:
    rest = Lot(Decimal("1000000"), "supplies_services")
    ok = _check(Lot(LOT_SERVICES - Decimal("0.01"), "supplies_services", exempt=True), rest)
    at = _check(Lot(LOT_SERVICES, "supplies_services", exempt=True), rest)
    assert ok["status"] == "PASS" and ok["exemption_possible"] is True
    assert at["status"] == "WARNING" and at["exemption_possible"] is False
    works_ok = _check(
        Lot(LOT_WORKS - Decimal("0.01"), "works", exempt=True), Lot(LOT_WORKS * 5, "works")
    )
    works_at = _check(Lot(LOT_WORKS, "works", exempt=True), Lot(LOT_WORKS * 5, "works"))
    assert works_ok["exemption_possible"] is True and works_at["exemption_possible"] is False


def test_share_of_exactly_20_percent_is_allowed_more_is_not() -> None:
    exempt = [Lot(Decimal("50000"), "supplies_services", exempt=True)] * 4  # 200 000
    exact = _check(*exempt, Lot(Decimal("800000"), "supplies_services"))  # 200 000 / 1 000 000
    over = _check(*exempt, Lot(Decimal("799999.99"), "supplies_services"))
    assert exact["exemption_possible"] is True and exact["share_within_limit"] is True
    assert over["exemption_possible"] is False and over["share_within_limit"] is False


def test_lot_limit_depends_on_the_kind_of_the_lot() -> None:
    result = _check(
        Lot(Decimal("90000"), "works", exempt=True),
        Lot(Decimal("90000"), "supplies_services", exempt=True),
        Lot(Decimal("5000000"), "works"),
    )
    lots = result["lots"]
    assert isinstance(lots, list)
    assert [lot["below_limit"] for lot in lots] == [True, False]
    assert result["exemption_possible"] is False


@pytest.mark.parametrize(
    ("on", "sentence", "note"),
    [
        (date(2016, 4, 18), "Absatz 7 Satz 3", False),
        (date(2023, 8, 24), "Absatz 7 Satz 3", True),
        (date(2024, 2, 13), "Absatz 7 Satz 3", True),
        (date(2024, 2, 14), "Absatz 7 Satz 2", False),
    ],
)
def test_small_lots_rule_version_by_date(on: date, sentence: str, note: bool) -> None:
    result = _check(
        Lot(Decimal("10000"), "supplies_services", exempt=True),
        Lot(Decimal("90000"), "supplies_services"),
        on=on,
    )
    rule = result["rule"]
    assert isinstance(rule, dict)
    assert sentence in rule["wording"] and "nicht übersteigt" in rule["wording"]
    assert (result["note"] is not None) is note


def test_small_lots_without_date_or_before_2016_need_review() -> None:
    lots = (Lot(Decimal("1"), "works", exempt=True), Lot(Decimal("9"), "works"))
    assert _check(*lots, on=None)["status"] == "REVIEW_REQUIRED"
    assert _check(*lots, on=date(2016, 4, 17))["status"] == "REVIEW_REQUIRED"
    assert ap.small_lots_rule(date(2016, 4, 17)) is None


@pytest.mark.parametrize(
    "lots",
    [
        [Lot(Decimal("1"), "works")],
        [Lot(Decimal("1"), "planning", exempt=True)],
        [Lot(Decimal("-1"), "works", exempt=True)],
        [Lot(Decimal("NaN"), "works", exempt=True)],
        [Lot(Decimal("Infinity"), "works", exempt=True)],
    ],
)
def test_invalid_lot_input_is_an_error(lots: list[Lot]) -> None:
    with pytest.raises(ValueError):
        ap.check_small_lots(lots, reference_date=date(2026, 1, 1))


def test_estimation_hints_quote_the_paragraphs_in_force() -> None:
    hints = {h["provision"]: h for h in ap.estimation_hints(date(2026, 11, 23))}
    assert set(hints) == {
        "§ 3 Abs. 1 VgV",
        "§ 3 Abs. 4 VgV",
        "§ 3 Abs. 7 VgV",
        "§ 3 Abs. 8 VgV",
        "§ 3 Abs. 9 VgV",
    }
    assert "Prämien oder Zahlungen an den Bewerber oder Bieter" in str(
        hints["§ 3 Abs. 1 VgV"]["wording"]
    )
    assert "Rahmenvereinbarung" in str(hints["§ 3 Abs. 4 VgV"]["wording"])
    assert "gleichartiger Lieferungen" in str(hints["§ 3 Abs. 8 VgV"]["wording"])
    assert "Planungsleistungen" not in str(hints["§ 3 Abs. 7 VgV"]["wording"])
    old = {h["provision"]: h for h in ap.estimation_hints(date(2020, 1, 1))}
    assert "Bei Planungsleistungen gilt dies nur für Lose über gleichartige Leistungen." in str(
        old["§ 3 Abs. 7 VgV"]["wording"]
    )
    assert ap.estimation_hints(date(2016, 4, 17)) == []
