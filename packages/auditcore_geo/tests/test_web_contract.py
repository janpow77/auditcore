"""REST-Vertrag der Geo-Oberfläche ohne Web-Framework (``auditcore_geo.web``)."""

from __future__ import annotations

import math
from typing import Any

import pytest

from auditcore_geo import KUGEL_MITTLERER_RADIUS, Punkt, grosskreis_m
from auditcore_geo.web import (
    ContractError,
    Settings,
    catalogue,
    from_utm,
    locate,
    radius_search,
    simplify,
    standard_zone,
    to_utm,
)

R1 = KUGEL_MITTLERER_RADIUS.profil_id
SQUARE = {
    "type": "Polygon",
    "coordinates": [[[8.66, 50.10], [8.68, 50.10], [8.68, 50.11], [8.66, 50.11], [8.66, 50.10]]],
}


def test_profile_nennt_empfehlungen_und_schaltet_geocoder_ab() -> None:
    data: dict[str, Any] = catalogue(Settings())
    assert data["empfohlenes_erdmodell"] == R1
    assert data["rand_gilt_als_innen_empfohlen"] is True
    assert {e["id"] for e in data["erdmodelle"]} == {R1, "kugel.6371000m"}
    assert data["geocoder"] == {"aktiv": False, "namensnennung": None}
    assert data["gpkg_quellen"] == []


def test_umkreis_sortiert_nach_entfernung_mit_kennungen() -> None:
    zentrum = {"lat": 50.1106, "lon": 8.6821}
    punkte = [
        {"id": "fern", "lat": 52.52, "lon": 13.405},
        {"id": "nah", "lat": 50.14, "lon": 8.68},
        {"lat": 50.1106, "lon": 8.6821},
    ]
    data: dict[str, Any] = radius_search(
        {"zentrum": zentrum, "punkte": punkte, "radius_m": 5000, "erdmodell": R1}, Settings()
    )
    assert [t["id"] for t in data["treffer"]] == ["2", "nah"]
    erwartet = grosskreis_m(Punkt(50.1106, 8.6821), Punkt(50.14, 8.68), KUGEL_MITTLERER_RADIUS)
    assert data["treffer"][1]["abstand_m"] == pytest.approx(erwartet)
    assert data["geprueft"] == 3


@pytest.mark.parametrize(
    ("aenderung", "code"),
    [
        ({"erdmodell": None}, "ungueltige_eingabe"),
        ({"erdmodell": "kugel.egal"}, "profil_fehler"),
        ({"radius_m": -1}, "ungueltige_eingabe"),
        ({"radius_m": True}, "ungueltige_eingabe"),
        ({"zentrum": {"lat": 91, "lon": 0}}, "koordinaten_fehler"),
        ({"punkte": "keine"}, "ungueltige_eingabe"),
        ({"punkte": [{"id": [1], "lat": 0, "lon": 0}]}, "ungueltige_eingabe"),
    ],
)
def test_umkreis_weist_ungueltiges_ab(aenderung: dict[str, Any], code: str) -> None:
    anfrage = {"zentrum": {"lat": 50, "lon": 8}, "punkte": [], "radius_m": 1, "erdmodell": R1}
    with pytest.raises(ValueError) as info:
        radius_search({**anfrage, **aenderung}, Settings())
    assert getattr(info.value, "code", None) == code


def test_umkreis_begrenzt_die_punktzahl() -> None:
    anfrage = {
        "zentrum": {"lat": 50, "lon": 8},
        "punkte": [{"lat": 50, "lon": 8}] * 3,
        "radius_m": 1,
        "erdmodell": R1,
    }
    with pytest.raises(ContractError) as info:
        radius_search(anfrage, Settings(max_points=2))
    assert info.value.status == 413


@pytest.mark.parametrize(
    ("punkt", "rand_innen", "lage", "enthaelt"),
    [
        ({"lat": 50.105, "lon": 8.67}, True, "innen", True),
        ({"lat": 50.10, "lon": 8.67}, True, "rand", True),
        ({"lat": 50.10, "lon": 8.67}, False, "rand", False),
        ({"lat": 50.12, "lon": 8.67}, True, "aussen", False),
    ],
)
def test_lage_mit_ausdruecklicher_randregel(
    punkt: dict[str, float], rand_innen: bool, lage: str, enthaelt: bool
) -> None:
    data = locate(
        {"punkt": punkt, "flaeche": SQUARE, "erdmodell": R1, "rand_gilt_als_innen": rand_innen}
    )
    assert (data["lage"], data["enthaelt"]) == (lage, enthaelt)
    if lage == "aussen":
        assert round(float(str(data["abstand_m"]))) == 1112


def test_lage_toleranz_macht_nahen_punkt_zum_rand() -> None:
    anfrage = {
        "punkt": {"lat": 50.10001, "lon": 8.67},
        "flaeche": SQUARE,
        "erdmodell": R1,
        "rand_gilt_als_innen": False,
        "rand_toleranz_m": 5,
    }
    data = locate(anfrage)
    assert (data["lage"], data["lage_mit_toleranz"], data["enthaelt"]) == ("innen", "rand", False)


