"""Vertrag der Bibliothek gegen Original und unabhängige Referenzen (PROJ, shapely)."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

import pytest

from auditcore_geo import (
    BEREICH_DEUTSCHLAND_OSINT,
    ETRS89_UTM32N,
    GRS80,
    KUGEL_6371_KM,
    KUGEL_MITTLERER_RADIUS,
    Achsenfolge,
    GeometrieFehler,
    KoordinatenFehler,
    Lage,
    ProfilFehler,
    Punkt,
    UtmZone,
    abstand_zur_strecke_lokal_m,
    achsenfolge_erkennen,
    douglas_peucker,
    enthaelt,
    flaeche_aus_geojson,
    flaechenschwerpunkt,
    geographisch_nach_utm,
    grosskreis_km,
    grosskreis_m,
    kugelprofil,
    lage,
    legacy,
    lies_gpkg_polygone,
    naechster_stuetzpunkt_m,
    randabstand_m,
    ring_vereinfachen,
    umkreis,
    utm_nach_geographisch,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "legacy_observed.json").read_text(encoding="utf-8")
)
CASES = FIXTURE["cases"]
GEOMETRIEN: dict[str, Any] = FIXTURE["inputs"]["geometrien"]


# ─────────────────────────────── Punkte und Achsenfolge


def test_point_axis_order_is_explicit() -> None:
    assert Punkt.aus_lonlat([8.68, 50.11]) == Punkt(lat=50.11, lon=8.68)
    assert Punkt.aus_latlon([50.11, 8.68]) == Punkt(lat=50.11, lon=8.68)
    assert Punkt(50.11, 8.68).als_lonlat() == (8.68, 50.11)
    with pytest.raises(KoordinatenFehler):
        Punkt.aus_folge([8.68, 50.11], Achsenfolge.UNBEKANNT)
    for lat, lon in ((91.0, 0.0), (0.0, 180.5), (math.nan, 0.0), (0.0, math.inf)):
        with pytest.raises(KoordinatenFehler):
            Punkt(lat, lon)
    with pytest.raises(KoordinatenFehler):
        Punkt(True, 1.0)  # type: ignore[arg-type]
    with pytest.raises(KoordinatenFehler):
        Punkt.aus_lonlat([8.0])


ERWARTETE_ACHSEN = {
    "lonlat_de": Achsenfolge.LON_LAT,
    "latlon_de": Achsenfolge.LAT_LON,
    "ausserhalb": Achsenfolge.UNBEKANNT,
    "gemischt_zuerst_latlon": Achsenfolge.UNBEKANNT,
    "leer": Achsenfolge.UNBEKANNT,
    "vierter_ring_erst": Achsenfolge.UNBEKANNT,
}


@pytest.mark.parametrize("case", CASES["achsenfolge"], ids=lambda c: c["name"])
def test_axis_detection_reports_unknown_instead_of_no_swap(case: dict[str, Any]) -> None:
    ringe = [[tuple(p) for p in r] for r in case["ringe"]]
    ergebnis = achsenfolge_erkennen(ringe, BEREICH_DEUTSCHLAND_OSINT)
    assert ergebnis is ERWARTETE_ACHSEN[case["name"]]
    if ergebnis is not Achsenfolge.UNBEKANNT:  # eindeutige Fälle wie im Original
        assert (ergebnis is Achsenfolge.LAT_LON) == case["osint_achsen_drehen"]["ok"]


# ─────────────────────────────── Entfernungen


def test_profiles_are_explicit() -> None:
    assert kugelprofil("kugel.r1_6371008_8m") is KUGEL_MITTLERER_RADIUS
    assert kugelprofil("kugel.6371000m") is KUGEL_6371_KM
    with pytest.raises(ProfilFehler):
        kugelprofil("kugel.standard")
    with pytest.raises(ProfilFehler):
        type(KUGEL_6371_KM)("x", 0.0, "", ())


@pytest.mark.parametrize("case", CASES["distanz"], ids=lambda c: str(c["eingabe"]))
def test_great_circle_matches_each_source_profile(case: dict[str, Any]) -> None:
    lat1, lon1, lat2, lon2 = case["eingabe"]
    a, b = Punkt(lat1, lon1), Punkt(lat2, lon2)
    r1 = grosskreis_m(a, b, KUGEL_MITTLERER_RADIUS)
    r0 = grosskreis_m(a, b, KUGEL_6371_KM)
    assert r1 == pytest.approx(case["osint_haversine_km"]["ok"] * 1000, rel=1e-12, abs=1e-9)
    assert r1 == pytest.approx(case["designer_gis_haversine_m"]["ok"], rel=1e-7, abs=1e-6)
    assert r0 == pytest.approx(
        case["designer_register_entfernung_km"]["ok"] * 1000, rel=1e-12, abs=1e-9
    )
    assert r0 == pytest.approx(case["designer_company_haversine_m"]["ok"], rel=1e-12, abs=1e-9)
    assert r0 == pytest.approx(case["flowsearch_natura_distance_m"]["ok"], rel=1e-12, abs=1e-9)
    assert r0 == pytest.approx(
        case["flowsearch_calculate_distance_km"]["ok"] * 1000, rel=1e-7, abs=1e-6
    )
    assert grosskreis_km(a, b, KUGEL_6371_KM) == pytest.approx(r0 / 1000)
    # Kugel gegen WGS-84-Ellipsoid (PROJ/geographiclib): unter 0,6 % Abweichung.
    referenz = case["referenz_wgs84_ellipsoid_m"]
    assert abs(r1 - referenz) <= 0.006 * referenz + 1e-3


def test_radius_profiles_differ_measurably() -> None:
    """Varianten nicht still vereinheitlicht: 6371,0088 km gegenüber 6371 km."""
    a, b = Punkt(50.1106, 8.6821), Punkt(52.52, 13.405)
    unterschied = grosskreis_m(a, b, KUGEL_MITTLERER_RADIUS) - grosskreis_m(a, b, KUGEL_6371_KM)
    assert 0.5 < unterschied < 0.7


def test_antipodal_points_are_clamped() -> None:
    assert grosskreis_m(Punkt(0, 0), Punkt(0, 180), KUGEL_MITTLERER_RADIUS) == pytest.approx(
        math.pi * KUGEL_MITTLERER_RADIUS.radius_m
    )


def _brute(zentrum: Punkt, punkte: list[Punkt], radius_m: float) -> list[int]:
    return sorted(
        (
            i
            for i, p in enumerate(punkte)
            if grosskreis_m(zentrum, p, KUGEL_MITTLERER_RADIUS) <= radius_m
        ),
    )


@pytest.mark.parametrize("case", CASES["umkreis"], ids=lambda c: c["name"])
def test_radius_search_has_no_false_negatives(case: dict[str, Any]) -> None:
    zentrum = Punkt(*case["zentrum"])
    punkte = [Punkt(*p) for p in case["punkte"]]
    radius = None if case["km"] is None else case["km"] * 1000
    treffer = umkreis(zentrum, punkte, radius, KUGEL_MITTLERER_RADIUS)
    if radius is None:
        assert [t.index for t in treffer] == [i for _, i in case["ergebnis"]["ok"]]
        return
    assert sorted(t.index for t in treffer) == _brute(zentrum, punkte, radius)
    alt = sorted(i for _, i in case["ergebnis"]["ok"])
    if case["name"] in ("hohe_breite_grosser_radius", "datumsgrenze"):
        assert alt != sorted(t.index for t in treffer)  # GEO-C02: Original verliert Treffer
    elif case["name"] != "grenze_genau":  # km→m-Umrechnung verschiebt die exakte Grenze um 1 ulp
        assert alt == sorted(t.index for t in treffer)


def test_radius_search_random_against_brute_force() -> None:
    rng = random.Random(3)
    for _ in range(40):
        zentrum = Punkt(rng.uniform(-89, 89), rng.uniform(-180, 180))
        punkte = [Punkt(rng.uniform(-90, 90), rng.uniform(-180, 180)) for _ in range(200)]
        radius = rng.choice([1e3, 5e4, 5e5, 2e6, 8e6])
        treffer = umkreis(zentrum, punkte, radius, KUGEL_MITTLERER_RADIUS)
        assert sorted(t.index for t in treffer) == _brute(zentrum, punkte, radius)
        assert [t.abstand_m for t in treffer] == sorted(t.abstand_m for t in treffer)


def test_radius_boundary_is_inclusive_and_validated() -> None:
    zentrum, p = Punkt(50.0, 8.0), Punkt(50.03, 8.04)
    d = grosskreis_m(zentrum, p, KUGEL_MITTLERER_RADIUS)
    assert [t.index for t in umkreis(zentrum, [p], d, KUGEL_MITTLERER_RADIUS)] == [0]
    for falsch in (-1.0, math.nan, math.inf):
        with pytest.raises(ValueError):
            umkreis(zentrum, [p], falsch, KUGEL_MITTLERER_RADIUS)


# ─────────────────────────────── Flächen


@pytest.mark.parametrize(
    "case", CASES["lage"], ids=lambda c: f"{c['geometrie']}-{c['punkt_lonlat']}"
)
def test_point_location_matches_shapely_including_boundary(case: dict[str, Any]) -> None:
    flaeche = flaeche_aus_geojson(GEOMETRIEN[case["geometrie"]])
    punkt = Punkt.aus_lonlat(case["punkt_lonlat"])
    ergebnis = lage(punkt, flaeche)
    assert ergebnis.value == case["referenz_shapely"]
    if ergebnis is not Lage.RAND:
        # Außerhalb des Randes stimmt die korrekte Mehrfachpolygonlogik (register) überein.
        assert (ergebnis is Lage.INNEN) == case["designer_register_punkt_in_gebiet"]["ok"]
    assert enthaelt(flaeche, punkt, rand_gilt_als_innen=True) == (ergebnis is not Lage.AUSSEN)
    assert enthaelt(flaeche, punkt, rand_gilt_als_innen=False) == (ergebnis is Lage.INNEN)


def test_multipolygon_second_part_is_inside() -> None:
    """GEO-C04: ``_point_in_geometry`` hält Punkte im zweiten Teil für außen."""
    geometrie = GEOMETRIEN["zwei_quadrate"]
    assert not legacy.designer_gis_punkt_in_geometrie(25.0, 5.0, geometrie)
    assert lage(Punkt(5.0, 25.0), flaeche_aus_geojson(geometrie)) is Lage.INNEN


def test_boundary_tolerance_needs_profile() -> None:
    flaeche = flaeche_aus_geojson(GEOMETRIEN["frankfurt"])
    nahe = Punkt(50.10005, 8.67)  # etwa 5,6 m nördlich der Südkante, innen
    assert lage(nahe, flaeche) is Lage.INNEN
    assert lage(nahe, flaeche, rand_toleranz_m=10.0, profil=KUGEL_MITTLERER_RADIUS) is Lage.RAND
    with pytest.raises(ProfilFehler):
        lage(nahe, flaeche, rand_toleranz_m=10.0)
    with pytest.raises(GeometrieFehler):
        lage(nahe, flaeche, rand_toleranz_m=-1.0)


@pytest.mark.parametrize("case", CASES["abstand"], ids=lambda c: str(c["punkt_lonlat"]))
def test_edge_distance_against_projected_reference(case: dict[str, Any]) -> None:
    flaeche = flaeche_aus_geojson(GEOMETRIEN["frankfurt"])
    punkt = Punkt.aus_lonlat(case["punkt_lonlat"])
    d = randabstand_m(punkt, flaeche, KUGEL_MITTLERER_RADIUS)
    if case["referenz_utm32_innen"]:
        assert d == 0.0
        # GEO-C04/C05: das Original meldet für einen Punkt im zweiten Teil einen Randabstand.
        assert case["designer_gis_edge_distance_m"]["ok"] > 0
    else:
        assert d == pytest.approx(case["referenz_utm32_rand_m"], rel=0.005)
        assert d == pytest.approx(case["designer_gis_edge_distance_m"]["ok"], rel=1e-9)
    stuetz = naechster_stuetzpunkt_m(punkt, flaeche, KUGEL_6371_KM, nur_aussenringe=False)
    assert round(stuetz, 1) == case["designer_company_distance_to_geometry_m"]["ok"]
    register = case["designer_register_naechste_nuts3"]["ok"]
    if register is not None:
        aussen = naechster_stuetzpunkt_m(punkt, flaeche, KUGEL_6371_KM, nur_aussenringe=True)
        assert aussen / 1000 == pytest.approx(register[1], rel=1e-12)


@pytest.mark.parametrize("case", CASES["abstand_ungueltig"])
def test_invalid_geometry_is_an_error_not_zero(case: dict[str, Any]) -> None:
    """GEO-C06: das Original liefert 0,0 m (= „im Schutzgebiet“) bzw. ``None``."""
    assert case["designer_company_distance_to_geometry_m"]["ok"] == 0.0
    with pytest.raises(GeometrieFehler):
        flaeche_aus_geojson(case["geometrie"])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "geometrie",
    [
        {"type": "Polygon", "coordinates": [[]]},
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], ["x", 1], [0, 0]]]},
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [math.nan, 1], [0, 0]]]},
        {"type": "MultiPolygon", "coordinates": [[]]},
        {"type": "MultiPolygon", "coordinates": "x"},
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [True, 1], [0, 0]]]},
    ],
)
def test_malformed_rings_are_rejected(geometrie: dict[str, Any]) -> None:
    """Unlesbar bleibt Fehler; zusammengefallene Ringe regelt GEO-C16 (test_entartete_ringe)."""
    with pytest.raises(GeometrieFehler):
        flaeche_aus_geojson(geometrie)


@pytest.mark.parametrize("case", CASES["schwerpunkt"], ids=lambda c: c["geometrie"])
def test_area_centroid_against_shapely(case: dict[str, Any]) -> None:
    geometrie = GEOMETRIEN[case["geometrie"]]
    if geometrie["type"] not in ("Polygon", "MultiPolygon"):
        with pytest.raises(GeometrieFehler):
            flaeche_aus_geojson(geometrie)
        return
    s = flaechenschwerpunkt(flaeche_aus_geojson(geometrie))
    rx, ry = case["referenz_shapely_schwerpunkt"]
    assert s.lon == pytest.approx(rx, abs=1e-9)
    assert s.lat == pytest.approx(ry, abs=1e-9)


def test_local_segment_distance_degenerate_segment() -> None:
    p, a = Punkt(50.0, 8.0), Punkt(50.001, 8.0)
    assert abstand_zur_strecke_lokal_m(p, a, a, KUGEL_MITTLERER_RADIUS) == pytest.approx(
        grosskreis_m(p, a, KUGEL_MITTLERER_RADIUS), rel=1e-6
    )


# ─────────────────────────────── UTM


@pytest.mark.parametrize("case", CASES["utm"], ids=lambda c: str(c["eingabe"]))
def test_utm_against_proj_within_a_millimetre(case: dict[str, Any]) -> None:
    ost, nord = case["eingabe"]
    punkt = utm_nach_geographisch(ost, nord, ETRS89_UTM32N)
    rlon, rlat = case["referenz_proj_lonlat"]
    fehler = math.hypot(
        (punkt.lon - rlon) * 111_320 * math.cos(math.radians(rlat)), (punkt.lat - rlat) * 110_574
    )
    assert fehler < 0.001
    assert (punkt.lon, punkt.lat) == tuple(case["osint_utm_nach_wgs84"]["ok"])
    zurueck = geographisch_nach_utm(Punkt(rlat, rlon), ETRS89_UTM32N)
    assert zurueck[0] == pytest.approx(ost, abs=0.001)
    assert zurueck[1] == pytest.approx(nord, abs=0.001)


def test_utm_zones_and_southern_hemisphere() -> None:
    zone33s = UtmZone(33, False, GRS80)
    p = Punkt(-33.9, 18.4)
    ost, nord = geographisch_nach_utm(p, zone33s)
    assert nord > 6_000_000
    q = utm_nach_geographisch(ost, nord, zone33s)
    assert (q.lat, q.lon) == pytest.approx((p.lat, p.lon), abs=1e-8)
    for falsch in (0, 61, True):
        with pytest.raises(ProfilFehler):
            UtmZone(falsch, True, GRS80)
    with pytest.raises(ProfilFehler):
        utm_nach_geographisch(math.nan, 0.0, ETRS89_UTM32N)


# ─────────────────────────────── GeoPackage

GUELTIG = {
    "polygon_le_ohne_huelle": 25832,
    "polygon_be_huelle_1": 25832,
    "polygon_le_huelle_2": 25832,
    "polygon_le_huelle_3": 25832,
    "polygon_le_huelle_4": 25832,
    "multipolygon_gemischt": 4258,
}


@pytest.mark.parametrize("case", CASES["wkb"], ids=lambda c: c["name"])
def test_geopackage_strict_reader(case: dict[str, Any]) -> None:
    blob = bytes.fromhex(case["blob_hex"])
    if case["name"] in GUELTIG:
        geometrie = lies_gpkg_polygone(blob)
        assert geometrie.srs_id == GUELTIG[case["name"]]
        assert json.loads(json.dumps(geometrie.polygone)) == case["osint_wkb_polygone"]["ok"]
    else:
        # GEO-C07: Original liest EWKB-Z, fremde Teile, Leerflag und Restbytes still falsch.
        with pytest.raises(GeometrieFehler):
            lies_gpkg_polygone(blob)


def test_geopackage_rejects_non_bytes() -> None:
    with pytest.raises(GeometrieFehler):
        lies_gpkg_polygone("GP")  # type: ignore[arg-type]


# ─────────────────────────────── Douglas-Peucker


@pytest.mark.parametrize(
    "case", CASES["douglas_peucker"], ids=lambda c: f"{c['linie']}-{c['toleranz']}"
)
def test_douglas_peucker_equals_original(case: dict[str, Any]) -> None:
    punkte = [tuple(p) for p in case["punkte"]]
    if case["toleranz"] < 0:
        with pytest.raises(GeometrieFehler):
            douglas_peucker(punkte, case["toleranz"])
        return
    assert (
        json.loads(json.dumps(douglas_peucker(punkte, case["toleranz"])))
        == case["osint_douglas_peucker"]["ok"]
    )
    assert (
        ring_vereinfachen(punkte, case["toleranz"], stellen=4)
        == case["osint_ring_vereinfachen"]["ok"]
    )


def test_douglas_peucker_long_line_without_recursion_limit() -> None:
    # Treppenfolge, bei der jede Teilung nur einen Punkt abspaltet.
    punkte = [(float(i), float(2**-i) if i < 1000 else 0.0) for i in range(5000)]
    assert len(douglas_peucker(punkte, 0.0)) >= 2
    with pytest.raises(GeometrieFehler):
        douglas_peucker([(0.0, 0.0), (math.nan, 1.0)], 0.1)


def test_decisions_of_2026_09_23_are_exported_not_silent() -> None:
    """Empfehlungen (vom Nutzer delegiert) sind Konstanten; Funktionen verlangen weiter Angaben."""
    import inspect

    from auditcore_geo import EMPFOHLEN_RAND_GILT_ALS_INNEN, EMPFOHLENES_ERDMODELL

    assert EMPFOHLENES_ERDMODELL is KUGEL_MITTLERER_RADIUS
    assert EMPFOHLEN_RAND_GILT_ALS_INNEN is True
    for funktion in (grosskreis_m, umkreis, randabstand_m):
        assert inspect.signature(funktion).parameters["profil"].default is inspect.Parameter.empty
    parameter = inspect.signature(enthaelt).parameters["rand_gilt_als_innen"]
    assert parameter.default is inspect.Parameter.empty
    quadrat = flaeche_aus_geojson(GEOMETRIEN["quadrat"])
    assert enthaelt(quadrat, Punkt(10.0, 5.0), rand_gilt_als_innen=EMPFOHLEN_RAND_GILT_ALS_INNEN)
