"""Adapters against the executed original connectors (same payloads, same requests).

The legacy fixture was produced by ``tools/capture_regulierung_connectors.py``
from ``janpow77/regulierung@853676d2`` with an in-process mock transport.
Each test replays the identical synthetic payload through the new adapter and
compares requests, parsed values and the rows the original stored. Deliberate
differences carry their number from ``docs/behavior-changes.md`` (PS-Cxx).
"""

from __future__ import annotations

import base64
import hashlib
from datetime import date
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs

from auditcore_harvest import RunStatus
from support import (
    BASE,
    BUNDESBANK_PARAMS,
    BUNDESBANK_URL,
    EIA_URL,
    OBSERVED,
    PAYLOADS,
    TK_PARAMS,
    TK_URL,
    eia_params,
    exchange,
    run,
    scenario,
)

from auditcore_price_sources import (
    BundesbankSeriesAdapter,
    DestatisTabellenAdapter,
    EiaSpotPriceAdapter,
    OverpassFuelStationAdapter,
    PageSnapshotAdapter,
    check_list_response,
    fuel_query,
    legacy_commodity_rows,
    legacy_exchange_rate_rows,
    legacy_station_fields,
    legacy_status,
    package_sha256,
)


def legacy_rows(name: str, kind: str) -> list[dict[str, Any]]:
    return [r for r in scenario(name)["rows"] if r["$type"] == kind]


def test_fixture_binding() -> None:
    assert OBSERVED["commit"] == "853676d2b1ab792395d63c62c9f96d5edcca8c2d"
    assert len(OBSERVED["scenarios"]) == 30
    for name, digest in OBSERVED["payload_sha256"].items():
        assert hashlib.sha256((PAYLOADS / name).read_bytes()).hexdigest() == digest, name


def test_bundesbank_request_and_stored_rows_match_the_original() -> None:
    legacy = scenario("bundesbank-ok")
    request = legacy["requests"][0]
    assert request["url"] == BUNDESBANK_URL and request["params"] == BUNDESBANK_PARAMS
    assert request["accept"] == "application/json"
    result, sink, replay = run(
        BundesbankSeriesAdapter(),
        exchanges=[exchange(BUNDESBANK_URL, BUNDESBANK_PARAMS, "bundesbank_fx.json")],
    )
    assert replay.calls[0]["header_names"] == ["accept"]
    records = list(sink.records.values())
    rows = legacy_exchange_rate_rows(records)
    old = legacy_rows("bundesbank-ok", "Wechselkurs")
    assert [(r["stichtag"].isoformat(), r["kurs"]) for r in rows] == [
        (o["stichtag"]["$date"], Decimal(str(o["kurs"]))) for o in old
    ]
    assert {(r["waehrung_basis"], r["waehrung_kurs"], r["quelle"]) for r in rows} == {
        ("USD", "EUR", "BUNDESBANK")
    }
    # PS-C01: missing observations are records with status fehlwert, not dropped
    missing = [r.normalized for r in records if r.normalized["wert"] is None]
    assert [m["zeitbezug"]["wert"] for m in missing] == ["2026-08-29", "2026-08-30"]
    assert {m["status_quelle"] for m in missing} == {"K"}
    # PS-C02: unreadable value, empty date and index without period are issues (partial)
    assert result.status is RunStatus.PARTIAL and len(result.issues) == 3
    unit = records[0].normalized["einheit"]
    assert unit["text"] == "USD je 1 EUR" and unit["herkunft"] == "quelle"
    assert unit["zaehler"] == "USD" and unit["nenner"] == "EUR" and unit["multiplikator"] == 0


def test_bundesbank_package_hash_and_empty_answer() -> None:
    legacy = scenario("bundesbank-ok")["result"]
    body = (PAYLOADS / "bundesbank_fx.json").read_bytes()
    assert package_sha256(body, canonical_json=True) == legacy["paket_sha256"]
    empty = scenario("bundesbank-empty")["result"]
    assert empty["status"] == "erfolg" and empty["anzahl_datensaetze"] == 0
    result, sink, _ = run(
        BundesbankSeriesAdapter(),
        exchanges=[exchange(BUNDESBANK_URL, BUNDESBANK_PARAMS, "bundesbank_empty.json")],
    )
    # PS-C03: an answer without observations is partial, not a silent success
    assert result.status is RunStatus.PARTIAL and not sink.records
    assert legacy_status(result) == "teilweise"


