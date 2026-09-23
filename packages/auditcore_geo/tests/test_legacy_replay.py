"""Die Legacy-Nachbildungen reproduzieren jeden aufgezeichneten Originalfall exakt."""

from __future__ import annotations

import json
import math
import struct
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from auditcore_geo import legacy

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "legacy_observed.json").read_text(encoding="utf-8")
)
CASES = FIXTURE["cases"]


def jsonable(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return {"float": repr(value)}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return value


def same(expected: dict[str, Any], call: Callable[[], Any]) -> None:
    if "ok" in expected:
        assert jsonable(call()) == expected["ok"]
    else:
        names = {"error": struct.error}
        with pytest.raises(names.get(expected["error"], Exception)) as info:
            call()
        assert type(info.value).__name__ == expected["error"]


DISTANZ = {
    "osint_haversine_km": lambda a, b, c, d: legacy.osint_haversine_km(a, b, c, d),
    "designer_gis_haversine_m": lambda a, b, c, d: legacy.designer_gis_haversine_m(b, a, d, c),
    "designer_register_entfernung_km": legacy.designer_register_entfernung_km,
    "designer_company_haversine_m": legacy.designer_company_haversine_m,
    "flowsearch_calculate_distance_km": legacy.flowsearch_calculate_distance_km,
    "flowsearch_natura_distance_m": legacy.flowsearch_natura_distance_m,
}


def test_fixture_is_bound_to_pinned_sources() -> None:
    assert FIXTURE["schema"] == "auditcore_geo.legacy_observed/1"
    assert FIXTURE["case_count"] == sum(len(v) for v in CASES.values()) >= 280
    assert {s["commit"] for s in FIXTURE["sources"].values()} == {
        "d361ddb9a502bb899065e799d50104f306cfdc89",
        "1254591156d3bdf6ccdf4050dec7713a61ad4a20",
        "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4",
        "3d1cb40221645935c323392d70d84102d05ac7bb",
    }


@pytest.mark.parametrize("case", CASES["distanz"], ids=lambda c: str(c["eingabe"]))
def test_distance_variants(case: dict[str, Any]) -> None:
    for name, function in DISTANZ.items():
        same(case[name], lambda f=function: f(*case["eingabe"]))


@pytest.mark.parametrize("case", CASES["umkreis"], ids=lambda c: c["name"])
def test_osint_radius(case: dict[str, Any]) -> None:
    lats = [p[0] for p in case["punkte"]]
    lons = [p[1] for p in case["punkte"]]
    z = case["zentrum"]
    same(case["ergebnis"], lambda: legacy.osint_umkreis(z[0], z[1], case["km"], lats, lons))


def _polygone(geometrie: dict[str, Any]) -> list[Any]:
    if geometrie["type"] == "MultiPolygon":
        return [[[tuple(p) for p in r] for r in poly] for poly in geometrie["coordinates"]]
    return [[[tuple(p) for p in r] for r in geometrie["coordinates"]]]


GEOMETRIEN: dict[str, dict[str, Any]] = FIXTURE["inputs"]["geometrien"]


@pytest.mark.parametrize(
    "case", CASES["lage"], ids=lambda c: f"{c['geometrie']}-{c['punkt_lonlat']}"
)
def test_point_in_polygon_variants(case: dict[str, Any]) -> None:
    lon, lat = case["punkt_lonlat"]
    geometrie = GEOMETRIEN[case["geometrie"]]
    polys = _polygone(geometrie)
    same(
        case["designer_gis_point_in_geometry"],
        lambda: legacy.designer_gis_punkt_in_geometrie(lon, lat, geometrie),
    )
    same(
        case["designer_register_punkt_in_gebiet"],
        lambda: legacy.designer_register_punkt_in_gebiet(lat, lon, polys),
    )
    same(case["osint_im_ring_aussenring"], lambda: legacy.osint_im_ring(lon, lat, polys[0][0]))


FRANKFURT = GEOMETRIEN["frankfurt"]


@pytest.mark.parametrize("case", CASES["abstand"], ids=lambda c: str(c["punkt_lonlat"]))
def test_edge_and_vertex_distances(case: dict[str, Any]) -> None:
    lon, lat = case["punkt_lonlat"]
    same(
        case["designer_gis_edge_distance_m"],
        lambda: legacy.designer_gis_randabstand_m(lon, lat, FRANKFURT),
    )
    same(
        case["designer_company_distance_to_geometry_m"],
        lambda: legacy.designer_company_abstand_zur_geometrie_m(lat, lon, FRANKFURT),
    )
    beobachtet = case["designer_register_naechste_nuts3"]["ok"]
    wert = legacy.designer_register_naechster_stuetzpunkt_km(lat, lon, _polygone(FRANKFURT))
    assert (None if beobachtet is None else beobachtet[1]) == wert


@pytest.mark.parametrize("case", CASES["abstand_ungueltig"])
def test_invalid_geometry_distances(case: dict[str, Any]) -> None:
    g = case["geometrie"]
    same(
        case["designer_company_distance_to_geometry_m"],
        lambda: legacy.designer_company_abstand_zur_geometrie_m(50.0, 8.0, g),
    )
    same(
        case["designer_gis_edge_distance_m"],
        lambda: legacy.designer_gis_randabstand_m(8.0, 50.0, g or {}),
    )


@pytest.mark.parametrize("case", CASES["schwerpunkt"], ids=lambda c: c["geometrie"])
def test_centre_variants(case: dict[str, Any]) -> None:
    geometrie = GEOMETRIEN[case["geometrie"]]
    same(
        case["flowsearch_get_geometry_center"],
        lambda: legacy.flowsearch_geometriezentrum(geometrie),
    )
    same(case["designer_gis_geometry_centroid"], lambda: legacy.designer_gis_schwerpunkt(geometrie))


@pytest.mark.parametrize("case", CASES["achsenfolge"], ids=lambda c: c["name"])
def test_axis_detection(case: dict[str, Any]) -> None:
    ringe = [[tuple(p) for p in r] for r in case["ringe"]]
    same(case["osint_achsen_drehen"], lambda: legacy.osint_achsen_drehen(ringe))


@pytest.mark.parametrize("case", CASES["utm"], ids=lambda c: str(c["eingabe"]))
def test_utm_bit_identical(case: dict[str, Any]) -> None:
    same(case["osint_utm_nach_wgs84"], lambda: legacy.osint_utm_nach_wgs84(*case["eingabe"]))


@pytest.mark.parametrize("case", CASES["wkb"], ids=lambda c: c["name"])
def test_wkb_lenient_original(case: dict[str, Any]) -> None:
    blob = bytes.fromhex(case["blob_hex"])
    same(case["osint_wkb_polygone"], lambda: legacy.osint_wkb_polygone(blob))


@pytest.mark.parametrize(
    "case", CASES["douglas_peucker"], ids=lambda c: f"{c['linie']}-{c['toleranz']}"
)
def test_douglas_peucker_identical(case: dict[str, Any]) -> None:
    punkte = [tuple(p) for p in case["punkte"]]
    same(
        case["osint_douglas_peucker"],
        lambda: legacy.osint_douglas_peucker(punkte, case["toleranz"]),
    )
    same(
        case["osint_ring_vereinfachen"],
        lambda: legacy.osint_ring_vereinfachen(punkte, case["toleranz"]),
    )
