"""Struktur der Refaktorierung 0.2.1: ausgelagerte Hilfen verhalten sich wie zuvor."""

from __future__ import annotations

import struct
from typing import Any

import pytest

from auditcore_geo import GeometrieFehler, flaeche_aus_ringen, legacy, lies_gpkg_polygone
from auditcore_geo._nominatim_daten import _rahmen, _zahl

harvest = pytest.importorskip("auditcore_harvest")
nominatim = pytest.importorskip("auditcore_geo.nominatim")

GUELTIG: dict[str, Any] = {
    "anfragen": [{"id": "a-1", "q": "Neustadt"}],
    "user_agent": "auditcore_geo-tests (https://github.com/janpow77/auditcore)",
    "budget": 1,
    "laufart": "einmalig",
}


@pytest.mark.parametrize(
    ("wert", "erwartet"),
    [
        (None, None),
        ([1], None),
        ({"a": 1}, None),
        ("x", None),
        ("nan", None),
        ("1.5", 1.5),
        (2, 2.0),
        (True, 1.0),
    ],
)
def test_zahl_liest_nur_json_zahlen_und_texte(wert: object, erwartet: float | None) -> None:
    assert _zahl(wert) == erwartet


def test_rahmen_nur_mit_vier_zahlen() -> None:
    assert _rahmen("1234") is None
    assert _rahmen(["1", "2", "3"]) is None
    assert _rahmen(["1", "2", "x", "4"]) is None
    assert _rahmen(["1", "2", "3", "4"]) == {"sued": 1.0, "nord": 2.0, "west": 3.0, "ost": 4.0}


@pytest.mark.parametrize(
    ("aenderung", "meldung"),
    [
        ({"anfragen": [{"id": "a", "strukturiert": {}}]}, "nichtleeres Objekt"),
        ({"anfragen": [{"id": "a", "strukturiert": {"land": "x"}}]}, "unbekanntes Feld"),
        ({"anfragen": [{"id": "a", "strukturiert": {"city": " "}}]}, "ist leer"),
        ({"anfragen": [{"id": "a", "q": " "}]}, "q ist leer"),
        ({"anfragen": ["a"]}, "muss ein Objekt sein"),
        ({"user_agent": "python-requests/2.0"}, "Standardkennung"),
        ({"budget": 0}, "budget"),
        ({"basis_url": "ftp://x"}, "Adresse sein"),
        ({"basis_url": "http://nominatim.openstreetmap.org"}, "https"),
        ({"budget": 5000}, "Tagesgrenze"),
        ({"limit": 41}, "limit"),
        ({"countrycodes": "DE"}, "countrycodes"),
        ({"email": " "}, "email ist leer"),
        ({"addressdetails": "ja"}, "addressdetails"),
    ],
)
def test_pruefe_konfiguration_meldet_wie_zuvor(aenderung: dict[str, Any], meldung: str) -> None:
    with pytest.raises(harvest.ConfigError, match=meldung):
        nominatim.pruefe_konfiguration({**GUELTIG, **aenderung})
    with pytest.raises(harvest.ConfigError, match=meldung):
        nominatim.NominatimAdapter().validate_config({**GUELTIG, **aenderung})


def test_gpkg_kopf_fehler() -> None:
    kopf = b"GP\x00\x01" + struct.pack("<i", 4326)
    with pytest.raises(GeometrieFehler, match="Version"):
        lies_gpkg_polygone(b"GP\x01\x01" + kopf[4:])
    with pytest.raises(GeometrieFehler, match="Erweiterter"):
        lies_gpkg_polygone(b"GP\x00\x21" + kopf[4:])
    with pytest.raises(GeometrieFehler, match="Leere"):
        lies_gpkg_polygone(b"GP\x00\x11" + kopf[4:])
    with pytest.raises(GeometrieFehler, match="Hüllrechteck"):
        lies_gpkg_polygone(b"GP\x00\x0f" + kopf[4:])


def test_flaechenleser_fehler() -> None:
    with pytest.raises(GeometrieFehler, match="Punktliste"):
        flaeche_aus_ringen([["kein ring"]])
    with pytest.raises(GeometrieFehler, match="nicht endlich"):
        flaeche_aus_ringen([[[(0.0, float("inf")), (1.0, 0.0), (1.0, 1.0)]]])
    with pytest.raises(GeometrieFehler, match="ohne Positionen"):
        flaeche_aus_ringen([[[]]])


def test_legacy_namen_bleiben_importierbar() -> None:
    assert all(getattr(legacy, name) is not None for name in legacy.__all__)
