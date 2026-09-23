"""Verhaltensgleiche Nachbildungen der Quellfunktionen (für Umstellung und Nachweis).

Jede Funktion reproduziert das in ``tests/fixtures/legacy_observed.json``
aufgezeichnete Verhalten des Originals exakt – einschließlich der dort
dokumentierten Mängel (GEO-C01 bis GEO-C12 in ``docs/behavior-changes.md``).
Neue Aufrufer verwenden die Funktionen der übrigen Module.
"""

from __future__ import annotations

import io
import math
import struct
from collections.abc import Mapping, Sequence
from typing import Any

from .projektion import ETRS89_UTM32N, utm_nach_geographisch_lonlat
from .vereinfachung import _douglas_peucker, _ring_vereinfachen

# ─────────────────────────────── osint@d361ddb ortsdienst/dienst.py

OSINT_ERDRADIUS_KM = 6371.0088


def osint_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """``haversine_km`` (Breite vor Länge, km, Radius 6371,0088 km)."""
    p = math.pi / 180
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    )
    return 2 * OSINT_ERDRADIUS_KM * math.asin(math.sqrt(min(1.0, a)))


def osint_umkreis(
    lat: float,
    lon: float,
    km: float | None,
    lats: Sequence[float],
    lons: Sequence[float],
) -> list[tuple[float, int]]:
    """``Bestand.umkreis`` ohne Fondsfilter: ``[(entfernung_km, index)]`` sortiert."""
    alle: list[tuple[float, int]] = []
    if km is None:
        for i, (la, lo) in enumerate(zip(lats, lons, strict=True)):
            alle.append((osint_haversine_km(lat, lon, la, lo), i))
    else:
        dlat = km / 111.0 + 1e-9
        dlon = km / (111.0 * max(0.05, math.cos(lat * math.pi / 180))) + 1e-9
        for i, (la, lo) in enumerate(zip(lats, lons, strict=True)):
            if abs(la - lat) > dlat or abs(lo - lon) > dlon:
                continue
            e = osint_haversine_km(lat, lon, la, lo)
            if e <= km:
                alle.append((e, i))
    alle.sort()
    return alle


# ─────────────────────────────── osint@d361ddb werkzeuge/betroffenheit.py


def osint_achsen_drehen(ringe: Sequence[Sequence[tuple[float, float]]]) -> bool:
    """``_achsen_drehen``: erstes passendes Paar entscheidet; unentscheidbar → ``False``."""
    for ring in ringe[:3]:
        for x, y in ring[:20]:
            if 47 <= x <= 56 and 5 <= y <= 16:
                return True
            if 47 <= y <= 56 and 5 <= x <= 16:
                return False
    return False


def osint_im_ring(lon: float, lat: float, ring: Sequence[tuple[float, float]]) -> bool:
    """``_im_ring`` (Strahlverfahren, ein Ring)."""
    drin = False
    j = len(ring) - 1
    for i, (x1, y1) in enumerate(ring):
        x2, y2 = ring[j]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            drin = not drin
        j = i
    return drin


# ─────────────────────────────── osint@d361ddb werkzeuge/bundeslaender_holen.py

OSINT_TOLERANZ_GRAD = 0.0025
OSINT_STELLEN = 4


def osint_utm_nach_wgs84(ost: float, nord: float) -> tuple[float, float]:
    """``utm_nach_wgs84``: ``(lon, lat)`` aus ETRS89/UTM 32N."""
    return utm_nach_geographisch_lonlat(ost, nord, ETRS89_UTM32N)


def osint_wkb_polygone(blob: bytes) -> list[list[list[tuple[float, float]]]]:
    """``wkb_polygone`` einschließlich seiner Nachsicht (Typ ``& 0xFF``, keine Teiltypprüfung)."""
    if blob[:2] != b"GP":
        raise ValueError("kein GeoPackage-Blob")
    flags = blob[3]
    huelle = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
    f = io.BytesIO(blob[8 + huelle :])

    def lesen() -> str:
        """Bytefolge des Originals (1 = little endian)."""
        return "<" if f.read(1)[0] == 1 else ">"

    def polygon(bo: str) -> list[list[tuple[float, float]]]:
        """Polygon wie im Original, ohne Längenprüfung."""
        (n_ringe,) = struct.unpack(bo + "I", f.read(4))
        ringe = []
        for _ in range(n_ringe):
            (n,) = struct.unpack(bo + "I", f.read(4))
            werte = struct.unpack(bo + f"{2 * n}d", f.read(16 * n))
            ringe.append([(werte[i], werte[i + 1]) for i in range(0, len(werte), 2)])
        return ringe

    bo = lesen()
    (typ,) = struct.unpack(bo + "I", f.read(4))
    typ &= 0xFF
    if typ == 3:
        return [polygon(bo)]
    if typ == 6:
        (n,) = struct.unpack(bo + "I", f.read(4))
        polys = []
        for _ in range(n):
            bo2 = lesen()
            struct.unpack(bo2 + "I", f.read(4))
            polys.append(polygon(bo2))
        return polys
    raise ValueError(f"WKB-Typ {typ} nicht vorgesehen")


