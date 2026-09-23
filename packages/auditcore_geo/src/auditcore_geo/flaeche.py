"""Flächen aus GeoJSON: Punkt in Fläche mit Rand, Randabstand, Schwerpunkt.

Ringe werden als Folgen ``(lon, lat)`` in Grad geführt (GeoJSON-Reihenfolge).
Jedes Polygon besteht aus einem Außenring und beliebig vielen Löchern; ein
Multipolygon aus mehreren Polygonen. Die Lage eines Punktes ist dreiwertig
(:class:`Lage`): Das Strahlverfahren der Quellen ordnet Randpunkte je nach
Kantenrichtung mal innen, mal außen zu – hier wird der Rand ausdrücklich
erkannt und der Aufrufer entscheidet, wie er zählt.

Zusammengefallene Ringe (GEO-C16): Ein Ring, dessen Punkte alle gleich sind
oder auf einer Geraden liegen, hat keine Fläche – typisch nach dem Runden
kleiner Gebiete auf wenige Nachkommastellen. Er verwirft die Geometrie nicht
mehr (0.1.0: ``GeometrieFehler`` für die ganze Fläche), sondern wird als
:class:`EntarteterRing` geführt und in :attr:`Flaeche.hinweise` genannt:

- ein zusammengefallener **Außenring** bleibt als Punkt- bzw. Linienobjekt
  erhalten; es zählt der Abstand zu ihm (Rand, Randabstand, Umkreis); ein
  Punkt genau darauf liegt auf dem Rand; seine Löcher entfallen;
- ein zusammengefallenes **Loch** hat die Fläche 0 und nimmt der Teilfläche
  nichts weg; es entfällt (mit Hinweis);
- die übrigen, gültigen Teilflächen und Löcher bleiben unverändert Fläche.

Wer lieber scheitert, ruft die Leser mit ``strikt=True`` auf.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar

from .distanz import Kugelprofil, Treffer, abstand_zur_strecke_lokal_m, grosskreis_m
from .errors import GeoError, GeometrieFehler, ProfilFehler
from .gpkg import GpkgGeometrie
from .koordinaten import Punkt

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


def _ist_folge(wert: Any) -> bool:
    return isinstance(wert, Sequence) and not isinstance(wert, (str, bytes))


def _positionen(roh: Any, name: str) -> Ring:
    """Zahlenpaare eines Rings ohne wiederholten Schlusspunkt; unlesbar → Fehler."""
    if not _ist_folge(roh):
        raise GeometrieFehler(f"{name}: Punktliste erwartet.")
    punkte: list[tuple[float, float]] = []
    for position in roh:
        if not _ist_folge(position) or len(position) < 2:
            raise GeometrieFehler(f"{name}: Position {position!r} ist kein Zahlenpaar.")
        x, y = position[0], position[1]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (x, y)):
            raise GeometrieFehler(f"{name}: Position {position!r} ist kein Zahlenpaar.")
        if not (math.isfinite(x) and math.isfinite(y)):
            raise GeometrieFehler(f"{name}: Position {position!r} ist nicht endlich.")
        punkte.append((float(x), float(y)))
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


def flaeche_aus_ringen(polygone: Sequence[Any], *, strikt: bool = False) -> Flaeche:
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
            for i, art in enumerate(arten):
                if art is not None:
                    raise GeometrieFehler(
                        f"Polygon {nummer}, Ring {i}: Ring ist auf {art.value} "
                        f"zusammengefallen ({VERTRAG_ENTARTETE_RINGE}, strikt)."
                    )
        if arten[0] is not None:
            entartet.append(
                EntarteterRing(nummer, 0, arten[0], _ohne_wiederholung(ringe[0]), len(ringe) - 1)
            )
            continue
        loecher: list[Ring] = []
        for i in range(1, len(ringe)):
            art = arten[i]
            if art is None:
                loecher.append(ringe[i])
            else:
                entartet.append(EntarteterRing(nummer, i, art, _ohne_wiederholung(ringe[i])))
        echte.append(Polygon(ringe[0], tuple(loecher)))
    return Flaeche(tuple(echte), tuple(entartet))


def flaeche_aus_geojson(geometrie: Mapping[str, Any], *, strikt: bool = False) -> Flaeche:
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
    koordinaten: Any = geometrie.get("coordinates")
    roh_polygone: list[Any]
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


def _kanten(ring: Ring) -> list[Kante]:
    """Kanten des geschlossenen Rings; ein einzelner Punkt ergibt die Kante ``(p, p)``."""
    return [(ring[i - 1], ring[i]) for i in range(len(ring))]


def _am_rand(
    punkt: Punkt, kanten: list[Kante], rand_toleranz_m: float, profil: Kugelprofil | None
) -> bool:
    """Punkt exakt auf einer Kante oder – mit Toleranz – höchstens so weit entfernt."""
    x, y = punkt.lon, punkt.lat
    for a, b in kanten:
        if _auf_strecke(x, y, a, b):
            return True
        if (
            rand_toleranz_m > 0
            and profil is not None
            and abstand_zur_strecke_lokal_m(punkt, Punkt(a[1], a[0]), Punkt(b[1], b[0]), profil)
            <= rand_toleranz_m
        ):
            return True
    return False


def _am_flaechenrand(
    punkt: Punkt, flaeche: Flaeche, rand_toleranz_m: float, profil: Kugelprofil | None
) -> bool:
    x, y = punkt.lon, punkt.lat
    for polygon in flaeche.polygone:
        if rand_toleranz_m == 0:
            west, sued, ost, nord = polygon.rechteck()
            if not (west <= x <= ost and sued <= y <= nord):
                continue  # ein Randpunkt liegt stets im Hüllrechteck
        for ring in polygon.ringe():
            if _am_rand(punkt, _kanten(ring), rand_toleranz_m, profil):
                return True
    return False


def _objekt_am_rand(
    punkt: Punkt, flaeche: Flaeche, rand_toleranz_m: float, profil: Kugelprofil | None
) -> EntarteterRing | None:
    for objekt in flaeche.objekte_ohne_flaeche:
        if _am_rand(punkt, _kanten(objekt.punkte), rand_toleranz_m, profil):
            return objekt
    return None


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
    einer Kante als Rand – etwa für vereinfachte Umringe. Ein Punkt auf
    einem zusammengefallenen Außenring (Punkt/Linie, GEO-C16) liegt auf dem
    Rand, sofern er nicht in einer echten Teilfläche liegt.
    """
    if not math.isfinite(rand_toleranz_m) or rand_toleranz_m < 0:
        raise GeometrieFehler("rand_toleranz_m muss endlich und nicht negativ sein.")
    if rand_toleranz_m > 0 and profil is None:
        raise ProfilFehler("Eine Randtoleranz in Metern verlangt ein Kugelprofil.")
    if _am_flaechenrand(punkt, flaeche, rand_toleranz_m, profil):
        return Lage.RAND
    x, y = punkt.lon, punkt.lat
    for polygon in flaeche.polygone:
        west, sued, ost, nord = polygon.rechteck()
        if not (west <= x <= ost and sued <= y <= nord):
            continue
        if not _strahl(x, y, polygon.aussen):
            continue
        if any(_strahl(x, y, loch) for loch in polygon.loecher):
            continue
        return Lage.INNEN
    if _objekt_am_rand(punkt, flaeche, rand_toleranz_m, profil) is not None:
        return Lage.RAND
    return Lage.AUSSEN


