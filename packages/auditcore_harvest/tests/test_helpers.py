"""Shared adapter helpers of 0.1.1: record, JSON decoding and page building."""

from __future__ import annotations

import pytest

from auditcore_harvest import (
    FetchContext,
    HarvestRecord,
    HarvestRequest,
    PageResult,
    PageStatus,
    ParserError,
    RecordIssue,
    decode_json,
    page_result,
)
from auditcore_harvest.engine import CancelToken, RateLimit, RetryPolicy
from auditcore_harvest.memory import FixedClock, StaticCredentials
from auditcore_harvest.reference import example_feed_source
from auditcore_harvest.transport import ReplayTransport


def _context() -> FetchContext:
    return FetchContext(
        HarvestRequest("example.feed", "run"),
        {},
        ReplayTransport(()),
        StaticCredentials(),
        FixedClock(),
        1.0,
        1,
    )


def test_record_equals_manual_construction() -> None:
    context = _context()
    source = example_feed_source()
    raw = {"id": "a", "x": 1}
    manual = HarvestRecord(
        source_id=source.source_id,
        record_id="a",
        raw=raw,
        normalized={"x": 1},
        provenance=context.provenance(source, "loc", raw),
        deleted=True,
    )
    assert context.record(source, "a", raw, {"x": 1}, "loc", deleted=True) == manual


def test_decode_json_and_parser_error_text() -> None:
    assert decode_json(b'{"a": [1]}') == {"a": [1]}
    with pytest.raises(ParserError, match=r"^Antwort ist kein JSON\.$"):
        decode_json(b"<html>")
    with pytest.raises(ParserError, match=r"^Quelle X: kaputt$") as caught:
        decode_json(b"\xff", "Quelle X: kaputt")
    assert isinstance(caught.value.__cause__, ValueError)


def test_page_result_matches_explicit_construction() -> None:
    issue = RecordIssue("loc#1", "kaputt")
    assert page_result([], [issue], {"offset": 5}, total_hint=9) == PageResult(
        records=(),
        next_cursor={"offset": 5},
        complete=False,
        status=PageStatus.PARTIAL,
        issues=(issue,),
        total_hint=9,
    )
    assert page_result([]) == PageResult((), None, complete=True)


def test_policies_stay_importable_from_engine() -> None:
    assert RetryPolicy().max_attempts == 3
    assert RateLimit().min_interval_seconds == 0.0
    assert CancelToken().cancelled is False


def test_deprecated_aliases_warn_and_return_new_object() -> None:
    from auditcore_harvest import deprecated_aliases

    marker = object()
    getattr_ = deprecated_aliases("pkg.mod", {"AlterName": ("NewName", marker)})
    with pytest.warns(DeprecationWarning, match="AlterName heißt jetzt NewName"):
        assert getattr_("AlterName") is marker
    with pytest.raises(AttributeError, match="pkg.mod"):
        getattr_("Unknown")
