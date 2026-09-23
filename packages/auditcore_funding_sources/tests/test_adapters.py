"""Adapters run through the real ``auditcore_harvest`` engine and its contract suite."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from auditcore_harvest import AdapterRegistry, HarvestEngine, HarvestRequest, RunStatus
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.testing import assert_adapter
from conftest import FIXTURES
from replay import BodyReplayTransport

from auditcore_funding_sources import adapters

DM_FIXTURE = FIXTURES / "deminimis_register_replay.json"
BASE = "https://aid-register.ec.europa.eu/eair/public/api"


def engine(transport: Any) -> HarvestEngine:
    clock = FixedClock()
    return HarvestEngine(
        transport=transport,
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    )


def run(adapter: Any, transport: Any, config: dict[str, Any]) -> Any:
    sink = ListSink()
    result = engine(transport).run(
        adapter, HarvestRequest(adapter.source.source_id, run_id="t"), sink, config=config
    )
    return result, sink


def test_deminimis_contract_suite() -> None:
    report = assert_adapter(
        adapters.DeMinimisRegisterAdapter,
        config={"country": "DE", "page_size": 2},
        transport_factory=lambda: BodyReplayTransport.from_file(DM_FIXTURE),
        min_records=5,
    )
    assert report.cases["full_replay"] == "PASS"


def test_deminimis_complete_snapshot_only_when_total_reached() -> None:
    result, sink = run(
        adapters.DeMinimisRegisterAdapter(),
        BodyReplayTransport.from_file(DM_FIXTURE),
        {"country": "DE", "page_size": 2},
    )
    assert result.status is RunStatus.COMPLETE and result.snapshot_complete
    assert result.records_delivered == 5
    masked = [r for r in sink.records.values() if r.normalized["beneficiary_masked"] == 1]
    assert len(masked) == 1
    record = sink.records[("funding.de_minimis_eaid", "DE-DM-2026-00003")]
    assert record.normalized["authority_level"] == "Hessen"
    assert record.normalized["country"] == "DEU"


def _exchanges() -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads(DM_FIXTURE.read_text())["exchanges"]
    return data


def test_deminimis_short_register_is_partial_not_complete() -> None:
    exchanges = _exchanges()
    exchanges[1]["response"]["body_json"] = {"count": 9}
    exchanges.append(
        {
            "request": {
                "method": "POST",
                "url": BASE + "/de-minimis-aid-awards",
                "json": {
                    "country": "CountryDEU",
                    "languageCode": "de",
                    "pageNumber": 3,
                    "pageSize": 2,
                },
            },
            "response": {"status": 200, "body_json": []},
        }
    )
    exchanges[3]["response"]["body_json"] = exchanges[3]["response"]["body_json"] * 1
    exchanges[3]["response"]["body_json"].append(
        dict(exchanges[3]["response"]["body_json"][0], referenceNumber="DE-DM-2026-00006")
    )
    result, _ = run(
        adapters.DeMinimisRegisterAdapter(),
        BodyReplayTransport(exchanges),
        {"country": "DE", "page_size": 2},
    )
    assert result.status is RunStatus.PARTIAL
    assert not result.snapshot_complete
    assert any("meldete 9" in i["message"] for i in result.to_dict()["issues"])


def test_deminimis_unknown_total_and_missing_reference() -> None:
    exchanges = _exchanges()
    exchanges[1]["response"]["body_json"] = {"total": 5}
    exchanges[3]["response"]["body_json"] = [{"beneficiaryName": "ohne Nummer"}]
    result, sink = run(
        adapters.DeMinimisRegisterAdapter(),
        BodyReplayTransport(exchanges),
        {"country": "DE", "page_size": 2},
    )
    assert result.status is RunStatus.PARTIAL and not result.snapshot_complete
    messages = " ".join(i["message"] for i in result.to_dict()["issues"])
    assert "ohne referenceNumber" in messages and "unbekannt" in messages
    assert len(sink.records) == 4


def test_deminimis_unexpected_shape_is_parser_error() -> None:
    exchanges = _exchanges()
    exchanges[0]["response"]["body_json"] = {"unerwartet": True}
    result, sink = run(
        adapters.DeMinimisRegisterAdapter(),
        BodyReplayTransport(exchanges),
        {"country": "DE", "page_size": 2},
    )
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == "parser_error"
    assert not sink.records


WORKSHOP_CONFIG = {
    "url": "https://daten.example.invalid/efre/liste.csv",
    "file_name": "liste.csv",
    "source_key": "hessen_efre",
    "fonds": "EFRE",
    "periode": "2021-2027",
    "country_code": "DE",
    "bundesland": "Hessen",
}


def test_workshop_contract_suite() -> None:
    assert_adapter(
        adapters.WorkshopBeneficiaryAdapter,
        config=WORKSHOP_CONFIG,
        transport_factory=lambda: BodyReplayTransport.from_file(
            FIXTURES / "workshop_file_replay.json"
        ),
        min_records=3,
    )


def _file(name: str, url: str) -> BodyReplayTransport:
    content = (FIXTURES / "files" / name).read_bytes()
    return BodyReplayTransport(
        [
            {
                "request": {"method": "GET", "url": url, "json": None},
                "response": {"status": 200, "body_b64": base64.b64encode(content).decode()},
            }
        ]
    )


def test_workshop_identity_equals_source_hash_and_sum_rows_are_issues() -> None:
    from auditcore_funding_sources import workshop

    result, sink = run(
        adapters.WorkshopBeneficiaryAdapter(),
        _file("semikolon_ohne_titel.csv", WORKSHOP_CONFIG["url"]),
        WORKSHOP_CONFIG,
    )
    assert result.status is RunStatus.PARTIAL  # Summenzeile, wie "failed" im Original
    rows = workshop.parse_file(
        (FIXTURES / "files" / "semikolon_ohne_titel.csv").read_bytes(), "x.csv"
    )
    expected = {
        workshop.compute_record_hash(r, "hessen_efre") for r in rows if not r.get("_skip_reason")
    }
    assert {key[1] for key in sink.records} == expected
    record = next(
        iter(
            r for r in sink.records.values() if r.normalized["beneficiary_name"] == "Beispiel GmbH"
        )
    )
    assert record.normalized["cost_total"] == "1234567.89" and record.normalized["plz"] == "1067"


def test_workshop_rejected_snapshot_delivers_nothing() -> None:
    bad = dict(WORKSHOP_CONFIG, file_name="liste.csv")
    content = (
        "Name des Begünstigten;Gesamtkosten;Unionsbeteiligung;PLZ\nA GmbH;100;150;1\n".encode()
    )
    bad["header_detection"] = "strict"  # legacy would take the numeric row as header (FS-W08)
    transport = BodyReplayTransport(
        [
            {
                "request": {"method": "GET", "url": bad["url"], "json": None},
                "response": {"status": 200, "body_b64": base64.b64encode(content).decode()},
            }
        ]
    )
    result, sink = run(adapters.WorkshopBeneficiaryAdapter(), transport, bad)
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == "parser_error"
    assert "EU-Anteil ist größer" in result.errors[0]["message"]
    assert not sink.records


FLOWSEARCH_CONFIG = {
    "url": "https://daten.example.invalid/bw/liste.csv",
    "source": {
        "source_key": "test_quelle",
        "bundesland": "Hessen",
        "fonds": "EFRE",
        "portal": "https://example.invalid/",
        "periode": "2021-2027",
    },
    "mapping": {
        "delimiter": ";",
        "skip_rows": 1,
        "header_row": 2,
        "columns": {
            "beneficiary_name": "Begünstigter",
            "project_name": "Vorhaben",
            "total_cost": "Gesamtkosten",
            "eu_contribution": "EU-Beitrag",
            "location": "Ort",
            "start_date": "Beginn",
        },
    },
}


def test_flowsearch_contract_suite_and_defaulted_amounts() -> None:
    assert_adapter(
        adapters.FlowsearchBeneficiaryAdapter,
        config=FLOWSEARCH_CONFIG,
        transport_factory=lambda: BodyReplayTransport.from_file(
            FIXTURES / "flowsearch_file_replay.json"
        ),
        min_records=2,
    )
    result, sink = run(
        adapters.FlowsearchBeneficiaryAdapter(),
        BodyReplayTransport.from_file(FIXTURES / "flowsearch_file_replay.json"),
        FLOWSEARCH_CONFIG,
    )
    second = next(
        r for r in sink.records.values() if r.normalized["beneficiary_name"] == "Zweite AG"
    )
    assert second.normalized["total_amount"] == 0.0
    assert set(second.normalized["defaulted"]) == {"total_cost", "eu_contribution"}


def test_registry_registers_every_adapter_explicitly() -> None:
    registry = AdapterRegistry()
    adapters.register(registry)
    assert set(registry.sources()) == {
        "funding.de_minimis_eaid",
        "funding.eu_beneficiaries",
        "funding.eu_beneficiaries.flowsearch",
    }


def test_fixture_paths_exist() -> None:
    for name in (
        "deminimis_register_replay.json",
        "workshop_file_replay.json",
        "flowsearch_file_replay.json",
    ):
        assert Path(FIXTURES / name).is_file()


def test_source_catalog_entries_are_valid_and_match_the_adapters() -> None:
    from auditcore_harvest.catalog import validate_catalog

    catalog = json.loads((FIXTURES.parent.parent / "docs" / "source-catalog.json").read_text())
    entries = {e.source_id: e for e in validate_catalog(catalog)}
    registry = AdapterRegistry()
    adapters.register(registry)
    for source_id in registry.sources():
        assert source_id in entries
    raw = {e["source_id"]: e for e in catalog["sources"]}
    assert raw["funding.state_aid"]["implementation"]["status"] == "PLANNED"
    assert all(raw[s]["live_test"]["status"] == "NOT_CONFIGURED" for s in registry.sources())
