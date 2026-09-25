"""Result types of all operations (field names follow the legacy dataclasses)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from auditcore_llm_client.jsontypes import JsonObject


@dataclass(frozen=True)
class ResponseTelemetry:
    """Routing information the gateway returns in response headers."""

    request_id: str = ""
    model: str = ""
    workers: tuple[str, ...] = ()
    spoke: str = ""
    failover: bool = False
    capability: str = ""


@dataclass(frozen=True)
class LlmResult:
    """Answer of ``generate``/``chat``."""

    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    raw_response: JsonObject = field(default_factory=dict)
    telemetry: ResponseTelemetry = field(default_factory=ResponseTelemetry)


@dataclass(frozen=True)
class OcrResult:
    """Answer of ``ocr`` (mapped from the ai-router ``OcrResponse``)."""

    text: str
    pages: list[JsonObject] = field(default_factory=list)
    spoke: str = ""
    model: str = ""
    duration_ms: int = 0
    confidence: float | None = None
    fields: JsonObject | None = None


@dataclass(frozen=True)
class RerankScore:
    """One scored document."""

    index: int
    score: float
    document: str | None = None


@dataclass(frozen=True)
class RerankResult:
    """Answer of ``rerank``; ``scores`` follow the order of the input documents.

    ``degraded`` marks the legacy behaviour of replacing a score list of the
    wrong length by zeros – callers can now see that this happened.
    """

    scores: list[float]
    results: list[RerankScore] = field(default_factory=list)
    model: str = ""
    spoke: str = ""
    duration_ms: int = 0
    degraded: bool = False


@dataclass(frozen=True)
class EmbedResult:
    """Answer of ``embed``; vectors follow the order of the input texts."""

    embeddings: list[list[float]]
    model: str = ""
    spoke: str = ""
    duration_ms: int = 0


@dataclass(frozen=True)
class ModelInfo:
    """One entry of the ai-router model list (``/api/tags``)."""

    name: str
    parameter_size: str = ""
    family: str = ""
    size_bytes: int = 0

    def to_dict(self) -> dict[str, str | int]:
        """Legacy dict form of cockpit."""
        return {
            "name": self.name,
            "parameter_size": self.parameter_size,
            "family": self.family,
            "size_bytes": self.size_bytes,
        }


class StreamEventKind(StrEnum):
    """Kind of a streamed chat event."""

    DELTA = "delta"
    DONE = "done"
    ERROR = "error"


@dataclass(frozen=True)
class StreamEvent:
    """One event of ``stream_chat``."""

    kind: StreamEventKind
    delta: str = ""
    error: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    eval_duration_ms: int = 0
    total_duration_ms: int = 0

    def to_dict(self) -> dict[str, str | int | bool | None]:
        """Legacy dict form of the cockpit stream."""
        if self.kind is StreamEventKind.DELTA:
            return {"delta": self.delta}
        if self.kind is StreamEventKind.ERROR:
            return {"error": self.error}
        return {
            "done": True,
            "eval_count": self.completion_tokens,
            "prompt_eval_count": self.prompt_tokens,
            "eval_duration_ms": self.eval_duration_ms,
            "total_duration_ms": self.total_duration_ms,
        }


@dataclass(frozen=True)
class UsageRecord:
    """Passed to ``ClientConfig.usage_hook`` after every LLM answer (audit-portal F3)."""

    operation: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