def test_bundesbank_errors() -> None:
    assert scenario("bundesbank-http-500")["result"]["status"] == "fehler"
    result, _, _ = run(
        BundesbankSeriesAdapter(),
        exchanges=[exchange(BUNDESBANK_URL, BUNDESBANK_PARAMS, "bundesbank_fx.json", status=500)],
    )
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == "transport_error"
    assert result.attempts == 3  # bounded retries (the original did not retry)
    assert legacy_status(result) == "fehler"


def test_eia_rows_window_and_units_match_the_original() -> None:
    legacy = scenario("eia-ok")
    request = legacy["requests"][0]
    assert request["secret_params_present"] == ["api_key"]
    params = {k: v for k, v in request["params"].items()}
    # legacy window: 30 days up to today (2026-09-02 in the capture)
    assert (params["start"], params["end"]) == ("2026-08-03", "2026-09-02")
    ours = eia_params(0, 5000, start="2026-08-03", end="2026-09-02")
    assert {k: v for k, v in ours.items() if k != "offset"} == params  # PS-C04 adds offset
    result, sink, replay = run(
        EiaSpotPriceAdapter(),
        exchanges=[exchange(EIA_URL, ours, "eia_brent.json")],
        config={"url": BASE},
        filters={"start": "2026-08-03", "end": "2026-09-02"},
    )
    assert "api_key" not in replay.calls[0]["params"]
    rows = legacy_commodity_rows(list(sink.records.values()))
    old = legacy_rows("eia-ok", "Rohstoffpreis")
    assert sorted(
        (r["stichtag"].isoformat(), r["preis_usd"], r["einheit"]) for r in rows
    ) == sorted((o["stichtag"]["$date"], Decimal(str(o["preis_usd"])), o["einheit"]) for o in old)
    # PS-C05: empty values are fehlwert records, the unreadable period is an issue
    missing = sorted(
        r.normalized["zeitbezug"]["wert"]
        for r in sink.records.values()
        if r.normalized["wert"] is None
    )
    assert missing == ["2026-08-29", "2026-08-30"]
    assert result.status is RunStatus.PARTIAL and len(result.issues) == 1
    unit = next(iter(sink.records.values())).normalized["einheit"]
    assert unit == {
        "text": "USD/Barrel",
        "quelle_text": "$/BBL",
        "herkunft": "quelle",
        "zaehler": "USD",
        "nenner": None,
        "multiplikator": None,
    }
    assert legacy["result"]["paket_sha256"] == package_sha256(
        (PAYLOADS / "eia_brent.json").read_bytes(), canonical_json=True
    )


def test_eia_default_window_follows_the_engine_clock() -> None:
    result, sink, replay = run(EiaSpotPriceAdapter())
    assert result.status is RunStatus.COMPLETE and result.pages == 2
    assert replay.calls[0]["params"]["start"] == "2026-08-02"
    assert replay.calls[1]["params"]["offset"] == "3"


def test_eia_missing_key_is_an_auth_error_before_any_request() -> None:
    assert scenario("eia-no-key-harvest")["requests"] == []
    result, _, replay = run(EiaSpotPriceAdapter(), secrets={})
    assert result.errors[0]["code"] == "auth_error" and replay.calls == []


def test_tankerkoenig_health_semantics_match_the_original() -> None:
    for name, payload, status in (
        ("tankerkoenig-health-ok", "tankerkoenig_list.json", 200),
        ("tankerkoenig-health-api-error", "tankerkoenig_error.json", 200),
        ("tankerkoenig-health-http-500", "tankerkoenig_list.json", 500),
    ):
        legacy = scenario(name)
        ours = check_list_response(status, (PAYLOADS / payload).read_bytes())
        assert list(ours) == legacy["result"], name
    request = scenario("tankerkoenig-health-ok")["requests"][0]
    assert request["url"] == TK_URL and request["secret_params_present"] == ["apikey"]
    assert {k: v for k, v in request["params"].items()} == {
        **TK_PARAMS,
        "lat": "50.6",
        "lng": "9.0",
    }