def osint_douglas_peucker(
    punkte: Sequence[tuple[float, float]], toleranz: float
) -> list[tuple[float, float]]:
    """``douglas_peucker`` (ergebnisgleich, ohne Rekursion; negative Toleranz behält alles)."""
    return _douglas_peucker(punkte, toleranz)


def osint_ring_vereinfachen(
    ring: Sequence[tuple[float, float]], toleranz: float
) -> list[list[float]] | None:
    """``ring_vereinfachen`` mit ``STELLEN = 4``."""
    return _ring_vereinfachen(ring, toleranz, OSINT_STELLEN)


# ─────────────── audit_designer@1254591 backend/app/api/vpai_notebook/gis/_common.py


def _designer_ringe(geometry: Mapping[str, Any]) -> list[list[tuple[float, float]]]:
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")
    rings: list[list[tuple[float, float]]] = []
    polys: list[Any] = []
    if gtype == "Polygon" and isinstance(coords, list):
        polys = [coords]
    elif gtype == "MultiPolygon" and isinstance(coords, list):
        polys = [p for p in coords if isinstance(p, list)]
    for poly in polys:
        for ring in poly:
            if isinstance(ring, list):
                rings.append(
                    [
                        (float(pt[0]), float(pt[1]))
                        for pt in ring
                        if isinstance(pt, list) and len(pt) >= 2
                    ]
                )
    return [r for r in rings if len(r) >= 3]


def _designer_im_ring(lon: float, lat: float, ring: Sequence[tuple[float, float]]) -> bool:
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        crosses = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if crosses:
            inside = not inside
        j = i
    return inside


def designer_gis_punkt_in_geometrie(lon: float, lat: float, geometry: Mapping[str, Any]) -> bool:
    """``_point_in_geometry``: erster Ring außen, **alle weiteren Ringe als Löcher**."""
    rings = _designer_ringe(geometry)
    if not rings:
        return False
    if not _designer_im_ring(lon, lat, rings[0]):
        return False
    return all(not _designer_im_ring(lon, lat, hole) for hole in rings[1:])


def designer_gis_schwerpunkt(geometry: Mapping[str, Any]) -> tuple[float, float] | None:
    """``_geometry_centroid``: Mittel aller Stützpunkte aller Ringe (inkl. Schlusspunkte)."""
    punkte = [p for ring in _designer_ringe(geometry) for p in ring]
    if not punkte:
        return None
    return (sum(p[0] for p in punkte) / len(punkte), sum(p[1] for p in punkte) / len(punkte))


def designer_gis_haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """``_haversine_distance_m`` (**Länge vor Breite**, m, Radius 6 371 008,8 m)."""
    r = 6371008.8
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(1e-15, 1.0 - a)))
    return r * c


def designer_gis_strecke_m(
    lon: float, lat: float, lon1: float, lat1: float, lon2: float, lat2: float
) -> float:
    """``_point_segment_distance_m`` (lokale Zylinderprojektion um den Punkt)."""
    r = 6371008.8
    lat0 = math.radians(lat)

    def _xy(lon_v: float, lat_v: float) -> tuple[float, float]:
        return (math.radians(lon_v - lon) * r * math.cos(lat0), math.radians(lat_v - lat) * r)

    x1, y1 = _xy(lon1, lat1)
    x2, y2 = _xy(lon2, lat2)
    vx, vy = x2 - x1, y2 - y1
    wx, wy = -x1, -y1
    seg_len2 = vx * vx + vy * vy
    if seg_len2 <= 1e-12:
        return math.hypot(x1, y1)
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / seg_len2))
    return math.hypot(x1 + t * vx, y1 + t * vy)


def designer_gis_randabstand_m(lon: float, lat: float, geometry: Mapping[str, Any]) -> float | None:
    """``_geometry_edge_distance_m``: 0 innen (nach ``_point_in_geometry``), sonst Kantenminimum."""
    if designer_gis_punkt_in_geometrie(lon, lat, geometry):
        return 0.0
    rings = _designer_ringe(geometry)
    if not rings:
        return None
    best: float | None = None
    for ring in rings:
        if len(ring) < 2:
            continue
        for idx in range(len(ring)):
            x1, y1 = ring[idx]
            x2, y2 = ring[(idx + 1) % len(ring)]
            d = designer_gis_strecke_m(lon, lat, x1, y1, x2, y2)
            if best is None or d < best:
                best = d
    return best


