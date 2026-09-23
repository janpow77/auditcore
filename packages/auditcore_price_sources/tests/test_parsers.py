"""Parser edge cases: SDMX-JSON, ffcsv, exact numbers, snapshots and run status mapping."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import pytest
from auditcore_harvest import (
    HarvestResult,
    ParserError,
    RecordIssue,
    ReplayTransport,
    Response,
    RunStatus,
)
from support import PAYLOADS

from auditcore_price_sources import (
    RecordingTransport,
    canonical_json_bytes,
    error_text,
    exact,
    legacy_status,
    package_sha256,
    parse_ffcsv,
    parse_sdmx_json,
)


def test_sdmx_units_status_and_issues() -> None:
    payload = json.loads((PAYLOADS / "bundesbank_fx.json").read_text("utf-8"))
    (series,) = parse_sdmx_json(payload, series_hint="x")
    assert series.series_id == "BBEX3.D.USD.EUR.BB.AC.000"
    assert [o.period for o in series.observations] == [
        "2026-08-28",
        "2026-08-29",
        "2026-08-30",
        "2026-08-31",
        "2026-09-01",
    ]
    assert [o.value for o in series.observations] == ["1.1012", None, None, "1.0987", "1.1050"]
    assert sorted(i.locator for i in series.issues) == [
        "BBEX3.D.USD.EUR.BB.AC.000#5",
        "BBEX3.D.USD.EUR.BB.AC.000#6",
        "BBEX3.D.USD.EUR.BB.AC.000#9",
    ]


@pytest.mark.parametrize("payload", [[], {"x": 1}, {"data": {"dataSets": {}}}, {"data": 3}])
def test_sdmx_structure_errors(payload: Any) -> None:
    with pytest.raises(ParserError):
        parse_sdmx_json(payload, series_hint="x")


def test_sdmx_without_unit_attributes_keeps_unit_unknown() -> None:
    payload = {
        "data": {
            "structure": {"dimensions": {"observation": [{"values": [{"id": "2026-01-02"}]}]}},
            "dataSets": [{"series": {"0": {"observations": {"0": ["2.5"]}}}}],
        }
    }
    (series,) = parse_sdmx_json(payload, series_hint="REIHE")
    assert series.series_id == "REIHE" and series.unit["text"] is None
    assert series.unit["herkunft"] == "unbekannt"


def test_ffcsv_markers_units_and_times() -> None:
    table = parse_ffcsv((PAYLOADS / "destatis_61243-0001.csv").read_text("utf-8"))
    assert table.structure == "ffcsv" and table.unreadable == 0
    assert [(r.time, r.period_code, r.value, r.marker) for r in table.rows] == [
        ("2026", "MONAT07", Decimal("118.4"), None),
        ("2026", "MONAT08", Decimal("117.9"), None),
        ("2026", "MONAT09", None, "..."),
        ("2025-P1Y", "MONAT12", None, "-"),
    ]
    assert {r.unit for r in table.rows} == {"2020=100"}


def test_ffcsv_unknown_structure_and_bad_rows() -> None:
    assert parse_ffcsv("").structure == "leer"
    unknown = parse_ffcsv("a;b\n1;2\n")
    assert unknown.structure == "unbekannt" and unknown.unreadable == 1
    bad = parse_ffcsv("time;value\n2026;1.234,5\n2026\n2026;abc\n2026;7,5\n")
    assert bad.unreadable == 3 and [r.value for r in bad.rows] == [Decimal("7.5")]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1.1490", Decimal("1.1490")),
        (71.25, Decimal("71.25")),
        (5, Decimal(5)),
        (None, None),
        ("", None),
        (False, None),
    ],
)
def test_exact_values(value: Any, expected: Decimal | None) -> None:
    assert exact(value) == expected


@pytest.mark.parametrize("value", ["n/a", "1,5", True, "inf", [1]])
def test_exact_rejects_non_numbers(value: Any) -> None:
    with pytest.raises(ValueError):
        exact(value)


def test_recording_transport_keeps_snapshots_without_secrets() -> None:
    inner = ReplayTransport(
        (
            {
                "request": {"method": "GET", "url": "https://x.invalid/a", "params": {"q": "1"}},
                "response": {
                    "status": 200,
                    "body_text": '{"b": 1, "a": 2}',
                    "headers": {"Content-Type": "application/json"},
                },
            },
        )
    )
    recorder = RecordingTransport(inner)
    response = recorder.request(
        "GET", "https://x.invalid/a", params={"q": "1", "apikey": "geheim"}, timeout=5
    )
    assert isinstance(response, Response)
    (snapshot,) = recorder.snapshots
    assert snapshot.params == {"q": "1"} and "geheim" not in json.dumps(snapshot.to_dict())
    assert canonical_json_bytes(snapshot.body) == b'{"a": 2, "b": 1}'
    assert package_sha256(snapshot.body, canonical_json=False) == snapshot.sha256
    small = RecordingTransport(inner, max_body_bytes=3)
    from auditcore_harvest import TransportError

    with pytest.raises(TransportError):
        small.request("GET", "https://x.invalid/a", params={"q": "1"}, timeout=5)


def _result(status: RunStatus, **extra: Any) -> HarvestResult:
    values: dict[str, Any] = dict(
        source_id="price.x",
        run_id="r",
        contract="c",
        status=status,
        started_at="s",
        finished_at="f",
        pages=0,
        records_received=0,
        records_delivered=0,
        duplicates_in_run=0,
        duplicates_at_sink=0,
        issues=(),
        errors=(),
        checkpoint_before=None,
        checkpoint_after=None,
        source_exhausted=False,
        snapshot_complete=False,
        attempts=0,
    )
    values.update(extra)
    return HarvestResult(**values)


def test_legacy_status_and_error_text() -> None:
    assert [legacy_status(_result(s)) for s in RunStatus] == [
        "erfolg",
        "teilweise",
        "fehler",
        "fehler",
    ]
    assert error_text(_result(RunStatus.COMPLETE)) is None
    text = error_text(
        _result(
            RunStatus.PARTIAL,
            errors=({"message": "HTTP 500"},),
            issues=(RecordIssue("tabelle", "HTTP 404"),),
        ),
    )
    assert text == "HTTP 500; tabelle: HTTP 404"
    long = error_text(_result(RunStatus.FAILED, errors=({"message": "x" * 900},)), limit=10)
    assert long == "x" * 10