def test_tankerkoenig_records_are_marked_as_pre_check_without_change_time() -> None:
    from auditcore_price_sources import TankerkoenigListAdapter

    result, sink, _ = run(TankerkoenigListAdapter())
    assert result.status is RunStatus.COMPLETE
    stations = {r.record_id: r.normalized for r in sink.records.values()}
    first = stations["00000000-0000-4000-8000-000000000001"]
    assert first["preise"] == {"diesel": "1.659", "e5": "1.799", "e10": "1.739"}
    assert first["zeitbezug"]["art"] == "abrufzeitpunkt" and first["beweismittel"] is False
    second = stations["00000000-0000-4000-8000-000000000002"]
    assert second["preise"] == {"diesel": None, "e5": None, "e10": "1.745"}
    assert (second["plz"], second["plz_aufgefuellt"]) == ("06108", True)
    assert stations["00000000-0000-4000-8000-000000000003"]["preise"]["e5"] is None
    # the original never ingested list.php (ADR-005); this stays a consumer decision
    assert scenario("tankerkoenig-run")["requests"] == []


def test_tankerkoenig_api_key_rejection_is_an_auth_error() -> None:
    from auditcore_price_sources import TankerkoenigListAdapter

    result, _, _ = run(
        TankerkoenigListAdapter(),
        exchanges=[exchange(TK_URL, TK_PARAMS, "tankerkoenig_error.json")],
    )
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == "auth_error"


def test_overpass_request_and_stored_rows_match_the_original() -> None:
    legacy = scenario("overpass-ok")
    request = legacy["requests"][0]
    assert request["method"] == "POST" and legacy["client_timeouts"] == ["180.0"]
    assert parse_qs(request["body"])["data"] == [fuel_query("DE-HE")]
    assert OBSERVED["static"]["overpass_query"] == fuel_query()
    result, sink, _ = run(
        OverpassFuelStationAdapter(),
        exchanges=[exchange(BASE, {}, "overpass_fuel.json", method="POST")],
    )
    rows = [
        row
        for record in sink.records.values()
        if (row := legacy_station_fields(record.normalized)) is not None
    ]
    old = legacy_rows("overpass-ok", "Tankstelle")
    keys = [k for k in rows[0]]
    assert sorted(tuple(r[k] for k in keys) for r in rows) == sorted(
        tuple(o[k] for k in keys) for o in old
    )
    # PS-C06: element without type is an issue; the way without coordinates is a record
    assert result.status is RunStatus.PARTIAL and len(result.issues) == 1
    without = sink.records[("price.overpass_fuel_stations", "osm-way-2004")].normalized
    assert without["koordinaten_herkunft"] == "fehlt" and legacy_station_fields(without) is None
    node = sink.records[("price.overpass_fuel_stations", "osm-node-1003")].normalized
    assert node["name"] is None and node["plz"] is None  # no placeholders in the new record
    raw = sink.records[("price.overpass_fuel_stations", "osm-node-1001")].raw
    assert raw["datenstand"] == "2026-09-01T06:00:00Z"
    assert legacy["result"]["paket_sha256"] == package_sha256(
        (PAYLOADS / "overpass_fuel.json").read_bytes(), canonical_json=True
    )


def test_overpass_remark_is_partial_not_success() -> None:
    assert scenario("overpass-remark")["result"]["status"] == "erfolg"
    result, sink, _ = run(
        OverpassFuelStationAdapter(),
        exchanges=[exchange(BASE, {}, "overpass_remark.json", method="POST")],
    )
    # PS-C07
    assert result.status is RunStatus.PARTIAL and len(sink.records) == 1
    assert "Query timed out" in result.issues[0].message


