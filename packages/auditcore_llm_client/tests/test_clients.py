"""Client behaviour beyond the legacy cases: timeouts, telemetry, selectors, loops."""

from __future__ import annotations

import asyncio
import logging
import threading

import pytest
from conftest import KEY, Gateway

from auditcore_llm_client import (
    AUDIT_DESIGNER,
    AsyncLlmClient,
    ClientConfig,
    InvalidResponseError,
    LlmClient,
    LlmClientError,
    Mode,
    RouterHealth,
    RouterTimeoutError,
    SecretValue,
    Sensitivity,
    Timeouts,
    UsageRecord,
    safe_call,
)

ROUTER = ClientConfig(base_url="http://r.test", app_id="app", api_key=SecretValue(KEY))
FLOW = ClientConfig(base_url="https://agent.test", app_id="app", mode=Mode.FLOW_AGENT,
                    api_key=SecretValue(KEY), sensitivity=Sensitivity.CONFIDENTIAL,
                    extra_headers={"X-Request-Source": "tests"})


def test_per_call_and_configured_timeouts_reach_httpx() -> None:
    gateway = Gateway([{"json": {"response": "x"}}, {"json": {"response": "y"}}])
    config = ClientConfig(base_url="http://r.test", app_id="a", timeouts=Timeouts(llm=42))
    with LlmClient(config, transport=gateway.transport()) as client:
        client.generate("p")
        client.generate("p", timeout=5)
    timeouts = [r.extensions["timeout"] for r in gateway.raw]
    assert timeouts[0]["read"] == 42 and timeouts[1]["read"] == 5


def test_timeout_is_structured() -> None:
    gateway = Gateway([{"raise": "timeout", "message": f"read {KEY}"}])
    with LlmClient(ROUTER, transport=gateway.transport()) as client, \
            pytest.raises(RouterTimeoutError) as info:
        client.embed(["a"])
    assert info.value.cause_type == "ReadTimeout" and KEY not in str(info.value)


def test_flow_agent_headers_selector_and_telemetry() -> None:
    headers = {"X-Flow-Agent-Request-Id": "r9", "X-Flow-Agent-Model": "m",
               "X-Flow-Agent-Workers": "w1", "X-Llm-Spoke": "s", "X-Llm-Failover": "1"}
    gateway = Gateway([{"json": {"choices": [{"message": {"content": "ok"}}]},
                        "headers": headers}])
    with LlmClient(FLOW, transport=gateway.transport()) as client:
        result = client.chat([], model="flow-agent-model:qwen3-32b", seed=3)
    assert gateway.requests[0]["headers"] == {
        "authorization": f"Bearer {KEY}", "content-type": "application/json",
        "x-flow-sensitivity": "confidential", "x-request-source": "tests"}
    assert gateway.requests[0]["body"]["model"] == "flow-agent-model:qwen3-32b"  # type: ignore[index]
    telemetry = result.telemetry
    assert (telemetry.request_id, telemetry.model, telemetry.workers) == ("r9", "m", ("w1",))
    assert telemetry.spoke == "s" and telemetry.failover


def test_usage_hook_and_think_tags() -> None:
    usage: list[UsageRecord] = []
    config = ClientConfig(base_url="http://r.test", app_id="a", profile=AUDIT_DESIGNER,
                          usage_hook=usage.append)
    gateway = Gateway([{"json": {"message": {"content": "<think>a</think> B"}, "eval_count": 2,
                                 "prompt_eval_count": 1, "total_duration": 3_000_000}}])
    with LlmClient(config, transport=gateway.transport()) as client:
        assert client.generate("p").content == "B"
    assert usage == [UsageRecord("generate", "qwen3:14b", 1, 2, 3)]
    assert gateway.requests[0]["body"]["keep_alive"] == "10m"  # type: ignore[index]


def test_invalid_json_and_vectors_are_structured_errors() -> None:
    gateway = Gateway([{"text": "{kaputt"}, {"json": {"data": [{"embedding": ["x"]}]}},
                       {"json": {"scores": ["x"]}}])
    health = RouterHealth()
    with LlmClient(ROUTER, transport=gateway.transport(), health=health) as client:
        for call in (lambda: client.chat([]), lambda: client.embed(["a"]),
                     lambda: client.rerank("q", ["a"])):
            with pytest.raises(InvalidResponseError):
                call()
    assert health.to_dict()["consecutive_failures"] == 3


def test_errors_and_logs_never_contain_the_key(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    responses = [{"status": 403, "text": f"echo {KEY}"}, {"raise": "connect", "message": KEY},
                 {"text": f"kein json {KEY}"}]
    gateway = Gateway(responses)
    health = RouterHealth()
    with LlmClient(ROUTER, transport=gateway.transport(), health=health) as client:
        messages = [safe_call(client.generate, "p")[1] for _ in responses]
    assert all(m and KEY not in m for m in messages)
    assert KEY not in caplog.text and KEY not in str(health.to_dict())


def test_safe_call_catches_unexpected_errors(caplog: pytest.LogCaptureFixture) -> None:
    def broken() -> int:
        raise ValueError("http://user:pw@host kaputt")

    assert safe_call(broken) == (None, "<url> kaputt")
    assert "ValueError" in caplog.text


def test_async_client_keeps_one_http_client_per_loop() -> None:
    gateway = Gateway([{"json": {"status": "ok"}}] * 3)
    client = AsyncLlmClient(ROUTER, transport=gateway.transport())

    async def run() -> int:
        await client.health()
        await client.health()
        count = len(client._clients)  # noqa: SLF001 - white-box check of the loop map
        await client.close()
        await client.close()
        return count

    assert asyncio.run(run()) == 1
    result: list[object] = []
    thread = threading.Thread(target=lambda: result.append(asyncio.run(client.health())))
    thread.start()
    thread.join()
    assert result == [{"status": "ok"}]


def test_async_error_is_recorded() -> None:
    gateway = Gateway([{"status": 500, "text": "x"}])
    health = RouterHealth()

    async def run() -> None:
        async with AsyncLlmClient(ROUTER, transport=gateway.transport(), health=health) as c:
            await c.ocr(b"x")

    with pytest.raises(LlmClientError):
        asyncio.run(run())
    assert health.to_dict()["consecutive_failures"] == 1


def test_lazy_client_import() -> None:
    import auditcore_llm_client as package

    assert package.LlmClient is LlmClient and package.AsyncLlmClient is AsyncLlmClient
    with pytest.raises(AttributeError):
        package.__getattr__("Unbekannt")
