"""Eigenschaftstests der Invarianten aus ``docs/spezifikation.md`` (Hypothesis).

Synthetische Spaltennamen und Tabellen; jede Testfunktion nennt ihre Invariante.
"""

from __future__ import annotations

from datetime import date, datetime
from io import BytesIO

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_reporting import (
    PROFILE_IDS,
    ExcelOptions,
    ReportTable,
    WorkbookLimitError,
    WorkbookLimits,
    get_number_format,
    get_profile_format,
    get_profile_metadata,
    render_workbook,
)
from auditcore_reporting.formats_v2 import (
    _COMPOUND,
    _WORDS,
    FORMATS,
    column_kind,
    get_number_format_v2,
)

openpyxl = pytest.importorskip("openpyxl")

EINSTELLUNG = settings(max_examples=150, deadline=None)
FORMATE = ('#,##0.00 "EUR"', "0.00%", "DD.MM.YYYY", "#,##0", "#,##0.00", "General")
# Stichwörter je Rang (Rang 0 = höchste Priorität), wie im Profil flowlib-legacy-v1.
STICHWOERTER = (
    (
        "betrag",
        "summe",
        "kosten",
        "ausgabe",
        "einnahme",
        "foerder",
        "bewillig",
        "auszahl",
        "gesamt",
        "netto",
        "brutto",
        "saldo",
    ),
    ("quote", "anteil", "prozent", "rate", "satz", "percent"),
    ("datum", "date", "von", "bis", "beginn", "ende", "stichtag", "zeitpunkt"),
    ("anzahl", "count", "nummer", "nr", "pos", "lfd"),
    ("stunden", "tage", "hours", "days"),
)
ALLE = [w for gruppe in STICHWOERTER for w in gruppe]
# Füllzeichen ohne Buchstaben: können kein Stichwort bilden.
FUELLUNG = st.text(alphabet=" _-0123456789%/().", max_size=6)


@EINSTELLUNG
@given(st.text(max_size=40))
def test_i1_formatwahl_total_und_deterministisch(name: str) -> None:
    """I1: jeder Spaltenname ergibt genau eines der sechs Formate, bei jedem Aufruf dasselbe."""
    fmt = get_number_format(name)
    assert fmt in FORMATE
    assert get_number_format(name) == fmt
    assert get_number_format(name, value=object()) == fmt


@EINSTELLUNG
@given(
    st.integers(0, 4),
    st.integers(0, 4),
    st.data(),
    FUELLUNG,
    st.text(alphabet=" _-0123456789", min_size=1, max_size=4),
    FUELLUNG,
    st.booleans(),
)
def test_i2_rangfolge_betrag_prozent_datum_anzahl_dauer(
    i: int, j: int, data, a: str, b: str, c: str, vorn: bool
) -> None:
    """I2: enthält ein Name Stichwörter mehrerer Ränge, entscheidet der höchste Rang –
    unabhängig von der Stellung im Namen."""
    w1 = data.draw(st.sampled_from(STICHWOERTER[i]))
    w2 = data.draw(st.sampled_from(STICHWOERTER[j]))
    name = a + (w1 + b + w2 if vorn else w2 + b + w1) + c
    assert get_number_format(name) == FORMATE[min(i, j)]


@EINSTELLUNG
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz _-0123456789", max_size=30))
def test_i3_gross_und_kleinschreibung_ohne_einfluss(name: str) -> None:
    """I3: ASCII-Groß-/Kleinschreibung ändert die Formatwahl nicht."""
    assert get_number_format(name.upper()) == get_number_format(name.lower())


@EINSTELLUNG
@given(st.text(max_size=30), st.text(max_size=12))
def test_i4_profile_ausdruecklich(name: str, profil: str) -> None:
    """I4: ``plain-v1`` liefert immer General, ``flowlib-legacy-v1`` die Heuristik;
    unbekannte Profile werden abgewiesen."""
    assert get_profile_format("plain-v1", name) == "General"
    assert get_profile_format("flowlib-legacy-v1", name) == get_number_format(name)
    assert get_profile_format("flowlib-v2", name) == get_number_format_v2(name)
    if profil not in PROFILE_IDS:
        with pytest.raises(ValueError):
            get_profile_format(profil, name)


@EINSTELLUNG
@given(st.sampled_from(PROFILE_IDS))
def test_i5_profilmetadaten_durch_hashes_gebunden(profil: str) -> None:
    """I5: Metadaten nur mit gültigem Inhalts- und Implementierungshash; stets frisch."""
    a = get_profile_metadata(profil)
    b = get_profile_metadata(profil)
    assert a == b and a is not b
    assert a["content"]["profile_id"] == profil


