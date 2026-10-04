"""Zuordnung der Fehlerkennziffern (VBA ``ToFZuordnen``) auf synthetischen Beschreibungen."""

from __future__ import annotations

import pytest

from auditcore_tyfindings import (
    EingabeFehler,
    Zuordnung,
    kennziffer_normalisieren,
    standardprofil,
    zuordnen,
)

# Kennziffer, synthetische Beschreibung, Unterkategorie, Weg, Gold-plating, Regel
FAELLE = [
    ("8.1", "Rechnung vor Beginn", "4.1", "Kennziffer", False, "kennziffer:8.1"),
    ("8.2", "nicht bezahlt", "4.2", "Kennziffer", False, "kennziffer:8.2"),
    ("8.5", "Vorsteuer", "4.5", "Kennziffer", False, "kennziffer:8.5"),
    ("8.8", "doppelt", "4.18", "Kennziffer", False, "kennziffer:8.8"),
    ("7.1", "Summe falsch übertragen", "10.1", "Kennziffer", False, "kennziffer:7.1"),
    ("5.2", "keine Rechnung", "9.2", "Kennziffer", False, "kennziffer:5.2"),
    ("5.1", "Teilnehmerzahl", "4.16", "Kennziffer", False, "kennziffer:5.1"),
    ("8.3", "beliebig", None, "nicht zugeordnet", False, "kennziffer:8.3"),
    ("8.9", "Skonto nicht abgezogen", "4.2", "Schlüsselwort", False, "kennziffer:8.9:regel:1"),
    ("8.9", "NACHLASS", "4.2", "Schlüsselwort", False, "kennziffer:8.9:regel:2"),
    ("8.9", "Rabatt", "4.2", "Schlüsselwort", False, "kennziffer:8.9:regel:3"),
    ("8.9", "Tagegeld zu hoch", "4.15", "Schlüsselwort", False, "kennziffer:8.9:regel:4"),
    ("8.9", "Frühstück enthalten", "4.15", "Schlüsselwort", False, "kennziffer:8.9:regel:5"),
    ("8.9", "Hotelkosten", "4.15", "Schlüsselwort", False, "kennziffer:8.9:regel:6"),
    ("8.9", "zu aktivieren", "4.18", "Schlüsselwort", False, "kennziffer:8.9:regel:7"),
    ("8.9", "ohne Schlagwort", "4.18", "Kennziffer", False, "kennziffer:8.9"),
    ("16", "mehr als 1.720 Stunden", "4.14", "Schlüsselwort", False, "kennziffer:16:regel:1"),
    ("16", "Stunden nicht belegt", "4.14", "Schlüsselwort", False, "kennziffer:16:regel:2"),
    ("16", "Personalkosten", "4.14", "Schlüsselwort", False, "kennziffer:16:regel:3"),
    ("16", "Beleg unter 50 EUR", "4.16", "Schlüsselwort", True, "kennziffer:16:regel:4"),
    ("16", "sonstiges", None, "nicht zugeordnet", False, "kennziffer:16"),
    ("ohne Kennziffer", "Skonto", None, "nicht zugeordnet", False, "kennziffer:ohne Kennziffer"),
    ("99.9", "Skonto", None, "nicht zugeordnet", False, None),
]


@pytest.mark.parametrize(
    ("kennziffer", "beschreibung", "tof", "weg", "gold_plating", "regel"),
    FAELLE,
    ids=[f"{f[0]}-{i}" for i, f in enumerate(FAELLE)],
)
def test_zuordnung_wie_vba(
    kennziffer: str,
    beschreibung: str,
    tof: str | None,
    weg: str,
    gold_plating: bool,
    regel: str | None,
) -> None:
    ergebnis = zuordnen(kennziffer, beschreibung)
    kategorie = None if tof is None else tof.split(".")[0]
    assert ergebnis == Zuordnung(tof, kategorie, weg, gold_plating, regel)  # type: ignore[arg-type]


def test_jede_kennzifferregel_hat_einen_fall() -> None:
    abgedeckt = {f[5] for f in FAELLE}
    profil = standardprofil()
    erwartet = {e.regel_id for e in profil.kennziffern.values()}
    erwartet |= {r.regel_id for e in profil.kennziffern.values() for r in e.regeln}
    assert erwartet <= abgedeckt


def test_erster_treffer_gewinnt_auch_bei_spaeterem_gold_plating() -> None:
    ergebnis = zuordnen("16", "Personal unter 50 EUR")
    assert (ergebnis.tof_unterkategorie, ergebnis.gold_plating) == ("4.14", False)


def test_gold_plating_nur_im_zugeordneten_fall() -> None:
    ergebnis = zuordnen("16", "Bagatelle unter 50 EUR")
    assert ergebnis.gold_plating and ergebnis.anzeige == "4.16" and ergebnis.zugeordnet


@pytest.mark.parametrize("kennziffer", ["8.10", "8.90", "1.10", "08.9", "8,9", "16.0"])
def test_kennziffer_wird_exakt_als_text_verglichen(kennziffer: str) -> None:
    assert zuordnen(kennziffer, "Skonto").zuordnungsweg == "nicht zugeordnet"


def test_kennziffer_als_zahl_ist_ein_fehler() -> None:
    with pytest.raises(EingabeFehler):
        zuordnen(8.9, "Skonto")  # type: ignore[arg-type]
    with pytest.raises(EingabeFehler):
        zuordnen("8.9", None)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("roh", "schluessel"),
    [
        (" 8.9 ", "8.9"),
        ("\xa016", "16"),
        ("", "ohne Kennziffer"),
        ("-", "ohne Kennziffer"),
        ("/", "ohne Kennziffer"),
        ("1.10", "1.10"),
    ],
)
def test_kennziffer_normalisieren_wie_vba_import(roh: str, schluessel: str) -> None:
    assert kennziffer_normalisieren(roh) == schluessel


def test_leere_kennziffer_wird_ohne_kennziffer() -> None:
    assert zuordnen("  ", "Skonto").regel_id == "kennziffer:ohne Kennziffer"


def test_nicht_zugeordnet_hat_keine_kategorie() -> None:
    ergebnis = zuordnen("8.3")
    assert ergebnis.anzeige == "nicht zugeordnet"
    assert ergebnis.tof_kategorie is None and not ergebnis.zugeordnet
