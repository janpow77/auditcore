"""Flächen aus GeoJSON: Punkt in Fläche mit Rand, Randabstand, Schwerpunkt.

Ringe werden als Folgen ``(lon, lat)`` in Grad geführt (GeoJSON-Reihenfolge).
Jedes Polygon besteht aus einem Außenring und beliebig vielen Löchern; ein
Multipolygon aus mehreren Polygonen. Die Lage eines Punktes ist dreiwertig
(:class:`Lage`): Das Strahlverfahren der Quellen ordnet Randpunkte je nach
Kantenrichtung mal innen, mal außen zu – hier wird der Rand ausdrücklich
erkannt und der Aufrufer entscheidet, wie er zählt.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .distanz import Kugelprofil, abstand_zur_strecke_lokal_m, grosskreis_m
from .errors import GeometrieFehler, ProfilFehler
from .koordinaten import Punkt

Ring = tuple[tuple[float, float], ...]


class Lage(StrEnum):
    """Lage eines Punktes zu einer Fläche."""

    INNEN = "innen"
    AUSSEN = "aussen"
    RAND = "rand"


def _ring(roh: Any, name: str) -> Ring:
    if not isinstance(roh, Sequence) or isinstance(roh, (str, bytes)):
        raise GeometrieFehler(f"{name}: Punktliste erwartet.")
    punkte: list[tuple[float, float]] = []
    for position in roh:
        if (
            not isinstance(position, Sequence)
            or isinstance(position, (str, bytes))
            or len(position) < 2
        ):
            raise GeometrieFehler(f"{name}: Position {position!r} ist kein Zahlenpaar.")
        x, y = position[0], position[1]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (x, y)):
            raise GeometrieFehler(f"{name}: Position {position!r} ist kein Zahlenpaar.")
        if not (math.isfinite(x) and math.isfinite(y)):
            raise GeometrieFehler(f"{name}: Position {position!r} ist nicht endlich.")
        punkte.append((float(x), float(y)))
    if len(punkte) > 1 and punkte[0] == punkte[-1]:
        punkte.pop()
    if len(set(punkte)) < 3:
        raise GeometrieFehler(f"{name}: Ring mit weniger als drei verschiedenen Punkten.")
    return tuple(punkte)


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
    """Ein oder mehrere Polygone (GeoJSON ``Polygon`` oder ``MultiPolygon``)."""

    polygone: tuple[Polygon, ...]

    def __post_init__(self) -> None:
        if not self.polygone:
            raise GeometrieFehler("Fläche ohne Polygon.")


def flaeche_aus_geojson(geometrie: Mapping[str, Any]) -> Flaeche:
    """``Polygon``/``MultiPolygon`` in GeoJSON-Achsenfolge; alles andere ist ein Fehler.

    Anders als die Quellen (die unlesbare Ringe verwerfen oder für eine
    unbekannte Geometrie ``(0, 0)`` bzw. ``0.0`` liefern) wird eine
    unbrauchbare Geometrie nie still zu einem Ergebnis.
    """
    if not isinstance(geometrie, Mapping):
        raise GeometrieFehler("GeoJSON-Geometrie (Objekt) erwartet.")
    art = geometrie.get("type")
    koordinaten = geometrie.get("coordinates")
    if art == "Polygon":
        roh_polygone = [koordinaten]
    elif art == "MultiPolygon":
        if not isinstance(koordinaten, Sequence) or isinstance(koordinaten, (str, bytes)):
            raise GeometrieFehler("MultiPolygon ohne Koordinatenliste.")
        roh_polygone = list(koordinaten)
    else:
        raise GeometrieFehler(f"Nicht unterstützter Geometrietyp: {art!r}")
    polygone: list[Polygon] = []
    for nummer, roh in enumerate(roh_polygone):
        if not isinstance(roh, Sequence) or isinstance(roh, (str, bytes)) or not roh:
            raise GeometrieFehler(f"Polygon {nummer}: Ringliste fehlt.")
        ringe = [_ring(r, f"Polygon {nummer}, Ring {i}") for i, r in enumerate(roh)]
        polygone.append(Polygon(ringe[0], tuple(ringe[1:])))
    return Flaeche(tuple(polygone))


def _auf_strecke(x: float, y: float, a: tuple[float, float], b: tuple[float, float]) -> bool:
    (x1, y1), (x2, y2) = a, b
    if (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) != 0.0:
        return False
    return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)


def _strahl(x: float, y: float, ring: Ring) -> bool:
    """Strahlverfahren wie in den Quellen (``_punkt_in_ring``/``_point_in_ring``/``_im_ring``)."""
    innen = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            innen = not innen
        j = i
    return innen


def _kanten(ring: Ring) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    return [(ring[i - 1], ring[i]) for i in range(len(ring))]


def lage(
    punkt: Punkt,
    flaeche: Flaeche,
    *,
    rand_toleranz_m: float = 0.0,
    profil: Kugelprofil | None = None,
) -> Lage:
    """Lage des Punktes: innen, außen oder auf dem Rand.

    Mit ``rand_toleranz_m == 0`` gilt nur ein exakt auf einer Kante oder
    Ecke liegender Punkt als Rand. Mit positiver Toleranz (Meter, lokale
    Näherung, benötigt ``profil``) zählt jeder Punkt in diesem Abstand zu
    einer Kante als Rand – etwa für vereinfachte Umringe.
    """
    if not math.isfinite(rand_toleranz_m) or rand_toleranz_m < 0:
        raise GeometrieFehler("rand_toleranz_m muss endlich und nicht negativ sein.")
    if rand_toleranz_m > 0 and profil is None:
        raise ProfilFehler("Eine Randtoleranz in Metern verlangt ein Kugelprofil.")
    x, y = punkt.lon, punkt.lat
    for polygon in flaeche.polygone:
        if rand_toleranz_m == 0:
            west, sued, ost, nord = polygon.rechteck()
            if not (west <= x <= ost and sued <= y <= nord):
                continue  # ein Randpunkt liegt stets im Hüllrechteck
        for ring in polygon.ringe():
            for a, b in _kanten(ring):
                if _auf_strecke(x, y, a, b):
                    return Lage.RAND
                if (
                    rand_toleranz_m > 0
                    and profil is not None
                    and abstand_zur_strecke_lokal_m(
                        punkt, Punkt(a[1], a[0]), Punkt(b[1], b[0]), profil
                    )
                    <= rand_toleranz_m
                ):
                    return Lage.RAND
    for polygon in flaeche.polygone:
        west, sued, ost, nord = polygon.rechteck()
        if not (west <= x <= ost and sued <= y <= nord):
            continue
        if not _strahl(x, y, polygon.aussen):
            continue
        if any(_strahl(x, y, loch) for loch in polygon.loecher):
            continue
        return Lage.INNEN
    return Lage.AUSSEN


def enthaelt(flaeche: Flaeche, punkt: Punkt, *, rand_gilt_als_innen: bool) -> bool:
    """Punkt in Fläche; wie der Rand zählt, muss der Aufrufer ausdrücklich sagen."""
    ergebnis = lage(punkt, flaeche)
    return ergebnis is Lage.INNEN or (ergebnis is Lage.RAND and rand_gilt_als_innen)


def randabstand_m(punkt: Punkt, flaeche: Flaeche, profil: Kugelprofil) -> float:
    """Abstand zum nächsten Rand in Metern; 0 für Punkte innen oder auf dem Rand.

    Über alle Kanten aller Ringe (auch Löcher und aller Teile eines
    Multipolygons) mit der lokalen Näherung :func:`abstand_zur_strecke_lokal_m`.
    """
    if lage(punkt, flaeche) is not Lage.AUSSEN:
        return 0.0
    bester = math.inf
    for polygon in flaeche.polygone:
        for ring in polygon.ringe():
            for a, b in _kanten(ring):
                d = abstand_zur_strecke_lokal_m(punkt, Punkt(a[1], a[0]), Punkt(b[1], b[0]), profil)
                bester = min(bester, d)
    return bester


def naechster_stuetzpunkt_m(
    punkt: Punkt, flaeche: Flaeche, profil: Kugelprofil, *, nur_aussenringe: bool
) -> float:
    """Großkreisabstand zum nächsten Stützpunkt (nicht zur Kante!) in Metern.

    Das ist das Maß von ``naechste_nuts3`` (nur Außenringe) und
    ``_distance_to_geometry_m`` (alle Ringe). Es überschätzt den Randabstand
    bei langen Kanten und gilt unabhängig davon, ob der Punkt innen liegt.
    """
    bester = math.inf
    for polygon in flaeche.polygone:
        ringe = (polygon.aussen,) if nur_aussenringe else polygon.ringe()
        for ring in ringe:
            for x, y in ring:
                bester = min(bester, grosskreis_m(punkt, Punkt(y, x), profil))
    return bester


def flaechenschwerpunkt(flaeche: Flaeche) -> Punkt:
    """Flächengewichteter Schwerpunkt, eben in Grad gerechnet (Löcher abgezogen).

    Für die Quellenfälle (Kreise, Schutzgebiete) eine brauchbare Näherung;
    der Schwerpunkt kann bei konkaven Flächen außerhalb liegen. Die Quellen
    nutzen stattdessen das Mittel der Stützpunkte (siehe ``legacy``).
    """
    # Um den ersten Stützpunkt verschoben, damit große Gradwerte nicht auslöschen.
    x0, y0 = flaeche.polygone[0].aussen[0]
    summe_a = summe_x = summe_y = 0.0
    for polygon in flaeche.polygone:
        for nummer, ring in enumerate(polygon.ringe()):
            a = cx = cy = 0.0
            verschoben = tuple((x - x0, y - y0) for x, y in ring)
            for (x1, y1), (x2, y2) in _kanten(verschoben):
                kreuz = x1 * y2 - x2 * y1
                a += kreuz
                cx += (x1 + x2) * kreuz
                cy += (y1 + y2) * kreuz
            flaeche_ring = abs(a) / 2
            if flaeche_ring == 0:
                continue
            vorzeichen = 1.0 if nummer == 0 else -1.0
            gx, gy = cx / (3 * a), cy / (3 * a)
            summe_a += vorzeichen * flaeche_ring
            summe_x += vorzeichen * flaeche_ring * gx
            summe_y += vorzeichen * flaeche_ring * gy
    if summe_a <= 0:
        raise GeometrieFehler("Fläche ohne positiven Inhalt; kein Schwerpunkt.")
    return Punkt(lat=y0 + summe_y / summe_a, lon=x0 + summe_x / summe_a)
