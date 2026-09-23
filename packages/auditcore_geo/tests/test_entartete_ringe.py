"""GEO-C16: zusammengefallene Ringe verwerfen die Geometrie nicht mehr.

Grundlage ist ``fixtures/entartet_observed.json`` (``tools/capture_entartet.py``):
Originalfunktionen aus audit_designer/flowsearch, ``auditcore_geo`` 0.1.0 und
eine shapely/pyproj-Referenz, tatsächlich ausgeführt auf synthetischen Fällen.
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path
from typing import Any

import pytest

from auditcore_geo import (
    EMPFOHLEN_RAND_GILT_ALS_INNEN,
    ETRS89_UTM32N,
    KUGEL_6371_KM,
    KUGEL_MITTLERER_RADIUS,
    VERTRAG_ENTARTETE_RINGE,
    EntarteterRing,
    Entartung,
    Flaeche,
    GeoError,
    GeometrieFehler,
    Lage,
    ProfilFehler,
    Punkt,
    RingRolle,
    enthaelt,
    flaeche_aus_geojson,
    flaeche_aus_gpkg,
    flaeche_aus_ringen,
    flaechen_im_umkreis,
    flaechenschwerpunkt,
    geographisch_nach_utm,
    lage,
    lies_gpkg_polygone,
    naechster_stuetzpunkt_m,
    randabstand_m,
    randbefund,
    utm_nach_geographisch_lonlat,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "entartet_observed.json").read_text(encoding="utf-8")
)
FAELLE: list[dict[str, Any]] = FIXTURE["cases"]
GEOMETRIE = {f["name"]: f["geometrie"] for f in FAELLE}
PUNKTE = [(f["name"], p) for f in FAELLE for p in f["punkte"]]

#: Fälle, in denen das Original (designer gis) dieselbe Kantenrechnung ausführt.
#: Ausgenommen: Ringe mit weniger als drei Positionen (Original: ``None``) und ein
#: zusammengefallener Außenring mit Loch (Original rechnet das Loch als Kante).
DESIGNER_GLEICH = {
    "punkt_3_gleich",
    "punkt_4_gleich",
    "linie_2_punkte",
    "kollinear_dezimal",
    "kollinear_hin_und_zurueck",
    "loch_als_linie",
    "loch_als_punkt",
    "multi_mit_punktteil",
    "multi_nur_entartet",
}


def _punkt(p: dict[str, Any]) -> Punkt:
    lon, lat = p["punkt_lonlat"]
    return Punkt(lat, lon)


# ─────────────────────────────── Beobachtetes Verhalten (Fixture)


def test_fixture_covers_the_required_shapes() -> None:
    assert set(GEOMETRIE) >= {
        "punkt_1_position",
        "punkt_2_gleich",
        "punkt_3_gleich",
        "kollinear_dezimal",
        "kollinear_hin_und_zurueck",
        "loch_als_linie",
        "loch_als_punkt",
        "multi_mit_punktteil",
    }
    assert len(PUNKTE) == 168


@pytest.mark.parametrize("fall", FAELLE, ids=lambda f: f["name"])
def test_version_010_rejected_the_whole_geometry(fall: dict[str, Any]) -> None:
    """0.1.0 verwarf die ganze Fläche; nur kollineare Ringe nahm es still an."""
    beobachtet = fall["auditcore_geo_010_flaeche_aus_geojson"]
    if fall["name"].startswith("kollinear"):
        assert beobachtet == {"ok": 1}
    else:
        assert beobachtet["error"] == "GeometrieFehler"
    # strikt=True weist beides ab.
    with pytest.raises(GeometrieFehler, match=VERTRAG_ENTARTETE_RINGE):
        flaeche_aus_geojson(fall["geometrie"], strikt=True)


@pytest.mark.parametrize("fall", FAELLE, ids=lambda f: f["name"])
def test_degenerate_rings_are_kept_and_reported(fall: dict[str, Any]) -> None:
    flaeche = flaeche_aus_geojson(fall["geometrie"])
    assert flaeche.entartet
    assert len(flaeche.hinweise) == len(flaeche.entartet)
    assert all(VERTRAG_ENTARTETE_RINGE in h for h in flaeche.hinweise)


@pytest.mark.parametrize(("name", "p"), PUNKTE, ids=lambda x: x if isinstance(x, str) else "")
def test_location_and_distance_against_reference(name: str, p: dict[str, Any]) -> None:
    """Lage wie shapely; Abstand zur Referenz in EPSG:25832 höchstens 0,5 % bzw. 0,5 m."""
    flaeche = flaeche_aus_geojson(GEOMETRIE[name])
    punkt = _punkt(p)
    assert lage(punkt, flaeche).value == p["referenz_lage"]
    abstand = randabstand_m(punkt, flaeche, KUGEL_MITTLERER_RADIUS)
    referenz = p["referenz_utm32_abstand_m"]
    assert abs(abstand - referenz) <= max(0.5, 0.005 * referenz)
    befund = randbefund(punkt, flaeche, KUGEL_MITTLERER_RADIUS)
    assert befund.lage.value == p["referenz_lage"]
    assert befund.abstand_m == abstand
    assert befund.hinweise == flaeche.hinweise


@pytest.mark.parametrize(("name", "p"), PUNKTE, ids=lambda x: x if isinstance(x, str) else "")
def test_distance_equals_designer_where_it_computed_the_same(name: str, p: dict[str, Any]) -> None:
    """Wo designer gis Ringe mit ≥ 3 Positionen behielt, ist der Abstand gleich."""
    original = p["designer_gis_edge_distance_m"]["ok"]
    if name not in DESIGNER_GLEICH:
        if name in {"punkt_1_position", "punkt_2_gleich"}:
            assert original is None  # Original: Gebiet fällt still heraus
        return
    abstand = randabstand_m(_punkt(p), flaeche_aus_geojson(GEOMETRIE[name]), KUGEL_MITTLERER_RADIUS)
    assert abstand == pytest.approx(original, rel=1e-9, abs=1e-9)


@pytest.mark.parametrize("fall", FAELLE, ids=lambda f: f["name"])
def test_centroid_against_shapely(fall: dict[str, Any]) -> None:
    """Echte Teilflächen bestimmen den Schwerpunkt; sonst Linien, sonst Punkte (wie shapely)."""
    schwerpunkt = flaechenschwerpunkt(flaeche_aus_geojson(fall["geometrie"]))
    x, y = fall["referenz_shapely_schwerpunkt"]
    assert schwerpunkt.lon == pytest.approx(x, abs=1e-9)
    assert schwerpunkt.lat == pytest.approx(y, abs=1e-9)


# ─────────────────────────────── Einzelne Fälle


A = (8.68, 50.11)


@pytest.mark.parametrize("anzahl", [1, 2, 3, 4])
def test_ring_of_identical_points_is_a_point(anzahl: int) -> None:
    flaeche = flaeche_aus_geojson({"type": "Polygon", "coordinates": [[list(A)] * anzahl]})
    assert flaeche.polygone == ()
    (ring,) = flaeche.entartet
    assert (ring.art, ring.rolle, ring.punkte) == (Entartung.PUNKT, RingRolle.AUSSEN, (A,))
    assert ring.beruecksichtigt
    assert ring.code == "entarteter_ring"
    assert lage(Punkt(50.11, 8.68), flaeche) is Lage.RAND
    assert enthaelt(flaeche, Punkt(50.11, 8.68), rand_gilt_als_innen=EMPFOHLEN_RAND_GILT_ALS_INNEN)
    assert not enthaelt(flaeche, Punkt(50.11, 8.68), rand_gilt_als_innen=False)
    # 50 m nördlich: das Gebiet fällt nicht aus der Prüfung.
    assert randabstand_m(Punkt(50.11045, 8.68), flaeche, KUGEL_MITTLERER_RADIUS) == pytest.approx(
        50.04, abs=0.01
    )
    assert "einen Punkt" in flaeche.hinweise[0]


def test_collinear_rings_are_lines_but_thin_slivers_stay_areas() -> None:
    linie = flaeche_aus_geojson(
        {"type": "Polygon", "coordinates": [[[8.1, 50.1], [8.2, 50.2], [8.3, 50.3], [8.1, 50.1]]]}
    )
    assert linie.entartet[0].art is Entartung.LINIE
    # Breite 1e-9 der Länge: echte (wenn auch schmale) Fläche, kein Rundungsrest.
    schmal = flaeche_aus_geojson(
        {"type": "Polygon", "coordinates": [[[0.0, 0.0], [1.0, 0.0], [0.5, 1e-9], [0.0, 0.0]]]}
    )
    assert schmal.entartet == () and len(schmal.polygone) == 1
    # Schleife mit Fläche 0 im Saldo ist nicht kollinear und bleibt Polygon.
    schleife = flaeche_aus_geojson(
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]}
    )
    assert schleife.entartet == ()


def test_degenerate_hole_is_dropped_with_hint() -> None:
    flaeche = flaeche_aus_geojson(GEOMETRIE["loch_als_linie"])
    (polygon,) = flaeche.polygone
    assert polygon.loecher == ()
    (loch,) = flaeche.entartet
    assert (loch.polygon, loch.ring, loch.art) == (0, 1, Entartung.LINIE)
    assert loch.rolle is RingRolle.LOCH
    assert not loch.beruecksichtigt
    assert flaeche.objekte_ohne_flaeche == ()
    assert "Loch" in flaeche.hinweise[0] and "entfällt" in flaeche.hinweise[0]
    # Punkt auf dem zusammengefallenen Loch liegt in der Fläche.
    assert lage(Punkt(50.11, 8.68), flaeche) is Lage.INNEN


def test_multipolygon_keeps_valid_part_and_point_part() -> None:
    flaeche = flaeche_aus_geojson(GEOMETRIE["multi_mit_punktteil"])
    assert len(flaeche.polygone) == 1
    (punktteil,) = flaeche.objekte_ohne_flaeche
    assert (punktteil.polygon, punktteil.art) == (1, Entartung.PUNKT)
    nah = Punkt(50.1105, 8.75)
    befund = randbefund(nah, flaeche, KUGEL_MITTLERER_RADIUS)
    assert befund.lage is Lage.AUSSEN
    assert befund.entarteter_ring == punktteil
    assert befund.abstand_m == pytest.approx(55.6, abs=0.1)
    innen = randbefund(Punkt(50.11, 8.68), flaeche, KUGEL_MITTLERER_RADIUS)
    assert (innen.lage, innen.abstand_m, innen.entarteter_ring) == (Lage.INNEN, 0.0, None)
    auf_punkt = randbefund(Punkt(50.11, 8.75), flaeche, KUGEL_MITTLERER_RADIUS)
    assert (auf_punkt.lage, auf_punkt.entarteter_ring) == (Lage.RAND, punktteil)
    am_quadrat = randbefund(Punkt(50.10, 8.68), flaeche, KUGEL_MITTLERER_RADIUS)
    assert (am_quadrat.lage, am_quadrat.entarteter_ring) == (Lage.RAND, None)
    nur_quadrat = GEOMETRIE["multi_mit_punktteil"]["coordinates"][0]
    assert flaechenschwerpunkt(flaeche) == flaechenschwerpunkt(
        flaeche_aus_geojson({"type": "Polygon", "coordinates": nur_quadrat})
    )


def test_degenerate_outer_ring_drops_its_holes_and_says_so() -> None:
    flaeche = flaeche_aus_geojson(GEOMETRIE["aussen_entartet_mit_loch"])
    (ring,) = flaeche.entartet
    assert ring.verworfene_loecher == 1
    assert "1 Loch/Löcher entfallen" in flaeche.hinweise[0]


def test_boundary_tolerance_applies_to_degenerate_objects() -> None:
    flaeche = flaeche_aus_geojson(GEOMETRIE["punkt_4_gleich"])
    nah = Punkt(50.11045, 8.68)  # rund 50 m
    assert lage(nah, flaeche) is Lage.AUSSEN
    assert lage(nah, flaeche, rand_toleranz_m=60, profil=KUGEL_MITTLERER_RADIUS) is Lage.RAND
    assert lage(nah, flaeche, rand_toleranz_m=40, profil=KUGEL_MITTLERER_RADIUS) is Lage.AUSSEN


def test_radius_search_over_areas_keeps_point_only_areas() -> None:
    flaechen = [
        flaeche_aus_geojson(GEOMETRIE["punkt_4_gleich"]),
        flaeche_aus_geojson(GEOMETRIE["loch_als_punkt"]),
        flaeche_aus_geojson(GEOMETRIE["multi_nur_entartet"]),
    ]
    zentrum = Punkt(50.11045, 8.68)
    treffer = flaechen_im_umkreis(zentrum, flaechen, 100.0, KUGEL_MITTLERER_RADIUS)
    assert [t.index for t in treffer] == [1, 0]
    assert treffer[0].abstand_m == 0.0
    assert treffer[1].abstand_m == pytest.approx(50.04, abs=0.01)
    alle = flaechen_im_umkreis(zentrum, flaechen, None, KUGEL_MITTLERER_RADIUS)
    assert [t.index for t in alle] == [1, 0, 2]
    for falsch in (-1.0, math.inf, math.nan, True):
        with pytest.raises(GeoError):
            flaechen_im_umkreis(zentrum, flaechen, falsch, KUGEL_MITTLERER_RADIUS)


def test_vertex_distance_includes_degenerate_outer_rings() -> None:
    flaeche = flaeche_aus_geojson(GEOMETRIE["multi_mit_punktteil"])
    nah = Punkt(50.1105, 8.75)
    for nur_aussen in (True, False):
        assert naechster_stuetzpunkt_m(
            nah, flaeche, KUGEL_6371_KM, nur_aussenringe=nur_aussen
        ) == pytest.approx(55.6, abs=0.1)


def test_unreadable_rings_remain_errors() -> None:
    for geometrie in (
        {"type": "Polygon", "coordinates": [[]]},
        {"type": "Polygon", "coordinates": [[[0, 0], ["x", 1]]]},
        {"type": "MultiPolygon", "coordinates": [[[[0, 0]]], []]},
    ):
        with pytest.raises(GeometrieFehler):
            flaeche_aus_geojson(geometrie)
    with pytest.raises(GeometrieFehler):
        flaeche_aus_ringen("x")  # type: ignore[arg-type]
    with pytest.raises(GeometrieFehler):
        Flaeche(())
    # Nur ein zusammengefallenes Loch ohne Fläche ist keine Fläche.
    loch = EntarteterRing(0, 1, Entartung.PUNKT, (A,))
    with pytest.raises(GeometrieFehler):
        Flaeche((), (loch,))


# ─────────────────────────────── GeoPackage


def _gpkg(ringe: list[list[tuple[float, float]]], srs_id: int) -> bytes:
    wkb = struct.pack("<BII", 1, 3, len(ringe))
    for ring in ringe:
        wkb += struct.pack("<I", len(ring))
        wkb += b"".join(struct.pack("<dd", x, y) for x, y in ring)
    return b"GP" + bytes([0, 1]) + struct.pack("<i", srs_id) + wkb


def test_geopackage_polygon_with_degenerate_hole_geographic() -> None:
    quadrat = [(8.66, 50.10), (8.70, 50.10), (8.70, 50.12), (8.66, 50.12), (8.66, 50.10)]
    loch = [(8.68, 50.11)] * 4
    geometrie = lies_gpkg_polygone(_gpkg([quadrat, loch], 4326))
    flaeche = flaeche_aus_gpkg(geometrie)
    assert len(flaeche.polygone[0].loecher) == 0
    assert flaeche.entartet[0].rolle is RingRolle.LOCH
    with pytest.raises(GeometrieFehler):
        flaeche_aus_gpkg(geometrie, strikt=True)


def test_geopackage_projected_needs_conversion() -> None:
    ost, nord = geographisch_nach_utm(Punkt(50.11, 8.68), ETRS89_UTM32N)
    geometrie = lies_gpkg_polygone(_gpkg([[(ost, nord)] * 4], 25832))
    with pytest.raises(ProfilFehler):
        flaeche_aus_gpkg(geometrie)
    flaeche = flaeche_aus_gpkg(
        geometrie, umrechnung=lambda x, y: utm_nach_geographisch_lonlat(x, y, ETRS89_UTM32N)
    )
    (objekt,) = flaeche.objekte_ohne_flaeche
    assert objekt.art is Entartung.PUNKT
    assert randabstand_m(Punkt(50.11045, 8.68), flaeche, KUGEL_MITTLERER_RADIUS) == pytest.approx(
        50.04, abs=0.01
    )
