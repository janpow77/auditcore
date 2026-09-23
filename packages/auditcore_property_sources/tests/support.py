"""Shared test helpers: recorded observations, synthetic pages and replay transports."""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import cache
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
PAGES = FIXTURES / "pages"
ROBOTS = FIXTURES / "robots"


@cache
def observed() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / "legacy_observed.json").read_text("utf-8"))
    return data


def cases(group: str, function: str) -> list[dict[str, Any]]:
    return [c for c in observed()["cases"] if c["group"] == group and c["function"] == function]


def page(name: str) -> str:
    return (PAGES / name).read_text(encoding="utf-8")


def robots_text(host: str) -> str:
    return (ROBOTS / f"{host}.txt").read_text(encoding="utf-8")


def exchange(
    url: str,
    body: str,
    *,
    method: str = "GET",
    status: int = 200,
    params: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    request: dict[str, Any] = {"method": method, "url": url}
    if params:
        request["params"] = dict(params)
    return {"request": request, "response": {"status": status, "body_text": body}}


def replay(
    pages: Mapping[str, str],
    *,
    robots: tuple[str, str] | None,
    extra: list[dict[str, Any]] | None = None,
) -> ReplayTransport:
    """Pages by URL plus robots.txt (``(robots url, text)``; ``None`` → HTTP 404)."""
    exchanges = [exchange(url, body) for url, body in pages.items()]
    hosts = {url.split("/")[2] for url in pages if url.startswith("http")}
    for host in hosts:
        robots_url = f"https://{host}/robots.txt"
        if robots is None:
            exchanges.append(exchange(robots_url, "", status=404))
        else:
            exchanges.append(exchange(robots[0], robots[1]))
    return ReplayTransport(tuple(exchanges + list(extra or [])))


def run(adapter: Any, transport: Any, config: Mapping[str, Any]) -> tuple[HarvestResult, ListSink]:
    clock = FixedClock()
    sink = ListSink()
    result = HarvestEngine(
        transport=transport,
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    ).run(adapter, HarvestRequest(adapter.source.source_id, run_id="test"), sink, config=config)
    return result, sink


def normalized(sink: ListSink) -> list[dict[str, Any]]:
    return sorted((dict(r.normalized) for r in sink.records.values()), key=lambda d: str(d["id"]))
