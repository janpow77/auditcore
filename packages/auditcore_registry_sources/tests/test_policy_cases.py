"""Framework catalogue cases (verwaltung-app-framework docs/pruefkatalog.md) for this library."""

from __future__ import annotations

import ast
import base64
from pathlib import Path
from typing import Any

from auditcore_harvest import HarvestEngine, HarvestRequest, ReplayTransport, RunStatus
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListEvents,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from replay_support import FILES

import auditcore_registry_sources
from auditcore_registry_sources import adapters

URL = "https://listen.example.invalid/eu_fsf.csv?token=geheim"


def _run(content: bytes) -> tuple[Any, ListSink, ListEvents]:
    transport = ReplayTransport(
        [
            {
                "request": {"method": "GET", "url": URL},
                "response": {"status": 200, "body_b64": base64.b64encode(content).decode()},
            }
        ]
    )
    clock = FixedClock()
    events = ListEvents()
    engine = HarvestEngine(
        transport=transport,
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
        events=events,
    )
    sink = ListSink()
    result = engine.run(
        adapters.OpenSanctionsListAdapter(),
        HarvestRequest("registry.opensanctions_lists", run_id="p"),
        sink,
        config={"list_key": "eu_fsf", "url": URL},
    )
    return result, sink, events


def test_t09_handover_contains_every_row_with_versions_and_raw_values() -> None:
    result, sink, _ = _run((FILES / "eu_fsf_targets.simple.csv").read_bytes())
    assert result.records_delivered == 8 and len(result.issues) == 2  # nothing dropped silently
    for record in sink.records.values():
        assert record.provenance.profile_version == "2026.09.1"
        assert record.provenance.adapter_version == "0.1.0"
        assert record.raw["id"] == record.normalized["entry_id"]
        assert record.provenance.raw_sha256 and record.normalized["content_sha256"]


def test_t30_renamed_or_missing_columns_are_visible_not_silent() -> None:
    result, sink, _ = _run(b"kennung;bezeichnung\n1;x\n")
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == "parser_error"
    assert "Pflichtspalten" in result.errors[0]["message"] and not sink.records


def test_t14_no_logging_no_print_and_no_secret_in_results() -> None:
    package = Path(auditcore_registry_sources.__file__).parent
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert not any(n.split(".")[0] == "logging" for n in names), path.name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "print", path.name
    result, _, events = _run(b"kaputt")
    assert "geheim" not in repr(result.to_dict())
    assert "geheim" not in repr(events.events)
