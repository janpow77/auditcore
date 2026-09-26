"""Rechenendpunkte des REST-Vertrags: Katalog, Umkreis, Lage, UTM (framework-frei)."""

from __future__ import annotations

from .. import __version__
from .._flaechenmodell import EMPFOHLEN_RAND_GILT_ALS_INNEN, EntarteterRing, flaeche_aus_geojson
from ..distanz import EMPFOHLENES_ERDMODELL, KUGELPROFILE, umkreis
from ..flaeche import lage, randbefund
from ..projektion import GRS80, WGS84, Ellipsoid, UtmZone, geographisch_nach_utm
from ..projektion import utm_nach_geographisch as _utm_to_point
from ._contract import Body, ContractError
from .settings import Settings

ELLIPSOIDS: dict[str, Ellipsoid] = {"GRS80": GRS80, "WGS84": WGS84}


def catalogue(settings: Settings) -> dict[str, object]:
    """``GET /profile``: Erdmodelle, Empfehlungen D1/D2, Grenzen und aktive Anschlüsse."""
    geocoder = settings.geocoder
    return {
        "bibliothek": f"auditcore_geo {__version__}",
        "erdmodelle": [
            {
                "id": p.profil_id,
                "radius_m": p.radius_m,
                "beschreibung": p.beschreibung,
                "empfohlen": p is EMPFOHLENES_ERDMODELL,
            }
            for p in KUGELPROFILE.values()
        ],
        "empfohlenes_erdmodell": EMPFOHLENES_ERDMODELL.profil_id,
        "rand_gilt_als_innen_empfohlen": EMPFOHLEN_RAND_GILT_ALS_INNEN,
        "ellipsoide": sorted(ELLIPSOIDS),
        "vereinfachung_einheiten": ["meter", "grad"],
        "grenzen": {
            "max_body_bytes": settings.max_body_bytes,
            "max_punkte": settings.max_points,
            "max_stuetzpunkte": settings.max_vertices,
            "max_gpkg_bytes": settings.max_gpkg_bytes,
            "max_gpkg_flaechen": settings.max_gpkg_areas,
        },
        "geocoder": {
            "aktiv": geocoder is not None,
            "namensnennung": geocoder.attribution if geocoder is not None else None,
        },
        "gpkg_quellen": sorted(settings.gpkg_sources),
    }


def _point_id(entry: Body, index: int) -> str:
    if not entry.has("id"):
        return str(index)
    raw = entry.value("id")
    if isinstance(raw, bool) or not isinstance(raw, (str, int)):
        raise ContractError(f"'{entry.name('id')}' muss Text oder ganze Zahl sein.")
    return str(raw)


def radius_search(request: object, settings: Settings) -> dict[str, object]:
    """``POST /umkreis``: Punkte bis einschließlich ``radius_m`` nach Entfernung."""
    body = Body.of(request)
    model = body.earth_model()
    centre = body.point("zentrum")
    radius = body.number("radius_m", minimum=0.0)
    entries = body.objects("punkte", settings.max_points)
    points = [entry.point() for entry in entries]
    ids = [_point_id(entry, index) for index, entry in enumerate(entries)]
    hits = umkreis(centre, points, radius, model)
    return {
        "erdmodell": model.profil_id,
        "radius_m": radius,
        "geprueft": len(points),
        "treffer": [{"index": t.index, "id": ids[t.index], "abstand_m": t.abstand_m} for t in hits],
    }


def _ring_dict(ring: EntarteterRing | None) -> dict[str, object] | None:
    if ring is None:
        return None
    return {
        "polygon": ring.polygon,
        "ring": ring.ring,
        "art": ring.art.value,
        "rolle": ring.rolle.value,
        "hinweis": ring.hinweis(),
    }


def locate(request: object) -> dict[str, object]:
    """``POST /lage``: Punkt in Fläche mit ausdrücklicher Randregel (D2) und Randabstand."""
    body = Body.of(request)
    model = body.earth_model()
    point = body.point("punkt")
    area = flaeche_aus_geojson(body.child("flaeche").data)
    boundary_inside = body.flag("rand_gilt_als_innen")
    tolerance = body.number("rand_toleranz_m", minimum=0.0) if body.has("rand_toleranz_m") else 0.0
    finding = randbefund(point, area, model)
    effective = lage(point, area, rand_toleranz_m=tolerance, profil=model).value
    return {
        "lage": finding.lage.value,
        "lage_mit_toleranz": effective,
        "rand_toleranz_m": tolerance,
        "rand_gilt_als_innen": boundary_inside,
        "enthaelt": effective == "innen" or (effective == "rand" and boundary_inside),
        "abstand_m": finding.abstand_m,
        "erdmodell": model.profil_id,
        "entarteter_ring": _ring_dict(finding.entarteter_ring),
        "hinweise": list(finding.hinweise),
    }


def standard_zone(lon: float) -> int:
    """Standard-UTM-Zone aus der Länge (ohne Sonderzonen Norwegen/Spitzbergen)."""
    return min(60, int((lon + 180.0) // 6.0) + 1)


def _epsg(zone: UtmZone, ellipsoid: str) -> int | None:
    if ellipsoid == "GRS80":
        return 25800 + zone.zone if zone.nordhalbkugel and 28 <= zone.zone <= 38 else None
    return (32600 if zone.nordhalbkugel else 32700) + zone.zone


def to_utm(request: object) -> dict[str, object]:
    """``POST /utm``: Rechts-/Hochwert eines Punktes; Zone aus der Länge oder vorgegeben."""
    body = Body.of(request)
    point = body.point("punkt")
    ellipsoid = body.choice("ellipsoid", ELLIPSOIDS)
    number = body.integer("zone", 1, 60) if body.has("zone") else standard_zone(point.lon)
    zone = UtmZone(number, point.lat >= 0, ELLIPSOIDS[ellipsoid])
    east, north = geographisch_nach_utm(point, zone)
    return {
        "zone": zone.zone,
        "nordhalbkugel": zone.nordhalbkugel,
        "ellipsoid": ellipsoid,
        "epsg": _epsg(zone, ellipsoid),
        "mittelmeridian": zone.mittelmeridian_grad,
        "ost": east,
        "nord": north,
    }


def from_utm(request: object) -> dict[str, object]:
    """``POST /utm/geographisch``: Punkt aus Rechts-/Hochwert, Zone und Halbkugel."""
    body = Body.of(request)
    ellipsoid = ELLIPSOIDS[body.choice("ellipsoid", ELLIPSOIDS)]
    zone = UtmZone(body.integer("zone", 1, 60), body.flag("nordhalbkugel"), ellipsoid)
    point = _utm_to_point(body.number("ost"), body.number("nord"), zone)
    return {"punkt": {"lat": point.lat, "lon": point.lon}, "zone": zone.zone}
