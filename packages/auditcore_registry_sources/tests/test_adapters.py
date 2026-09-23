"""Adapters run through the real ``auditcore_harvest`` engine and its contract suite."""

from __future__ import annotations

import base64
from typing import Any

import pytest
from auditcore_harvest import HarvestEngine, HarvestRequest, ReplayTransport, RunStatus
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.testing import assert_adapter
from replay_support import FILES

from auditcore_registry_sources import adapters

BASE = "https://example.invalid/"
FILES_BY_URL = {
    "un_sc.csv": "un_sc_targets.simple.csv",
    "eu_fsf.csv": "eu_fsf_targets.simple.csv",
    "leer.csv": "leer_nur_kopf.csv",
    "eu_fsf.xml": "eu_fsf_export.xml",
    "ofac.xml": "ofac_sdn.xml",
    "ofac-vollstaendig.xml": "ofac_sdn_vollstaendig.xml",
    "un.xml": "un_sc_consolidated.xml",
    "kaputt.xml": "kaputt.xml",
    "zer/status": "zer_status.json",
    "zer/status-abweichend": "zer_status_abweichend.json",
    "zer/register": "zer_register.json",
    "ihk": "ihk_locations.json",
    "hwk": "zdh_handwerkskammern.html",
}


def transport() -> ReplayTransport:
    exchanges = [
        {
            "request": {"method": "GET", "url": BASE + path},
            "response": {
                "status": 200,
                "headers": {"Last-Modified": "Tue, 22 Sep 2026 18:00:00 GMT"},
                "body_b64": base64.b64encode((FILES / name).read_bytes()).decode(),
            },
        }
        for path, name in FILES_BY_URL.items()
    ]
    return ReplayTransport(exchanges)


def run(adapter: Any, config: dict[str, Any]) -> tuple[Any, ListSink]:
    clock = FixedClock()
    engine = HarvestEngine(
        transport=transport(),
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    )
    sink = ListSink()
    result = engine.run(
        adapter, HarvestRequest(adapter.source.source_id, run_id="t"), sink, config=config
    )
    return result, sink


CONTRACT = [
    (adapters.OpenSanctionsListAdapter, {"list_key": "un_sc", "url": BASE + "un_sc.csv"}, 2),
    (
        adapters.OfficialSanctionsXmlAdapter,
        {"list_key": "ofac_sdn", "url": BASE + "ofac-vollstaendig.xml", "format": "ofac_sdn_xml"},
        3,
    ),
    (
        adapters.ZerRegisterAdapter,
        {"register_url": BASE + "zer/register", "status_url": BASE + "zer/status"},
        3,
    ),
    (adapters.IhkLocationsAdapter, {"url": BASE + "ihk"}, 3),
    (adapters.HwkPageAdapter, {"url": BASE + "hwk", "expected": 4}, 4),
]


@pytest.mark.parametrize(("factory", "config", "minimum"), CONTRACT, ids=lambda x: str(x)[:40])
def test_contract_suite(factory: Any, config: dict[str, Any], minimum: int) -> None:
    report = assert_adapter(
        factory, config=config, transport_factory=transport, min_records=minimum
    )
    assert report.cases["full_replay"] == "PASS"


def test_list_snapshot_with_bad_rows_is_partial_and_never_complete() -> None:
    result, sink = run(
        adapters.OpenSanctionsListAdapter(), {"list_key": "eu_fsf", "url": BASE + "eu_fsf.csv"}
    )
    assert result.status is RunStatus.PARTIAL and not result.snapshot_complete
    assert result.records_delivered == 8 and len(result.issues) == 2
    record = sink.records[("registry.opensanctions_lists", "eu_fsf:eu-fsf-demo-0002")]
    assert record.normalized["as_of"] == "Tue, 22 Sep 2026 18:00:00 GMT"
    assert record.normalized["name"] == "Müller-Lüdenscheidt Handels GmbH"
    clean, _ = run(
        adapters.OpenSanctionsListAdapter(), {"list_key": "un_sc", "url": BASE + "un_sc.csv"}
    )
    assert clean.status is RunStatus.COMPLETE and clean.snapshot_complete


def test_empty_or_broken_delivery_fails_instead_of_emptying_the_inventory() -> None:
    result, sink = run(
        adapters.OpenSanctionsListAdapter(), {"list_key": "x", "url": BASE + "leer.csv"}
    )
    assert result.status is RunStatus.FAILED and not sink.records
    assert result.errors[0]["code"] == "parser_error"
    broken, _ = run(
        adapters.OfficialSanctionsXmlAdapter(),
        {"list_key": "eu", "url": BASE + "kaputt.xml", "format": "eu_fsf_xml"},
    )
    assert broken.status is RunStatus.FAILED


def test_register_total_mismatch_and_short_chamber_page_are_partial() -> None:
    zer, _ = run(
        adapters.ZerRegisterAdapter(),
        {"register_url": BASE + "zer/register", "status_url": BASE + "zer/status-abweichend"},
    )
    assert zer.status is RunStatus.PARTIAL and "7" in zer.issues[0].message
    ok, sink = run(
        adapters.ZerRegisterAdapter(),
        {"register_url": BASE + "zer/register", "status_url": BASE + "zer/status"},
    )
    assert ok.status is RunStatus.COMPLETE and ok.records_delivered == 3
    hwk, _ = run(adapters.HwkPageAdapter(), {"url": BASE + "hwk"})
    assert hwk.status is RunStatus.PARTIAL and "53" in hwk.issues[0].message


def test_xml_adapter_eu_entries() -> None:
    result, sink = run(
        adapters.OfficialSanctionsXmlAdapter(),
        {"list_key": "eu_fsf", "url": BASE + "eu_fsf.xml", "format": "eu_fsf_xml"},
    )
    assert result.status is RunStatus.PARTIAL  # one entity without name is an issue
    record = sink.records[("registry.official_sanctions_xml", "eu_fsf:990003")]
    assert record.normalized["birth_date"] == "1975"


def test_configuration_errors() -> None:
    from auditcore_harvest import ConfigError

    with pytest.raises(ConfigError):
        adapters.OpenSanctionsListAdapter().validate_config({"list_key": "x", "url": "ftp://x"})
    with pytest.raises(ConfigError):
        adapters.OfficialSanctionsXmlAdapter().validate_config(
            {"list_key": "x", "url": BASE, "format": "csv"}
        )
    with pytest.raises(ConfigError):
        adapters.HwkPageAdapter().validate_config({"url": BASE, "expected": 0})
