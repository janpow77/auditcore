"""Public operations as (request, parser) pairs – identical for sync and async."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from auditcore_llm_client.config import ClientConfig, Mode
from auditcore_llm_client.engine import Operation, with_timeout
from auditcore_llm_client.jsontypes import JsonObject, JsonValue
from auditcore_llm_client.parsing import (
    parse_embed,
    parse_health,
    parse_llm,
    parse_models,
    parse_ocr,
)
from auditcore_llm_client.parsing_rerank import parse_rerank
from auditcore_llm_client.profiles import RerankRoute
from auditcore_llm_client.received import ReceivedResponse
from auditcore_llm_client.results import EmbedResult, LlmResult, ModelInfo, OcrResult, RerankResult
from auditcore_llm_client.wire import Messages
from auditcore_llm_client.wire_llm import Sampling, build_chat, build_generate
from auditcore_llm_client.wire_services import (
    build_embed,
    build_health,
    build_models,
    build_ocr,
    build_rerank,
)


def sampling(
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    json_mode: bool = False,
    seed: int | None = None,
    options: Mapping[str, JsonValue] | None = None,
    reasoning_effort: str | None = None,
) -> Sampling:
    """Collect sampling arguments of a public call."""
    return Sampling(model, temperature, max_tokens, json_mode, seed, dict(options or {}),
                    reasoning_effort)


def generate_op(config: ClientConfig, prompt: str, system: str | None, params: Sampling,
                timeout: float | None) -> Operation[LlmResult]:
    """Single prompt."""
    request = with_timeout(build_generate(config, prompt, system, params), timeout)
    model = params.model or config.model_defaults.llm
    strip = config.profile.strip_think_tags

    def parse(received: ReceivedResponse) -> LlmResult:
        return parse_llm(received, model, strip)

    return Operation(request, parse)


def chat_op(config: ClientConfig, messages: Messages, params: Sampling,
            timeout: float | None) -> Operation[LlmResult]:
    """Chat completion."""
    request = with_timeout(build_chat(config, messages, params), timeout)
    body = request.json_body or {}
    model = str(body.get("model") or "")
    strip = config.profile.strip_think_tags

    def parse(received: ReceivedResponse) -> LlmResult:
        return parse_llm(received, model, strip)

    return Operation(request, parse)


def embed_op(config: ClientConfig, texts: Sequence[str], model: str | None,
             timeout: float | None) -> Operation[EmbedResult]:
    """Embeddings; an empty input needs no request."""
    items = list(texts)
    eff_model = model or config.model_defaults.embed
    if not items:
        return Operation(None, lambda _: EmbedResult(embeddings=[], model=eff_model))
    request = with_timeout(build_embed(config, items, model), timeout)
    return Operation(request, lambda received: parse_embed(received, len(items), eff_model))


def rerank_op(config: ClientConfig, query: str, documents: Sequence[str], top_k: int | None,
              model: str | None, timeout: float | None) -> Operation[RerankResult]:
    """Reranking; an empty document list needs no request."""
    docs = list(documents)
    eff_model = model or config.model_defaults.rerank
    if not docs:
        return Operation(None, lambda _: RerankResult(scores=[], model=eff_model))
    prefer_results = (
        config.mode is Mode.AI_ROUTER
        and config.profile.rerank_route is RerankRoute.RERANKER_WITH_FALLBACK
    )
    request = with_timeout(build_rerank(config, query, docs, top_k, model), timeout)
    return Operation(
        request, lambda received: parse_rerank(received, docs, eff_model, prefer_results)
    )


def ocr_op(config: ClientConfig, content: bytes, filename: str, content_type: str,
           model: str, language: str, timeout: float | None) -> Operation[OcrResult]:
    """Multipart OCR."""
    request = with_timeout(
        build_ocr(config, content, filename, content_type, model, language), timeout
    )
    flow_agent = config.mode is Mode.FLOW_AGENT
    return Operation(request, lambda received: parse_ocr(received, model, flow_agent))


def health_op(config: ClientConfig, capability: str) -> Operation[JsonObject]:
    """Gateway health or Flow-Agent readiness."""
    flow_agent = config.mode is Mode.FLOW_AGENT
    return Operation(
        build_health(config, capability),
        lambda received: parse_health(received, capability, flow_agent),
    )


def models_op(config: ClientConfig) -> Operation[list[ModelInfo]]:
    """ai-router model list."""
    return Operation(build_models(config), parse_models)