ZELLE = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-999_999_999_999_999, max_value=999_999_999_999_999),
    # Der ganze endliche Bereich, auch die größte Zahl (Befund B2 behoben).
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(alphabet=st.characters(codec="utf-8", exclude_categories=("Cs", "Cc")), max_size=20),
    st.sampled_from(["=1+1", '=HYPERLINK("http://x")', "+SUM(A1)", "@x", "-2"]),
    st.dates(min_value=date(1900, 3, 1), max_value=date(9999, 12, 31)),
)


def _lesen(payload: bytes) -> list[list[object]]:
    wb = openpyxl.load_workbook(BytesIO(payload))
    return [[c.value for c in row] for row in wb.worksheets[0].iter_rows(min_row=2)]


@settings(max_examples=40, deadline=None)
@given(st.lists(st.lists(ZELLE, min_size=3, max_size=3), min_size=1, max_size=8))
def test_i6_werte_verlustfrei_texte_nie_als_formel(zeilen) -> None:
    """I6: übergebene Werte kommen unverändert zurück (Gleitkommazahlen bitgleich);
    Texte mit ``=``, ``+``, ``@`` bleiben Text (Datentyp ``s``), es entsteht
    keine Formel.

    Profil ``plain-v1``: Unter ``flowlib-legacy-v1`` bestimmt der Spaltenname das
    Zahlenformat auch für Werte anderen Typs (Befund B1 der Spezifikation).
    """
    tabelle = ReportTable("Daten", ("A", "B", "C"), zeilen, profile="plain-v1")
    payload = render_workbook([tabelle])
    gelesen = _lesen(payload)
    for original, zurueck in zip(zeilen, gelesen, strict=True):
        for wert, z in zip(original, zurueck, strict=True):
            if isinstance(wert, date) and not isinstance(wert, datetime):
                assert isinstance(z, datetime) and z.date() == wert
            elif isinstance(wert, str) and wert == "":
                assert z in ("", None)
            else:
                assert z == wert
    wb = openpyxl.load_workbook(BytesIO(payload))
    for row in wb.worksheets[0].iter_rows(min_row=2):
        for cell in row:
            if isinstance(cell.value, str):
                assert cell.data_type == "s"


@EINSTELLUNG
@given(st.integers(min_value=1, max_value=20), st.integers(min_value=0, max_value=5))
def test_i7_grenzen_ohne_teilartefakt(grenze: int, ueber: int) -> None:
    """I7: mehr Zeilen als ``max_rows_per_sheet`` → ``WorkbookLimitError``; bis zur
    Grenze entsteht eine vollständige Datei."""
    zeilen = [[n] for n in range(grenze + ueber)]
    optionen = ExcelOptions(limits=WorkbookLimits(max_rows_per_sheet=grenze))
    if ueber:
        with pytest.raises(WorkbookLimitError):
            render_workbook([ReportTable("T", ("Anzahl",), zeilen)], optionen)
    else:
        datei = render_workbook([ReportTable("T", ("Anzahl",), zeilen)], optionen)
        assert len(_lesen(datei)) == grenze


@EINSTELLUNG
@given(st.integers(min_value=1, max_value=5), st.integers(min_value=0, max_value=6))
def test_i8_zeilenform_muss_zu_den_spalten_passen(spalten: int, breite: int) -> None:
    """I8: Zeilen, deren Breite oder Schlüssel nicht zu den Spalten passen, werden abgewiesen."""
    namen = tuple(f"Spalte {k}" for k in range(spalten))
    tabelle = ReportTable("T", namen, [[1] * breite])
    if breite == spalten:
        render_workbook([tabelle])
    else:
        with pytest.raises(ValueError):
            render_workbook([tabelle])
    with pytest.raises(ValueError):
        render_workbook([ReportTable("T", namen, [{"fremd": 1}])])


@EINSTELLUNG
@given(st.sampled_from(PROFILE_IDS), st.sampled_from(ALLE))
def test_i9_zahlenformat_folgt_profil_und_ueberschreibung(profil: str, spalte: str) -> None:
    """I9: das Zellformat ist die ausdrückliche Überschreibung, sonst das Profilformat
    für Spaltenname und Wert (nur ``flowlib-v2`` wertet den Wert aus)."""
    tabelle = ReportTable("T", (spalte, "frei"), [[1, 2]], profile=profil, formats={"frei": "0.0"})
    wb = openpyxl.load_workbook(BytesIO(render_workbook([tabelle])))
    a, b = next(wb.worksheets[0].iter_rows(min_row=2))
    assert a.number_format == get_profile_format(profil, spalte, 1)
    assert b.number_format == "0.0"


