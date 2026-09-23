"""Nominatim-Adapter: Vertrag von auditcore_harvest, Nutzungsbedingungen, Anfragebildung."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from auditcore_harvest import (
    ConfigError,
    HarvestEngine,
    HarvestRequest,
    RateLimit,
    ReplayTransport,
    Response,
    RunStatus,
)
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.testing import assert_adapter

from auditcore_geo.nominatim import (
    MINDESTABSTAND_REGELMAESSIG_S,
    NominatimAdapter,
    empfohlene_laufparameter,
    pruefe_laufparameter,
)

FIXTURES = Path(__file__).parent / "fixtures"
REPLAY = FIXTURES / "nominatim_synthetic.json"
LEGACY = json.loads((FIXTURES / "legacy_observed.json").read_text(encoding="utf-8"))

KONFIG: dict[str, Any] = {
    "anfragen": [
        {"id": "vorhaben-1", "q": "Musterstraße 1,  60311 Musterstadt"},
        {"id": "vorhaben-2", "q": "Neustadt"},
        {
            "id": "vorhaben-3",
            "strukturiert": {"street": "Beispielweg 9", "postalcode": "99999", "city": "Nirgendwo"},
        },
    ],
    "user_agent": "auditcore_geo-tests/0.1.0 (https://github.com/janpow77/auditcore)",
    "budget": 3,
    "laufart": "einmalig",
    "countrycodes": "de",
    "limit": 2,
}


def lauf(transport: Any, konfig: dict[str, Any] = KONFIG) -> tuple[Any, ListSink, ClockSleeper]:
    clock = FixedClock()
    sleeper = ClockSleeper(clock)
    rate, request = empfohlene_laufparameter(konfig, "lauf-1")
    engine = HarvestEngine(
        transport, StaticCredentials({}), MemoryStateStore(), clock, sleeper, rate_limit=rate
    )
    sink = ListSink()
    return engine.run(NominatimAdapter(), request, sink, config=konfig), sink, sleeper


def test_adapter_fulfils_the_harvest_contract() -> None:
    report = assert_adapter(
        NominatimAdapter,
        config=KONFIG,
        transport_factory=lambda: ReplayTransport.from_file(REPLAY),
        min_records=3,
    )
    assert report.passed


def test_records_keep_every_hit_without_invented_confidence() -> None:
    result, sink, sleeper = lauf(ReplayTransport.from_file(REPLAY))
    assert result.status is RunStatus.COMPLETE
    records = {r.record_id: r.normalized for r in sink.records.values()}
    assert records["vorhaben-1"]["status"] == "treffer"
    assert records["vorhaben-1"]["treffer"][0]["lat"] == 50.11
    assert records["vorhaben-1"]["anfrage"]["q"] == "Musterstraße 1, 60311 Musterstadt"
    zweideutig = records["vorhaben-2"]
    assert zweideutig["anzahl"] == 2  # Mehrdeutigkeit bleibt sichtbar, kein erster Treffer gewählt
    assert all("konfidenz" not in t for t in zweideutig["treffer"])
    assert records["vorhaben-3"]["status"] == "kein_treffer"
    assert "OpenStreetMap" in records["vorhaben-1"]["lizenz"]
    # Takt am öffentlichen Endpunkt: mindestens 1 s zwischen den Anfragen.
    assert sleeper.sleeps and min(sleeper.sleeps) >= 1.0


class _Fehler:
    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        return Response(503, b"", {}, url)


def test_service_failure_is_not_a_missing_hit() -> None:
    """GEO-C10: flowworkshop meldet einen Netzfehler wie „nicht gefunden“ (``None``)."""
    workshop = [f for f in LEGACY["cases"]["nominatim"] if f["eingabe"] == "Fehlerstadt"]
    assert any(f["ergebnis"] == {"ok": None} for f in workshop)
    result, sink, _ = lauf(_Fehler())
    assert result.status is RunStatus.FAILED
    assert not sink.records
    assert result.errors and result.errors[0]["code"] == "transport_error"


def _mit(**aenderung: Any) -> dict[str, Any]:
    return {**KONFIG, **aenderung}


@pytest.mark.parametrize(
    "konfig",
    [
        _mit(user_agent="python-requests/2.31"),
        _mit(user_agent="Mozilla/5.0 (X11; Linux x86_64)"),
        _mit(user_agent=""),
        _mit(budget=2),
        _mit(budget=0),
        _mit(laufart="dauernd"),
        _mit(basis_url="http://nominatim.openstreetmap.org"),
        _mit(limit=41),
        _mit(countrycodes="DE"),
        _mit(anfragen=[]),
        _mit(anfragen=[{"id": "a", "q": "x"}, {"id": "a", "q": "y"}]),
        _mit(anfragen=[{"id": "a", "q": "x", "strukturiert": {"city": "y"}}]),
        _mit(anfragen=[{"id": "a", "strukturiert": {"hausnummer": "1"}}]),
        _mit(anfragen=[{"id": "", "q": "x"}]),
        _mit(email=""),
        _mit(addressdetails="ja"),
    ],
)
def test_configuration_enforces_usage_policy(konfig: dict[str, Any]) -> None:
    with pytest.raises(ConfigError):
        NominatimAdapter().validate_config(konfig)


def test_run_parameters_enforce_rate_and_budget() -> None:
    request = HarvestRequest("geo.nominatim_search", "x", max_pages=3)
    with pytest.raises(ConfigError):
        pruefe_laufparameter(KONFIG, RateLimit(0.5), request)
    with pytest.raises(ConfigError):
        pruefe_laufparameter(KONFIG, RateLimit(1.0), HarvestRequest("geo.nominatim_search", "x"))
    pruefe_laufparameter(KONFIG, RateLimit(1.0), request)
    regelmaessig = _mit(laufart="regelmaessig")
    with pytest.raises(ConfigError):
        pruefe_laufparameter(regelmaessig, RateLimit(1.0), request)
    rate, _ = empfohlene_laufparameter(regelmaessig, "x")
    assert rate.min_interval_seconds == MINDESTABSTAND_REGELMAESSIG_S
    eigene = _mit(basis_url="https://geocoder.intern.example")
    assert empfohlene_laufparameter(eigene, "x")[0].min_interval_seconds == 0.0


class _Aufzeichnung:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        self.calls.append({"url": url, **kwargs})
        return Response(200, b"[]", {}, url)


@pytest.mark.parametrize(
    ("aufrufer", "zusatz"),
    [
        ("osint.vorhaben_verorten.abfragen", {"addressdetails": False, "accept_language": "de"}),
        ("audit_designer.gis._geocode_address", {"addressdetails": True}),
    ],
)
def test_request_formation_matches_the_sources(aufrufer: str, zusatz: dict[str, Any]) -> None:
    """Gleiche Suchparameter wie osint und audit_designer (jsonv2, limit 1, countrycodes de)."""
    fall = next(
        f for f in LEGACY["cases"]["nominatim"] if f["aufrufer"] == aufrufer and f["anfragen"]
    )
    original = fall["anfragen"][0]
    konfig = {
        "anfragen": [{"id": "a", "q": original["params"]["q"]}],
        "user_agent": "auditcore_geo-tests/0.1.0",
        "budget": 1,
        "laufart": "einmalig",
        "countrycodes": "de",
        "limit": 1,
        **zusatz,
    }
    transport = _Aufzeichnung()
    lauf(transport, konfig)
    gesendet = transport.calls[0]
    assert gesendet["url"] == original["url"]
    erwartet = dict(original["params"])
    if "accept_language" in zusatz:  # osint sendet die Sprache als Kopfzeile, hier als Parameter
        erwartet["accept-language"] = "de"
    assert gesendet["params"] == erwartet
    assert set(gesendet["headers"]) == {"User-Agent"}


def test_workshop_format_json_differs_from_jsonv2() -> None:
    """GEO-C11: flowworkshop fragt ``format=json`` ab (Feld ``class``), der Adapter jsonv2."""
    workshop = next(
        f for f in LEGACY["cases"]["nominatim"] if f["aufrufer"].startswith("flowworkshop")
    )
    assert workshop["anfragen"][0]["params"]["format"] == "json"


def test_designer_confidence_is_invented() -> None:
    """GEO-C12: audit_designer setzt 0,85/0,95 aus ``class``; jsonv2 liefert ``category``."""
    faelle = [
        f
        for f in LEGACY["cases"]["nominatim"]
        if f["aufrufer"] == "audit_designer.gis._geocode_address" and "ok" in f["ergebnis"]
    ]
    assert sorted(f["ergebnis"]["ok"][2] for f in faelle) == [0.85, 0.95]


def test_email_is_sent_but_never_part_of_the_record() -> None:
    transport = _Aufzeichnung()
    konfig = _mit(email="kontakt@example.invalid", anfragen=[{"id": "a", "q": "x"}], budget=1)
    _, sink, _ = lauf(transport, konfig)
    assert transport.calls[0]["params"]["email"] == "kontakt@example.invalid"
    assert "example.invalid" not in json.dumps([r.normalized for r in sink.records.values()])
