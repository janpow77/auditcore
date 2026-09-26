"""Punkte, Koordinatenreferenzsysteme und Achsenfolge.

Die Quellanwendungen mischen zwei Achsenfolgen: GeoJSON (RFC 7946) und die
Rechenfunktionen in ``audit_designer`` (``_haversine_distance_m``) führen
Länge vor Breite, ``osint`` (``haversine_km``) und ``flowsearch`` Breite vor
Länge; GML 3.2 liefert EPSG:4326 in der Behördenfolge Breite, Länge. Ein
:class:`Punkt` trägt deshalb benannte Felder und wird nur über Konstruktoren
mit ausdrücklicher Achsenfolge aus Zahlenpaaren gebildet.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from auditcore_common.numeric import require_finite

from .errors import KoordinatenFehler


class Achsenfolge(StrEnum):
    """Reihenfolge eines Zahlenpaares."""

    LON_LAT = "lon_lat"
    LAT_LON = "lat_lon"
    UNBEKANNT = "unbekannt"


def _endlich(wert: float, name: str) -> float:
    """:func:`auditcore_common.numeric.require_finite` mit den Meldungen des Pakets."""
    return require_finite(
        wert,
        not_number=lambda: KoordinatenFehler(f"{name} ist keine Zahl: {wert!r}"),
        not_finite=lambda: KoordinatenFehler(f"{name} ist nicht endlich: {wert!r}"),
    )


@dataclass(frozen=True)
class Punkt:
    """Geographische Koordinate in Grad (Breite ``lat``, Länge ``lon``).

    Das Bezugssystem steht nicht im Punkt; es ergibt sich aus der Quelle
    (in der Regel WGS 84 bzw. ETRS89, die in Europa um unter einen Meter
    voneinander abweichen). Ungültige Werte werden abgewiesen, nie geklemmt.
    """

    lat: float
    lon: float

    def __post_init__(self) -> None:
        lat = _endlich(self.lat, "Breite")
        lon = _endlich(self.lon, "Länge")
        if not -90.0 <= lat <= 90.0:
            raise KoordinatenFehler(f"Breite außerhalb von -90..90: {lat}")
        if not -180.0 <= lon <= 180.0:
            raise KoordinatenFehler(f"Länge außerhalb von -180..180: {lon}")
        object.__setattr__(self, "lat", lat)
        object.__setattr__(self, "lon", lon)

    @classmethod
    def aus_lonlat(cls, werte: Sequence[float]) -> Punkt:
        """Aus ``[lon, lat, …]`` (GeoJSON-Reihenfolge); weitere Werte (Höhe) werden ignoriert."""
        return cls.aus_folge(werte, Achsenfolge.LON_LAT)

    @classmethod
    def aus_latlon(cls, werte: Sequence[float]) -> Punkt:
        """Aus ``[lat, lon]`` (Behördenfolge EPSG:4326, GML 3.2)."""
        return cls.aus_folge(werte, Achsenfolge.LAT_LON)

    @classmethod
    def aus_folge(cls, werte: Sequence[float], achsenfolge: Achsenfolge) -> Punkt:
        """Aus einem Zahlenpaar in ausdrücklich genannter Achsenfolge."""
        if isinstance(werte, (str, bytes)) or len(werte) < 2:
            raise KoordinatenFehler(f"Zahlenpaar erwartet: {werte!r}")
        if achsenfolge is Achsenfolge.LON_LAT:
            return cls(lat=werte[1], lon=werte[0])
        if achsenfolge is Achsenfolge.LAT_LON:
            return cls(lat=werte[0], lon=werte[1])
        raise KoordinatenFehler("Achsenfolge unbekannt; kein Punkt ohne ausdrückliche Folge.")

    def als_lonlat(self) -> tuple[float, float]:
        """``(lon, lat)`` für GeoJSON."""
        return (self.lon, self.lat)

    def als_latlon(self) -> tuple[float, float]:
        """``(lat, lon)``."""
        return (self.lat, self.lon)


@dataclass(frozen=True)
class Koordinatenreferenzsystem:
    """Beschreibung eines Bezugssystems; die Bibliothek transformiert keine Datumsangaben."""

    kennung: str
    name: str
    achsenfolge: Achsenfolge
    einheit: str


#: WGS 84 geographisch; Achsenfolge der EPSG-Registrierung ist Breite, Länge.
EPSG_4326 = Koordinatenreferenzsystem("EPSG:4326", "WGS 84", Achsenfolge.LAT_LON, "Grad")
#: OGC CRS84 = WGS 84 in der Reihenfolge Länge, Breite (GeoJSON, RFC 7946).
OGC_CRS84 = Koordinatenreferenzsystem(
    "OGC:CRS84", "WGS 84 (Länge, Breite)", Achsenfolge.LON_LAT, "Grad"
)
#: ETRS89 geographisch (Bezugssystem der amtlichen deutschen Geobasisdaten).
EPSG_4258 = Koordinatenreferenzsystem("EPSG:4258", "ETRS89", Achsenfolge.LAT_LON, "Grad")
#: ETRS89 / UTM Zone 32N (Rechtswert, Hochwert in Metern), z. B. BKG VG2500.
EPSG_25832 = Koordinatenreferenzsystem(
    "EPSG:25832", "ETRS89 / UTM Zone 32N", Achsenfolge.UNBEKANNT, "Meter"
)


@dataclass(frozen=True)
class Bereich:
    """Achsparalleles Rechteck in Grad; dient nur Plausibilitäts- und Vorfilterzwecken."""

    sued: float
    west: float
    nord: float
    ost: float

    def enthaelt(self, lat: float, lon: float) -> bool:
        """Liegt ``(lat, lon)`` im Rechteck (Ränder eingeschlossen)?"""
        return self.sued <= lat <= self.nord and self.west <= lon <= self.ost


#: Bereich, an dem ``osint`` (``werkzeuge/betroffenheit.py:_achsen_drehen``) die
#: Achsenfolge deutscher GML-Antworten erkennt: Breite 47–56, Länge 5–16 Grad.
BEREICH_DEUTSCHLAND_OSINT = Bereich(sued=47.0, west=5.0, nord=56.0, ost=16.0)


def achsenfolge_erkennen(
    ringe: Iterable[Sequence[tuple[float, float]]],
    bereich: Bereich,
    *,
    ringe_max: int = 3,
    punkte_max: int = 20,
) -> Achsenfolge:
    """Achsenfolge von Zahlenpaaren anhand eines bekannten Gebiets bestimmen.

    Geprüft werden die ersten ``ringe_max`` Ringe mit je ``punkte_max``
    Paaren (wie im Original). Anders als ``_achsen_drehen`` entscheidet nicht
    das erste passende Paar: Widersprechen sich die Paare oder passt keines
    in den Bereich, ist das Ergebnis :attr:`Achsenfolge.UNBEKANNT` – der
    Aufrufer muss dann entscheiden, statt still „nicht drehen“ zu erhalten.
    """
    gesehen: set[Achsenfolge] = set()
    for nummer, ring in enumerate(ringe):
        if nummer >= ringe_max:
            break
        for x, y in list(ring)[:punkte_max]:
            als_latlon = bereich.enthaelt(x, y)
            als_lonlat = bereich.enthaelt(y, x)
            if als_latlon and not als_lonlat:
                gesehen.add(Achsenfolge.LAT_LON)
            elif als_lonlat and not als_latlon:
                gesehen.add(Achsenfolge.LON_LAT)
    if len(gesehen) == 1:
        return gesehen.pop()
    return Achsenfolge.UNBEKANNT