def test_overpass_rate_limit_is_retried_with_retry_after() -> None:
    assert scenario("overpass-429")["result"]["status"] == "fehler"
    result, _, replay = run(
        OverpassFuelStationAdapter(),
        exchanges=[
            exchange(
                BASE,
                {},
                "overpass_fuel_clean.json",
                method="POST",
                status=429,
                headers={"Retry-After": "30"},
                once=True,
            ),
            exchange(BASE, {}, "overpass_fuel_clean.json", method="POST"),
        ],
    )
    assert result.status is RunStatus.COMPLETE and len(replay.calls) == 2


def test_page_snapshot_matches_the_original_hash() -> None:
    legacy = scenario("eu-oil-ok")["result"]
    result, sink, _ = run(PageSnapshotAdapter())
    record = next(iter(sink.records.values()))
    assert record.normalized["sha256"] == legacy["paket_sha256"]
    assert legacy_status(result) == legacy["status"] == "erfolg"
    assert record.normalized["preise_extrahiert"] is False
    assert (
        base64.b64decode(record.raw["inhalt_b64"])
        == (PAYLOADS / "eu_oil_bulletin.html").read_bytes()
    )
    assert scenario("eu-oil-404")["result"]["status"] == "fehler"
    failed, _, _ = run(
        PageSnapshotAdapter(),
        exchanges=[exchange(f"{BASE}/weekly-oil-bulletin", {}, "eu_oil_bulletin.html", status=404)],
    )
    assert legacy_status(failed) == "fehler"


def test_destatis_moved_adapter_reproduces_count_and_package_hash() -> None:
    legacy = scenario("destatis-ok")
    assert [r["params"]["name"] for r in legacy["requests"]] == ["61243-0001", "61241-0004"]
    assert all(r["secret_params_present"] == ["password"] for r in legacy["requests"])
    result, sink, _ = run(DestatisTabellenAdapter())
    assert result.status is RunStatus.COMPLETE
    records = list(sink.records.values())
    blob = b"\n".join(base64.b64decode(r.raw["inhalt_b64"]) for r in records)
    assert hashlib.sha256(blob).hexdigest() == legacy["result"]["paket_sha256"]
    assert (
        sum(r.normalized["datensaetze"] for r in records) == legacy["result"]["anzahl_datensaetze"]
    )
    first = records[0].normalized["inhalt"]
    assert first["einheiten"] == ["2020=100"] and first["fehlwerte"] == 2 and first["werte"] == 2
    assert first["zeitangaben"] == ["2025-P1Y", "2026"]
    assert first["periodencodes"] == ["MONAT07", "MONAT08", "MONAT09", "MONAT12"]
    declared = OBSERVED["static"]["destatis_source"]
    ours = DestatisTabellenAdapter().source.to_dict()
    assert {**ours, "adapter_version": declared["adapter_version"]} == declared


def test_destatis_partial_and_binary_behavior_is_unchanged() -> None:
    from support import DESTATIS_URL, destatis_params

    assert scenario("destatis-one-table-500")["result"]["status"] == "teilweise"
    result, sink, _ = run(
        DestatisTabellenAdapter(),
        exchanges=[
            exchange(
                DESTATIS_URL, destatis_params("61243-0001"), "destatis_61243-0001.csv", status=500
            ),
            exchange(DESTATIS_URL, destatis_params("61241-0004"), "destatis_61241-0004.csv"),
        ],
    )
    assert legacy_status(result) == "teilweise" and len(sink.records) == 1
    assert "Binärdaten" in scenario("destatis-binary")["result"]["fehlermeldung"]


def test_connectors_without_adapter_are_documented() -> None:
    assert scenario("mtsk-run")["requests"] == []
    assert scenario("mtsk-run")["result"]["metadaten"] == {"hinweis": "OP-01", "modus": "push"}
    assert set(OBSERVED["static"]["connectors"]) >= {"mtsk", "mehr_tanken", "handelsregister"}
    assert date.fromisoformat("2026-09-02")  # capture date of the legacy window
