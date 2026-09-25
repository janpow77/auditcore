"""Adresssuche: nur mit ausdrücklich angeschlossenem Geocoder, Nominatim über harvest."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

harvest = pytest.importorskip("auditcore_harvest")
pytest.importorskip("starlette")

from auditcore_harvest import ReplayTransport  # noqa: E402
from auditcore_harvest.memory import ClockSleeper, FixedClock  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from auditcore_geo.web import (  # noqa: E402
    Geocoder,
    GeocoderError,
    NominatimGeocoder,
    Settings,
    catalogue,
    create_app,
)

REPLAY = Path(__file__).parent / "fixtures" / "nominatim_synthetic.json"
ANFRAGE = "Musterstraße 1, 60311 Musterstadt"


def _geocoder(**kwargs: Any) -> tuple[NominatimGeocoder, ReplayTransport, ClockSleeper]:
    transport = ReplayTransport.from_file(REPLAY)
    clock = FixedClock()
    sleeper = ClockSleeper(clock)
    geocoder = NominatimGeocoder(
        transport,
        clock,
        sleeper,
        user_agent="auditcore_geo-tests/0.3.0 (https://github.com/janpow77/auditcore)",
        limit=2,
        **kwargs,
    )
    return geocoder, transport, sleeper


def test_nominatim_sucht_und_speichert_zwischen() -> None:
    geocoder, transport, _ = _geocoder()
    assert isinstance(geocoder, Geocoder)
    treffer = geocoder.search(ANFRAGE)
    assert treffer[0]["lat"] == 50.11
    assert str(treffer[0]["anzeigename"]).startswith("Musterstraße 1")
    assert geocoder.search(f"  {ANFRAGE.upper()} ") == treffer
    assert len(transport.calls) == 1 and geocoder.sent_today == 1
    assert "OpenStreetMap" in geocoder.attribution


def test_tagesgrenze_des_oeffentlichen_dienstes() -> None:
    geocoder, transport, _ = _geocoder(sent_today=1000)
    with pytest.raises(GeocoderError) as info:
        geocoder.search(ANFRAGE)
    assert info.value.status == 429 and transport.calls == []


def test_dienstfehler_ist_kein_leeres_ergebnis() -> None:
    geocoder, _, _ = _geocoder()
    with pytest.raises(GeocoderError) as info:
        geocoder.search("Unbekannte Anfrage ohne Aufzeichnung")
    assert info.value.status == 502


def test_rest_endpunkt_mit_geocoder() -> None:
    geocoder, _, _ = _geocoder()
    settings = Settings(geocoder=geocoder)
    assert catalogue(settings)["geocoder"] == {
        "aktiv": True,
        "namensnennung": geocoder.attribution,
    }
    client = TestClient(create_app("/geo", settings=settings))
    antwort = client.post("/geo/geocode", json={"anfrage": ANFRAGE})
    assert antwort.status_code == 200 and antwort.json()["treffer"][0]["rang"] == 1
    leer = client.post("/geo/geocode", json={"anfrage": " "})
    assert leer.status_code == 422
    fehler = client.post("/geo/geocode", json={"anfrage": "nicht aufgezeichnet"})
    assert fehler.status_code == 502 and fehler.json()["error"]["code"] == "geocoder_fehler"
