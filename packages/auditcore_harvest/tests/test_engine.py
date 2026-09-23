"""Engine flow: paging, retries, limits, checkpoints, snapshot and error contracts."""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import pytest

from auditcore_harvest import (
    AuthKind,
    CancelToken,
    Capabilities,
    ConfigError,
    FetchContext,
    HarvestEngine,
    HarvestRecord,
    HarvestRequest,
    PageResult,
    PageStatus,
    ParserError,
    RateLimit,
    RateLimitError,
    RecordIssue,
    RetryPolicy,
    RunStatus,
    SinkReceipt,
    SnapshotSemantics,
    Source,
    TransportError,
)
from auditcore_harvest.errors import CheckpointConflict
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListEvents,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.transport import ReplayTransport


def source(
    semantics: SnapshotSemantics = SnapshotSemantics.FULL_SNAPSHOT_REPLACE, profile: str = "1"
) -> Source:
    return Source(
        "test.quelle",
        "Test",
        "test",
        "1.0.0",
        profile,
        "application/json",
        AuthKind.NONE,
        Capabilities(pagination=True),
        semantics,
    )


@dataclass
class Scripted:
    """Adapter returning scripted pages or raising scripted errors per call."""

    script: list[Any]
    source: Source = field(default_factory=source)
    calls: list[Mapping[str, Any] | None] = field(default_factory=list)

    def validate_config(self, config: Mapping[str, Any]) -> None:
        if config.get("invalid"):
            raise ConfigError("ungültig")

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        self.calls.append(cursor)
        step = self.script.pop(0)
        if isinstance(step, BaseException):
            raise step
        return step


def rec(i: int | str, src: str = "test.quelle", value: str = "v") -> HarvestRecord:
    from auditcore_harvest.model import Provenance

    return HarvestRecord(
        src,
        str(i),
        {"i": i},
        {"value": value},
        Provenance(src, "1.0.0", "1", "2026-09-01T08:00:00+00:00", f"#{i}", "h"),
    )


def page(ids: list[int], nxt: str | None, **kw: Any) -> PageResult:
    return PageResult(
        tuple(rec(i) for i in ids), None if nxt is None else {"p": nxt}, complete=nxt is None, **kw
    )


def engine(**kw: Any) -> tuple[HarvestEngine, FixedClock, ClockSleeper, MemoryStateStore]:
    clock = FixedClock()
    sleeper = ClockSleeper(clock)
    state = kw.pop("state", MemoryStateStore())
    return (
        HarvestEngine(
            ReplayTransport(()),
            StaticCredentials(),
            state,
            clock,
            sleeper,
            rng=random.Random(0),
            **kw,
        ),
        clock,
        sleeper,
        state,
    )


REQ = HarvestRequest("test.quelle", "r1")


def test_pages_are_followed_until_complete_and_checkpointed() -> None:
    eng, _, _, state = engine()
    adapter = Scripted([page([1, 2], "2"), page([3], "3"), page([4], None)])
    sink = ListSink()
    result = eng.run(adapter, REQ, sink)
    assert result.status is RunStatus.COMPLETE and result.pages == 3
    assert result.records_delivered == 4 and result.source_exhausted
    assert result.snapshot_complete
    assert adapter.calls == [None, {"p": "2"}, {"p": "3"}]
    checkpoint = state.load("test.quelle")
    assert checkpoint is not None and checkpoint.finished and checkpoint.records_confirmed == 4


def test_duplicates_within_run_and_at_sink_are_counted() -> None:
    eng, *_ = engine()
    sink = ListSink()
    eng.run(Scripted([page([1, 2], None)]), REQ, sink)
    again = eng.run(
        Scripted([page([1], "2"), page([1, 2], None)]), HarvestRequest("test.quelle", "r2"), sink
    )
    assert again.duplicates_in_run == 1 and again.duplicates_at_sink == 2
    assert again.records_delivered == 0


def test_retry_with_backoff_then_success() -> None:
    eng, _, sleeper, _ = engine(retry=RetryPolicy(max_attempts=3, base_delay=2.0, jitter=0.0))
    adapter = Scripted([TransportError("x"), TransportError("y"), page([1], None)])
    result = eng.run(adapter, REQ, ListSink())
    assert result.status is RunStatus.COMPLETE and result.attempts == 3
    assert sleeper.sleeps == [2.0, 4.0]


