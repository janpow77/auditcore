"""GeoPackage-Dateien über die Web-Schnittstelle lesen (synthetische Dateien)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from geopackage_builder import SQUARE, gpkg_blob, gpkg_file

from auditcore_geo import ETRS89_UTM32N, Punkt, geographisch_nach_utm
from auditcore_geo.web import ContractError, Settings, read_geopackage, read_source


def test_geographische_flaechen_mit_bezeichnung() -> None:
    daten = gpkg_file(
        [("Gebiet A", gpkg_blob([[SQUARE]], 4326)), (None, gpkg_blob([[SQUARE]], 4326))]
    )
    result: dict[str, Any] = read_geopackage(daten, Settings())
    assert result["tabellen"] == ["gebiete"] and result["srs_id"] == 4326
    assert result["umgerechnet"] is False and result["abgeschnitten"] is False
    erste = result["flaechen"][0]
    assert erste["bezeichnung"] == "Gebiet A" and erste["geometrie"]["type"] == "MultiPolygon"
    assert erste["geometrie"]["coordinates"][0][0][0] == [8.66, 50.10]
    assert result["flaechen"][1]["bezeichnung"] is None


def test_utm_32n_wird_zurueckgerechnet() -> None:
    ring = [geographisch_nach_utm(Punkt(lat=y, lon=x), ETRS89_UTM32N) for x, y in SQUARE]
    result: dict[str, Any] = read_geopackage(
        gpkg_file([("UTM", gpkg_blob([[ring]], 25832))], 25832), Settings()
    )
    assert result["umgerechnet"] is True
    lon, lat = result["flaechen"][0]["geometrie"]["coordinates"][0][0][0]
    assert (lon, lat) == pytest.approx((8.66, 50.10), abs=1e-7)


def test_fehlerhafte_geometrie_wird_gemeldet_nicht_verworfen() -> None:
    daten = gpkg_file(
        [("gut", gpkg_blob([[SQUARE]], 4326)), ("kaputt", b"GP\x00\x01xxxx"), ("leer", None)]
    )
    result: dict[str, Any] = read_geopackage(daten, Settings())
    assert len(result["flaechen"]) == 1
    assert [f["id"] for f in result["fehler"]] == ["2", "3"]


def test_grenzen_und_abschneiden() -> None:
    daten = gpkg_file([(f"G{i}", gpkg_blob([[SQUARE]], 4326)) for i in range(3)])
    result: dict[str, Any] = read_geopackage(daten, Settings(max_gpkg_areas=2))
    assert len(result["flaechen"]) == 2 and result["abgeschnitten"] is True
    with pytest.raises(ContractError) as info:
        read_geopackage(daten, Settings(max_gpkg_bytes=100))
    assert info.value.status == 413


@pytest.mark.parametrize(
    ("daten", "code"),
    [
        (b"kein sqlite", "kein_geopackage"),
        (b"SQLite format 3\x00" + b"\x00" * 200, "kein_geopackage"),
    ],
)
def test_keine_geopackage_datei(daten: bytes, code: str) -> None:
    with pytest.raises(ContractError) as info:
        read_geopackage(daten, Settings())
    assert info.value.code == code


def test_unbekannte_tabelle_und_bezugssystem() -> None:
    daten = gpkg_file([("A", gpkg_blob([[SQUARE]], 3035))], 3035)
    with pytest.raises(ContractError, match="srs_id 3035"):
        read_geopackage(daten, Settings())
    with pytest.raises(ContractError) as info:
        read_geopackage(daten, Settings(), "fehlt")
    assert info.value.status == 404


def test_benannte_quelle_des_servers(tmp_path: Path) -> None:
    datei = tmp_path / "schutzgebiete.gpkg"
    datei.write_bytes(gpkg_file([("Schutzgebiet", gpkg_blob([[SQUARE]], 4326))], table="schutz"))
    settings = Settings(gpkg_sources={"schutz": datei})
    result: dict[str, Any] = read_source("schutz", settings)
    assert result["quelle"] == "schutz" and result["tabelle"] == "schutz"
    with pytest.raises(ContractError) as info:
        read_source("andere", settings)
    assert info.value.status == 404
