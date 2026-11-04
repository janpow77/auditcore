"""Parameter von 0.2.0: Lesart, Einheitenmenge, Spaltenskala, Gleitkommapuffer, Rundung."""

from __future__ import annotations

import re
from dataclasses import replace
from decimal import ROUND_HALF_EVEN, Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from auditcore_reportgates import (
    BASIC_UNITS,
    DEFAULT_SYNTAX,
    PERCENT,
    PERCENTAGE_POINTS,
    BoundValue,
    ClaimSyntax,
    PointReading,
    PrintedNumber,
    Verdict,
    ambiguous_numbers,
    check_paragraph,
    exact,
    extract_claims,
    format_de,
    read_number,
    same_value,
    scale_of,
    tolerance,
    unit_of,
)

LEGACY = ClaimSyntax(units=BASIC_UNITS, point=PointReading.SPLIT, masks=())
YEARS = range(1900, 2101)

# Lesart des FlowStat-Prosa-Gates bis audit_designer 5bc3d61 (Referenz für SPLIT).
_LEGACY_NUMBER = re.compile(
    r"(?:(?<![\w\d])(?P<vorzeichen>[-–−])\s?)?"
    r"(?P<zahl>\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)"
    r"(?:\s?(?P<einheit>%|Prozentpunkte|Prozentpunkt|Prozent|Mio\.|Mrd\.|Tsd\.))?"
)
_LEGACY_ABBREVIATION = re.compile(
    r"\b(?:bzw|ca|rd|ggf|inkl|zzgl|evtl|Mio|Mrd|Tsd|Nr|Abs|Art|vgl|z|B|d|h|u|a)\."
)
_LEGACY_SENTENCE = re.compile(r"[.;:!?]\s+[A-ZÄÖÜ]")


def _legacy_value(text: str) -> tuple[float, int]:
    if "," in text:
        return float(text.replace(".", "").replace(",", ".")), len(text.split(",")[1])
    return float(text.replace(".", "")), 0


def _legacy(text: str) -> list[tuple[int, float, int, str, str]]:
    raw = []
    for m in _LEGACY_NUMBER.finditer(text):
        value, decimals = _legacy_value(m["zahl"])
        value = -value if m["vorzeichen"] else value
        raw.append((m.start(), value, decimals, m.group().strip(), m["einheit"] or ""))
    result = []
    for index, (pos, value, decimals, token, unit) in enumerate(raw):
        year = decimals == 0 and value.is_integer() and 1900 <= value <= 2100
        inherited = ""
        if not unit and not year:
            for f_pos, _, _, _, f_unit in raw[index + 1 :]:
                gap = text[pos + len(token) : f_pos]
                if len(gap) > 40 or _LEGACY_SENTENCE.search(_LEGACY_ABBREVIATION.sub("  ", gap)):
                    break
                if f_unit:
                    inherited = f_unit
                    break
        result.append((pos, value, decimals, token, unit or inherited))
    return result


def _as_legacy(text: str) -> list[tuple[int, float, int, str, str]]:
    result = []
    for claim in extract_claims(text, allowed_years=YEARS, syntax=LEGACY):
        value = float(claim.number.value)
        decimals = claim.number.decimals or 0
        # FlowStat: auch „2.024“ ist ein Jahr und erbt keine Einheit.
        year = decimals == 0 and value.is_integer() and 1900 <= value <= 2100
        unit = "" if year and claim.unit_inherited else claim.unit_text
        result.append((claim.position, value, decimals, claim.token, unit))
    return result


_PIECES = st.sampled_from(
    [
        "1",
        "23",
        "2024",
        "2.024",
        "1.234",
        "1.234,5",
        "2.5",
        "10.10",
        "8,4",
        ",",
        ".",
        " ",
        "-",
        "– ",
        "%",
        " %",
        " Prozent",
        " Prozentpunkte",
        " %-Punkte",
        " Pp.",
        " Mio.",
        " Mio. Euro",
        " Millionen",
        " Euro",
        " bzw. ",
        " und ",
        ". Danach ",
        " Vorhaben",
        "x",
    ]
)


