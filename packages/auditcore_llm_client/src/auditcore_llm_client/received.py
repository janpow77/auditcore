"""Transport-neutral view of a gateway response and the HTTP error mapping."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from auditcore_llm_client.errors import (
    EgressDeniedError,
    InvalidResponseError,
    LlmClientError,
    RouterHttpError,
    SensitivityRejectedError,
)
from auditcore_llm_client.results import ResponseTelemetry

#: Characters of an error body that are kept in the message (legacy: 200).
ERROR_BODY_CHARS = 200


@dataclass(frozen=True)
class ReceivedResponse:
    """Status, lower-case headers and body of one response."""

    status: int
    content: bytes
    path: str
    headers: Mapping[str, str] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Body decoded as UTF-8 (replacement characters for invalid bytes)."""
        return self.content.decode("utf-8", "replace")

    def json(self) -> object:
        """Parsed body; an empty body counts as ``{}`` (legacy behaviour)."""
        if not self.content:
            return {}
        try:
            parsed: object = json.loads(self.content)
        except ValueError:
            raise InvalidResponseError(
                f"{self.path}: Antwort ist kein JSON", endpoint=self.path
            ) from None
        return parsed

    def header(self, name: str) -> str:
        """Header value or ``""``."""
        return self.headers.get(name.lower(), "")

    def telemetry(self) -> ResponseTelemetry:
        """Routing headers of ai-router (``X-Llm-*``) and Flow-Agent (``X-Flow-Agent-*``)."""
        workers = self.header("x-flow-agent-workers")
        return ResponseTelemetry(
            request_id=self.header("x-flow-agent-request-id"),
            model=self.header("x-flow-agent-model"),
            workers=tuple(w for w in workers.split(",") if w),
            spoke=self.header("x-llm-spoke"),
            failover=self.header("x-llm-failover") == "1",
            capability=self.header("x-flow-agent-capability"),
        )


def retry_after_seconds(value: str) -> float | None:
    """Parse a ``Retry-After`` header in seconds (HTTP dates are ignored)."""
    try:
        seconds = float(value)
    except ValueError:
        return None
    return max(0.0, seconds)


def _policy_error_type(received: ReceivedResponse) -> type[LlmClientError] | None:
    """Flow-Agent policy answers (flow-agent ``ai_gateway``: 400 sensitivity, 403 egress)."""
    detail = received.text
    if received.status == 400 and "Sensitivit" in detail:
        return SensitivityRejectedError
    if received.status == 403 and "Egress" in detail:
        return EgressDeniedError
    return None


def error_for_status(
    received: ReceivedResponse, secrets: Iterable[str], *, flow_agent: bool = False
) -> LlmClientError:
    """HTTP error with the first 200 body characters, redacted.

    In Flow-Agent mode sensitivity (400) and egress (403) rejections get their
    own, non-retryable error types.
    """
    body = received.text[:ERROR_BODY_CHARS]
    error_type = (_policy_error_type(received) if flow_agent else None) or RouterHttpError
    return error_type(
        f"{received.path} HTTP {received.status}: {body}",
        status_code=received.status,
        endpoint=received.path,
        retry_after=retry_after_seconds(received.header("retry-after")),
        secrets=secrets,
    )
