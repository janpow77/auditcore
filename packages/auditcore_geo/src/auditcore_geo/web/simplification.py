"""``POST /vereinfachung``: Douglas-Peucker je Ring, Toleranz in Metern oder Grad."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from .._flaechenmodell import flaeche_aus_geojson
from ..flaeche import flaechenschwerpunkt
from ..koordinaten import Punkt
from ..projektion import WGS84, UtmZone, geographisch_nach_utm, utm_nach_geographisch_lonlat
from ..vereinfachung import ring_vereinfachen
from ._contract import Body, ContractError
from .calculations import standard_zone
from .settings import Settings

Position = tuple[float, float]
Transform = Callable[[float, float], Position]


def _rings(geometry: dict[str, object]) -> list[list[list[Position]]]:
    """Polygons → rings → ``(lon, lat)`` positions of a validated GeoJSON geometry."""
    coordinates = geometry["coordinates"]
    polygons = [coordinates] if geometry["type"] == "Polygon" else coordinates
    assert isinstance(polygons, list)
    return [
        [[(float(p[0]), float(p[1])) for p in ring] for ring in polygon] for polygon in polygons
    ]


def _digits(body: Body) -> int | None:
    return body.integer("stellen", 0, 12) if body.has("stellen") else None


def _projection(geometry: dict[str, object]) -> tuple[UtmZone, Transform, Transform]:
    centre = flaechenschwerpunkt(flaeche_aus_geojson(geometry))
    zone = UtmZone(standard_zone(centre.lon), centre.lat >= 0, WGS84)

    def forward(lon: float, lat: float) -> Position:
        return geographisch_nach_utm(Punkt(lat=lat, lon=lon), zone)

    def back(east: float, north: float) -> Position:
        return utm_nach_geographisch_lonlat(east, north, zone)

    return zone, forward, back


def _simplify_ring(
    ring: Sequence[Position],
    tolerance: float,
    digits: int | None,
    transforms: tuple[Transform, Transform] | None,
) -> list[list[float]] | None:
    if transforms is None:
        return ring_vereinfachen(ring, tolerance, stellen=digits)
    forward, back = transforms
    simplified = ring_vereinfachen([forward(x, y) for x, y in ring], tolerance, stellen=None)
    if simplified is None:
        return None
    return [list(back(x, y)) for x, y in simplified]


def _simplify_polygon(
    polygon: Sequence[Sequence[Position]],
    tolerance: float,
    digits: int | None,
    transforms: tuple[Transform, Transform] | None,
) -> tuple[list[list[list[float]]] | None, list[int]]:
    """Simplified rings and the numbers of dropped rings; a dropped outer ring drops all."""
    outer = _simplify_ring(polygon[0], tolerance, digits, transforms)
    if outer is None:
        return None, list(range(len(polygon)))
    rings, lost = [outer], []
    for number, ring in enumerate(polygon[1:], 1):
        result = _simplify_ring(ring, tolerance, digits, transforms)
        if result is None:
            lost.append(number)
        else:
            rings.append(result)
    return rings, lost


def simplify(request: object, settings: Settings) -> dict[str, object]:
    """Vereinfachte Geometrie mit Stützpunktzahl vorher/nachher und entfallenen Ringen.

    ``einheit="grad"`` rechnet wie die Quelle in Koordinateneinheiten;
    ``einheit="meter"`` projiziert jeden Ring in die UTM-Zone des
    Flächenschwerpunkts (WGS 84), vereinfacht dort und rechnet zurück.
    Fällt ein Außenring weg, entfällt das Polygon samt Löchern.
    """
    body = Body.of(request)
    geometry = dict(body.child("flaeche").data)
    flaeche_aus_geojson(geometry)  # validates type, rings and coordinates
    tolerance = body.number("toleranz", minimum=0.0)
    unit, digits = body.choice("einheit", ("meter", "grad")), _digits(body)
    polygons = _rings(geometry)
    before = sum(len(ring) for polygon in polygons for ring in polygon)
    if before > settings.max_vertices:
        raise ContractError(
            f"{before} Stützpunkte; höchstens {settings.max_vertices} je Anfrage.",
            status=413,
            code="zu_gross",
        )
    zone: UtmZone | None = None
    transforms: tuple[Transform, Transform] | None = None
    if unit == "meter":
        zone, forward, back = _projection(geometry)
        transforms = (forward, back)
    kept: list[list[list[list[float]]]] = []
    dropped: list[dict[str, int]] = []
    for index, polygon in enumerate(polygons):
        rings, lost = _simplify_polygon(polygon, tolerance, digits, transforms)
        dropped += [{"polygon": index, "ring": ring} for ring in lost]
        if rings is not None:
            kept.append(rings)
    after = sum(len(ring) for polygon in kept for ring in polygon)
    return {
        "geometrie": {"type": "MultiPolygon", "coordinates": kept} if kept else None,
        "stuetzpunkte_vorher": before,
        "stuetzpunkte_nachher": after,
        "entfallene_ringe": dropped,
        "einheit": unit,
        "toleranz": tolerance,
        "utm_zone": zone.zone if zone else None,
    }
