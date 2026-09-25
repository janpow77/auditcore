"""Nachbildungen aus ``audit_designer@1254591`` (GIS, Register-Geocoding, Firmendaten)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

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
