"""Thinking field, plain ``/api/chat`` profile and client pools per gateway URL."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping

import httpx
import pytest
from conftest import Gateway

from auditcore_llm_client import (
    AUDIT_DESIGNER,
    DIRECT_OLLAMA_PORT,
    OLLAMA_CHAT_PLAIN,
    PROFILES,
    AsyncLlmClientPool,
    BreakerPolicy,
    CircuitOpenError,
    ClientConfig,
    ConfigurationError,
    LlmClient,
    LlmClientPool,
    LlmResult,
    RouterUnavailableError,
    config_from_env,
    validate_base_url,
)

PLAIN = ClientConfig(base_url="http://r.test", app_id="app", profile=OLLAMA_CHAT_PLAIN)


def _generate(config: ClientConfig, answer: Mapping[str, object], **kwargs: object) -> LlmResult:
    gateway = Gateway([{"json": dict(answer)}])
    with LlmClient(config, transport=gateway.transport()) as client:
        return client.generate("Frage", **kwargs)  # type: ignore[arg-type]


def test_ollama_chat_thinking_is_separate_field() -> None:
    answer = {"message": {"content": "", "thinking": "Begründung"}, "model": "m"}
    result = _generate(PLAIN, answer)
    assert result.content == "" and result.thinking == "Begründung"
    assert result.content_or_thinking == "Begründung"


def test_content_wins_over_thinking() -> None:
    result = _generate(PLAIN, {"message": {"content": "Antwort", "thinking": "Weg"}})
    assert result.content_or_thinking == "Antwort" and result.thinking == "Weg"


def test_ollama_generate_thinking() -> None:
    config = ClientConfig(base_url="http://r.test", app_id="app")
    result = _generate(config, {"response": " ", "thinking": "nur gedacht"})
    assert result.thinking == "nur gedacht" and result.content_or_thinking == "nur gedacht"


@pytest.mark.parametrize("field", ["reasoning_content", "reasoning"])
def test_openai_reasoning_fields(field: str) -> None:
    body = {"choices": [{"message": {"content": None, field: "abgewogen"}}], "model": "m"}
    gateway = Gateway([{"json": body}])
    config = ClientConfig(base_url="http://r.test", app_id="app")
    with LlmClient(config, transport=gateway.transport()) as client:
        result = client.chat([{"role": "user", "content": "x"}])
    assert result.content == "" and result.thinking == "abgewogen"


def test_without_thinking_field_defaults_empty() -> None:
    result = _generate(PLAIN, {"message": {"content": "Antwort"}})
    assert result.thinking == "" and result.content_or_thinking == "Antwort"
    assert LlmResult(content="x", model="m").thinking == ""
    assert LlmResult(content="", model="m", raw_response={"choices": []}).thinking == ""


def test_plain_profile_sends_only_caller_values() -> None:
    gateway = Gateway([{"json": {"message": {"content": "a"}}}, {"json": {"message": {}}}])
    with LlmClient(PLAIN, transport=gateway.transport()) as client:
        client.generate("Frage")
        client.generate("Frage", system="S", temperature=0.1, options={"num_ctx": 4096})
    first, second = (json.loads(r.content) for r in gateway.raw)
    assert gateway.raw[0].url.path == "/api/chat"
    assert first == {
        "model": OLLAMA_CHAT_PLAIN.default_llm_model,
        "messages": [{"role": "user", "content": "Frage"}],
        "stream": False,
    }
    assert second["options"] == {"temperature": 0.1, "num_ctx": 4096}
    assert "keep_alive" not in second and "think" not in second


def test_plain_profile_registered_and_existing_profiles_unchanged() -> None:
    assert PROFILES["ollama_chat_plain"] is OLLAMA_CHAT_PLAIN
    assert not OLLAMA_CHAT_PLAIN.strip_think_tags and OLLAMA_CHAT_PLAIN.think is None
    assert dict(AUDIT_DESIGNER.chat_options)["num_ctx"] == 16384
    config = config_from_env(OLLAMA_CHAT_PLAIN, {"AI_ROUTER_URL": "http://r.test:7842"})
    assert config.profile is OLLAMA_CHAT_PLAIN


def test_plain_profile_keeps_think_tags() -> None:
    result = _generate(PLAIN, {"message": {"content": "<think>x</think>Antwort"}})
    assert result.content == "<think>x</think>Antwort"


def test_port_11434_rejected_with_reason() -> None:
    assert DIRECT_OLLAMA_PORT == 11434
    with pytest.raises(ConfigurationError, match="Ollama"):
        validate_base_url("http://gpu.test:11434/")
    assert validate_base_url(" https://gateway.test/ ") == "https://gateway.test"


def test_pool_reuses_client_per_normalised_url() -> None:
    gateway = Gateway([{"json": {"response": "a"}}, {"json": {"response": "b"}}])
    with LlmClientPool(PLAIN, transport=gateway.transport()) as pool:
        assert pool.config is PLAIN
        first = pool.client("http://a.test/")
        assert pool.client("http://a.test") is first
        assert pool.client() is not first and pool.client().config.base_url == "http://r.test"
        first.generate("x")
        pool.client("http://b.test").generate("y")
        assert pool.urls == ["http://a.test", "http://r.test", "http://b.test"]
    assert [r.url.host for r in gateway.raw] == ["a.test", "b.test"]


def test_pool_rejects_direct_ollama_and_bad_size() -> None:
    with LlmClientPool(PLAIN) as pool, pytest.raises(ConfigurationError):
        pool.client("http://gpu.test:11434")
    with pytest.raises(ConfigurationError):
        LlmClientPool(PLAIN, max_clients=0)


def test_pool_evicts_and_closes_least_recently_used() -> None:
    with LlmClientPool(PLAIN, max_clients=2) as pool:
        kept = pool.client("http://a.test")
        evicted = pool.client("http://b.test")
        pool.client("http://a.test")
        pool.client("http://c.test")
        assert pool.urls == ["http://a.test", "http://c.test"]
        assert evicted._http.is_closed and not kept._http.is_closed  # noqa: SLF001


def test_pool_breaker_is_per_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "down.test":
            raise httpx.ConnectError("weg", request=request)
        return httpx.Response(200, json={"response": "ok"})

    config = ClientConfig(
        base_url="http://r.test", app_id="app", breaker=BreakerPolicy(failure_threshold=1)
    )
    with LlmClientPool(config, transport=httpx.MockTransport(handler)) as pool:
        with pytest.raises(RouterUnavailableError):
            pool.client("http://down.test").generate("x")
        with pytest.raises(CircuitOpenError):
            pool.client("http://down.test").generate("x")
        assert pool.client("http://up.test").generate("x").content == "ok"


def test_async_pool() -> None:
    gateway = Gateway([{"json": {"message": {"content": "", "thinking": "t"}}}])

    async def run() -> tuple[str, list[str]]:
        async with AsyncLlmClientPool(PLAIN, transport=gateway.transport(), max_clients=1) as pool:
            client = await pool.client("http://a.test")
            assert await pool.client("http://a.test") is client
            result = await client.generate("x")
            await pool.client("http://b.test")
            return result.content_or_thinking, pool.urls

    assert asyncio.run(run()) == ("t", ["http://b.test"])
