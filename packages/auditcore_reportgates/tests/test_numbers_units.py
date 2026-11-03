"""Gedruckte Zahlen, Fehlwert gegen Null, Einheiten und Umrechnung."""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from auditcore_reportgates import (
    MISSING,
    PERCENT,
    PERCENTAGE_POINTS,
    Dimension,
    PrintedNumber,
    conversion_exponent,
    exact,
    format_de,
    read_cell,
    read_number,
    relative_deviation,
    same_value,
    tolerance,
    unit_of,
)


@pytest.mark.parametrize(
    ("text", "value", "decimals"),
    [
        ("1.234,50", "1234.50", 2),
        ("2,2 %", "2.2", 1),
        ("– 5,1", "-5.1", 1),
        ("1.234", "1234", 0),
        ("13,34*", "13.34", 2),
        ("0,00", "0.00", 2),
    ],
)
def test_deutsche_zahl(text: str, value: str, decimals: int) -> None:
    number = read_number(text)
    assert number is not None
    assert number.value == Decimal(value)
    assert number.decimals == decimals


def test_mehrdeutiges_wird_nicht_gelesen() -> None:
    assert read_number("2.5") is None
    assert read_number("abc") is None


@pytest.mark.parametrize("marker", ["k. A.", "K.A.", "-", "–", "n. v.", "", None])
def test_fehlwert(marker: object) -> None:
    assert read_cell(marker) is MISSING


def test_null_ist_kein_fehlwert() -> None:
    cell = read_cell("0,00")
    assert isinstance(cell, PrintedNumber)
    assert cell.value == 0
    assert isinstance(read_cell(0), PrintedNumber)


def test_text_bleibt_text() -> None:
    assert read_cell(" Hessen ") == "Hessen"


def test_bool_ist_keine_zahl() -> None:
    with pytest.raises(TypeError):
        exact(True)


def test_format_null_und_fehlwert() -> None:
    assert format_de(0) == "0,00"
    assert format_de(Decimal("-0.001")) == "0,00"
    assert format_de(None) == "k. A."
    assert format_de(MISSING) == "k. A."
    assert format_de(1234567.891, 2) == "1.234.567,89"
    assert format_de(-2.5, 0) == "-3"
    with pytest.raises(ValueError):
        format_de(1, -1)


def test_toleranz_halbe_gedruckte_einheit() -> None:
    printed = read_number("15,8")
    assert printed is not None
    assert tolerance(printed, exact(15.78)) == Decimal("0.05")
    assert same_value(exact(15.75), printed)
    assert not same_value(exact(15.74), printed)
    assert tolerance(exact(1), exact(1)) == 0


def test_relative_abweichung() -> None:
    assert relative_deviation(Decimal(11), Decimal(10)) == Decimal("0.1")
    assert relative_deviation(Decimal(1), Decimal(0)) is None


@pytest.mark.parametrize(
    ("text", "dimension", "exponent"),
    [
        ("Prozentpunkte", Dimension.POINTS, 0),
        ("Veränderung (Pp.)", Dimension.POINTS, 0),
        ("Anteil 2022 (%)", Dimension.SHARE, 0),
        ("Prozent", Dimension.SHARE, 0),
        ("Zuwendung (Mio. Euro)", Dimension.ABSOLUTE, 6),
        ("in Tsd. Euro", Dimension.ABSOLUTE, 3),
        ("Mrd.", Dimension.ABSOLUTE, 9),
        ("Betrag (Euro)", Dimension.ABSOLUTE, 0),
        ("Anzahl", Dimension.ABSOLUTE, None),
    ],
)
def test_einheit(text: str, dimension: Dimension, exponent: int | None) -> None:
    unit = unit_of(text)
    assert unit.dimension is dimension
    assert unit.exponent == exponent


def test_prozent_ist_nicht_prozentpunkt() -> None:
    assert conversion_exponent(PERCENT, PERCENTAGE_POINTS) is None
    assert conversion_exponent(unit_of("Mio. Euro"), PERCENT) is None


def test_faktor_aus_spalteneinheit() -> None:
    assert conversion_exponent(unit_of("Euro"), unit_of("Mio.")) == -6
    assert conversion_exponent(unit_of("Tsd. Euro"), unit_of("Mio. Euro")) == -3
    assert conversion_exponent(unit_of("Anzahl"), unit_of("Mio.")) == 0


@given(st.decimals(min_value=-(10**9), max_value=10**9, places=2, allow_nan=False))
def test_format_und_lesen_umkehrbar(value: Decimal) -> None:
    number = read_number(format_de(value, 2))
    assert number is not None
    assert number.value == value


@pytest.mark.parametrize("wert", [float("nan"), float("inf"), Decimal("NaN"), Decimal("-Infinity")])
def test_nan_und_unendlich_werden_abgewiesen(wert: object) -> None:
    with pytest.raises(ValueError):
        exact(wert)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        read_cell(wert)
    with pytest.raises(ValueError):
        format_de(wert)  # type: ignore[arg-type]
    assert read_number("NaN") is None


def test_punkt_und_doppelpunkt_sind_fehlwerte() -> None:
    assert read_cell(".") is MISSING and read_cell(":") is MISSING
    assert read_cell("–") is MISSING
    null = read_cell("–", dash_is_zero=True)
    assert isinstance(null, PrintedNumber) and null.value == 0
    assert read_cell("k. A.", missing_markers={"n/a"}) == "k. A."


@pytest.mark.parametrize(
    ("kopf", "dimension"),
    [
        ("Förderquote", Dimension.SHARE),
        ("Frauenanteil", Dimension.SHARE),
        ("%-Punkte", Dimension.POINTS),
    ],
)
def test_quote_und_anteil_in_komposita(kopf: str, dimension: Dimension) -> None:
    assert unit_of(kopf).dimension is dimension


def test_europa_ist_keine_waehrung() -> None:
    assert unit_of("Europa").exponent is None
    assert unit_of("Mittel in Euro").exponent == 0
    assert unit_of("EUR").exponent == 0