def test_retry_after_is_honoured_and_capped() -> None:
    eng, _, sleeper, _ = engine(retry=RetryPolicy(max_attempts=3, max_retry_after=60))
    ok = eng.run(Scripted([RateLimitError("r", retry_after=30), page([1], None)]), REQ, ListSink())
    assert ok.status is RunStatus.COMPLETE and sleeper.sleeps == [30.0]
    eng2, _, sleeper2, _ = engine(retry=RetryPolicy(max_attempts=3, max_retry_after=60))
    stop = eng2.run(Scripted([RateLimitError("r", retry_after=3600)]), REQ, ListSink())
    assert stop.status is RunStatus.FAILED and stop.errors[0]["code"] == "rate_limited"
    assert stop.errors[0]["retry_after"] == 3600 and sleeper2.sleeps == []


def test_non_retryable_errors_stop_immediately() -> None:
    eng, *_ = engine()
    result = eng.run(Scripted([ParserError("kaputt")]), REQ, ListSink())
    assert result.status is RunStatus.FAILED and result.attempts == 1
    assert result.errors[0]["code"] == "parser_error"


def test_adapter_bug_becomes_structured_parser_error() -> None:
    eng, *_ = engine()
    result = eng.run(Scripted([KeyError("feld")]), REQ, ListSink())
    assert result.errors[0]["code"] == "parser_error" and "KeyError" in result.errors[0]["message"]


def test_rate_limit_spacing_between_requests() -> None:
    eng, _, sleeper, _ = engine(rate_limit=RateLimit(1.5))
    eng.run(Scripted([page([1], "2"), page([2], "3"), page([3], None)]), REQ, ListSink())
    assert sleeper.sleeps == [1.5, 1.5]


def test_incomplete_page_without_cursor_is_not_a_silent_end() -> None:
    eng, *_ = engine()
    bad = PageResult((rec(1),), None, complete=False)
    result = eng.run(Scripted([bad]), REQ, ListSink())
    assert result.status is RunStatus.FAILED and "stilles Ende" in result.errors[0]["message"]


def test_cursor_that_does_not_advance_is_detected() -> None:
    eng, *_ = engine()
    result = eng.run(Scripted([page([1], "2"), page([2], "2")]), REQ, ListSink())
    assert result.status is RunStatus.PARTIAL and "Cursor" in result.errors[0]["message"]


def test_foreign_records_are_rejected() -> None:
    eng, *_ = engine()
    foreign = PageResult((rec(1, src="andere.quelle"),), None, complete=True)
    assert eng.run(Scripted([foreign]), REQ, ListSink()).errors[0]["code"] == "parser_error"


def test_sink_failure_keeps_checkpoint_and_resume_loses_nothing() -> None:
    eng, _, _, state = engine()
    sink = ListSink(fail_on_page=2)
    first = eng.run(Scripted([page([1], "2"), page([2], None)]), REQ, sink)
    assert first.status is RunStatus.PARTIAL and first.errors[0]["code"] == "sink_error"
    checkpoint = state.load("test.quelle")
    assert checkpoint is not None and checkpoint.cursor == {"p": "2"} and not checkpoint.finished
    adapter = Scripted([page([2], None)])
    second = eng.run(adapter, HarvestRequest("test.quelle", "r2"), sink)
    assert adapter.calls == [{"p": "2"}] and second.status is RunStatus.COMPLETE
    assert set(sink.records) == {("test.quelle", "1"), ("test.quelle", "2")}
    assert not second.snapshot_complete  # resumed mid-snapshot: no replace allowed


def test_sink_must_confirm_exactly_the_delivered_records() -> None:
    class Liar:
        def deliver(self, records: Any, *, run_id: str, page: int) -> SinkReceipt:
            return SinkReceipt(())

    eng, _, _, state = engine()
    result = eng.run(Scripted([page([1], None)]), REQ, Liar())
    assert result.errors[0]["code"] == "sink_error" and state.load("test.quelle") is None


def test_checkpoint_conflict_stops_the_run() -> None:
    class Conflicting(MemoryStateStore):
        def save(self, checkpoint: Any, expected: Any) -> None:
            raise CheckpointConflict("parallel")

    eng, *_ = engine(state=Conflicting())
    result = eng.run(Scripted([page([1], None)]), REQ, ListSink())
    assert result.status is RunStatus.FAILED and result.errors[0]["code"] == "checkpoint_conflict"


