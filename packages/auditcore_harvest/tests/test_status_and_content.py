"""Issue #236: HTTP status, error kind, status policy, Retry-After cap and binary content."""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

import pytest

from auditcore_harvest import (
    AuthError,
    AuthKind,
    BinaryContent,
    Capabilities,
    Cursor,
    ErrorKind,
    FetchContext,
    HarvestEngine,
    HarvestError,
    HarvestRecord,
    HarvestRequest,
    PageResult,
    Provenance,
    RateLimitError,
    Response,
    RetryPolicy,
    RunStatus,
    SnapshotSemantics,
    Source,
    StatusPolicy,
    TransportError,
    page_result,
    raise_for_status,
)
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.model import JSON
from auditcore_harvest.transport import ReplayTransport

SOURCE = Source(
    "test.status",
    "Status",
    "test",
    "1.0.0",
    "1",
    "application/pdf",
    AuthKind.NONE,
    Capabilities(pagination=False),
    SnapshotSemantics.INCREMENTAL_UPSERT,
)


@dataclass
class Replies:
    """Transport answering with a fixed list of responses in order."""

    replies: list[Response]
    calls: int = 0

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        timeout: float,
    ) -> Response:
        self.calls += 1
        return self.replies.pop(0)


@dataclass
class DocumentAdapter:
    """Raw-document adapter: one PDF per run, status checked through the context."""

    source: Source = SOURCE
    seen: list[int] = field(default_factory=list)

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        return None

    def fetch_page(self, context: FetchContext, cursor: Cursor | None) -> PageResult:
        response = context.check(
            context.transport.request("GET", "https://s.invalid/d.pdf", timeout=context.timeout)
        )
        self.seen.append(response.status)
        if response.status == 404:
            return page_result([])
        content = BinaryContent(response.body, "application/pdf")
        record = context.record(
            self.source,
            "d",
            {"url": response.url},
            {"size": content.size},
            "d.pdf",
            content=content,
        )
        return page_result([record])


def run(
    replies: list[Response], **engine_options: object
) -> tuple[RunStatus, HarvestEngine, ListSink, Mapping[str, JSON], ClockSleeper]:
    clock = FixedClock()
    sleeper = ClockSleeper(clock)
    engine = HarvestEngine(
        Replies(replies),
        StaticCredentials(),
        MemoryStateStore(),
        clock,
        sleeper,
        rng=random.Random(0),
        **engine_options,  # type: ignore[arg-type]
    )
    sink = ListSink()
    result = engine.run(DocumentAdapter(), HarvestRequest("test.status", "r"), sink)
    return result.status, engine, sink, result.to_dict(), sleeper


def test_raised_errors_carry_http_status_and_kind() -> None:
    cases: list[tuple[int, type[HarvestError], ErrorKind, bool]] = [
        (429, RateLimitError, ErrorKind.RATE_LIMITED, True),
        (401, AuthError, ErrorKind.AUTH, False),
        (503, TransportError, ErrorKind.HTTP_STATUS, True),
        (408, TransportError, ErrorKind.HTTP_STATUS, True),
        (404, TransportError, ErrorKind.HTTP_STATUS, False),
        (302, TransportError, ErrorKind.HTTP_STATUS, False),
    ]
    for status, kind_of_error, kind, retryable in cases:
        with pytest.raises(kind_of_error) as raised:
            raise_for_status(Response(status, b""))
        assert raised.value.http_status == status and raised.value.kind is kind
        assert raised.value.retryable is retryable
        view = raised.value.to_dict()
        assert view["http_status"] == status and view["error_kind"] == kind.value


def test_errors_without_response_have_kind_but_no_status() -> None:
    error = TransportError("weg")
    assert error.kind is ErrorKind.NETWORK and error.to_dict()["http_status"] is None
    timeout = TransportError("zu langsam", kind=ErrorKind.TIMEOUT)
    assert timeout.to_dict()["error_kind"] == "timeout"
    replay = ReplayTransport([{"request": {"url": "u"}, "response": {"raise": "timeout"}}])
    with pytest.raises(TransportError) as recorded:
        replay.request("GET", "u", timeout=1)
    assert recorded.value.kind is ErrorKind.TIMEOUT


def test_status_policy_is_configurable() -> None:
    lenient = StatusPolicy(accept=frozenset({404}))
    assert raise_for_status(Response(404, b""), lenient).status == 404
    assert raise_for_status(Response(500, b""), StatusPolicy(check=False)).status == 500
    strict = StatusPolicy(retry_server_errors=False, retryable=frozenset({599}))
    with pytest.raises(TransportError) as raised:
        raise_for_status(Response(502, b""), strict)
    assert not raised.value.retryable
    with pytest.raises(TransportError) as listed:
        raise_for_status(Response(599, b""), strict)
    assert listed.value.retryable
    custom = StatusPolicy(rate_limited=frozenset({503}), auth=frozenset({418}))
    with pytest.raises(RateLimitError):
        raise_for_status(Response(503, b"", {"Retry-After": "3"}), custom)
    with pytest.raises(AuthError):
        raise_for_status(Response(418, b""), custom)


