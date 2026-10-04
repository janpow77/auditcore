"""Paritätstest gegen eine Ergebnismappe der VBA-Auswertung (modAKB_ToF als Referenz).

Die Mappe enthält echte, personenbezogene Daten und liegt nie im Repository.
Der Test läuft nur, wenn ``AUDITCORE_TYFINDINGS_PARITY_XLSX`` auf die Mappe
zeigt; sonst wird er übersprungen. Gelesen werden die Tabellen ``tblBelege``
und ``tblMaengel``. Meldungen nennen nur Tabelle, Excel-Zeile, Kennziffer und
erwartete/gefundene Zuordnung – nie Beschreibungen oder andere Zellinhalte.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from auditcore_tyfindings import Zuordnung, formal_zuordnen, zuordnen

UMGEBUNG = "AUDITCORE_TYFINDINGS_PARITY_XLSX"
Abweichung = tuple[str, int, str, tuple[object, ...], tuple[object, ...]]


def _mappe() -> Path:
    pfad = os.environ.get(UMGEBUNG)
    if not pfad:
        pytest.skip(f"{UMGEBUNG} nicht gesetzt (Ergebnismappe mit Echtdaten, nur lokal)")
    return Path(pfad)


def _zeilen(pfad: Path, tabelle: str) -> Iterator[tuple[int, dict[str, object]]]:
    openpyxl = pytest.importorskip("openpyxl")
    mappe = openpyxl.load_workbook(pfad, read_only=False, data_only=True)
    for blatt in mappe.worksheets:
        for name, bereich in blatt.tables.items():
            if name.lower() != tabelle.lower():
                continue
            zellen = list(blatt[bereich])
            kopf = [str(c.value) for c in zellen[0]]
            for zeile in zellen[1:]:
                yield zeile[0].row, dict(zip(kopf, (c.value for c in zeile), strict=True))
            return
    pytest.fail(f"Tabelle {tabelle} fehlt in der Mappe")


def _text(wert: object) -> str:
    return "" if wert is None else str(wert)


def _ausgabe(ergebnis: Zuordnung, mit_gold_plating: bool) -> tuple[object, ...]:
    teile: tuple[object, ...] = (
        ergebnis.anzeige,
        ergebnis.zuordnungsweg,
        ergebnis.tof_kategorie or "",
    )
    return (*teile, int(ergebnis.gold_plating)) if mit_gold_plating else teile


def _vergleich_belege(pfad: Path) -> tuple[int, list[Abweichung]]:
    anzahl = 0
    abweichungen: list[Abweichung] = []
    for nummer, zeile in _zeilen(pfad, "tblBelege"):
        anzahl += 1
        kennziffer = _text(zeile["Fehlerkennziffer"])
        erwartet = (
            _text(zeile["ToF-Unterkategorie"]),
            _text(zeile["Zuordnungsweg"]),
            _text(zeile["ToF-Kategorie"]),
            int(str(zeile["Gold-plating-Kandidat (1 ja)"] or 0)),
        )
        gefunden = _ausgabe(zuordnen(kennziffer, _text(zeile["Beschreibung"])), True)
        if gefunden != erwartet:
            abweichungen.append(("tblBelege", nummer, kennziffer, erwartet, gefunden))
    return anzahl, abweichungen


def _vergleich_maengel(pfad: Path) -> tuple[int, list[Abweichung]]:
    anzahl = 0
    abweichungen: list[Abweichung] = []
    for nummer, zeile in _zeilen(pfad, "tblMaengel"):
        anzahl += 1
        erwartet = (
            _text(zeile["ToF-Unterkategorie"]),
            _text(zeile["Zuordnungsweg"]),
            _text(zeile["ToF-Kategorie"]),
        )
        gefunden = _ausgabe(formal_zuordnen(_text(zeile["Beschreibung"])), False)
        if gefunden != erwartet:
            abweichungen.append(("tblMaengel", nummer, "", erwartet, gefunden))
    return anzahl, abweichungen


def test_belege_gleich_vba() -> None:
    anzahl, abweichungen = _vergleich_belege(_mappe())
    print(f"tblBelege: {anzahl} Zeilen, {len(abweichungen)} Abweichungen")
    assert anzahl > 0
    assert abweichungen == []


def test_maengel_gleich_vba() -> None:
    anzahl, abweichungen = _vergleich_maengel(_mappe())
    print(f"tblMaengel: {anzahl} Zeilen, {len(abweichungen)} Abweichungen")
    assert anzahl > 0
    assert abweichungen == []