def test_profile_version_change_refuses_foreign_cursor() -> None:
    eng, _, _, state = engine()
    eng.run(Scripted([page([1], "2"), ParserError("stop")]), REQ, ListSink())
    newer = Scripted([page([1], None)], source=source(profile="2"))
    result = eng.run(newer, REQ, ListSink())
    assert result.status is RunStatus.FAILED and "Profilversion" in result.errors[0]["message"]
    assert newer.calls == []


def test_finished_snapshot_restarts_but_incremental_continues() -> None:
    eng, _, _, _ = engine()
    eng.run(Scripted([page([1], None)]), REQ, ListSink())
    restart = Scripted([page([1], None)])
    eng.run(restart, REQ, ListSink())
    assert restart.calls == [None]
    inc_engine, *_ = engine()
    marker = PageResult((rec(1),), {"since": "2026-09-01"}, complete=True)
    inc = source(SnapshotSemantics.INCREMENTAL_UPSERT)
    inc_engine.run(Scripted([marker], source=inc), REQ, ListSink())
    follow = Scripted([PageResult((), {"since": "2026-09-02"}, complete=True)], source=inc)
    result = inc_engine.run(follow, REQ, ListSink())
    assert follow.calls == [{"since": "2026-09-01"}] and not result.snapshot_complete


def test_issues_make_the_run_partial_not_complete() -> None:
    eng, *_ = engine()
    flawed = PageResult((rec(1),), None, True, PageStatus.PARTIAL, (RecordIssue("#2", "x"),))
    result = eng.run(Scripted([flawed]), REQ, ListSink())
    assert result.status is RunStatus.PARTIAL and not result.snapshot_complete
    assert result.issues[0].locator == "#2"


@pytest.mark.parametrize(
    ("request_", "script", "code"),
    [
        (HarvestRequest("test.quelle", "r", max_pages=1), [page([1], "2")], "limit_reached"),
        (HarvestRequest("test.quelle", "r", max_records=1), [page([1], "2")], "limit_reached"),
    ],
)
def test_limits_end_the_run_as_partial(
    request_: HarvestRequest, script: list[Any], code: str
) -> None:
    eng, *_ = engine()
    result = eng.run(Scripted(script), request_, ListSink())
    assert result.status is RunStatus.PARTIAL and result.errors[0]["code"] == code


def test_deadline_prevents_waiting_beyond_the_run_duration() -> None:
    eng, _, sleeper, _ = engine(retry=RetryPolicy(max_attempts=5, base_delay=100.0, jitter=0))
    result = eng.run(
        Scripted([TransportError("x")]),
        HarvestRequest("test.quelle", "r", max_duration_seconds=50),
        ListSink(),
    )
    assert result.status is RunStatus.FAILED and sleeper.sleeps == []


def test_cancel_and_config_and_source_mismatch() -> None:
    eng, *_ = engine()
    token = CancelToken()
    token.cancel()
    assert (
        eng.run(Scripted([page([1], None)]), REQ, ListSink(), cancel=token).status
        is RunStatus.CANCELLED
    )
    bad = eng.run(Scripted([]), REQ, ListSink(), config={"invalid": True})
    assert bad.status is RunStatus.FAILED and bad.errors[0]["code"] == "config_error"
    other = eng.run(Scripted([]), HarvestRequest("x.y", "r"), ListSink())
    assert other.errors[0]["code"] == "config_error"


def test_events_are_bounded_and_carry_no_config() -> None:
    events = ListEvents()
    eng, *_ = engine(events=events)
    eng.run(
        Scripted([page([1], None)]), REQ, ListSink(), config={"url": "https://x", "note": "geheim"}
    )
    kinds = [e["event"] for e in events.events]
    assert kinds == ["run_started", "page_confirmed", "run_finished"]
    assert "geheim" not in repr(events.events)


def test_result_serialisation_contains_contract_version() -> None:
    eng, *_ = engine()
    data = eng.run(Scripted([page([1], None)]), REQ, ListSink()).to_dict()
    assert data["contract"] == "auditcore_harvest.contract/1" and data["status"] == "complete"
