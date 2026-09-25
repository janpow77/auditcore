"""Request builders for text generation, chat and streaming.

Each builder reproduces the recorded request of a legacy client (see
``tests/fixtures/legacy_*_observed.json``); the dialect comes from
``ClientConfig.mode`` and ``ClientConfig.profile``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from auditcore_llm_client.config import ClientConfig, Mode
from auditcore_llm_client.jsontypes import JsonObject, JsonValue
from auditcore_llm_client.profiles import GenerateRoute
from auditcore_llm_client.wire import Messages, PreparedRequest, message_list, put_optional

#: Temperature flowinvoice sends to the Flow-Agent when the caller gives none.
FLOW_AGENT_DEFAULT_TEMPERATURE = 0.3
#: Prefix of Flow-Agent model selectors (``flow-agent-high``, ``flow-agent-model:<id>``).
FLOW_AGENT_SELECTOR_PREFIX = "flow-agent-"


@dataclass(frozen=True)
class Sampling:
    """Sampling parameters of one call (``None`` = profile default or omitted)."""

    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    json_mode: bool = False
    seed: int | None = None
    options: Mapping[str, JsonValue] = field(default_factory=dict)
    #: OpenAI ``reasoning_effort`` (``none|low|medium|high``); on Ollama routes it
    #: becomes ``think`` (``none`` = false). ``None`` leaves the router default:
    #: the ai-router disables thinking for ``qwen3.5*`` models unless the client asks.
    reasoning_effort: str | None = None


def ollama_think(sampling: Sampling, fixed: bool | None) -> bool | None:
    """``think`` flag for Ollama routes: explicit reasoning effort wins over the profile."""
    if sampling.reasoning_effort is not None:
        return sampling.reasoning_effort != "none"
    return fixed


def flow_agent_model(config: ClientConfig, model: str | None) -> str:
    """Model selector for the Flow-Agent: explicit selector or the configured quality."""
    if model and model.startswith(FLOW_AGENT_SELECTOR_PREFIX):
        return model
    return f"flow-agent-{config.quality.value}"


def _temperature(config: ClientConfig, sampling: Sampling) -> float | None:
    if sampling.temperature is not None:
        return sampling.temperature
    return config.profile.default_temperature


def _max_tokens(config: ClientConfig, sampling: Sampling) -> int | None:
    if sampling.max_tokens is not None:
        return sampling.max_tokens
    return config.profile.default_max_tokens


def _openai_chat_body(config: ClientConfig, messages: list[JsonValue], sampling: Sampling,
                      model: str) -> JsonObject:
    body: JsonObject = {"model": model, "messages": messages, "stream": False}
    put_optional(body, "temperature", _temperature(config, sampling))
    put_optional(body, "max_tokens", _max_tokens(config, sampling))
    put_optional(body, "seed", sampling.seed)
    put_optional(body, "reasoning_effort", sampling.reasoning_effort)
    if sampling.json_mode:
        body["response_format"] = {"type": "json_object"}
    return body


def build_chat(config: ClientConfig, messages: Messages, sampling: Sampling) -> PreparedRequest:
    """OpenAI-compatible chat completion (all apps)."""
    if config.mode is Mode.FLOW_AGENT:
        model = flow_agent_model(config, sampling.model)
    else:
        model = sampling.model or config.model_defaults.llm
    body = _openai_chat_body(config, message_list(messages), sampling, model)
    return PreparedRequest(
        operation="chat",
        method="POST",
        path=f"{config.app_prefix}/v1/chat/completions",
        timeout=config.timeouts.llm,
        json_body=body,
    )


def _prompt_messages(system: str | None, prompt: str) -> list[JsonValue]:
    messages: list[JsonValue] = []
    if system is not None:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _ollama_chat(config: ClientConfig, prompt: str, system: str | None,
                 sampling: Sampling) -> PreparedRequest:
    """audit_designer ``call_llm``: ``/api/chat`` with fixed options, 404 → OpenAI route."""
    profile = config.profile
    model = sampling.model or config.model_defaults.llm
    messages = _prompt_messages(system, prompt)
    options: JsonObject = {}
    put_optional(options, "temperature", _temperature(config, sampling))
    put_optional(options, "num_predict", _max_tokens(config, sampling))
    options.update(dict(profile.chat_options))
    options.update(sampling.options)
    put_optional(options, "seed", sampling.seed)
    body: JsonObject = {"model": model, "messages": messages, "stream": False}
    put_optional(body, "think", ollama_think(sampling, profile.think))
    put_optional(body, "keep_alive", config.keep_alive or profile.default_keep_alive)
    body["options"] = options
    if sampling.json_mode:
        body["format"] = "json"
    fallback = PreparedRequest(
        operation="generate",
        method="POST",
        path="/v1/chat/completions",
        timeout=config.timeouts.llm,
        json_body=_openai_chat_body(config, list(messages), sampling, model),
    )
    return PreparedRequest(
        operation="generate",
        method="POST",
        path="/api/chat",
        timeout=config.timeouts.llm,
        json_body=body,
        fallback_on_404=fallback,
    )


def _ollama_generate(config: ClientConfig, prompt: str, system: str | None,
                     sampling: Sampling) -> PreparedRequest:
    """flowinvoice/audit-portal ``call_llm``: Ollama ``/api/generate``."""
    options: JsonObject = {}
    put_optional(options, "temperature", _temperature(config, sampling))
    put_optional(options, "num_predict", _max_tokens(config, sampling))
    put_optional(options, "seed", sampling.seed)
    options.update(sampling.options)
    body: JsonObject = {
        "model": sampling.model or config.model_defaults.llm,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        body["system"] = system
    put_optional(body, "think", ollama_think(sampling, None))
    if options:
        body["options"] = options
    if sampling.json_mode:
        body["format"] = "json"
    return PreparedRequest(
        operation="generate", method="POST", path="/api/generate",
        timeout=config.timeouts.llm, json_body=body,
    )


def _context_window(options: Mapping[str, JsonValue]) -> int | None:
    value = options.get("num_ctx")
    return int(value) if isinstance(value, int | float) and value else None


def _flow_agent_generate(config: ClientConfig, prompt: str, system: str | None,
                         sampling: Sampling) -> PreparedRequest:
    """Provider-neutral ``/generate`` (``AiGenerateRequest``, extra fields forbidden).

    ``reasoning_effort`` is not part of the contract; the gateway sends ``think=false``.
    """
    temperature = sampling.temperature
    body: JsonObject = {
        "prompt": prompt,
        "capability": "chat",
        "quality": config.quality.value,
        "temperature": FLOW_AGENT_DEFAULT_TEMPERATURE if temperature is None else temperature,
    }
    if system:
        body["system"] = system
    put_optional(body, "max_tokens", sampling.max_tokens)
    if sampling.json_mode:
        body["response_format"] = "json"
    put_optional(body, "min_context_window", _context_window(sampling.options))
    return PreparedRequest(
        operation="generate", method="POST", path=f"{config.app_prefix}/generate",
        timeout=config.timeouts.llm, json_body=body,
    )


def build_generate(config: ClientConfig, prompt: str, system: str | None,
                   sampling: Sampling) -> PreparedRequest:
    """Single prompt with optional system prompt, in the dialect of mode and profile."""
    if config.mode is Mode.FLOW_AGENT:
        return _flow_agent_generate(config, prompt, system, sampling)
    if config.profile.generate_route is GenerateRoute.OLLAMA_CHAT:
        return _ollama_chat(config, prompt, system, sampling)
    return _ollama_generate(config, prompt, system, sampling)


def build_stream_chat(config: ClientConfig, messages: Messages, sampling: Sampling,
                      think: bool | None = None) -> PreparedRequest:
    """Streaming chat: Ollama NDJSON (ai-router, cockpit) or OpenAI SSE (Flow-Agent)."""
    timeouts = config.timeouts
    if config.mode is Mode.FLOW_AGENT:
        body = _openai_chat_body(config, message_list(messages), sampling,
                                 flow_agent_model(config, sampling.model))
        body["stream"] = True
        path = f"{config.app_prefix}/v1/chat/completions"
    else:
        body = {"model": sampling.model or config.model_defaults.llm,
                "messages": message_list(messages), "stream": True}
        if sampling.options:
            body["options"] = dict(sampling.options)
        put_optional(body, "think", think if think is not None else ollama_think(sampling, None))
        path = "/api/chat"
    return PreparedRequest(
        operation="stream_chat", method="POST", path=path, timeout=timeouts.llm,
        json_body=body, stream=True, connect_timeout=timeouts.stream_connect,
    )
