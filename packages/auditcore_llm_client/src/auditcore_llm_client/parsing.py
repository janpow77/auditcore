"""Turn gateway responses into result objects (legacy field mapping)."""

from __future__ import annotations

import logging
import re

from auditcore_llm_client.errors import InvalidResponseError, NotAssignedError
from auditcore_llm_client.jsontypes import (
    JsonObject,
    JsonValue,
    as_int,
    as_list,
    as_object,
    as_optional_float,
    as_text,
    first_text,
    strict_number,
)
from auditcore_llm_client.received import ReceivedResponse
from auditcore_llm_client.results import EmbedResult, LlmResult, ModelInfo, OcrResult

log = logging.getLogger("auditcore_llm_client")

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_NANOS_PER_MS = 1_000_000


def strip_think_tags(text: str) -> str:
    """Remove ``<think>…</think>`` reasoning blocks (Qwen3/DeepSeek)."""
    if not text or "<think>" not in text:
        return text
    return _THINK.sub("", text).strip()


def _openai_content(data: JsonObject) -> str:
    choices = as_list(data.get("choices"))
    if not choices:
        return ""
    return as_text(as_object(as_object(choices[0]).get("message")).get("content"))


def parse_llm(received: ReceivedResponse, model: str, strip_think: bool) -> LlmResult:
    """Parse ``/api/chat``, ``/api/generate``, ``/v1/chat/completions`` or ``…/generate``."""
    data = as_object(received.json())
    path = received.path
    if path.endswith("/v1/chat/completions"):
        usage = as_object(data.get("usage"))
        content = _openai_content(data)
        tokens = (as_int(usage.get("prompt_tokens")), as_int(usage.get("completion_tokens")))
        latency = 0
        answered_model = as_text(data.get("model"), model)
    elif path.endswith("/generate") and path != "/api/generate":
        content = as_text(data.get("content"))
        tokens, latency = (0, 0), 0
        answered_model = first_text(data.get("model_id"), model)
    else:
        message = as_object(data.get("message"))
        content = as_text(message.get("content") if message else data.get("response"))
        tokens = (as_int(data.get("prompt_eval_count")), as_int(data.get("eval_count")))
        latency = as_int(data.get("total_duration")) // _NANOS_PER_MS
        answered_model = as_text(data.get("model"), model)
    return LlmResult(
        content=strip_think_tags(content) if strip_think else content,
        model=answered_model,
        input_tokens=tokens[0],
        output_tokens=tokens[1],
        latency_ms=latency,
        raw_response=data,
        telemetry=received.telemetry(),
    )


def _vectors(items: list[JsonValue], expected: int, path: str) -> list[list[float]]:
    if len(items) != expected:
        raise InvalidResponseError(
            f"{path}: erwartete {expected} Vektoren, bekam {len(items)}", endpoint=path
        )
    try:
        return [[strict_number(x) for x in as_list(vector)] for vector in items]
    except ValueError:
        raise InvalidResponseError(f"{path}: ungültiger Vektor", endpoint=path) from None


def _index(item: JsonValue) -> int:
    return as_int(as_object(item).get("index"))


def parse_embed(received: ReceivedResponse, expected: int, model: str) -> EmbedResult:
    """``{"embeddings": [...]}`` (``/api/embed``) or OpenAI ``{"data": [{index, embedding}]}``."""
    data = as_object(received.json())
    path = received.path
    if path.endswith("/api/embed") and data.get("embeddings") is not None:
        vectors = _vectors(as_list(data.get("embeddings")), expected, path)
    else:
        items = sorted(as_list(data.get("data")), key=_index)
        raw = [as_object(item).get("embedding") for item in items]
        vectors = _vectors(raw, expected, path)
    return EmbedResult(
        embeddings=vectors,
        model=as_text(data.get("model"), model),
        spoke=as_text(data.get("spoke")),
        duration_ms=as_int(data.get("duration_ms")),
    )


def _fields(value: JsonValue) -> JsonObject | None:
    return as_object(value) if isinstance(value, dict) else None


def parse_ocr(received: ReceivedResponse, model: str, flow_agent: bool) -> OcrResult:
    """ai-router ``OcrResponse`` or vision-service answer behind the Flow-Agent."""
    payload = as_object(received.json())
    confidence = as_optional_float(payload.get("confidence"))
    duration = as_int(payload.get("duration_ms"))
    if flow_agent:
        return OcrResult(
            text=as_text(payload.get("text")),
            spoke=received.header("x-flow-agent-capability"),
            model=first_text(payload.get("backend"), model),
            duration_ms=duration,
            confidence=confidence,
        )
    return OcrResult(
        text=as_text(payload.get("text")),
        pages=[as_object(page) for page in as_list(payload.get("pages"))],
        spoke=as_text(payload.get("spoke")),
        model=as_text(payload.get("model"), model),
        duration_ms=duration,
        confidence=confidence,
        fields=_fields(payload.get("fields")),
    )


def parse_health(received: ReceivedResponse, capability: str, flow_agent: bool) -> JsonObject:
    """Health JSON; non-JSON answers become ``{"status": "ok", "raw": text}`` (legacy)."""
    try:
        parsed = received.json()
    except InvalidResponseError:
        return {"status": "ok", "raw": received.text}
    if not isinstance(parsed, dict):
        return {"status": "ok", "raw": received.text}
    data = as_object(parsed)
    if flow_agent and data.get("status") != "assigned":
        reasons = data.get("reasons") or ""
        status = data.get("status")
        message = f"flow-agent capability '{capability}' nicht zugewiesen: {status} {reasons}"
        raise NotAssignedError(message[:200], endpoint=received.path)
    return data


def _model_info(entry: JsonObject) -> ModelInfo:
    details = as_object(entry.get("details"))
    return ModelInfo(
        name=first_text(entry.get("name")),
        parameter_size=first_text(details.get("parameter_size")),
        family=first_text(details.get("family")),
        size_bytes=as_int(entry.get("size")),
    )


def parse_models(received: ReceivedResponse) -> list[ModelInfo]:
    """cockpit ``/api/tags`` mapping; non-object entries are skipped."""
    data = received.json()
    entries = data.get("models") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise InvalidResponseError("unerwartete Antwort von /api/tags", endpoint=received.path)
    return [_model_info(as_object(entry)) for entry in entries if isinstance(entry, dict)]
