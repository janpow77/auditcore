"""First proof of the shared core: real adapters of different families through one engine.

Run in an environment where ``auditcore_harvest``, ``auditcore_legal_sources``
and ``auditcore_procurement`` are installed, from a checkout that contains
their recorded fixtures::

    python tools/first_proof.py <checkout-root> <output.json>

For every adapter the same :class:`HarvestEngine` implementation executes:
full replay with paging, duplicate counting, an idempotent re-run against the
same sink, a transport failure in the middle of the run followed by resume
from the confirmed checkpoint, a sink failure followed by resume, and a
checkpoint consistency check. Everything uses recorded fixtures only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from auditcore_harvest import CONTRACT_VERSION, HarvestEngine, HarvestRequest, RunStatus
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.testing import FlakyTransport, check_adapter
from auditcore_harvest.transport import ReplayTransport


def engine(
    transport: Any, credentials: dict[tuple[str, str], str], state: MemoryStateStore
) -> HarvestEngine:
    clock = FixedClock()
    return HarvestEngine(
        transport, StaticCredentials(credentials), state, clock, ClockSleeper(clock)
    )


def content(sink: ListSink) -> set[tuple[tuple[str, str], str]]:
    return {(k, r.content_hash) for k, r in sink.records.items()}


def prove(
    name: str,
    factory: Callable[[], Any],
    transport: Callable[[], Any],
    config: dict[str, Any],
    credentials: dict[tuple[str, str], str],
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = factory().source
    request = lambda run: HarvestRequest(source.source_id, run, filters=dict(filters or {}))  # noqa: E731
    checks: dict[str, Any] = {}

    state, sink = MemoryStateStore(), ListSink()
    full = engine(transport(), credentials, state).run(
        factory(), request("voll"), sink, config=config
    )
    checkpoint = state.load(source.source_id)
    checks["replay_and_paging"] = {
        "status": "PASS" if full.status is RunStatus.COMPLETE and full.pages >= 2 else "FAIL",
        "pages": full.pages,
        "records": full.records_delivered,
        "duplicates_in_run": full.duplicates_in_run,
    }
    checks["checkpoint_consistency"] = {
        "status": "PASS"
        if checkpoint is not None
        and checkpoint.finished
        and checkpoint.records_confirmed == len(sink.records)
        and checkpoint.pages_confirmed == full.pages
        else "FAIL",
        "records_confirmed": None if checkpoint is None else checkpoint.records_confirmed,
    }
    before_rerun = content(sink)
    again = engine(transport(), credentials, state).run(
        factory(), request("wieder"), sink, config=config
    )
    checks["idempotent_sink"] = {
        "status": "PASS"
        if again.records_delivered == 0
        and content(sink) == before_rerun
        and again.duplicates_at_sink == len(before_rerun)
        else "FAIL",
        "duplicates_at_sink": again.duplicates_at_sink,
    }
    if full.pages >= 2:
        state2, sink2 = MemoryStateStore(), ListSink()
        broken = engine(
            FlakyTransport(transport(), frozenset(range(2, 50))), credentials, state2
        ).run(factory(), request("teilfehler"), sink2, config=config)
        resumed = engine(transport(), credentials, state2).run(
            factory(), request("fortsetzung"), sink2, config=config
        )
        checks["resume_after_partial_failure"] = {
            "status": "PASS"
            if broken.status in (RunStatus.PARTIAL, RunStatus.FAILED)
            and broken.errors
            and broken.errors[0]["code"] == "transport_error"
            and resumed.status is RunStatus.COMPLETE
            and content(sink2) == content(sink)
            else "FAIL",
            "first_run": broken.status.value,
            "delivered_before_failure": broken.records_delivered,
            "resumed_from_cursor": resumed.checkpoint_before is not None
            and resumed.checkpoint_before.cursor is not None,
        }
    state3, sink3 = MemoryStateStore(), ListSink(fail_on_page=full.pages)
    failed = engine(transport(), credentials, state3).run(
        factory(), request("senke"), sink3, config=config
    )
    resumed = engine(transport(), credentials, state3).run(
        factory(), request("senke2"), sink3, config=config
    )
    checks["resume_after_sink_failure"] = {
        "status": "PASS"
        if failed.errors
        and failed.errors[0]["code"] == "sink_error"
        and resumed.status is RunStatus.COMPLETE
        and content(sink3) == content(sink)
        else "FAIL",
    }
    report = check_adapter(
        factory,
        config=config,
        transport_factory=transport,
        credentials=credentials,
        request_filters=filters,
    )
    checks["contract_suite"] = {
        "status": "PASS" if report.passed else "FAIL",
        "cases": report.cases,
    }
    return {
        "adapter": name,
        "source_id": source.source_id,
        "family": source.family,
        "adapter_version": source.adapter_version,
        "profile_version": source.profile_version,
        "status": "PASS" if all(c["status"] == "PASS" for c in checks.values()) else "FAIL",
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    legal = args.root / "packages/auditcore_legal_sources/tests/fixtures/replay"
    procurement = args.root / "packages/auditcore_procurement/tests"
    sys.path.insert(0, str(procurement))
    from auditcore_legal_sources.adapters import DipDrucksachenAdapter
    from auditcore_procurement import sources
    from page_replay import PageReplay  # procurement's recorded-page transport

    results = [
        prove(
            "auditcore_legal_sources:DipDrucksachenAdapter",
            DipDrucksachenAdapter,
            lambda: ReplayTransport.from_file(legal / "dip.json"),
            {
                "profile": {"id": "auditdatabase.esi", "version": "2026.09.2"},
                "keywords": ["EFRE", "Strukturfonds"],
            },
            {("legal.dip_bundestag", "api_key"): "fixture-key-nicht-echt"},
        ),
        prove(
            "auditcore_procurement.sources:TedAwardsAdapter",
            sources.TedAwardsAdapter,
            lambda: PageReplay.from_file(procurement / "fixtures/replay/ted_awards.json"),
            {"api_url": "https://api.ted.europa.eu/v3/notices/search", "page_size": 2},
            {},
        ),
    ]
    modules = {
        n: importlib.import_module(n)
        for n in ("auditcore_harvest", "auditcore_legal_sources", "auditcore_procurement")
    }
    document = {
        "status": "PASS"
        if all(r["status"] == "PASS" for r in results) and len({r["family"] for r in results}) >= 2
        else "FAIL",
        "contract": CONTRACT_VERSION,
        "engine": f"{HarvestEngine.__module__}.{HarvestEngine.__qualname__}",
        "modules": {
            n: {
                "file": m.__file__,
                "sha256": hashlib.sha256(Path(str(m.__file__)).read_bytes()).hexdigest(),
            }
            for n, m in modules.items()
        },
        "adapters": results,
        "funding": "PENDING: Funding-Adapter zum Prüfzeitpunkt nicht committet",
    }
    args.output.write_text(json.dumps(document, indent=1, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {"status": document["status"], "adapters": {r["adapter"]: r["status"] for r in results}}
        )
    )


if __name__ == "__main__":
    main()
