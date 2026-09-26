"""Nachbildungen aus ``flowsearch@10cb2a3``."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

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
