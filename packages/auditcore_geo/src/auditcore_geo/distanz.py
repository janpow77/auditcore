"""Entfernungen auf der Kugel mit ausdrücklichem Erdmodell.

Die Quellanwendungen rechnen dieselbe Haversine-Formel mit zwei Radien
(6 371 008,8 m und 6 371 000 m), in zwei Einheiten (km, m) und zwei
Achsenfolgen. Die Varianten bleiben als benannte :class:`Kugelprofil`
erhalten; keine Funktion hat einen stillen Standardradius.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .errors import GeoError, ProfilFehler
from .koordinaten import Punkt


@dataclass(frozen=True)
class Kugelprofil:
    """Kugelförmiges Erdmodell mit Radius in Metern und Herkunft der Variante."""

    profil_id: str
    radius_m: float
    beschreibung: str
    quellen: tuple[str, ...]

    def __post_init__(self) -> None:
        if not (math.isfinite(self.radius_m) and self.radius_m > 0):
            raise ProfilFehler(f"Radius muss positiv und endlich sein: {self.radius_m}")


#: Mittlerer Erdradius R1 = (2a + b) / 3 des GRS80/WGS 84 (6 371 008,8 m).
KUGEL_MITTLERER_RADIUS = Kugelprofil(
    "kugel.r1_6371008_8m",
    6_371_008.8,
    "Mittlerer Erdradius R1 des Ellipsoids GRS80/WGS 84",
    (
        "janpow77/osint ortsdienst/dienst.py:ERDRADIUS_KM (6371.0088 km)",
        "janpow77/audit_designer backend/app/api/vpai_notebook/gis/_common.py:"
        "_haversine_distance_m (6371008.8 m)",
    ),
)
#: Gerundeter Radius 6 371 000 m.
KUGEL_6371_KM = Kugelprofil(
    "kugel.6371000m",
    6_371_000.0,
    "Gerundeter Erdradius 6371 km",
    (
        "janpow77/audit_designer backend/app/core/shared/research/register/geocoding.py:"
        "_entfernung_km (6371.0 km)",
        "janpow77/audit_designer backend/app/modules/vp_ai/services/company/"
        "company_records.py:_haversine_m (6371000.0 m)",
        "janpow77/flowsearch backend/app/api/eu_beneficiaries.py:calculate_distance (6371 km)",
        "janpow77/flowsearch backend/app/services/natura2000_service.py:"
        "_calculate_distance (6371000 m)",
    ),
)

#: Empfohlenes Profil für neue gemeinsame Bestände (Entscheidung vom 23.09.2026,
#: vom Nutzer delegiert). Keine Funktion verwendet es still; es wird ausdrücklich
#: übergeben. ``KUGEL_6371_KM`` bleibt für Replay und Altbestände.
EMPFOHLENES_ERDMODELL = KUGEL_MITTLERER_RADIUS

KUGELPROFILE: dict[str, Kugelprofil] = {
    p.profil_id: p for p in (KUGEL_MITTLERER_RADIUS, KUGEL_6371_KM)
}


def kugelprofil(profil_id: str) -> Kugelprofil:
    """Profil nach Kennung oder :class:`ProfilFehler`."""
    try:
        return KUGELPROFILE[profil_id]
    except KeyError as exc:
        raise ProfilFehler(f"Unbekanntes Kugelprofil: {profil_id!r}") from exc


def grosskreis_m(a: Punkt, b: Punkt, profil: Kugelprofil) -> float:
    """Großkreisentfernung in Metern (Haversine, numerisch geklemmt).

    Die Klemmung ``min(1, √h)`` verhindert den Wertebereichsfehler von
    ``asin`` bei nahezu antipodalen Punkten, den ungeklemmte Varianten der
    Quellen auslösen können.
    """
    phi1, phi2 = math.radians(a.lat), math.radians(b.lat)
    dphi = phi2 - phi1
    dlam = math.radians(b.lon - a.lon)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * profil.radius_m * math.asin(min(1.0, math.sqrt(h)))


def grosskreis_km(a: Punkt, b: Punkt, profil: Kugelprofil) -> float:
    """Großkreisentfernung in Kilometern."""
    return grosskreis_m(a, b, profil) / 1000.0


def abstand_zur_strecke_lokal_m(p: Punkt, a: Punkt, b: Punkt, profil: Kugelprofil) -> float:
    """Kürzester Abstand von ``p`` zur Strecke ``a``–``b`` in Metern.

    Näherung wie in ``audit_designer`` (``_point_segment_distance_m``):
    lokale abstandstreue Zylinderprojektion um ``p``. Für Strecken bis in den
    Bereich weniger Kilometer genau genug; keine Geodäsie auf dem Ellipsoid.
    """
    breite0 = math.cos(math.radians(p.lat))

    def xy(q: Punkt) -> tuple[float, float]:
        """Lokale ebene Koordinaten in Metern um ``p``."""
        return (
            math.radians(q.lon - p.lon) * profil.radius_m * breite0,
            math.radians(q.lat - p.lat) * profil.radius_m,
        )

    x1, y1 = xy(a)
    x2, y2 = xy(b)
    vx, vy = x2 - x1, y2 - y1
    laenge2 = vx * vx + vy * vy
    if laenge2 <= 1e-12:
        return math.hypot(x1, y1)
    t = max(0.0, min(1.0, (-x1 * vx - y1 * vy) / laenge2))
    return math.hypot(x1 + t * vx, y1 + t * vy)


@dataclass(frozen=True)
class Treffer:
    """Ein Punkt im Umkreis: Index in der Eingabefolge und Entfernung in Metern."""

    index: int
    abstand_m: float


def _laengendifferenz(a: float, b: float) -> float:
    """Betrag der Längendifferenz in Grad, über die Datumsgrenze hinweg (0..180)."""
    return abs((b - a + 180.0) % 360.0 - 180.0)


def umkreis(
    zentrum: Punkt,
    punkte: Sequence[Punkt],
    radius_m: float | None,
    profil: Kugelprofil,
) -> list[Treffer]:
    """Alle Punkte bis einschließlich ``radius_m``, nach (Entfernung, Index) sortiert.

    ``radius_m=None`` liefert alle Punkte nach Entfernung (wie ``km=None`` im
    Ortsdienst). Der Rechteckvorfilter ist auf der Kugel exakt (größte
    Längenausdehnung ``asin(sin θ / cos φ)``), berücksichtigt Pole und
    Datumsgrenze und verwirft deshalb keinen Punkt im Umkreis.
    """
    if radius_m is None:
        treffer = [Treffer(i, grosskreis_m(zentrum, p, profil)) for i, p in enumerate(punkte)]
        return sorted(treffer, key=lambda t: (t.abstand_m, t.index))
    if isinstance(radius_m, bool) or not math.isfinite(radius_m) or radius_m < 0:
        raise GeoError(f"Radius muss endlich und nicht negativ sein: {radius_m!r}")
    theta = radius_m / profil.radius_m
    dlat = math.degrees(theta) + 1e-9
    phi = math.radians(zentrum.lat)
    if theta >= math.pi or abs(zentrum.lat) + math.degrees(theta) >= 90.0:
        dlon: float | None = None
    else:
        dlon = math.degrees(math.asin(min(1.0, math.sin(theta) / math.cos(phi)))) + 1e-9
    ergebnis: list[Treffer] = []
    for i, p in enumerate(punkte):
        if abs(p.lat - zentrum.lat) > dlat:
            continue
        if dlon is not None and _laengendifferenz(zentrum.lon, p.lon) > dlon:
            continue
        abstand = grosskreis_m(zentrum, p, profil)
        if abstand <= radius_m:
            ergebnis.append(Treffer(i, abstand))
    ergebnis.sort(key=lambda t: (t.abstand_m, t.index))
    return ergebnis
