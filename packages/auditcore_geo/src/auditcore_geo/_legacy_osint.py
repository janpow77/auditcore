"""Nachbildungen aus ``osint@d361ddb`` (Ortsdienst, Betroffenheit, Bundesländer)."""

from __future__ import annotations

import io
import math
import struct
from collections.abc import Sequence

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
