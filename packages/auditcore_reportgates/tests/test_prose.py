"""Prosa-Zahlen-Gate: Treffer, Widerspruch, ungebundene Zahl, nicht prüfbar."""

from decimal import Decimal

from auditcore_reportgates import (
    NO_CLAIMS,
    PERCENT,
    BoundValue,
    ClaimStatus,
    GateResult,
    Verdict,
    check_claim,
    check_paragraph,
    combine,
    exact,
    extract_claims,
    read_number,
    unit_of,
)


def _value(text: str, unit: str, source: str = "Tabelle 1") -> BoundValue:
    number = read_number(text)
    assert number is not None
    return BoundValue(number, unit_of(unit), source)


def test_masken_und_jahreszahlen() -> None:
    claims = extract_claims(
        "Laut Tabelle 7 (Stand 15.02.2024) stieg der Wert 2023 nach Art. 5 "
        "je 100.000 Einwohner auf 3,4 %."
    )
    assert [c.number.text for c in claims if not c.is_year] == ["3,4"]
    assert any(c.is_year for c in claims)


def test_einheit_wird_im_satz_geerbt() -> None:
    claims = extract_claims("Die Quote lag bei 8,4 bzw. 8,5 %. Danach 12 Vorhaben.")
    units = [c.unit for c in claims]
    assert units[0] == PERCENT and units[1] == PERCENT
    assert claims[2].unit_stated is False


def test_jahreszahl_erbt_keine_einheit() -> None:
    claims = extract_claims("Zwischen 2021 und 2022 um 3,4 %.")
    assert claims[0].is_year and claims[1].is_year


def test_negatives_vorzeichen() -> None:
    claims = extract_claims("Rückgang um – 5,1 %.")
    assert claims[0].number.value == Decimal("-5.1")


def test_treffer_nach_skalierung_aus_spalteneinheit() -> None:
    values = [BoundValue(exact(15_782_365), unit_of("Euro"), "Tabelle 7")]
    result = check_paragraph("Bewilligt wurden 15,8 Mio. Euro.", values)
    assert result.verdict is Verdict.PASSED
    assert result.checked == 1


def test_zahl_ohne_einheit_in_spalteneinheit_gelesen() -> None:
    values = [_value("15,8", "Mio. Euro")]
    assert check_paragraph("Insgesamt 15,8 für das Programm.", values).passed


def test_widerspruch_innerhalb_zehn_prozent() -> None:
    values = [_value("15,8", "Mio. Euro")]
    result = check_paragraph("Bewilligt wurden 16,9 Mio. Euro.", values, location="S. 3")
    assert result.verdict is Verdict.FAILED
    assert result.findings[0].code == ClaimStatus.CONTRADICTION.value
    assert result.findings[0].location == "S. 3"
    assert "Abweichung" in result.findings[0].message


def test_abweichung_ueber_zehn_prozent_ist_befund() -> None:
    values = [_value("15,8", "Mio. Euro")]
    result = check_paragraph("Bewilligt wurden 25,0 Mio. Euro.", values)
    assert result.verdict is Verdict.FAILED
    assert result.findings[0].code == ClaimStatus.UNBOUND.value


def test_prozentpunkte_nicht_gegen_prozent() -> None:
    values = [_value("2,5", "Anteil (%)")]
    result = check_paragraph("Der Anteil stieg um 2,5 Prozentpunkte.", values)
    assert result.verdict is Verdict.FAILED
    check = check_claim(extract_claims("2,5 Prozentpunkte")[0], values)
    assert check.status is ClaimStatus.UNBOUND and check.nearest is None


def test_kontextwert_bindet() -> None:
    values = [_value("15,8", "Mio. Euro"), BoundValue(exact(50), unit_of("Anzahl"), "Kontext")]
    assert check_paragraph("Die 50 größten Vorhaben erhielten 15,8 Mio. Euro.", values).passed


def test_nicht_pruefbar_ist_not_run() -> None:
    ohne_zahl = check_paragraph("Im Jahr 2024 wurde berichtet.", [])
    assert ohne_zahl.verdict is Verdict.NOT_RUN and ohne_zahl.reason == NO_CLAIMS
    ohne_werte = check_paragraph("Es waren 12 Vorhaben.", [])
    assert ohne_werte.verdict is Verdict.NOT_RUN and ohne_werte.reason == "keine_werte"


def test_combine() -> None:
    passed = GateResult("p", Verdict.PASSED, checked=2)
    neutral = GateResult("p", Verdict.NOT_RUN, NO_CLAIMS)
    open_ = GateResult("p", Verdict.NOT_RUN, "keine_werte")
    assert combine("prose", [passed, neutral]).verdict is Verdict.PASSED
    assert combine("prose", [passed, open_]).verdict is Verdict.NOT_RUN
    assert combine("prose", [neutral]).verdict is Verdict.NOT_RUN
    failed = check_paragraph("Es waren 99 Vorhaben.", [_value("12", "Anzahl")])
    assert combine("prose", [passed, failed]).verdict is Verdict.FAILED
