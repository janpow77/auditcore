"""Streaming (NDJSON and Flow-Agent SSE) and the cached model list."""

from __future__ import annotations

import asyncio

import pytest
from conftest import KEY, Gateway

from auditcore_llm_client import (
    AsyncLlmClient,
    ClientConfig,
    InvalidResponseError,
    LlmClient,
    Mode,
    ModelCatalog,
    ModelInfo,
    RouterHttpError,
    RouterUnavailableError,
    SecretValue,
    StreamEventKind,
    UnsupportedOperationError,
)
from auditcore_llm_client.streaming import NdjsonDecoder, SseDecoder, decoder_for

FLOW = ClientConfig(base_url="https://agent.test", app_id="app", mode=Mode.FLOW_AGENT,
                    api_key=SecretValue(KEY))
SSE = [
    ": keep-alive",
    'data: {"choices": [{"delta": {"role": "assistant"}}]}',
    'data: {"choices": [{"delta": {"content": "Hal"}}]}',
    "data: kaputt",
    'data: {"choices": [{"delta": {"content": "lo"}}], '
    '"usage": {"prompt_tokens": 4, "completion_tokens": 2}}',
    "data: [DONE]",
    'data: {"choices": [{"delta": {"content": "zu spät"}}]}',
]


def test_flow_agent_stream_uses_sse_and_selector() -> None:
    gateway = Gateway([{"lines": SSE, "headers": {"content-type": "text/event-stream"}}])
    with LlmClient(FLOW, transport=gateway.transport()) as client:
        events = list(client.stream_chat([{"role": "user", "content": "Hi"}], max_tokens=5))
    assert [e.delta for e in events if e.kind is StreamEventKind.DELTA] == ["Hal", "lo"]
    assert events[-1].kind is StreamEventKind.DONE and events[-1].completion_tokens == 2
    request = gateway.requests[0]
    assert request["url"] == "https://agent.test/api/v1/ai/apps/app/v1/chat/completions"
    assert request["body"] == {"model": "flow-agent-high", "stream": True, "max_tokens": 5,
                               "messages": [{"role": "user", "content": "Hi"}]}
    assert request["headers"]["authorization"] == f"Bearer {KEY}"  # type: ignore[index]


def test_async_stream_and_in_stream_error() -> None:
    lines = ['data: {"choices": [{"delta": {"content": "a"}}]}', 'data: {"error": "abgebrochen"}']
    gateway = Gateway([{"lines": lines}])

    async def run() -> list[object]:
        async with AsyncLlmClient(FLOW, transport=gateway.transport()) as client:
            return [e.to_dict() async for e in client.stream_chat([])]

    assert asyncio.run(run()) == [{"delta": "a"}, {"error": "abgebrochen"}]


def test_stream_http_error_raises_redacted() -> None:
    gateway = Gateway([{"status": 502, "text": f"bad {KEY}"}])
    with LlmClient(FLOW, transport=gateway.transport()) as client, \
            pytest.raises(RouterHttpError) as info:
        list(client.stream_chat([]))
    assert info.value.status_code == 502 and KEY not in str(info.value)


def test_decoders_edge_cases() -> None:
    ndjson = NdjsonDecoder()
    assert ndjson.feed("[1, 2]") == [] and ndjson.feed("  ") == []
    done = ndjson.feed('{"done": true, "eval_count": true}')
    assert done[0].completion_tokens is None and ndjson.finished
    assert ndjson.feed('{"message": {"content": "x"}}') == []
    sse = SseDecoder()
    assert sse.feed("event: x") == [] and sse.feed("data: 5") == []
    assert isinstance(decoder_for("/api/chat"), NdjsonDecoder)
    assert isinstance(decoder_for("/x/v1/chat/completions"), SseDecoder)


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_catalog_cache_error_ttl_and_stale_window() -> None:
    clock = Clock()
    catalog = ModelCatalog("http://r.test", clock)
    assert catalog.cached() is None
    good = catalog.succeeded([ModelInfo("m")])
    assert catalog.cached() is good and good.state == "ok"
    clock.now = 60
    assert catalog.cached() is None
    failed = catalog.failed(RouterHttpError("x", status_code=429, retry_after=12.7))
    assert (failed.state, failed.retry_after, failed.cache_ttl) == ("overloaded", 12, 12.0)
    assert failed.stale and failed.models == (ModelInfo("m"),)
    clock.now = 70
    assert catalog.cached() is failed
    failed = catalog.failed(RouterUnavailableError("x"))
    assert (failed.reachable, failed.cache_ttl, failed.http_status) == (False, 5.0, None)
    clock.now = 301
    stale_view = catalog.failed(InvalidResponseError("x"))
    assert stale_view.stale is False and stale_view.models == () and stale_view.http_status == 200
    catalog.succeeded([])
    assert catalog.cached().state == "empty"  # type: ignore[union-attr]


def test_catalog_hides_expired_stale_models_from_cache() -> None:
    clock = Clock()
    catalog = ModelCatalog("http://r.test", clock)
    catalog.succeeded([ModelInfo("m")])
    clock.now = 299
    catalog.failed(RouterHttpError("x", status_code=429, retry_after=60))
    clock.now = 300
    view = catalog.cached()
    assert view is not None and view.models == () and view.stale is False


def test_model_snapshot_is_cached_between_calls() -> None:
    gateway = Gateway([{"json": {"models": [{"name": "a"}]}}])
    config = ClientConfig(base_url="http://r.test", app_id="cockpit")
    with LlmClient(config, transport=gateway.transport()) as client:
        first = client.model_snapshot()
        assert client.model_snapshot() is first and len(gateway.requests) == 1
    with LlmClient(FLOW, transport=gateway.transport()) as client, \
            pytest.raises(UnsupportedOperationError):
        client.list_models()