def enthaelt(flaeche: Flaeche, punkt: Punkt, *, rand_gilt_als_innen: bool) -> bool:
    """Punkt in Fläche; wie der Rand zählt, muss der Aufrufer ausdrücklich sagen."""
    ergebnis = lage(punkt, flaeche)
    return ergebnis is Lage.INNEN or (ergebnis is Lage.RAND and rand_gilt_als_innen)


def _naechstes(
    punkt: Punkt, flaeche: Flaeche, profil: Kugelprofil
) -> tuple[float, EntarteterRing | None]:
    """Kleinster Kantenabstand und – falls maßgeblich – der zusammengefallene Ring."""
    bester = math.inf
    objekt: EntarteterRing | None = None
    for polygon in flaeche.polygone:
        for ring in polygon.ringe():
            for a, b in _kanten(ring):
                d = abstand_zur_strecke_lokal_m(punkt, Punkt(a[1], a[0]), Punkt(b[1], b[0]), profil)
                bester = min(bester, d)
    for entartet in flaeche.objekte_ohne_flaeche:
        for a, b in _kanten(entartet.punkte):
            d = abstand_zur_strecke_lokal_m(punkt, Punkt(a[1], a[0]), Punkt(b[1], b[0]), profil)
            if d < bester:
                bester, objekt = d, entartet
    return bester, objekt


def randabstand_m(punkt: Punkt, flaeche: Flaeche, profil: Kugelprofil) -> float:
    """Abstand zum nächsten Rand in Metern; 0 für Punkte innen oder auf dem Rand.

    Über alle Kanten aller Ringe (auch Löcher und aller Teile eines
    Multipolygons) und alle zusammengefallenen Außenringe (Punkt/Linie,
    GEO-C16) mit der lokalen Näherung :func:`abstand_zur_strecke_lokal_m`.
    """
    if lage(punkt, flaeche) is not Lage.AUSSEN:
        return 0.0
    return _naechstes(punkt, flaeche, profil)[0]


@dataclass(frozen=True)
class Randbefund:
    """Lage und Randabstand samt Hinweisen der Fläche.

    ``entarteter_ring`` ist gesetzt, wenn der Abstand bzw. die Randlage auf
    einen zusammengefallenen Außenring zurückgeht (GEO-C16); ``hinweise``
    sind die Hinweise der Fläche (:attr:`Flaeche.hinweise`).
    """

    lage: Lage
    abstand_m: float
    entarteter_ring: EntarteterRing | None
    hinweise: tuple[str, ...]