def test_lage_verlangt_randregel_und_meldet_entartete_ringe() -> None:
    with pytest.raises(ContractError, match="rand_gilt_als_innen"):
        locate({"punkt": {"lat": 0, "lon": 0}, "flaeche": SQUARE, "erdmodell": R1})
    punktflaeche = {"type": "Polygon", "coordinates": [[[8.7, 50.2]] * 4]}
    data: dict[str, Any] = locate(
        {
            "punkt": {"lat": 50.2, "lon": 8.7},
            "flaeche": punktflaeche,
            "erdmodell": R1,
            "rand_gilt_als_innen": True,
        }
    )
    assert data["lage"] == "rand" and data["entarteter_ring"]["art"] == "punkt"
    assert "GEO-C16" in data["hinweise"][0]


def test_utm_hin_und_zurueck() -> None:
    hin: dict[str, Any] = to_utm(
        {"punkt": {"lat": 50.10181, "lon": 8.678392}, "ellipsoid": "GRS80"}
    )
    assert (hin["zone"], hin["epsg"], hin["nordhalbkugel"]) == (32, 25832, True)
    assert hin["ost"] == pytest.approx(477000.0, abs=0.05)
    assert hin["nord"] == pytest.approx(5550000.0, abs=0.05)
    zurueck: dict[str, Any] = from_utm(
        {
            "ost": hin["ost"],
            "nord": hin["nord"],
            "zone": 32,
            "nordhalbkugel": True,
            "ellipsoid": "GRS80",
        }
    )
    assert zurueck["punkt"]["lat"] == pytest.approx(50.10181, abs=1e-6)
    sued: dict[str, Any] = to_utm({"punkt": {"lat": -33.9, "lon": 18.4}, "ellipsoid": "WGS84"})
    assert (sued["zone"], sued["epsg"]) == (34, 32734)
    assert standard_zone(180.0) == 60 and standard_zone(-180.0) == 1
    with pytest.raises(ContractError, match="ellipsoid"):
        to_utm({"punkt": {"lat": 50, "lon": 8}})
    with pytest.raises(ContractError, match="zone"):
        from_utm({"ost": 1.0, "nord": 1.0, "nordhalbkugel": True, "ellipsoid": "GRS80"})


def _kreis(n: int, radius: float = 0.01) -> dict[str, object]:
    ring = [
        [
            8.68 + radius * math.cos(2 * math.pi * i / n),
            50.11 + radius * math.sin(2 * math.pi * i / n),
        ]
        for i in range(n)
    ]
    return {"type": "Polygon", "coordinates": [[*ring, ring[0]]]}


def test_vereinfachung_in_metern_und_grad() -> None:
    kreis = _kreis(200)
    meter: dict[str, Any] = simplify(
        {"flaeche": kreis, "toleranz": 50, "einheit": "meter"}, Settings()
    )
    assert meter["stuetzpunkte_vorher"] == 201
    assert 4 <= meter["stuetzpunkte_nachher"] < 40 and meter["utm_zone"] == 32
    grad: dict[str, Any] = simplify(
        {"flaeche": kreis, "toleranz": 0.0, "einheit": "grad", "stellen": 4}, Settings()
    )
    assert grad["utm_zone"] is None
    assert grad["geometrie"]["coordinates"][0][0][0] == [round(8.69, 4), round(50.11, 4)]


def test_vereinfachung_meldet_entfallene_ringe() -> None:
    mit_loch = _kreis(40, 0.02)
    loch = _kreis(40, 0.0001)["coordinates"]
    assert isinstance(loch, list) and isinstance(mit_loch["coordinates"], list)
    mit_loch["coordinates"] = [mit_loch["coordinates"][0], loch[0]]
    data: dict[str, Any] = simplify(
        {"flaeche": mit_loch, "toleranz": 100, "einheit": "meter"}, Settings()
    )
    assert data["entfallene_ringe"] == [{"polygon": 0, "ring": 1}]
    alles: dict[str, Any] = simplify(
        {"flaeche": _kreis(10, 1e-6), "toleranz": 1000, "einheit": "meter"}, Settings()
    )
    assert alles["geometrie"] is None and alles["entfallene_ringe"] == [{"polygon": 0, "ring": 0}]


@pytest.mark.parametrize(
    "aenderung",
    [{"einheit": "fuss"}, {"stellen": 13}, {"stellen": True}, {"toleranz": -1}],
)
def test_vereinfachung_weist_ab(aenderung: dict[str, object]) -> None:
    with pytest.raises(ContractError):
        simplify({"flaeche": SQUARE, "toleranz": 1, "einheit": "grad", **aenderung}, Settings())
    with pytest.raises(ContractError) as info:
        simplify(
            {"flaeche": _kreis(50), "toleranz": 1, "einheit": "grad"},
            Settings(max_vertices=10),
        )
    assert info.value.status == 413