@pytest.mark.parametrize(
    "wert", [1.7976931348623157e308, -1.7976931348623157e308, 0.1 + 0.2, 5e-324, 2.0**53 + 2]
)
def test_i6_groesste_gleitkommazahl_verlustfrei(wert: float) -> None:
    """I6 (Befund B2 behoben): auch die größte endliche Gleitkommazahl und Werte, die
    17 Stellen brauchen, kommen bitgleich zurück."""
    datei = render_workbook([ReportTable("T", ("A",), [[wert]], profile="plain-v1")])
    assert _lesen(datei)[0][0] == wert


# --- Profil flowlib-v2 (Befund B1 behoben) -------------------------------------------

# Vorsilben ohne die Buchstaben längerer Fachbegriffe: ändern die Wortart nicht.
VORSILBE = st.text(alphabet="xqj", max_size=4)
KENNUNGEN = list(_COMPOUND["identifier"])
BEGRIFFE = [(art, t) for art, terme in _COMPOUND.items() if art != "neutral" for t in terme]
WERTE = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(max_size=5),
    st.dates(),
)


@EINSTELLUNG
@given(VORSILBE, st.sampled_from(KENNUNGEN), FUELLUNG, WERTE)
def test_i10_kennungen_nie_mit_zahlenformat(vorsilbe: str, term: str, rest: str, wert) -> None:
    """I10: Spalten mit Kennungen (Postleitzahl, Kontonummer, IBAN, Steuernummer …)
    erhalten unter ``flowlib-v2`` nie Tausendertrenner, Prozent oder Währung."""
    fmt = get_number_format_v2(vorsilbe + term.capitalize() + rest, wert)
    if isinstance(wert, date):
        assert fmt == "DD.MM.YYYY"
    elif isinstance(wert, bool):
        assert fmt == "General"
    elif isinstance(wert, (int, float)):
        assert fmt == "0"
    else:
        assert fmt == "@"


@EINSTELLUNG
@given(st.text(max_size=30), WERTE)
def test_i11_werttyp_vor_spaltenname(name: str, wert) -> None:
    """I11: unter ``flowlib-v2`` bestimmt ein Datumswert das Datumsformat, Text und
    Wahrheitswerte erhalten kein Zahlenformat, Zahlen nie das Datumsformat."""
    fmt = get_number_format_v2(name, wert)
    if isinstance(wert, bool):
        assert fmt == "General"
    elif isinstance(wert, date):
        assert fmt == "DD.MM.YYYY"
    elif isinstance(wert, str):
        assert fmt in ("General", "@")
    elif isinstance(wert, (int, float)):
        assert fmt != "DD.MM.YYYY"


@EINSTELLUNG
@given(VORSILBE, st.sampled_from(BEGRIFFE))
def test_i12_kopf_des_kompositums_entscheidet(vorsilbe: str, begriff) -> None:
    """I12: in einem zusammengesetzten Wort entscheidet der Kopf (das Wortende), nicht
    ein Teilwort irgendwo im Namen; ohne Wert gilt das Format der Wortart."""
    art, term = begriff
    name = (vorsilbe + term).capitalize()
    assert column_kind(name) == art
    erwartet = "@" if art == "identifier" else FORMATS[art]
    assert get_number_format_v2(name) == erwartet


@EINSTELLUNG
@given(st.sampled_from([w for ws in _WORDS.values() for w in ws if w != "%"]), VORSILBE)
def test_i12_kurzwoerter_nur_als_ganzes_wort(wort: str, vorsilbe: str) -> None:
    """I12: kurze Begriffe (``nr``, ``id``, ``von``, ``bis``, ``ende`` …) zählen nur als
    ganzes Wort; als Wortende eines längeren Worts bleiben sie ohne Wirkung."""
    assert column_kind(f"xq{vorsilbe}{wort}") is None
    assert column_kind(f"Spalte {wort}") is not None


UMLAUTE = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}


@EINSTELLUNG
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyzäöüß _-.%0123456789", max_size=30), WERTE)
def test_i13_schreibweise_ohne_einfluss(name: str, wert) -> None:
    """I13: Groß-/Kleinschreibung und die Umschreibung von Umlauten (ä/ae …) ändern die
    Formatwahl von ``flowlib-v2`` nicht."""
    umschrieben = "".join(UMLAUTE.get(c, c) for c in name)
    fmt = get_number_format_v2(name, wert)
    assert get_number_format_v2(name.upper(), wert) == fmt
    assert get_number_format_v2(umschrieben, wert) == fmt
