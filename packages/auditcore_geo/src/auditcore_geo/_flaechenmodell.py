"""Flächenmodell und Leser: Ringe, Polygone, zusammengefallene Ringe (GEO-C16).

Die Lage-, Abstands- und Schwerpunktfunktionen stehen in :mod:`auditcore_geo.flaeche`,
das alle Namen dieses Moduls wieder ausgibt.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, TypeGuard

from .errors import GeometrieFehler, ProfilFehler
from .gpkg import GpkgGeometrie

Ring = tuple[tuple[float, float], ...]
Kante = tuple[tuple[float, float], tuple[float, float]]


#: Empfohlene Randregel (Entscheidung vom 23.09.2026, vom Nutzer delegiert):
#: Randpunkte zählen als innen – ein möglicher Schutzgebietsbezug wird eher
#: gemeldet als übersehen. ``enthaelt`` verlangt die Angabe weiterhin ausdrücklich.
EMPFOHLEN_RAND_GILT_ALS_INNEN = True

#: Vertragsnummer der Behandlung zusammengefallener Ringe.
VERTRAG_ENTARTETE_RINGE = "GEO-C16"

#: Ein Ring gilt als Linie, wenn kein Punkt weiter als dieser Bruchteil der
#: Ringausdehnung von der Geraden abweicht (1e-12: bei 1 000 km rund 1 µm).
#: Die Schranke fängt Rundungsreste dezimal kollinearer Koordinaten ab.
KOLLINEAR_RELATIV = 1e-12

#: ``srs_id`` eines GeoPackage, deren Koordinaten ohne Umrechnung ``(lon, lat)`` sind.
GEOGRAPHISCHE_SRS_IDS = frozenset({4326, 4258})


class Lage(StrEnum):
    """Lage eines Punktes zu einer Fläche."""

    INNEN = "innen"
    AUSSEN = "aussen"
    RAND = "rand"


class Entartung(StrEnum):
    """Worauf ein Ring zusammengefallen ist."""

    PUNKT = "punkt"
    LINIE = "linie"


class RingRolle(StrEnum):
    """Außenring oder Loch."""

    AUSSEN = "aussen"
    LOCH = "loch"


@dataclass(frozen=True)
class EntarteterRing:
    """Ein auf Punkt oder Linie zusammengefallener Ring (GEO-C16).

    ``polygon`` und ``ring`` sind die Nummern in der Eingabe (Ring 0 =
    Außenring). ``punkte`` sind die Stützpunkte ohne Schlusspunkt und ohne
    unmittelbare Wiederholungen. Nur Außenringe werden als Objekt
    berücksichtigt; ``verworfene_loecher`` zählt die dabei entfallenen Löcher.
    """

    code: ClassVar[str] = "entarteter_ring"
    vertrag: ClassVar[str] = VERTRAG_ENTARTETE_RINGE

    polygon: int
    ring: int
    art: Entartung
    punkte: Ring
    verworfene_loecher: int = 0

    @property
    def rolle(self) -> RingRolle:
        """Außenring (Ring 0) oder Loch."""
        return RingRolle.AUSSEN if self.ring == 0 else RingRolle.LOCH

    @property
    def beruecksichtigt(self) -> bool:
        """``True`` für Außenringe (Punkt-/Linienobjekt mit Abstand), ``False`` für Löcher."""
        return self.rolle is RingRolle.AUSSEN

    def hinweis(self) -> str:
        """Lesbarer Hinweis für Prüfvermerk oder Oberfläche."""
        art = "einen Punkt" if self.art is Entartung.PUNKT else "eine Linie"
        ort = f"Polygon {self.polygon}, Ring {self.ring}"
        if self.beruecksichtigt:
            text = (
                f"{ort}: Außenring ist auf {art} zusammengefallen; "
                "berücksichtigt als Objekt ohne Fläche (Abstand zählt)"
            )
            if self.verworfene_loecher:
                text += f", {self.verworfene_loecher} Loch/Löcher entfallen"
        else:
            text = f"{ort}: Loch ist auf {art} zusammengefallen; entfällt (Fläche 0)"
        return f"{text} ({self.vertrag})."


def _ist_folge(wert: object) -> TypeGuard[Sequence[object]]:
    return isinstance(wert, Sequence) and not isinstance(wert, (str, bytes))


def _is_number(wert: object) -> TypeGuard[int | float]:
    return isinstance(wert, (int, float)) and not isinstance(wert, bool)


def _position(position: object, name: str) -> tuple[float, float]:
    """Ein endliches Zahlenpaar; alles andere ist ein Fehler."""
    if not _ist_folge(position) or len(position) < 2:
        raise GeometrieFehler(f"{name}: Position {position!r} ist kein Zahlenpaar.")
    x, y = position[0], position[1]
    if not (_is_number(x) and _is_number(y)):
        raise GeometrieFehler(f"{name}: Position {position!r} ist kein Zahlenpaar.")
    if not (math.isfinite(x) and math.isfinite(y)):
        raise GeometrieFehler(f"{name}: Position {position!r} ist nicht endlich.")
    return float(x), float(y)


def _positionen(roh: object, name: str) -> Ring:
    """Zahlenpaare eines Rings ohne wiederholten Schlusspunkt; unlesbar → Fehler."""
    if not _ist_folge(roh):
        raise GeometrieFehler(f"{name}: Punktliste erwartet.")
    punkte = [_position(position, name) for position in roh]
    if not punkte:
        raise GeometrieFehler(f"{name}: Ring ohne Positionen.")
    if len(punkte) > 1 and punkte[0] == punkte[-1]:
        punkte.pop()
    return tuple(punkte)


def _ohne_wiederholung(ring: Ring) -> Ring:
    """Unmittelbar wiederholte Punkte (auch über den Ringschluss) entfernen."""
    punkte: list[tuple[float, float]] = []
    for p in ring:
        if not punkte or punkte[-1] != p:
            punkte.append(p)
    while len(punkte) > 1 and punkte[-1] == punkte[0]:
        punkte.pop()
    return tuple(punkte)


def _entartung(ring: Ring) -> Entartung | None:
    """``PUNKT``/``LINIE`` für einen Ring ohne Fläche, sonst ``None``."""
    verschieden = set(ring)
    if len(verschieden) == 1:
        return Entartung.PUNKT
    if len(verschieden) == 2:
        return Entartung.LINIE
    x0, y0 = ring[0]
    fx, fy = max(ring, key=lambda p: (p[0] - x0) ** 2 + (p[1] - y0) ** 2)
    dx, dy = fx - x0, fy - y0
    schranke = KOLLINEAR_RELATIV * (dx * dx + dy * dy)
    if all(abs(dx * (y - y0) - dy * (x - x0)) <= schranke for x, y in ring):
        return Entartung.LINIE
    return None


@dataclass(frozen=True)
class Polygon:
    """Außenring und Löcher; Ringe ohne wiederholten Schlusspunkt."""

    aussen: Ring
    loecher: tuple[Ring, ...] = ()

    def ringe(self) -> tuple[Ring, ...]:
        """Außenring gefolgt von den Löchern."""
        return (self.aussen, *self.loecher)

    def rechteck(self) -> tuple[float, float, float, float]:
        """``(west, sued, ost, nord)`` des Außenrings."""
        xs = [x for x, _ in self.aussen]
        ys = [y for _, y in self.aussen]
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass(frozen=True)
class Flaeche:
    """Echte Teilflächen und zusammengefallene Ringe (GeoJSON ``Polygon``/``MultiPolygon``).

    ``polygone`` sind die Teilflächen, ``entartet`` die zusammengefallenen
    Ringe (GEO-C16). Eine Fläche braucht mindestens eine Teilfläche oder
    einen zusammengefallenen Außenring.
    """

    polygone: tuple[Polygon, ...]
    entartet: tuple[EntarteterRing, ...] = ()

    def __post_init__(self) -> None:
        if not self.polygone and not self.objekte_ohne_flaeche:
            raise GeometrieFehler("Fläche ohne Polygon.")

    @property
    def objekte_ohne_flaeche(self) -> tuple[EntarteterRing, ...]:
        """Zusammengefallene Außenringe, die als Punkt-/Linienobjekt zählen."""
        return tuple(e for e in self.entartet if e.beruecksichtigt)

    @property
    def hinweise(self) -> tuple[str, ...]:
        """Ein Hinweis je zusammengefallenem Ring; leer, wenn alles Fläche ist."""
        return tuple(e.hinweis() for e in self.entartet)


def _check_strict(nummer: int, arten: Sequence[Entartung | None]) -> None:
    """Mit ``strikt=True`` ist jeder zusammengefallene Ring ein Fehler."""
    for i, art in enumerate(arten):
        if art is not None:
            raise GeometrieFehler(
                f"Polygon {nummer}, Ring {i}: Ring ist auf {art.value} "
                f"zusammengefallen ({VERTRAG_ENTARTETE_RINGE}, strikt)."
            )


def _polygon_from_rings(
    nummer: int, ringe: Sequence[Ring], arten: Sequence[Entartung | None]
) -> tuple[Polygon | None, list[EntarteterRing]]:
    """Echtes Polygon mit gültigen Löchern oder – bei zusammengefallenem Außenring – keines."""
    aussen_art = arten[0]
    if aussen_art is not None:
        ring = EntarteterRing(nummer, 0, aussen_art, _ohne_wiederholung(ringe[0]), len(ringe) - 1)
        return None, [ring]
    loecher: list[Ring] = []
    entartet: list[EntarteterRing] = []
    for i in range(1, len(ringe)):
        art = arten[i]
        if art is None:
            loecher.append(ringe[i])
        else:
            entartet.append(EntarteterRing(nummer, i, art, _ohne_wiederholung(ringe[i])))
    return Polygon(ringe[0], tuple(loecher)), entartet


def flaeche_aus_ringen(polygone: Sequence[object], *, strikt: bool = False) -> Flaeche:
    """Fläche aus Polygonen (je Ringe aus ``(lon, lat)``-Paaren, Ring 0 außen).

    Zusammengefallene Ringe werden nach GEO-C16 geführt; mit ``strikt=True``
    ist jeder zusammengefallene Ring ein :class:`GeometrieFehler`.
    Unlesbare Ringe (keine Zahlen, nicht endlich, leer) sind stets ein Fehler.
    """
    if not _ist_folge(polygone):
        raise GeometrieFehler("Polygonliste erwartet.")
    echte: list[Polygon] = []
    entartet: list[EntarteterRing] = []
    for nummer, roh in enumerate(polygone):
        if not _ist_folge(roh) or not roh:
            raise GeometrieFehler(f"Polygon {nummer}: Ringliste fehlt.")
        ringe = [_positionen(r, f"Polygon {nummer}, Ring {i}") for i, r in enumerate(roh)]
        arten = [_entartung(r) for r in ringe]
        if strikt:
            _check_strict(nummer, arten)
        polygon, zusammengefallen = _polygon_from_rings(nummer, ringe, arten)
        entartet.extend(zusammengefallen)
        if polygon is not None:
            echte.append(polygon)
    return Flaeche(tuple(echte), tuple(entartet))


def flaeche_aus_geojson(geometrie: Mapping[str, object], *, strikt: bool = False) -> Flaeche:
    """``Polygon``/``MultiPolygon`` in GeoJSON-Achsenfolge; alles andere ist ein Fehler.

    Anders als die Quellen (die unlesbare Ringe verwerfen oder für eine
    unbekannte Geometrie ``(0, 0)`` bzw. ``0.0`` liefern) wird eine
    unbrauchbare Geometrie nie still zu einem Ergebnis. Zusammengefallene
    Ringe sind kein Fehler, sondern stehen in :attr:`Flaeche.hinweise`
    (GEO-C16); ``strikt=True`` weist jeden zusammengefallenen Ring ab – auch
    kollineare Ringe, die 0.1.0 still als Polygon ohne Fläche annahm.
    """
    if not isinstance(geometrie, Mapping):
        raise GeometrieFehler("GeoJSON-Geometrie (Objekt) erwartet.")
    art = geometrie.get("type")
    koordinaten = geometrie.get("coordinates")
    roh_polygone: list[object]
    if art == "Polygon":
        roh_polygone = [koordinaten]
    elif art == "MultiPolygon":
        if not _ist_folge(koordinaten):
            raise GeometrieFehler("MultiPolygon ohne Koordinatenliste.")
        roh_polygone = list(koordinaten)
    else:
        raise GeometrieFehler(f"Nicht unterstützter Geometrietyp: {art!r}")
    return flaeche_aus_ringen(roh_polygone, strikt=strikt)


def flaeche_aus_gpkg(
    geometrie: GpkgGeometrie,
    *,
    umrechnung: Callable[[float, float], tuple[float, float]] | None = None,
    strikt: bool = False,
) -> Flaeche:
    """Fläche aus :func:`lies_gpkg_polygone`; zusammengefallene Ringe nach GEO-C16.

    Ohne ``umrechnung`` nur für geographische ``srs_id`` (4326, 4258), deren
    Koordinaten im GeoPackage ``(lon, lat)`` sind. Projizierte Daten (etwa
    EPSG:25832) brauchen eine Umrechnung ``(x, y) → (lon, lat)``, z. B.
    ``lambda x, y: utm_nach_geographisch_lonlat(x, y, ETRS89_UTM32N)``.
    """
    if umrechnung is None:
        if geometrie.srs_id not in GEOGRAPHISCHE_SRS_IDS:
            raise ProfilFehler(
                f"srs_id {geometrie.srs_id} ist nicht geographisch; "
                "Umrechnung (x, y) → (lon, lat) angeben."
            )
        return flaeche_aus_ringen(geometrie.polygone, strikt=strikt)
    umgerechnet = [
        [[umrechnung(x, y) for x, y in ring] for ring in polygon] for polygon in geometrie.polygone
    ]
    return flaeche_aus_ringen(umgerechnet, strikt=strikt)
