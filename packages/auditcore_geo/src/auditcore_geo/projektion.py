"""Transversale Mercatorprojektion (UTM) nach Krüger, Reihe bis n³.

Die Rückrechnung ist ausdrucksgleich mit ``osint``
``werkzeuge/bundeslaender_holen.py:utm_nach_wgs84`` (Zone 32, GRS80) und
liefert dort bitgleiche Werte; sie ist hier um Zone, Halbkugel und
Ellipsoid parametrisiert und um die Hinrechnung ergänzt. Es findet **keine
Datumstransformation** statt: Aus ETRS89/UTM (GRS80) entstehen ETRS89-
Koordinaten. Dass diese in Europa um unter einen Meter von WGS 84
abweichen, ist eine fachliche Annahme des Aufrufers, keine Umrechnung.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import ProfilFehler
from .koordinaten import Punkt


@dataclass(frozen=True)
class Ellipsoid:
    """Rotationsellipsoid mit großer Halbachse ``a`` (m) und Abplattung ``f``."""

    name: str
    a: float
    f: float


#: GRS80 (ETRS89); Wert der Quelle ``osint``.
GRS80 = Ellipsoid("GRS80", 6_378_137.0, 1 / 298.257222101)
#: WGS 84.
WGS84 = Ellipsoid("WGS 84", 6_378_137.0, 1 / 298.257223563)


@dataclass(frozen=True)
class UtmZone:
    """UTM-Zone (1–60), Halbkugel und Ellipsoid; Maßstab 0,9996, Rechtswert-Offset 500 km."""

    zone: int
    nordhalbkugel: bool
    ellipsoid: Ellipsoid

    def __post_init__(self) -> None:
        if (
            isinstance(self.zone, bool)
            or not isinstance(self.zone, int)
            or not 1 <= self.zone <= 60
        ):
            raise ProfilFehler(f"UTM-Zone muss 1..60 sein: {self.zone!r}")

    @property
    def mittelmeridian_grad(self) -> float:
        """Länge des Mittelmeridians in Grad."""
        return float(self.zone * 6 - 183)


#: ETRS89 / UTM Zone 32N (EPSG:25832).
ETRS89_UTM32N = UtmZone(32, True, GRS80)

K0 = 0.9996
E0 = 500_000.0
N0_SUED = 10_000_000.0


@dataclass(frozen=True)
class _Reihe:
    a_rect: float
    alpha: tuple[float, float, float]
    beta: tuple[float, float, float]
    delta: tuple[float, float, float]
    e: float


def _reihe(ellipsoid: Ellipsoid) -> _Reihe:
    f = ellipsoid.f
    n = f / (2 - f)
    a_rect = ellipsoid.a / (1 + n) * (1 + n**2 / 4 + n**4 / 64)
    alpha = (
        n / 2 - 2 * n**2 / 3 + 5 * n**3 / 16,
        13 * n**2 / 48 - 3 * n**3 / 5,
        61 * n**3 / 240,
    )
    beta = (
        n / 2 - 2 * n**2 / 3 + 37 * n**3 / 96,
        n**2 / 48 + n**3 / 15,
        17 * n**3 / 480,
    )
    delta = (
        2 * n - 2 * n**2 / 3 - 2 * n**3,
        7 * n**2 / 3 - 8 * n**3 / 5,
        56 * n**3 / 15,
    )
    return _Reihe(a_rect, alpha, beta, delta, math.sqrt(f * (2 - f)))


def utm_nach_geographisch_lonlat(ost: float, nord: float, zone: UtmZone) -> tuple[float, float]:
    """``(lon, lat)`` in Grad aus Rechts-/Hochwert in Metern (Achsenfolge der Quelle)."""
    reihe = _reihe(zone.ellipsoid)
    n0 = 0.0 if zone.nordhalbkugel else N0_SUED
    lambda0 = math.radians(zone.mittelmeridian_grad)
    xi = (nord - n0) / (K0 * reihe.a_rect)
    eta = (ost - E0) / (K0 * reihe.a_rect)
    xi_s = xi - sum(
        b * math.sin(2 * j * xi) * math.cosh(2 * j * eta) for j, b in enumerate(reihe.beta, 1)
    )
    eta_s = eta - sum(
        b * math.cos(2 * j * xi) * math.sinh(2 * j * eta) for j, b in enumerate(reihe.beta, 1)
    )
    chi = math.asin(math.sin(xi_s) / math.cosh(eta_s))
    phi = chi + sum(d * math.sin(2 * j * chi) for j, d in enumerate(reihe.delta, 1))
    lam = lambda0 + math.atan2(math.sinh(eta_s), math.cos(xi_s))
    return math.degrees(lam), math.degrees(phi)


def utm_nach_geographisch(ost: float, nord: float, zone: UtmZone) -> Punkt:
    """Geographischer :class:`Punkt` aus UTM; Länge auf -180..180 normiert."""
    for wert in (ost, nord):
        if isinstance(wert, bool) or not math.isfinite(wert):
            raise ProfilFehler(f"UTM-Koordinate nicht endlich: {wert!r}")
    lon, lat = utm_nach_geographisch_lonlat(ost, nord, zone)
    if not -180.0 <= lon <= 180.0:
        lon = (lon + 180.0) % 360.0 - 180.0
    return Punkt(lat=lat, lon=lon)


def geographisch_nach_utm(punkt: Punkt, zone: UtmZone) -> tuple[float, float]:
    """``(ost, nord)`` in Metern; Hinrechnung nach Krüger (n³)."""
    reihe = _reihe(zone.ellipsoid)
    phi = math.radians(punkt.lat)
    lam = math.radians(punkt.lon - zone.mittelmeridian_grad)
    lam = (lam + math.pi) % (2 * math.pi) - math.pi
    e = reihe.e
    t = math.sinh(math.atanh(math.sin(phi)) - e * math.atanh(e * math.sin(phi)))
    xi_s = math.atan2(t, math.cos(lam))
    eta_s = math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    ost = E0 + K0 * reihe.a_rect * (
        eta_s
        + sum(
            a * math.cos(2 * j * xi_s) * math.sinh(2 * j * eta_s)
            for j, a in enumerate(reihe.alpha, 1)
        )
    )
    nord = (
        K0
        * reihe.a_rect
        * (
            xi_s
            + sum(
                a * math.sin(2 * j * xi_s) * math.cosh(2 * j * eta_s)
                for j, a in enumerate(reihe.alpha, 1)
            )
        )
    )
    if not zone.nordhalbkugel:
        nord += N0_SUED
    return ost, nord
