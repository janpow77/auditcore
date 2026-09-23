"""Recorded legacy behavior (executed originals) next to the core's corrected contract.

Each test asserts the observation from ``legacy_harvest_observed.json`` and
the core behavior for the equivalent situation (IDs in docs/behavior-changes.md).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_harvest import HarvestEngine, HarvestRequest, RetryPolicy, RunStatus
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.reference import JsonApiAdapter, example_json_source
from auditcore_harvest.transport import ReplayTransport

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "legacy_harvest_observed.json").read_text(
        encoding="utf-8"
    )
)
ADB = FIXTURE["sources"]["auditdatabase"]
DES = FIXTURE["sources"]["audit_designer"]
REG = FIXTURE["sources"]["regulierung"]


def cases(family: dict[str, Any]) -> dict[str, Any]:
    return {c["name"]: c for c in family["cases"]}


def run_json(exchanges: list[dict[str, Any]]) -> Any:
    clock = FixedClock()
    engine = HarvestEngine(
        ReplayTransport(exchanges),
        StaticCredentials(),
        MemoryStateStore(),
        clock,
        ClockSleeper(clock),
        retry=RetryPolicy(max_attempts=2),
    )
    adapter = JsonApiAdapter(example_json_source())
    return engine.run(
        adapter,
        HarvestRequest("example.json_api", "r"),
        ListSink(),
        config={"url": "https://j.invalid/"},
    )


def test_sources_are_pinned_and_blob_verified() -> None:
    assert ADB["commit"] == "bba911e918e102426d4ca2f88fd377fe8ca585e4"
    assert DES["commit"] == "030a71e083ef0feddc14545b095a4945bc0bbd7a"
    assert REG["commit"] == "a5d48ea4b90a410210ec25e707781ef9e21ad743"
    assert all(len(f["git_blob"]) == 40 for s in FIXTURE["sources"].values() for f in s["files"])


def test_hc01_rate_limit_is_not_success() -> None:
    legacy = ADB["scenarios"]["dip-rate-limited"]["result"]
    assert legacy["success"] is True and legacy["documents"] == 0  # 429 überall: "Erfolg", leer
    result = run_json(
        [
            {
                "request": {"url": "https://j.invalid/"},
                "response": {"status": 429, "headers": {"Retry-After": "1"}},
            }
        ]
        * 2
    )
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == "rate_limited"


def test_hc02_partial_failures_are_visible() -> None:
    legacy = ADB["scenarios"]["dip-partial-failure"]["result"]
    assert legacy["success"] is True and legacy["error"] is None  # 500 + Timeout verschluckt
    ok_page = {"items": [{"id": "1"}], "next": "t2"}
    result = run_json(
        [
            {
                "request": {"url": "https://j.invalid/"},
                "response": {"status": 200, "body_json": ok_page},
            },
            {
                "request": {"url": "https://j.invalid/", "params": {"cursor": "t2"}},
                "response": {"status": 500},
            },
        ]
    )
    assert result.status is RunStatus.PARTIAL and result.records_delivered == 1
    assert result.errors[0]["code"] == "transport_error"


def test_hc03_no_pagination_in_legacy_bases() -> None:
    for name in ("dip-ok", "dip-ok-limit-5"):
        assert ADB["scenarios"][name]["cursor_requested"] is False
    assert ADB["scenarios"]["dip-ok-limit-5"]["result"]["documents"] == 5  # hartes Abschneiden


def test_hc04_timeouts_and_retries_observed() -> None:
    assert ADB["scenarios"]["dip-ok"]["client_timeouts"] == ["30.0"]
    assert DES["scenarios"]["fetch-html-200"]["client_timeouts"] == ["30"]
    assert REG["static"]["retry_implemented"] is False
    assert DES["static"]["per_source_timeout_api_seconds"] == 600


def test_hc05_errors_become_empty_text_in_designer_fetch() -> None:
    for name in ("fetch-html-404", "fetch-timeout", "fetch-pdf"):
        assert DES["scenarios"][name]["text"] == ""


def test_hc06_regulierung_distinguishes_partial() -> None:
    assert REG["scenarios"]["destatis-all-ok"]["result"]["status"] == "erfolg"
    assert REG["scenarios"]["destatis-one-table-500"]["result"]["status"] == "teilweise"
    assert REG["scenarios"]["destatis-rate-limit-429"]["result"]["status"] == "fehler"
    assert REG["scenarios"]["run-missing-credentials"]["protocol_rows"] == 0


def test_hc07_legacy_date_parser_returns_none_for_every_format() -> None:
    parsed = [c["output"] for n, c in cases(ADB).items() if n.startswith("parse-date")]
    assert parsed and all(value is None for value in parsed)


@pytest.mark.parametrize(
    ("family", "title_only", "empty_content"),
    [
        (ADB, "content-hash-title-only", "content-hash-empty-content-falls-back"),
        (DES, "content-hash-['title']", "content-hash-['abstract', 'content', 'title']"),
    ],
)
def test_hc08_legacy_content_hash_falls_back_to_title(
    family: dict[str, Any], title_only: str, empty_content: str
) -> None:
    observed = cases(family)
    assert observed[title_only]["output"] == observed[empty_content]["output"]