@given(st.lists(_PIECES, max_size=14).map("".join))
def test_split_mit_grundeinheiten_entspricht_der_flowstat_lesart(text: str) -> None:
    assert _as_legacy(text) == _legacy(text)


def test_grundeinheiten_lassen_euro_und_pp_weg() -> None:
    claims = extract_claims("5 Euro, 3 Pp. und 2 %-Punkte", syntax=LEGACY)
    assert [(c.number.value, c.unit_text) for c in claims] == [
        (Decimal(5), "%"),
        (Decimal(3), "%"),
        (Decimal(2), "%"),
    ]
    assert claims[2].unit == PERCENT and claims[0].unit_inherited


def test_standard_kennt_alle_einheiten() -> None:
    claims = extract_claims("5 Euro, 3 Pp. und 2 %-Punkte")
    assert [c.unit_text for c in claims] == ["Euro", "Pp.", "%-Punkte"]
    assert claims[2].unit == PERCENTAGE_POINTS
    assert not any(c.unit_inherited for c in claims)


def test_punkt_lesarten() -> None:
    text = "Es waren 2.5 und 10.10 Mio."
    assert extract_claims(text) == []
    assert ambiguous_numbers(text) == ["2.5", "10.10 Mio."]
    dezimal = extract_claims(text, syntax=ClaimSyntax(point=PointReading.DECIMAL))
    assert [(c.number.value, c.number.decimals) for c in dezimal] == [
        (Decimal("2.5"), 1),
        (Decimal("10.10"), 2),
    ]
    assert dezimal[0].unit_inherited and dezimal[0].unit_text == "Mio."
    geteilt = extract_claims(text, syntax=ClaimSyntax(point=PointReading.SPLIT))
    assert [c.number.value for c in geteilt] == [2, 5, 10, 10]
    assert ambiguous_numbers(text, syntax=ClaimSyntax(point=PointReading.SPLIT)) == []


def test_dezimalpunkt_laesst_tausendergruppen_stehen() -> None:
    syntax = ClaimSyntax(point=PointReading.DECIMAL)
    assert [c.number.value for c in extract_claims("1.234 Vorhaben", syntax=syntax)] == [1234]
    assert ambiguous_numbers("1.2.3 und 2,5,3", syntax=syntax) == ["1.2.3", "2,5,3"]


def test_angehaengte_ziffer_ist_kein_abgeschnittener_wert() -> None:
    """Bis 0.1.0 las „10.10“ als 1 und „1.2345“ als 1.234."""
    assert extract_claims("10.10 und 1.2345") == []
    assert ambiguous_numbers("10.10 und 1.2345") == ["10.10", "1.2345"]


def test_masken_abschaltbar() -> None:
    assert extract_claims("gemäß § 5") == []
    ohne = extract_claims("gemäß § 5", syntax=ClaimSyntax(masks=()))
    assert [c.number.value for c in ohne] == [5]


def test_check_paragraph_mit_syntax() -> None:
    werte = [BoundValue(exact(2.5), unit_of("Mio. Euro"), "T1")]
    strikt = check_paragraph("Es waren 2.5 Mio. Euro.", werte)
    assert strikt.verdict is Verdict.FAILED
    dezimal = ClaimSyntax(point=PointReading.DECIMAL)
    assert check_paragraph("Es waren 2.5 Mio. Euro.", werte, syntax=dezimal).verdict is (
        Verdict.PASSED
    )
    assert ClaimSyntax() == DEFAULT_SYNTAX


def test_token_und_einheitentext() -> None:
    (claim,) = extract_claims("Rückgang um – 5,1 % im Jahr")
    assert claim.token == "– 5,1 %" and claim.unit_text == "%" and not claim.unit_inherited


