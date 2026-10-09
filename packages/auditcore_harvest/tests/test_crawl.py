"""Issue #236 (5): multi-stage runs/crawls and the raw-document contract case."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Mapping, Sequence

import pytest

from auditcore_harvest import (
    AuthKind,
    BinaryContent,
    Capabilities,
    ConfigError,
    FetchContext,
    HarvestEngine,
    HarvestRequest,
    ParserError,
    RunStatus,
    SnapshotSemantics,
    Source,
    decode_json,
)
from auditcore_harvest.aio import AsyncFetchContext, AsyncHarvestEngine
from auditcore_harvest.crawl import (
    CRAWL_CURSOR,
    AsyncCrawlAdapter,
    CrawlAdapter,
    CrawlLimits,
    CrawlTask,
    Frontier,
    StageResult,
)
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.model import JSON
from auditcore_harvest.testing import MalformedExpectation, check_adapter
from auditcore_harvest.transport import ReplayTransport

SOURCE = Source(
    "test.crawl",
    "Crawl",
    "test",
    "1.0.0",
    "1",
    "application/pdf",
    AuthKind.NONE,
    Capabilities(pagination=True),
    SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
)
INDEX = "https://k.invalid/index"


def exchanges() -> list[Mapping[str, JSON]]:
    """Index lists two sub-pages; sub-page a links to b (again) and c; documents are PDFs."""
    pages = {
        INDEX: {"links": ["https://k.invalid/a", "https://k.invalid/b"]},
        "https://k.invalid/a": {"links": ["https://k.invalid/b", "https://k.invalid/c"]},
        "https://k.invalid/b": {"links": []},
        "https://k.invalid/c": {"links": []},
    }
    replies: list[Mapping[str, JSON]] = [
        {"request": {"url": url}, "response": {"status": 200, "body_json": body}}
        for url, body in pages.items()
    ]
    for name in ("a", "b", "c"):
        replies.append(
            {
                "request": {"url": f"https://k.invalid/{name}.pdf"},
                "response": {"status": 200, "body_text": f"%PDF {name}"},
            }
        )
    return replies


def seeds(config: Mapping[str, JSON]) -> Sequence[CrawlTask]:
    return [CrawlTask("page", str(config.get("start", INDEX)))]


def page_stage(context: FetchContext, task: CrawlTask) -> StageResult:
    response = context.check(context.transport.request("GET", task.locator, timeout=1))
    links = decode_json(response.body)["links"]
    found = [CrawlTask("page", link, task.depth + 1) for link in links]
    found += [CrawlTask("document", f"{link}.pdf", task.depth + 1) for link in links]
    return StageResult(discovered=found)


def document_stage(context: FetchContext, task: CrawlTask) -> StageResult:
    response = context.check(context.transport.request("GET", task.locator, timeout=1))
    content = BinaryContent(response.body, "application/pdf")
    record = context.record(
        SOURCE,
        task.locator,
        {"url": task.locator},
        {"size": content.size},
        task.locator,
        content=content,
    )
    return StageResult(records=[record])


def adapter(limits: CrawlLimits | None = None) -> CrawlAdapter:
    return CrawlAdapter(
        SOURCE, seeds, {"page": page_stage, "document": document_stage}, limits=limits
    )


def engine(transport: ReplayTransport, state: MemoryStateStore | None = None) -> HarvestEngine:
    clock = FixedClock()
    return HarvestEngine(
        transport,
        StaticCredentials(),
        state or MemoryStateStore(),
        clock,
        ClockSleeper(clock),
        rng=random.Random(0),
    )


def test_crawl_follows_a_changing_candidate_list_once_per_candidate() -> None:
    sink = ListSink()
    result = engine(ReplayTransport(exchanges())).run(
        adapter(), HarvestRequest("test.crawl", "r"), sink
    )
    assert result.status is RunStatus.COMPLETE and result.snapshot_complete
    assert sorted(k[1] for k in sink.records) == [
        "https://k.invalid/a.pdf",
        "https://k.invalid/b.pdf",
        "https://k.invalid/c.pdf",
    ]
    assert result.pages == 7  # index, a, b, a.pdf, b.pdf, c, c.pdf


def test_crawl_resumes_from_the_frontier_in_the_checkpoint() -> None:
    state = MemoryStateStore()
    first = engine(ReplayTransport(exchanges()), state).run(
        adapter(), HarvestRequest("test.crawl", "r1", max_pages=3), ListSink()
    )
    assert first.status is RunStatus.PARTIAL and first.checkpoint_after is not None
    cursor = first.checkpoint_after.cursor
    assert cursor is not None and cursor["format"] == CRAWL_CURSOR and cursor["done"] == 3
    sink = ListSink()
    rest = engine(ReplayTransport(exchanges()), state).run(
        adapter(), HarvestRequest("test.crawl", "r2"), sink
    )
    assert rest.status is RunStatus.COMPLETE and rest.pages == 4 and len(sink.records) == 3


def test_limits_turn_dropped_candidates_into_issues() -> None:
    result = engine(ReplayTransport(exchanges())).run(
        adapter(CrawlLimits(max_depth=1, max_tasks=4)),
        HarvestRequest("test.crawl", "r"),
        ListSink(),
    )
    assert result.status is RunStatus.PARTIAL
    messages = {issue.message for issue in result.issues}
    assert any("Höchsttiefe" in m for m in messages) and any("Aufgabenlimit" in m for m in messages)


def test_frontier_cursor_round_trip_and_errors() -> None:
    frontier = Frontier.start(
        [CrawlTask("page", "x", data={"k": 1}), CrawlTask("page", "x")], CrawlLimits()
    )
    assert len(frontier.pending) == 1
    assert Frontier.from_cursor(frontier.to_cursor()) == frontier
    with pytest.raises(ParserError):
        Frontier.from_cursor({"p": 1})
    with pytest.raises(ParserError):
        Frontier.from_cursor({"format": CRAWL_CURSOR, "pending": [{"stage": "x"}]})


def test_unknown_stages_and_validation() -> None:
    with pytest.raises(ConfigError):
        CrawlAdapter(SOURCE, seeds, {"document": document_stage}).validate_config({})

    def strict(config: Mapping[str, JSON]) -> None:
        raise ConfigError("ungültig")

    with pytest.raises(ConfigError):
        CrawlAdapter(SOURCE, seeds, {"page": page_stage}, validate=strict).validate_config({})
    empty = CrawlAdapter(SOURCE, lambda config: [], {"page": page_stage})
    result = engine(ReplayTransport([])).run(empty, HarvestRequest("test.crawl", "r"), ListSink())
    assert result.status is RunStatus.COMPLETE and result.records_delivered == 0
    rogue = CrawlAdapter(
        SOURCE, seeds, {"page": lambda c, t: StageResult(discovered=[CrawlTask("x", "y")])}
    )
    failed = engine(ReplayTransport([])).run(rogue, HarvestRequest("test.crawl", "r"), ListSink())
    assert failed.errors[0]["code"] == "config_error"


def test_async_crawl_adapter() -> None:
    async def page(context: AsyncFetchContext, task: CrawlTask) -> StageResult:
        if task.depth:
            record = context.record(SOURCE, task.locator, {}, {"d": task.depth}, task.locator)
            return StageResult(records=[record])
        return StageResult(discovered=[CrawlTask("page", "kind", 1), CrawlTask("page", "kind", 1)])

    async def scenario() -> RunStatus:
        clock = FixedClock()
        crawl = AsyncCrawlAdapter(SOURCE, seeds, {"page": page})
        eng = AsyncHarvestEngine(None, StaticCredentials(), MemoryStateStore(), clock)  # type: ignore[arg-type]
        sink = ListSink()
        result = await eng.run(crawl, HarvestRequest("test.crawl", "r"), sink)
        assert list(sink.records) == [("test.crawl", "kind")]
        return result.status

    assert asyncio.run(scenario()) is RunStatus.COMPLETE
    empty = AsyncCrawlAdapter(SOURCE, lambda config: [], {})
    assert (
        asyncio.run(
            AsyncHarvestEngine(None, StaticCredentials(), MemoryStateStore(), FixedClock()).run(  # type: ignore[arg-type]
                empty, HarvestRequest("test.crawl", "r"), ListSink()
            )
        ).status
        is RunStatus.COMPLETE
    )


def document_seeds(config: Mapping[str, JSON]) -> Sequence[CrawlTask]:
    return [CrawlTask("document", "https://k.invalid/a.pdf")]


def raw_document_adapter() -> CrawlAdapter:
    """Raw-document adapter: passes the PDF bytes through without parsing."""

    def stage(context: FetchContext, task: CrawlTask) -> StageResult:
        response = context.check(context.transport.request("GET", task.locator, timeout=1))
        content = BinaryContent(response.body, "application/pdf")
        record = context.record(
            SOURCE, "a", {"url": task.locator}, {}, task.locator, content=content
        )
        return StageResult(records=[record])

    return CrawlAdapter(SOURCE, document_seeds, {"document": stage})


def test_contract_suite_accepts_raw_document_adapters() -> None:
    def transport() -> ReplayTransport:
        return ReplayTransport(exchanges())

    raw = check_adapter(
        raw_document_adapter,
        config={},
        transport_factory=transport,
        malformed=MalformedExpectation.RAW_DOCUMENT,
    )
    assert raw.passed, raw.cases
    strict = check_adapter(raw_document_adapter, config={}, transport_factory=transport)
    assert strict.cases["malformed_response"].startswith("FAIL")
    skipped = check_adapter(
        raw_document_adapter,
        config={},
        transport_factory=transport,
        malformed=MalformedExpectation.NOT_APPLICABLE,
    )
    assert skipped.cases["malformed_response"].startswith("SKIPPED") and skipped.passed
    parsing = check_adapter(
        adapter, config={}, transport_factory=transport, malformed=MalformedExpectation.RAW_DOCUMENT
    )
    assert parsing.cases["malformed_response"].startswith("FAIL: Rohdokument abgelehnt")