def test_engine_status_policy_reaches_the_adapter() -> None:
    status, *_ = run([Response(404, b"")])
    assert status is RunStatus.FAILED
    status, _, sink, _, _ = run(
        [Response(404, b"")], status_policy=StatusPolicy(accept=frozenset({404}))
    )
    assert status is RunStatus.COMPLETE and not sink.records


def test_result_reports_http_status_and_kind_of_the_final_error() -> None:
    status, _, _, view, _ = run([Response(403, b"")])
    assert status is RunStatus.FAILED
    assert view["http_status"] == 403 and view["error_kind"] == "auth"
    assert view["errors"][0]["http_status"] == 403
    status, _, _, view, _ = run([Response(200, b"%PDF-1.7", url="https://s.invalid/d.pdf")])
    assert status is RunStatus.COMPLETE
    assert view["http_status"] is None and view["error_kind"] is None


def test_retry_after_above_the_limit_ends_the_run_by_default() -> None:
    limited = Response(429, b"", {"Retry-After": "600"})
    status, _, _, view, sleeper = run([limited, Response(200, b"%PDF")])
    assert status is RunStatus.FAILED and view["error_kind"] == "rate_limited"
    assert view["http_status"] == 429 and sleeper.sleeps == []


def test_retry_after_cap_shortens_the_wait_instead_of_giving_up() -> None:
    limited = Response(429, b"", {"Retry-After": "600"})
    status, _, sink, _, sleeper = run(
        [limited, Response(200, b"%PDF")], retry=RetryPolicy(retry_after_cap=30.0)
    )
    assert status is RunStatus.COMPLETE and sleeper.sleeps == [30.0] and len(sink.records) == 1
    short = RetryPolicy(retry_after_cap=30.0)
    assert short.delay(1, RateLimitError("x", retry_after=4), random.Random(0)) == 4.0
    assert short.delay(3, RateLimitError("x", retry_after=4), random.Random(0)) is None
    assert RetryPolicy().delay(1, RateLimitError("x", retry_after=300), random.Random(0)) == 300


def provenance() -> Provenance:
    return Provenance("test.status", "1.0.0", "1", "2026-09-01T08:00:00+00:00", "d.pdf", "h")


def test_binary_content_travels_natively_and_changes_the_hash() -> None:
    plain = HarvestRecord("test.status", "d", {}, {"n": 1}, provenance())
    pdf = BinaryContent(b"%PDF-1.7\x00\xff", "application/pdf")
    with_content = HarvestRecord("test.status", "d", {}, {"n": 1}, provenance(), content=pdf)
    other = HarvestRecord(
        "test.status", "d", {}, {"n": 1}, provenance(), content=BinaryContent(b"%PDF-2")
    )
    assert "content" not in plain.to_dict()
    assert len({plain.content_hash, with_content.content_hash, other.content_hash}) == 3
    assert with_content.content is pdf and with_content.content.data.endswith(b"\xff")
    view = with_content.to_dict()["content"]
    assert view["media_type"] == "application/pdf" and view["size"] == 10
    assert BinaryContent.from_dict(view) == pdf
    meta = with_content.to_dict(include_content_data=False)["content"]
    assert "data_b64" not in meta and meta["sha256"] == pdf.sha256


def test_record_hash_without_content_is_unchanged() -> None:
    record = HarvestRecord("test.status", "d", {}, {"n": 1}, provenance())
    assert record.content_hash == (
        HarvestRecord("test.status", "d", {}, {"n": 1}, provenance()).content_hash
    )
    from auditcore_harvest import canonical_hash

    assert record.content_hash == canonical_hash({"normalized": {"n": 1}, "deleted": False})


def test_binary_content_validation() -> None:
    with pytest.raises(TypeError):
        BinaryContent("text", "text/plain")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        BinaryContent(b"x", "pdf")
    with pytest.raises(ValueError):
        BinaryContent.from_dict({"media_type": "application/pdf"})
    with pytest.raises(ValueError):
        BinaryContent.from_dict({"data_b64": "eA==", "sha256": "0" * 64})


def test_engine_delivers_binary_records() -> None:
    status, _, sink, _, _ = run([Response(200, b"%PDF-1.7", url="https://s.invalid/d.pdf")])
    assert status is RunStatus.COMPLETE
    (record,) = sink.records.values()
    assert record.content == BinaryContent(b"%PDF-1.7", "application/pdf")
    assert record.normalized == {"size": 8}
