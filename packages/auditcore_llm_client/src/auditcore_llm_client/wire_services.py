"""Request builders for embeddings, reranking, OCR, health and the model list."""

from __future__ import annotations

from collections.abc import Sequence

from auditcore_llm_client.config import ClientConfig, Mode
from auditcore_llm_client.errors import UnsupportedOperationError
from auditcore_llm_client.jsontypes import JsonObject, JsonValue
from auditcore_llm_client.profiles import EmbedRoute, HealthAuth, RerankRoute
from auditcore_llm_client.wire import FormFile, HeaderMode, PreparedRequest, put_optional

#: Tesseract language codes of the vision service (flowinvoice ``_TESSERACT_LANGS``).
TESSERACT_LANGUAGES = {
    "deu": "deu",
    "de": "deu",
    "ger": "deu",
    "german": "deu",
    "eng": "eng",
    "en": "eng",
    "english": "eng",
}


def tesseract_language(language: str | None) -> str | None:
    """``auto``/empty → ``None`` (a literal ``auto`` makes Tesseract fail)."""
    if not language or language.lower() in {"auto", "any"}:
        return None
    return TESSERACT_LANGUAGES.get(language.lower(), language)


def _texts(texts: Sequence[str]) -> list[JsonValue]:
    return [str(text) for text in texts]


def build_embed(config: ClientConfig, texts: Sequence[str], model: str | None) -> PreparedRequest:
    """Embeddings; the Flow-Agent chooses the model itself."""
    timeout = config.timeouts.embed
    if config.mode is Mode.FLOW_AGENT:
        return PreparedRequest(
            operation="embed", method="POST", path=f"{config.app_prefix}/v1/embeddings",
            timeout=timeout, json_body={"input": _texts(texts)},
        )
    body: JsonObject = {"model": model or config.model_defaults.embed, "input": _texts(texts)}
    openai = PreparedRequest(
        operation="embed", method="POST", path="/v1/embeddings", timeout=timeout,
        json_body=body,
    )
    if config.profile.embed_route is EmbedRoute.OLLAMA_EMBED_WITH_FALLBACK:
        primary = PreparedRequest(
            operation="embed", method="POST", path="/api/embed", timeout=timeout,
            json_body=dict(body),
        )
        return primary.with_fallback(openai)
    return openai


def build_rerank(config: ClientConfig, query: str, documents: Sequence[str],
                 top_k: int | None, model: str | None) -> PreparedRequest:
    """Reranking: ``passages`` on ``/v1/rerank``, ``documents`` on ``/api/reranker``."""
    timeout = config.timeouts.rerank
    passages: JsonObject = {"query": query, "passages": _texts(documents)}
    if config.mode is not Mode.FLOW_AGENT:
        passages["model"] = model or config.model_defaults.rerank
    put_optional(passages, "top_k", top_k)
    openai = PreparedRequest(
        operation="rerank", method="POST", path=f"{config.app_prefix}/v1/rerank",
        timeout=timeout, json_body=passages,
    )
    if config.mode is Mode.FLOW_AGENT or (
        config.profile.rerank_route is not RerankRoute.RERANKER_WITH_FALLBACK
    ):
        return openai
    body: JsonObject = {
        "model": model or config.model_defaults.rerank,
        "query": query,
        "documents": _texts(documents),
    }
    put_optional(body, "top_k", top_k)
    primary = PreparedRequest(
        operation="rerank", method="POST", path="/api/reranker", timeout=timeout, json_body=body,
    )
    return primary.with_fallback(openai)


def _ocr_form(config: ClientConfig, model: str, language: str) -> tuple[tuple[str, str], ...]:
    if config.mode is not Mode.FLOW_AGENT:
        return (("model", model), ("language", language))
    backend = "auto" if (model or "auto").lower() == "auto" else model.lower()
    lang = tesseract_language(language)
    return (("backend", backend),) + ((("lang", lang),) if lang else ())


def build_ocr(config: ClientConfig, content: bytes, filename: str, content_type: str,
              model: str, language: str) -> PreparedRequest:
    """Multipart OCR; the Flow-Agent forwards the vision-service dialect opaquely."""
    field = "image" if config.mode is Mode.FLOW_AGENT else "file"
    path = f"{config.app_prefix}/v1/ocr" if config.mode is Mode.FLOW_AGENT else "/api/ocr"
    return PreparedRequest(
        operation="ocr", method="POST", path=path, timeout=config.timeouts.ocr,
        form=_ocr_form(config, model, language),
        files=(FormFile(field, filename, content, content_type),),
        headers=HeaderMode.AUTH,
    )


def build_health(config: ClientConfig, capability: str) -> PreparedRequest:
    """Flow-Agent readiness per capability, or the public ai-router ``/health``."""
    timeout = config.timeouts.health
    if config.mode is Mode.FLOW_AGENT:
        return PreparedRequest(
            operation="health", method="GET", path=f"{config.app_prefix}/ready",
            timeout=timeout, params=(("capability", capability),), headers=HeaderMode.AUTH,
        )
    headers = HeaderMode.JSON if config.profile.health_auth is HealthAuth.FULL else HeaderMode.NONE
    return PreparedRequest(
        operation="health", method="GET", path="/health", timeout=timeout, headers=headers,
    )


def build_models(config: ClientConfig) -> PreparedRequest:
    """Model list of the ai-router (cockpit ``/api/tags``)."""
    if config.mode is Mode.FLOW_AGENT:
        raise UnsupportedOperationError(
            "Der Flow-Agent wählt Modelle selbst; eine Modellliste gibt es nur beim ai-router.",
            endpoint="/api/tags",
        )
    return PreparedRequest(
        operation="models", method="GET", path="/api/tags", timeout=config.timeouts.models,
        headers=HeaderMode.AUTH,
    )
