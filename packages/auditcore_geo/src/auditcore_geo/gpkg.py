"""Flächengeometrien aus GeoPackage-Blobs (GeoPackageBinary + ISO-WKB) lesen.

Grundlage ist ``osint`` ``werkzeuge/bundeslaender_holen.py:wkb_polygone``.
Gelesen werden zweidimensionale ``Polygon`` (3) und ``MultiPolygon`` (6).
Anders als das Original wird die ``srs_id`` des Kopfes zurückgegeben (sie
bestimmt Bezugssystem und Achsenfolge), und jede Abweichung – Z/M-Werte,
EWKB-Kennbits, fremde Teilgeometrien, abgeschnittene Blobs, Restbytes,
leere Geometrie, erweiterte Typen – ist ein :class:`GeometrieFehler`
statt eines still falsch gelesenen Ergebnisses.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from .errors import GeometrieFehler

#: Hüllrechteck-Größe in Bytes je Kennung (GeoPackage 1.3, Tabelle 2.1.3.1.1).
HUELLE_BYTES = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}

GpkgRing = tuple[tuple[float, float], ...]
GpkgPolygon = tuple[GpkgRing, ...]


@dataclass(frozen=True)
class GpkgGeometrie:
    """Polygone (je Liste von Ringen mit Punkten in Quellkoordinaten) und ``srs_id``."""

    srs_id: int
    polygone: tuple[GpkgPolygon, ...]


class _Leser:
    """Sequenzieller Leser mit Längenprüfung."""

    def __init__(self, daten: bytes, start: int) -> None:
        self.daten = daten
        self.pos = start

    def bytes(self, anzahl: int) -> bytes:
        """Die nächsten ``anzahl`` Bytes oder Fehler bei abgeschnittenem Blob."""
        ende = self.pos + anzahl
        if anzahl < 0 or ende > len(self.daten):
            raise GeometrieFehler("Blob ist abgeschnitten.")
        teil = self.daten[self.pos : ende]
        self.pos = ende
        return teil

    def reihenfolge(self) -> str:
        """WKB-Bytefolge als ``struct``-Präfix."""
        kennung = self.bytes(1)[0]
        if kennung not in (0, 1):
            raise GeometrieFehler(f"Unbekannte WKB-Bytefolge {kennung}.")
        return "<" if kennung == 1 else ">"

    def uint(self, folge: str) -> int:
        """Vorzeichenlose 32-Bit-Zahl."""
        (wert,) = struct.unpack(folge + "I", self.bytes(4))
        return int(wert)

    def typ(self, folge: str) -> int:
        """Geometrietyp; EWKB-Kennbits und Z/M-Typen sind Fehler."""
        wert = self.uint(folge)
        if wert & 0xE0000000:
            raise GeometrieFehler(f"EWKB-Kennbits im Typ {wert:#x} sind nicht vorgesehen.")
        if wert in (1003, 2003, 3003, 1006, 2006, 3006):
            raise GeometrieFehler(f"WKB-Typ {wert} mit Z/M-Werten wird nicht gelesen.")
        return wert

    def polygon(self, folge: str) -> GpkgPolygon:
        """Ein Polygon als Ringe von Punktpaaren."""
        ringe: list[GpkgRing] = []
        for _ in range(self.uint(folge)):
            anzahl = self.uint(folge)
            werte = struct.unpack(folge + f"{2 * anzahl}d", self.bytes(16 * anzahl))
            ringe.append(tuple((werte[i], werte[i + 1]) for i in range(0, len(werte), 2)))
        return tuple(ringe)


def lies_gpkg_polygone(blob: bytes) -> GpkgGeometrie:
    """Polygone eines GeoPackage-Blobs samt ``srs_id``."""
    if not isinstance(blob, (bytes, bytearray, memoryview)):
        raise GeometrieFehler("Blob (bytes) erwartet.")
    daten = bytes(blob)
    if len(daten) < 8 or daten[:2] != b"GP":
        raise GeometrieFehler("Kein GeoPackage-Blob.")
    if daten[2] != 0:
        raise GeometrieFehler(f"GeoPackageBinary-Version {daten[2]} nicht vorgesehen.")
    flags = daten[3]
    if flags & 0b0010_0000:
        raise GeometrieFehler("Erweiterter GeoPackage-Geometrietyp wird nicht gelesen.")
    if flags & 0b0001_0000:
        raise GeometrieFehler("Leere Geometrie.")
    huelle = HUELLE_BYTES.get((flags >> 1) & 7)
    if huelle is None:
        raise GeometrieFehler(f"Ungültige Hüllrechteck-Kennung {(flags >> 1) & 7}.")
    kopf_folge = "<" if flags & 1 else ">"
    (srs_id,) = struct.unpack(kopf_folge + "i", daten[4:8])
    leser = _Leser(daten, 8)
    leser.bytes(huelle)
    folge = leser.reihenfolge()
    typ = leser.typ(folge)
    if typ == 3:
        polygone: tuple[GpkgPolygon, ...] = (leser.polygon(folge),)
    elif typ == 6:
        teile = []
        for _ in range(leser.uint(folge)):
            teil_folge = leser.reihenfolge()
            teil_typ = leser.typ(teil_folge)
            if teil_typ != 3:
                raise GeometrieFehler(f"MultiPolygon enthält Teilgeometrie vom Typ {teil_typ}.")
            teile.append(leser.polygon(teil_folge))
        polygone = tuple(teile)
    else:
        raise GeometrieFehler(f"WKB-Typ {typ} nicht vorgesehen (nur Polygon/MultiPolygon).")
    if leser.pos != len(daten):
        raise GeometrieFehler(f"{len(daten) - leser.pos} unerwartete Restbytes nach der Geometrie.")
    return GpkgGeometrie(int(srs_id), polygone)
