"""Formalregeln für nichtfinanzielle Mängel (VBA ``ToFFormalZuordnen``)."""

from __future__ import annotations

import pytest

from auditcore_tyfindings import EingabeFehler, formal_zuordnen, standardprofil

# synthetische Beschreibung, Unterkategorie, Regel
FAELLE = [
    ("Wirtschaftliche Eigentümer fehlen", "9.3", "formal:1"),
    ("Eigentümer nicht erfasst", "9.3", "formal:2"),
    ("Publizitätspflicht", "8.1", "formal:3"),
    ("Kommunikation fehlt", "8.1", "formal:4"),
    ("ohne Logo", "8.1", "formal:5"),
    ("kein Plakat", "8.1", "formal:6"),
    ("Förderhinweis fehlt", "8.1", "formal:7"),
    ("Beihilfe nicht geprüft", "2.11", "formal:8"),
    ("De-minimis-Erklärung", "2.11", "formal:9"),
    ("TAM-Meldung offen", "2.11", "formal:10"),
    ("Transparenzpflicht", "2.11", "formal:11"),
    ("Buchführung unklar", "10.2", "formal:12"),
    ("Buchhaltung", "10.2", "formal:13"),
    ("Kostenstelle fehlt", "10.2", "formal:14"),
    ("nicht getrennt", "10.2", "formal:15"),
    ("Aufbewahrungsfrist", "9.2", "formal:16"),
    ("Prüfpfad", "9.2", "formal:17"),
    ("digitalisiert", "9.2", "formal:18"),
    ("Original fehlt", "9.2", "formal:19"),
    ("Belegdaten", "9.1", "formal:20"),
    ("Rechnungsdatum", "9.1", "formal:21"),
    ("Rg.Dat. leer", "9.1", "formal:22"),
    ("Zahldatum", "9.1", "formal:23"),
    ("Datum fehlt", "9.1", "formal:24"),
    ("Rechnungsnummer", "9.1", "formal:25"),
    ("Re-Nr. fehlt", "9.1", "formal:26"),
    ("Unterlagen unvollständig", "9.1", "formal:27"),
    ("Nachweis fehlt", "9.1", "formal:28"),
    ("Unterschrift fehlt", "9.1", "formal:29"),
    ("Betrag falsch", "9.1", "formal:30"),
]


@pytest.mark.parametrize(("beschreibung", "tof", "regel"), FAELLE, ids=[f[2] for f in FAELLE])
def test_formalregel(beschreibung: str, tof: str, regel: str) -> None:
    ergebnis = formal_zuordnen(beschreibung)
    assert (ergebnis.tof_unterkategorie, ergebnis.regel_id) == (tof, regel)
    assert ergebnis.zuordnungsweg == "Schlüsselwort"
    assert ergebnis.tof_kategorie == tof.split(".")[0]
    assert not ergebnis.gold_plating


def test_alle_formalregeln_abgedeckt_und_keine_verdeckt() -> None:
    regeln = standardprofil().formalregeln
    assert {r.regel_id for r in regeln} == {f[2] for f in FAELLE}
    for regel in regeln:
        assert formal_zuordnen(regel.suchwort).regel_id == regel.regel_id


def test_erster_treffer_gewinnt() -> None:
    assert formal_zuordnen("Logo und Datum fehlen").tof_unterkategorie == "8.1"


def test_ohne_treffer_nicht_zugeordnet() -> None:
    ergebnis = formal_zuordnen("Sonstiger Hinweis")
    assert ergebnis.zuordnungsweg == "nicht zugeordnet"
    assert ergebnis.tof_unterkategorie is None and ergebnis.regel_id is None


def test_beschreibung_als_text() -> None:
    with pytest.raises(EingabeFehler):
        formal_zuordnen(None)  # type: ignore[arg-type]
