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
        "Laut Tabelle 7 (Stand 15.02.2024) stieg der Wert im Jahr 2023 nach Art. 5 "
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


def test_ganzzahl_ohne_kontext_ist_keine_jahreszahl() -> None:
    claims = extract_claims("Gefördert wurden 2000 Vorhaben.")
    assert not claims[0].is_year
    assert (
        check_paragraph("Gefördert wurden 2000 Vorhaben.", [_value("1990", "")]).verdict
        is Verdict.FAILED
    )


def test_tausenderpunkt_ist_nie_jahr() -> None:
    assert not extract_claims("Im Jahr 2.024 Vorhaben.")[0].is_year


def test_jahr_im_kontext_und_als_spanne() -> None:
    texte = ("seit 2019 gefördert", "im Zeitraum 2021 bis 2023", "Werte 2022–2024", "2022 – 2024")
    for text in texte:
        claims = extract_claims(text)
        assert claims and all(c.is_year for c in claims), text
    spanne = extract_claims("2022 – 2024")
    assert [c.number.value for c in spanne] == [Decimal(2022), Decimal(2024)]


def test_jahr_per_parameter() -> None:
    assert extract_claims("Der Wert 2023 stieg.", allowed_years=[2023])[0].is_year
    result = check_paragraph("Der Wert 2023 stieg.", [], allowed_years=[2023])
    assert result.reason == NO_CLAIMS


def test_prozentpunkt_schreibweisen() -> None:
    for text in ("um 1,5 %-Punkte", "um 1,5 %-Punkt", "um 1,5 Prozentpunkten", "um 1,5 Pp."):
        (claim,) = extract_claims(text)
        assert claim.unit.dimension.value == "points", text


def test_maske_je_mit_dezimalkomma() -> None:
    claims = extract_claims("Kosten je 1,5 Stellen lagen bei 3,4 %.")
    assert [c.number.text for c in claims] == ["3,4"]


def test_mehrdeutige_zahl_wird_nicht_zerlegt() -> None:
    assert extract_claims("Es flossen 2.5 Mio. Euro.") == []
    result = check_paragraph("Es flossen 2.5 Mio. Euro.", [_value("5", "Mio. Euro")])
    assert result.verdict is Verdict.FAILED
    assert [f.code for f in result.findings] == ["zahl_mehrdeutig"]


def test_no_claims_ist_vor_verwendung_definiert() -> None:
    from pathlib import Path

    import auditcore_reportgates.prose as prose

    source = Path(prose.__file__).read_text(encoding="utf-8")
    assert source.index("NO_CLAIMS =") < source.index("def check_paragraph")


def _years_of(text: str) -> list[tuple[str, bool]]:
    return [(c.number.text, c.is_year) for c in extract_claims(text)]


def test_betraege_und_zaehlwerte_mit_praeposition_sind_keine_jahre() -> None:
    assert _years_of("von 10 bis 2000 Euro") == [("10", False), ("2000", False)]
    assert _years_of("zwischen 1950 und 2100 Euro") == [("1950", False), ("2100", False)]
    assert _years_of("bis 2050 Vorhaben") == [("2050", False)]
    assert _years_of("ab 2000 Teilnehmenden") == [("2000", False)]
    assert _years_of("zwischen 2000 und 2050 Vorhaben") == [("2000", False), ("2050", False)]


def test_euro_ist_einheit() -> None:
    (claim,) = extract_claims("Es flossen 2000 Euro.")
    assert claim.unit_stated and not claim.is_year
    (mio,) = extract_claims("Es flossen 1,5 Mio. Euro.")
    assert mio.unit.exponent == 6
    assert extract_claims("rund 300 € je Fall")[0].unit_stated
    assert not extract_claims("in Europa 2000 Vorhaben")[0].unit_stated


def test_jahreskontext_bleibt_jahr() -> None:
    assert _years_of("bis 2027") == [("2027", True)]
    assert _years_of("im Jahr 2024") == [("2024", True)]
    assert _years_of("2022–2024") == [("2022", True), ("2024", True)]


def test_satzanfang_vor_verb_oder_komma_ist_jahr() -> None:
    assert _years_of("2023 stieg die Quote.") == [("2023", True)]
    assert _years_of("Gut. 2023, als die Quote stieg.") == [("2023", True)]
    assert _years_of("2023 Vorhaben wurden gefördert.") == [("2023", False)]
    result = check_paragraph("2023 Vorhaben wurden gefördert.", [_value("12", "Anzahl")])
    assert result.verdict is Verdict.FAILED
