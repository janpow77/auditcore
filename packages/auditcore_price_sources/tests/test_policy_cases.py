"""Framework catalogue cases (verwaltung-app-framework docs/pruefkatalog.md) for this library."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from auditcore_harvest import RunStatus
from auditcore_harvest.memory import ListEvents
from support import SECRETS, run

import auditcore_price_sources
from auditcore_price_sources import FACTORIES, EiaSpotPriceAdapter


def test_t09_handover_has_every_record_with_unit_time_reference_and_versions() -> None:
    """Handover: each record carries versions, raw value hash, unit and time reference."""
    for source_id, factory in FACTORIES.items():
        result, sink, _ = run(factory())
        assert result.status is RunStatus.COMPLETE, source_id
        assert result.records_delivered == len(sink.records) > 0
        for record in sink.records.values():
            data = record.to_dict()
            assert data["provenance"]["profile_version"] == "2026.09.1"
            assert data["provenance"]["adapter_version"] == factory().source.adapter_version
            assert len(data["provenance"]["raw_sha256"]) == 64
            normalized = data["normalized"]
            if "zeitbezug" in normalized:
                assert normalized["zeitbezug"]["art"]
            if normalized.get("schema") == "auditcore_price_sources.observation/1":
                assert normalized["einheit"]["herkunft"] in {"quelle", "profil", "unbekannt"}
                assert normalized["status"] in {"vorhanden", "fehlwert"}


def test_t14_results_events_and_snapshots_contain_no_secrets() -> None:
    """Protokolle: API keys never appear in results, events, records or recorded requests."""
    from auditcore_harvest import HarvestEngine, HarvestRequest
    from auditcore_harvest.memory import (
        ClockSleeper,
        FixedClock,
        ListSink,
        MemoryStateStore,
        StaticCredentials,
    )
    from support import CASES, transport

    for source_id in ("price.eia_brent", "price.tankerkoenig", "price.destatis_genesis"):
        events = ListEvents()
        clock = FixedClock()
        replay = transport(source_id)
        sink = ListSink()
        result = HarvestEngine(
            transport=replay,
            credentials=StaticCredentials(SECRETS),
            state=MemoryStateStore(),
            clock=clock,
            sleeper=ClockSleeper(clock),
            events=events,
        ).run(
            FACTORIES[source_id](),
            HarvestRequest(source_id, run_id="p"),
            sink,
            config=CASES[source_id]["config"],
        )
        text = json.dumps(
            [
                result.to_dict(),
                events.events,
                [r.to_dict() for r in sink.records.values()],
                replay.calls,
            ],
            default=str,
        )
        for secret in SECRETS.values():
            assert secret not in text, source_id


def test_t14_library_does_not_log_or_print() -> None:
    for path in Path(auditcore_price_sources.__file__).parent.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert not any(n.startswith("logging") for n in names), path.name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "print", path.name


def test_t30_source_unit_and_missing_values_are_never_silently_replaced() -> None:
    """Import profile: unit origin stated, missing values stay None, bad rows are issues."""
    result, sink, _ = run(EiaSpotPriceAdapter())
    units = {r.normalized["einheit"]["herkunft"] for r in sink.records.values()}
    assert units == {"quelle"}
    assert any(r.normalized["wert"] is None for r in sink.records.values())
    assert all(r.normalized["wert"] != "0" for r in sink.records.values())
