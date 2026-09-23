"""Replay transports and configurations for the adapters (synthetic payloads only)."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from auditcore_harvest import HarvestEngine, HarvestRequest, HarvestResult, ReplayTransport
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)

FIXTURES = Path(__file__).parent / "fixtures"
PAYLOADS = FIXTURES / "payloads"
OBSERVED = json.loads((FIXTURES / "regulierung_connectors_observed.json").read_text("utf-8"))
BASE = "https://example.invalid/api"
SECRETS = {
    ("price.eia_brent", "api_key"): "geheimer-eia-schluessel",
    ("price.tankerkoenig", "api_key"): "geheimer-tk-schluessel",
    ("price.destatis_genesis", "token"): "geheimes-genesis-token",
}


def scenario(name: str) -> dict[str, Any]:
    """Observed legacy scenario by name."""
    return next(s for s in OBSERVED["scenarios"] if s["scenario"] == name)


def body(name: str) -> dict[str, str]:
    """Replay response body of a payload file."""
    return {"body_b64": base64.b64encode((PAYLOADS / name).read_bytes()).decode()}


def exchange(url: str, params: dict[str, str], name: str, **response: Any) -> dict[str, Any]:
    """Recorded exchange; ``once=True`` lets the answer be used a single time."""
    once = bool(response.pop("once", False))
    return {
        "request": {"method": response.pop("method", "GET"), "url": url, "params": params},
        "response": {"status": response.pop("status", 200), **body(name), **response},
        "once": once,
    }


BUNDESBANK_URL = f"{BASE}/data/BBEX3/D.USD.EUR.BB.AC.000"
BUNDESBANK_PARAMS = {"format": "json", "lastNObservations": "30"}
EIA_URL = f"{BASE}/petroleum/pri/spt/data/"


def eia_params(
    offset: int, length: int, start: str = "2026-08-02", end: str = "2026-09-01"
) -> dict[str, str]:
    return {
        "frequency": "daily",
        "data[0]": "value",
        "facets[product][]": "EPCBRENT",
        "start": start,
        "end": end,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": str(offset),
        "length": str(length),
    }


TK_URL = f"{BASE}/list.php"
TK_PARAMS = {"lat": "50.6", "lng": "9.0", "rad": "1", "type": "all"}
DESTATIS_URL = f"{BASE}/data/tablefile"


def destatis_params(table: str) -> dict[str, str]:
    return {
        "username": "fixture-user",
        "name": table,
        "area": "all",
        "compress": "false",
        "transpose": "false",
        "format": "ffcsv",
        "language": "de",
    }


#: clean payloads for the contract suite (a complete run); problem payloads are used separately
CASES: dict[str, dict[str, Any]] = {
    "price.bundesbank": {
        "config": {"url": BASE},
        "exchanges": [exchange(BUNDESBANK_URL, BUNDESBANK_PARAMS, "bundesbank_fx_clean.json")],
    },
    "price.eia_brent": {
        "config": {"url": BASE, "page_size": 3},
        "exchanges": [
            exchange(EIA_URL, eia_params(0, 3), "eia_brent_clean_page1.json"),
            exchange(EIA_URL, eia_params(3, 3), "eia_brent_clean_page2.json"),
        ],
    },
    "price.tankerkoenig": {
        "config": {"url": BASE, "lat": 50.6, "lng": 9.0, "rad": 1},
        "exchanges": [exchange(TK_URL, TK_PARAMS, "tankerkoenig_list.json")],
    },
    "price.overpass_fuel_stations": {
        "config": {"url": BASE},
        "exchanges": [exchange(BASE, {}, "overpass_fuel_clean.json", method="POST")],
    },
    "price.eu_oil_bulletin": {
        "config": {"url": f"{BASE}/weekly-oil-bulletin"},
        "exchanges": [
            exchange(
                f"{BASE}/weekly-oil-bulletin",
                {},
                "eu_oil_bulletin.html",
                headers={"content-type": "text/html; charset=utf-8"},
            )
        ],
    },
    "price.destatis_genesis": {
        "config": {"url": DESTATIS_URL, "username": "fixture-user"},
        "exchanges": [
            exchange(DESTATIS_URL, destatis_params(t), f"destatis_{t}.csv")
            for t in ("61243-0001", "61241-0004")
        ],
    },
}


def transport(source_id: str, exchanges: list[dict[str, Any]] | None = None) -> ReplayTransport:
    return ReplayTransport(tuple(exchanges or CASES[source_id]["exchanges"]))


def run(
    adapter: Any,
    *,
    exchanges: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
    filters: dict[str, Any] | None = None,
    secrets: dict[tuple[str, str], str] | None = None,
) -> tuple[HarvestResult, ListSink, ReplayTransport]:
    """One engine run with a fixed clock and in-memory sink."""
    source_id = adapter.source.source_id
    replay = transport(source_id, exchanges)
    clock = FixedClock()
    engine = HarvestEngine(
        transport=replay,
        credentials=StaticCredentials(SECRETS if secrets is None else secrets),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    )
    sink = ListSink()
    result = engine.run(
        adapter,
        HarvestRequest(source_id, run_id="test", filters=filters or {}),
        sink,
        config=config if config is not None else CASES[source_id]["config"],
    )
    return result, sink, replay