def randbefund(punkt: Punkt, flaeche: Flaeche, profil: Kugelprofil) -> Randbefund:
    """:func:`lage` und :func:`randabstand_m` in einem, mit Herkunft des Abstands."""
    ort = lage(punkt, flaeche)
    if ort is Lage.INNEN:
        return Randbefund(ort, 0.0, None, flaeche.hinweise)
    if ort is Lage.RAND:
        objekt = None
        if not _am_flaechenrand(punkt, flaeche, 0.0, None):
            objekt = _objekt_am_rand(punkt, flaeche, 0.0, None)
        return Randbefund(ort, 0.0, objekt, flaeche.hinweise)
    abstand, objekt = _naechstes(punkt, flaeche, profil)
    return Randbefund(ort, abstand, objekt, flaeche.hinweise)


def flaechen_im_umkreis(
    zentrum: Punkt,
    flaechen: Sequence[Flaeche],
    radius_m: float | None,
    profil: Kugelprofil,
) -> list[Treffer]:
    """Alle Flächen mit :func:`randabstand_m` bis einschließlich ``radius_m``.

    Sortiert nach (Abstand, Index) wie :func:`umkreis`; ``radius_m=None``
    liefert alle. Zusammengefallene Außenringe zählen mit ihrem Abstand
    (GEO-C16) – ein Gebiet, das nur noch aus einem Punkt besteht, fällt
    nicht heraus.
    """
    if radius_m is not None and (
        isinstance(radius_m, bool) or not math.isfinite(radius_m) or radius_m < 0
    ):
        raise GeoError(f"Radius muss endlich und nicht negativ sein: {radius_m!r}")
    treffer = []
    for i, flaeche in enumerate(flaechen):
        abstand = randabstand_m(zentrum, flaeche, profil)
        if radius_m is None or abstand <= radius_m:
            treffer.append(Treffer(i, abstand))
    return sorted(treffer, key=lambda t: (t.abstand_m, t.index))


def naechster_stuetzpunkt_m(
    punkt: Punkt, flaeche: Flaeche, profil: Kugelprofil, *, nur_aussenringe: bool
) -> float:
    """Großkreisabstand zum nächsten Stützpunkt (nicht zur Kante!) in Metern.

    Das ist das Maß von ``naechste_nuts3`` (nur Außenringe) und
    ``_distance_to_geometry_m`` (alle Ringe). Es überschätzt den Randabstand
    bei langen Kanten und gilt unabhängig davon, ob der Punkt innen liegt.
    Zusammengefallene Außenringe zählen mit ihren Stützpunkten.
    """
    bester = math.inf
    for polygon in flaeche.polygone:
        ringe = (polygon.aussen,) if nur_aussenringe else polygon.ringe()
        for ring in ringe:
            for x, y in ring:
                bester = min(bester, grosskreis_m(punkt, Punkt(y, x), profil))
    for objekt in flaeche.objekte_ohne_flaeche:
        for x, y in objekt.punkte:
            bester = min(bester, grosskreis_m(punkt, Punkt(y, x), profil))
    return bester


def _enden(punkte: Ring) -> tuple[tuple[float, float], tuple[float, float]]:
    """Die beiden äußersten Punkte einer (nahezu) kollinearen Punktfolge."""
    x0, y0 = punkte[0]
    a = max(punkte, key=lambda p: (p[0] - x0) ** 2 + (p[1] - y0) ** 2)
    b = max(punkte, key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
    return a, b


def _schwerpunkt_ohne_flaeche(objekte: tuple[EntarteterRing, ...]) -> Punkt:
    """Schwerpunkt der Objekte ohne Fläche: Linien längengewichtet, sonst Punktmittel.

    Wie bei einer gemischten Geometrie zählt die höchste Dimension: Gibt es
    Linien, bestimmen sie den Schwerpunkt, sonst das Mittel der Punkte.
    """
    linien = [_enden(o.punkte) for o in objekte if o.art is Entartung.LINIE]
    if linien:
        summe_l = summe_x = summe_y = 0.0
        for (x1, y1), (x2, y2) in linien:
            laenge = math.hypot(x2 - x1, y2 - y1)
            summe_l += laenge
            summe_x += laenge * (x1 + x2) / 2
            summe_y += laenge * (y1 + y2) / 2
        return Punkt(lat=summe_y / summe_l, lon=summe_x / summe_l)
    punkte = [o.punkte[0] for o in objekte]
    return Punkt(
        lat=sum(y for _, y in punkte) / len(punkte), lon=sum(x for x, _ in punkte) / len(punkte)
    )


def flaechenschwerpunkt(flaeche: Flaeche) -> Punkt:
    """Flächengewichteter Schwerpunkt, eben in Grad gerechnet (Löcher abgezogen).

    Für die Quellenfälle (Kreise, Schutzgebiete) eine brauchbare Näherung;
    der Schwerpunkt kann bei konkaven Flächen außerhalb liegen. Die Quellen
    nutzen stattdessen das Mittel der Stützpunkte (siehe ``legacy``).
    Zusammengefallene Ringe haben die Fläche 0 und zählen nur, wenn es keine
    echte Teilfläche gibt (GEO-C16): dann Linien längengewichtet, sonst das
    Mittel der Punkte.
    """
    if not flaeche.polygone:
        return _schwerpunkt_ohne_flaeche(flaeche.objekte_ohne_flaeche)
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
