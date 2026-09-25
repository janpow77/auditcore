"""Transport-neutral request description and header construction (stdlib only)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum

from auditcore_llm_client.config import ClientConfig, Mode
from auditcore_llm_client.jsontypes import JsonObject, JsonValue

Messages = Sequence[Mapping[str, str]]


class HeaderMode(StrEnum):
    """Which headers a request carries."""

    #: No headers at all (public ai-router ``/health`` of flowinvoice/audit-portal).
    NONE = "none"
    #: Auth headers plus ``Content-Type: application/json``.
    JSON = "json"
    #: Auth headers only (multipart bodies, GET requests).
    AUTH = "auth"


@dataclass(frozen=True)
class FormFile:
    """One multipart file part."""

    field: str
    filename: str
    content: bytes
    content_type: str


@dataclass(frozen=True)
class PreparedRequest:
    """A fully described gateway request; the transport only adds the base URL."""

    operation: str
    method: str
    path: str
    timeout: float
    json_body: JsonObject | None = None
    params: tuple[tuple[str, str], ...] = ()
    form: tuple[tuple[str, str], ...] = ()
    files: tuple[FormFile, ...] = ()
    headers: HeaderMode = HeaderMode.JSON
    stream: bool = False
    connect_timeout: float | None = None
    #: Sent instead when the gateway answers HTTP 404 (audit_designer route fallbacks).
    fallback_on_404: PreparedRequest | None = None

    def with_fallback(self, fallback: PreparedRequest) -> PreparedRequest:
        """Copy with a 404 fallback."""
        return replace(self, fallback_on_404=fallback)


def request_headers(config: ClientConfig, mode: HeaderMode) -> dict[str, str]:
    """Headers of one request, including credentials (never logged)."""
    if mode is HeaderMode.NONE:
        return {}
    headers: dict[str, str] = {}
    if config.mode is Mode.FLOW_AGENT:
        if config.api_key is not None:
            headers["Authorization"] = f"Bearer {config.api_key.reveal()}"
    else:
        headers["X-App-Id"] = config.app_id
        if config.api_key is not None:
            headers["X-Api-Key"] = config.api_key.reveal()
    if config.sensitivity is not None:
        headers["X-Flow-Sensitivity"] = config.sensitivity.value
    headers.update(config.extra_headers)
    if mode is HeaderMode.JSON:
        headers["Content-Type"] = "application/json"
    return headers


def message_list(messages: Messages) -> list[JsonValue]:
    """Copy chat messages into plain JSON objects."""
    return [{str(k): str(v) for k, v in message.items()} for message in messages]


def put_optional(body: JsonObject, key: str, value: JsonValue) -> None:
    """Set ``key`` only when ``value`` is not ``None``."""
    if value is not None:
        body[key] = value