# ─────── audit_designer@1254591 backend/app/core/shared/research/register/geocoding.py


def designer_register_entfernung_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """``_entfernung_km`` (Breite vor Länge, km, Radius 6371,0 km, ungeklemmt)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _register_im_ring(lon: float, lat: float, ring: Sequence[tuple[float, float]]) -> bool:
    innen = False
    anzahl = len(ring)
    j = anzahl - 1
    for i in range(anzahl):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat):
            schnitt = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < schnitt:
                innen = not innen
        j = i
    return innen


def designer_register_punkt_in_gebiet(
    lat: float, lon: float, flaechen: Sequence[Sequence[Sequence[tuple[float, float]]]]
) -> bool:
    """``_punkt_in_gebiet`` ohne Hüllrechteck: je Fläche Außenring, weitere Ringe als Löcher."""
    for flaeche in flaechen:
        if not _register_im_ring(lon, lat, flaeche[0]):
            continue
        if any(_register_im_ring(lon, lat, loch) for loch in flaeche[1:]):
            continue
        return True
    return False


def designer_register_naechster_stuetzpunkt_km(
    lat: float,
    lon: float,
    flaechen: Sequence[Sequence[Sequence[tuple[float, float]]]],
    toleranz_km: float = 5.0,
) -> float | None:
    """Abstandsmaß aus ``naechste_nuts3`` für **ein** Gebiet: Hüllrechteck-Vorfilter
    (``toleranz_km / 111`` Grad, in der Länge doppelt), dann nächster Stützpunkt
    der Außenringe in km."""
    punkte = [p for flaeche in flaechen for ring in flaeche for p in ring]
    rand = toleranz_km / 111.0
    if not (
        min(p[1] for p in punkte) - rand <= lat <= max(p[1] for p in punkte) + rand
        and min(p[0] for p in punkte) - 2 * rand <= lon <= max(p[0] for p in punkte) + 2 * rand
    ):
        return None
    beste: float | None = None
    for flaeche in flaechen:
        for punkt in flaeche[0]:
            abstand = designer_register_entfernung_km(lat, lon, punkt[1], punkt[0])
            if beste is None or abstand < beste:
                beste = abstand
    return beste


# ─── audit_designer@1254591 backend/app/modules/vp_ai/services/company/company_records.py


def designer_company_haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """``_haversine_m`` (Breite vor Länge, m, Radius 6 371 000 m, geklemmt)."""
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def designer_company_abstand_zur_geometrie_m(lat: float, lng: float, geometry: Any) -> float:
    """``_distance_to_geometry_m``: nächster Stützpunkt, gerundet auf 0,1 m; ungültig → 0.0."""
    if not isinstance(geometry, dict):
        return 0.0
    coords = geometry.get("coordinates")
    if not coords:
        return 0.0

    def iter_points(obj: Any) -> Any:
        """Alle Zahlenpaare als (Breite, Länge), rekursiv."""
        if isinstance(obj, (list, tuple)):
            if (
                len(obj) >= 2
                and isinstance(obj[0], (int, float))
                and isinstance(obj[1], (int, float))
            ):
                yield float(obj[1]), float(obj[0])
            else:
                for x in obj:
                    yield from iter_points(x)

    points = list(iter_points(coords))
    if not points:
        return 0.0
    min_d = min(designer_company_haversine_m(lat, lng, p_lat, p_lon) for p_lat, p_lon in points)
    return round(float(min_d), 1)


# ─────────────────────────────── flowsearch@10cb2a3 backend/app


def flowsearch_calculate_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """``api/eu_beneficiaries.py:calculate_distance`` (km, Radius 6371, atan2)."""
    r = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def flowsearch_natura_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """``services/natura2000_service.py:_calculate_distance`` (m, Radius 6 371 000, ungeklemmt)."""
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return c * 6371000


def flowsearch_geometriezentrum(geometry: Mapping[str, Any]) -> tuple[float, float]:
    """``_get_geometry_center``: Stützpunktmittel des ersten Rings; sonst ``(0, 0)``."""
    geom_type = geometry.get("type")
    if geom_type == "Point":
        coords = geometry.get("coordinates", [0, 0])
        return (coords[0], coords[1])
    if geom_type == "Polygon":
        ring = geometry.get("coordinates", [[]])[0]
        if ring:
            return (sum(c[0] for c in ring) / len(ring), sum(c[1] for c in ring) / len(ring))
    elif geom_type == "MultiPolygon":
        ring = geometry.get("coordinates", [[[]]])[0][0]
        if ring:
            return (sum(c[0] for c in ring) / len(ring), sum(c[1] for c in ring) / len(ring))
    return (0, 0)
