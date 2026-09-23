"""Framework catalogue cases (verwaltung-app-framework docs/pruefkatalog.md) for this library."""

from __future__ import annotations

import ast
import base64
from pathlib import Path
from typing import Any

from auditcore_harvest import HarvestEngine, HarvestRequest, RunStatus
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from replay import BodyReplayTransport

import auditcore_funding_sources
from auditcore_funding_sources import adapters, workshop

CONFIG = {
    "url": "https://daten.example.invalid/efre/liste.csv",
    "file_name": "liste.csv",
    "source_key": "hessen_efre",
    "fonds": "EFRE",
    "periode": "2021-2027",
    "country_code": "DE",
}


def _run(content: bytes, config: dict[str, Any] | None = None) -> tuple[Any, ListSink]:
    config = config or CONFIG
    transport = BodyReplayTransport(
        [
            {
                "request": {"method": "GET", "url": config["url"], "json": None},
                "response": {"status": 200, "body_b64": base64.b64encode(content).decode()},
            }
        ]
    )
    clock = FixedClock()
    sink = ListSink()
    engine = HarvestEngine(
        transport=transport,
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    )
    result = engine.run(
        adapters.WorkshopBeneficiaryAdapter(),
        HarvestRequest("funding.eu_beneficiaries", run_id="p"),
        sink,
        config=config,
    )
    return result, sink


def test_t09_handover_contains_every_row_with_versions_and_raw_values() -> None:
    content = (
        "Name des Begünstigten;Gesamtkosten;PLZ\nA GmbH;1.000,50;34117\nB GmbH;20;60311\n"
        "C GmbH;30;01067\n"
    ).encode()
    result, sink = _run(content)
    assert result.status is RunStatus.COMPLETE and result.records_delivered == 3
    for record in sink.records.values():
        assert record.provenance.profile_version == "2026.09.1"
        assert record.provenance.adapter_version == auditcore_funding_sources.__version__
        assert record.raw and record.provenance.raw_sha256
    amounts = sorted(r.normalized["cost_total"] for r in sink.records.values())
    assert amounts == ["1000.50", "20", "30"]


def test_t30_renamed_or_missing_columns_are_visible_not_silent() -> None:
    renamed = b"Partner;Kosten\nA GmbH;10\n"
    result, sink = _run(renamed)
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == "parser_error"
    assert not sink.records
    mapped = dict(CONFIG, field_mapping={"name": "Partner"})
    result, sink = _run(renamed, mapped)
    assert result.status is RunStatus.COMPLETE and len(sink.records) == 1


def test_t30_number_and_date_formats_follow_the_named_profile() -> None:
    rows = workshop.parse_file(
        "Name des Begünstigten;Gesamtkosten;Datum des Beginns\nA;1,200,000.50;15/03/2024\n"
        "B;1.200.000,50;2024-03-15\n".encode(),
        "x.csv",
    )
    assert [str(workshop.parse_amount(r["cost_total_raw"])) for r in rows] == ["1200000.50"] * 2
    assert {workshop.parse_date(r["project_start_raw"]) for r in rows} == {
        workshop.parse_date("2024-03-15")
    }
    assert workshop.profile()["version"] == "2026.09.1"


def test_t14_no_logging_and_results_without_configuration_secrets() -> None:
    package = Path(auditcore_funding_sources.__file__).parent
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert not any(n.split(".")[0] == "logging" for n in names), path.name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "print", path.name
    result, _ = _run(b"kaputt")
    assert "daten.example.invalid" not in repr(result.to_dict())