@pytest.mark.parametrize(
    ("kopf", "skala"),
    [
        ("Veränderung Mio. Euro (%)", 6),
        ("Anteil Tsd. Euro", 3),
        ("Mrd. Euro", 9),
        ("Zuwendung (Euro)", 0),
        ("Betrag €", 0),
        ("Europa", None),
        ("Anteil (%)", None),
    ],
)
def test_spaltenskala_auch_bei_mischueberschriften(kopf: str, skala: int | None) -> None:
    assert scale_of(kopf) == skala


def test_spaltenskala_mit_eigener_waehrung() -> None:
    eigene = re.compile(r"\beur\b|euro")
    assert scale_of("Europa", currency=eigene) == 0
    assert scale_of("Betrag €", currency=eigene) is None
    assert unit_of("Veränderung Mio. Euro (%)") == PERCENT


def test_gleitkommapuffer() -> None:
    ist = PrintedNumber(Decimal(str(15.850000000000001)), None)
    soll = read_number("15,8")
    assert soll is not None
    assert not same_value(ist, soll)
    assert same_value(ist, soll, epsilon=Decimal("1e-9"))
    assert not same_value(PrintedNumber(Decimal("15.851"), None), soll, epsilon=Decimal("1e-9"))
    assert tolerance(exact(1), exact(1), epsilon=Decimal("0.1")) == Decimal("0.1")
    with pytest.raises(ValueError, match="negativ"):
        tolerance(ist, soll, epsilon=-1)
    with pytest.raises(ValueError, match="endlich"):
        same_value(ist, soll, epsilon=float("inf"))


@given(
    st.floats(-1e6, 1e6, allow_nan=False),
    st.floats(-1e6, 1e6, allow_nan=False),
    st.integers(0, 4),
)
def test_puffer_entspricht_dem_gleitkommavergleich(ist: float, soll: float, stellen: int) -> None:
    """Exakte Binärwerte plus 1e-9 wie ``abs(ist - soll) <= 0,5·10^-s + 1e-9``."""
    gedruckt = PrintedNumber(Decimal(soll), stellen)
    bibliothek = same_value(PrintedNumber(Decimal(ist), None), gedruckt, epsilon=Decimal("1e-9"))
    erwartet = abs(ist - soll) <= 0.5 * 10.0**-stellen + 1e-9
    abstand = abs(Decimal(ist) - Decimal(soll)) - tolerance(gedruckt, gedruckt, epsilon=1e-9)
    if abs(abstand) > Decimal("1e-15"):
        assert bibliothek is erwartet


def test_rundungsart() -> None:
    assert format_de(0.125) == "0,13"
    assert format_de(0.125, rounding=ROUND_HALF_EVEN) == "0,12"
    assert format_de(Decimal(2.675), rounding=ROUND_HALF_EVEN) == "2,67"
    assert format_de(2.675, rounding=ROUND_HALF_EVEN) == "2,68"
    with pytest.raises(ValueError, match="Rundungsart"):
        format_de(1, rounding="kaufmännisch")


def test_negative_nachkommastellen() -> None:
    with pytest.raises(ValueError, match="nichtnegative ganze Zahl.*Zehner"):
        format_de(1234, -1)


@given(st.floats(-1e12, 1e12, allow_nan=False), st.integers(0, 4))
def test_half_even_auf_binaerwert_entspricht_format(wert: float, stellen: int) -> None:
    python = f"{wert:,.{stellen}f}"
    if python.lstrip("-").strip("0.,") == "":
        python = python.lstrip("-")  # format_de druckt keine negative Null
    erwartet = python.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    assert format_de(Decimal(wert), stellen, rounding=ROUND_HALF_EVEN) == erwartet


def test_beschreibende_felder_zaehlen_nicht_zur_gleichheit() -> None:
    (claim,) = extract_claims("5 %")
    assert claim == replace(claim, token="", unit_text="", unit_inherited=True)


def test_typpruefung_epsilon_und_stellen() -> None:
    with pytest.raises(ValueError, match="endlich"):
        tolerance(exact(1), exact(1), epsilon=True)
    for falsch in (True, 1.5):
        with pytest.raises(ValueError, match="nichtnegative ganze Zahl"):
            format_de(1, falsch)  # type: ignore[arg-type]
