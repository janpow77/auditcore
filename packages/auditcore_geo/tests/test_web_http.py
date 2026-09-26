"""Starlette-Routen und optionaler FastAPI-Router von auditcore_geo.web."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from geopackage_builder import SQUARE, gpkg_blob, gpkg_file  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from auditcore_geo.web import Settings, create_app, create_router  # noqa: E402

PREFIX = "/api/geo"
R1 = "kugel.r1_6371008_8m"


def _fastapi_client(settings: Settings) -> TestClient:
    fastapi = pytest.importorskip("fastapi")
    app = fastapi.FastAPI()
    app.include_router(create_router(PREFIX, settings=settings))
    return TestClient(app)


@pytest.fixture(params=["starlette", "fastapi"])
def client(request: pytest.FixtureRequest, tmp_path: Path) -> TestClient:
    datei = tmp_path / "demo.gpkg"
    datei.write_bytes(gpkg_file([("Demo", gpkg_blob([[SQUARE]], 4326))]))
    settings = Settings(gpkg_sources={"demo": datei}, max_body_bytes=4096)
    if request.param == "fastapi":
        return _fastapi_client(settings)
    return TestClient(create_app(PREFIX, settings=settings))


def test_profile_und_rechnen(client: TestClient) -> None:
    profil: dict[str, Any] = client.get(f"{PREFIX}/profile").json()
    assert profil["gpkg_quellen"] == ["demo"] and profil["geocoder"]["aktiv"] is False
    anfrage = {
        "zentrum": {"lat": 50.0, "lon": 8.0},
        "punkte": [{"id": "a", "lat": 50.001, "lon": 8.0}],
        "radius_m": 500,
        "erdmodell": R1,
    }
    umkreis = client.post(f"{PREFIX}/umkreis", json=anfrage)
    assert umkreis.status_code == 200 and umkreis.json()["treffer"][0]["id"] == "a"
    utm = client.post(f"{PREFIX}/utm", json={"punkt": {"lat": 50, "lon": 8}, "ellipsoid": "GRS80"})
    assert utm.json()["zone"] == 32
    zurueck = client.post(
        f"{PREFIX}/utm/geographisch",
        json={**utm.json(), "ellipsoid": "GRS80"},
    )
    assert zurueck.status_code == 200


def test_fehler_als_json(client: TestClient) -> None:
    kaputt = client.post(f"{PREFIX}/lage", content=b"{nein")
    assert kaputt.status_code == 400 and kaputt.json()["error"]["code"] == "ungueltiges_json"
    gross = client.post(f"{PREFIX}/umkreis", content=b"[" + b"1," * 4000 + b"1]")
    assert gross.status_code == 413
    geo = client.post(
        f"{PREFIX}/lage",
        json={
            "punkt": {"lat": 0, "lon": 0},
            "flaeche": {"type": "Point", "coordinates": [0, 0]},
            "erdmodell": R1,
            "rand_gilt_als_innen": True,
        },
    )
    assert geo.status_code == 422 and geo.json()["error"]["code"] == "geometrie_fehler"
    aus = client.post(f"{PREFIX}/geocode", json={"anfrage": "Musterstraße 1"})
    assert aus.status_code == 404 and aus.json()["error"]["code"] == "geocoder_abgeschaltet"


def test_gpkg_hochladen_und_quelle(client: TestClient) -> None:
    daten = gpkg_file([("Hochgeladen", gpkg_blob([[SQUARE]], 4326))])
    antwort = client.post(
        f"{PREFIX}/gpkg",
        content=daten,
        headers={"Content-Type": "application/geopackage+sqlite3"},
    )
    assert antwort.status_code == 200
    assert antwort.json()["flaechen"][0]["bezeichnung"] == "Hochgeladen"
    assert client.get(f"{PREFIX}/gpkg/quellen").json() == {"quellen": ["demo"]}
    quelle = client.get(f"{PREFIX}/gpkg/quellen/demo?tabelle=gebiete")
    assert quelle.status_code == 200 and quelle.json()["quelle"] == "demo"
    assert client.get(f"{PREFIX}/gpkg/quellen/fehlt").status_code == 404
    assert client.post(f"{PREFIX}/gpkg", content=b"nein").status_code == 422


def test_import_laedt_weder_framework_noch_harvest() -> None:
    code = (
        "import sys, auditcore_geo.web; "
        "assert 'starlette' not in sys.modules, 'starlette'; "
        "assert 'fastapi' not in sys.modules, 'fastapi'; "
        "assert 'auditcore_harvest' not in sys.modules, 'harvest'"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
