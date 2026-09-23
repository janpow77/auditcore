"""TED and HAD adapters through the real auditcore_harvest engine and contract suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from auditcore_harvest import HarvestEngine, HarvestRequest, ReplayTransport, Response
from auditcore_harvest.catalog import validate_catalog
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.testing import assert_adapter
from page_replay import PageReplay

from auditcore_procurement import sources

REPLAY = Path(__file__).parent / "fixtures" / "replay"
TED_CONFIG = {"api_url": "https://api.ted.europa.eu/v3/notices/search", "page_size": 2}


def ted_transport(name: str = "ted_awards.json") -> PageReplay:
    return PageReplay.from_file(REPLAY / name)


def had_transport() -> ReplayTransport:
    return ReplayTransport.from_file(REPLAY / "had_search.json")


def engine(transport: object) -> HarvestEngine:
    clock = FixedClock()
    return HarvestEngine(
        transport=transport,
        credentials=StaticCredentials({}),  # type: ignore[arg-type]
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    )


def test_ted_adapter_passes_the_harvest_contract_suite() -> None:
    report = assert_adapter(
        sources.TedAwardsAdapter, config=TED_CONFIG, transport_factory=ted_transport, min_records=3
    )
    assert report.passed


def test_had_adapter_passes_the_harvest_contract_suite() -> None:
    report = assert_adapter(
        sources.HadSearchAdapter,
        config={"variant": "designer"},
        transport_factory=had_transport,
        request_filters={"company_name": "Kita"},
        min_records=2,
    )
    assert report.passed


def test_ted_run_pages_records_issues_and_coverage() -> None:
    transport = ted_transport("ted_awards_partial.json")
    sink = ListSink()
    result = engine(transport).run(
        sources.TedAwardsAdapter(),
        HarvestRequest(sources.TED_SOURCE_ID, run_id="r1"),
        sink,
        config=TED_CONFIG,
    )
    assert result.status.value == "partial"  # winnerless notice reported, not dropped silently
    ids = sorted(key[1] for key in sink.records)
    assert ids == ["100-2024", "101-2024", "102-2024"]
    assert all(
        r.normalized["coverage"] == "award_notices_with_winner" for r in sink.records.values()
    )
    assert [c["body"]["page"] for c in transport.calls] == [1, 2]
    assert result.issues
    assert result.source_exhausted


def test_ted_query_includes_award_filter_and_filters() -> None:
    adapter = sources.TedAwardsAdapter()
    query = adapter.query({"country": "DEU", "cpv_codes": ["72000000"]})
    assert query.endswith("notice-type=can-standard AND winner-name=*")
    assert adapter.query({"query": "buyer-country=DEU"}) == "buyer-country=DEU"


@pytest.mark.parametrize(
    "config",
    [
        {"api_url": "http://api.ted.europa.eu/v3"},
        {"api_url": "https://x", "page_size": 0},
        {"api_url": "https://x", "page_size": 251},
        {"api_url": "https://x", "fields": "a"},
        {},
    ],
)
def test_ted_config_is_validated(config: dict) -> None:
    from auditcore_harvest import ConfigError

    with pytest.raises(ConfigError):
        sources.TedAwardsAdapter().validate_config(config)


class _Fixed:
    def __init__(self, response: Response) -> None:
        self.response = response

    def request(self, method: str, url: str, **kwargs: object) -> Response:
        return self.response


@pytest.mark.parametrize(
    ("body", "code"),
    [
        (b"not json", "parser_error"),
        (b"[1]", "parser_error"),
        (b'{"notices": {"a": 1}}', "parser_error"),
    ],
)
def test_ted_unreadable_answers_are_parser_errors(body: bytes, code: str) -> None:
    result = engine(_Fixed(Response(200, body))).run(
        sources.TedAwardsAdapter(),
        HarvestRequest(sources.TED_SOURCE_ID, run_id="x"),
        ListSink(),
        config=TED_CONFIG,
    )
    assert result.status.value == "failed"
    assert result.errors[0]["code"] == code


@pytest.mark.parametrize(
    ("status", "variant", "outcome"),
    [
        (404, "designer", "complete"),
        (404, "flowinvoice", "failed"),
        (403, "designer", "failed"),
    ],
)
def test_had_status_semantics(status: int, variant: str, outcome: str) -> None:
    result = engine(_Fixed(Response(status, b""))).run(
        sources.HadSearchAdapter(),
        HarvestRequest(sources.HAD_SOURCE_ID, run_id="x", filters={"company_name": "Kita"}),
        ListSink(),
        config={"variant": variant},
    )
    assert result.status.value == outcome


def test_had_requires_company_filter_and_known_variant() -> None:
    from auditcore_harvest import ConfigError

    with pytest.raises(ConfigError):
        sources.HadSearchAdapter().validate_config({"variant": "portal"})
    result = engine(had_transport()).run(
        sources.HadSearchAdapter(),
        HarvestRequest(sources.HAD_SOURCE_ID, run_id="x"),
        ListSink(),
        config={"variant": "designer"},
    )
    assert result.status.value == "failed"


def test_had_record_ids_are_stable() -> None:
    sink = ListSink()
    engine(had_transport()).run(
        sources.HadSearchAdapter(),
        HarvestRequest(sources.HAD_SOURCE_ID, run_id="x", filters={"company_name": "Kita"}),
        sink,
        config={"variant": "designer"},
    )
    ids = sorted(key[1] for key in sink.records)
    assert ids == ["had-4711", "had-99"]
    assert sources._had_record_id({"titel": "a", "datum": "b"}).startswith("had-h-")


def test_catalog_entries_are_valid() -> None:
    from importlib import resources

    data = json.loads(
        resources.files("auditcore_procurement")
        .joinpath("sources_catalog.json")
        .read_text(encoding="utf-8")
    )
    entries = validate_catalog(data)
    assert {e.source_id for e in entries} == {
        "procurement.ted_awards",
        "procurement.had_search",
        "procurement.ted_company_flowinvoice",
        "procurement.ted_company_designer",
    }
