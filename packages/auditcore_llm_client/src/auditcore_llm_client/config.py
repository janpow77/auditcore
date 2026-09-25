"""Client configuration: target, credentials, timeouts, resilience, profile.

Principles:

* FlowAgent (or the ai-router in front of it) is the only GPU path. The client
  talks to exactly one configured gateway URL; direct Ollama hosts are refused
  and there is no local fallback.
* Keys only come from configuration or environment; there are no default keys
  and no default hosts (the public package must not carry internal addresses).
* A key is held as :class:`SecretValue` and never appears in ``repr``, messages
  or logs.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from urllib.parse import urlsplit

from auditcore_llm_client.errors import ConfigurationError
from auditcore_llm_client.profiles import GENERIC, ModelDefaults, Profile
from auditcore_llm_client.resilience import BreakerPolicy, RetryPolicy
from auditcore_llm_client.results import UsageRecord

#: Default port of a bare Ollama server; the client must never talk to it directly.
DIRECT_OLLAMA_PORT = 11434
_AUTH_HEADERS = frozenset(
    {"authorization", "x-api-key", "x-app-id", "cookie", "proxy-authorization"}
)
_APP_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class SecretValue:
    """A credential that does not reveal itself in ``repr``/``str``."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        if not value:
            raise ConfigurationError("Leerer Schlüssel ist nicht zulässig.")
        self._value = value

    def reveal(self) -> str:
        """The plain value – only for building the request header."""
        return self._value

    def __repr__(self) -> str:
        return "SecretValue('***')"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SecretValue) and other._value == self._value

    def __hash__(self) -> int:
        return hash(("SecretValue", self._value))


def unwrap_secret(value: object) -> SecretValue | None:
    """Accept ``str``, pydantic ``SecretStr`` or ``None`` (legacy ``_unwrap_secret``)."""
    if value is None or isinstance(value, SecretValue):
        return value
    reveal = getattr(value, "get_secret_value", None)
    if callable(reveal):
        try:
            plain = reveal()
        except Exception:  # noqa: BLE001 - a broken secret object counts as missing
            return None
        return SecretValue(str(plain)) if plain else None
    text = str(value)
    return SecretValue(text) if text else None


class Mode(StrEnum):
    """Which gateway dialect the client speaks."""

    AI_ROUTER = "ai_router"
    FLOW_AGENT = "flow_agent"


class Quality(StrEnum):
    """Flow-Agent quality selector; the gateway picks the model."""

    FAST = "fast"
    BALANCED = "balanced"
    HIGH = "high"


class Sensitivity(StrEnum):
    """Value of ``X-Flow-Sensitivity`` (Flow-Agent egress policy)."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass(frozen=True)
class Timeouts:
    """Per-operation timeouts in seconds (defaults of all legacy clients)."""

    llm: float = 600.0
    ocr: float = 180.0
    rerank: float = 30.0
    embed: float = 60.0
    health: float = 10.0
    models: float = 6.0
    stream_connect: float = 10.0


def validate_base_url(url: str) -> str:
    """Normalise and check the gateway URL; raise :class:`ConfigurationError`."""
    cleaned = url.strip().rstrip("/")
    parts = urlsplit(cleaned)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ConfigurationError("Gateway-URL muss mit http:// oder https:// beginnen.")
    if parts.username or parts.password:
        raise ConfigurationError("Zugangsdaten gehören nicht in die Gateway-URL.")
    if parts.query or parts.fragment:
        raise ConfigurationError("Gateway-URL darf keine Query und kein Fragment enthalten.")
    if parts.port == DIRECT_OLLAMA_PORT:
        raise ConfigurationError(
            "Direkter Ollama-Zugriff ist nicht zulässig; "
            "FlowAgent/ai-router ist der einzige GPU-Weg."
        )
    return cleaned


def _check_extra_headers(headers: Mapping[str, str]) -> None:
    for name in headers:
        if name.lower() in _AUTH_HEADERS:
            raise ConfigurationError(f"Header {name} wird nur vom Client selbst gesetzt.")


@dataclass(frozen=True)
class ClientConfig:
    """Everything a client needs; build it directly or via ``config_from_env``."""

    base_url: str
    app_id: str
    mode: Mode = Mode.AI_ROUTER
    api_key: SecretValue | None = None
    profile: Profile = GENERIC
    models: ModelDefaults | None = None
    quality: Quality = Quality.HIGH
    sensitivity: Sensitivity | None = None
    #: Ollama ``keep_alive`` of the audit_designer ``/api/chat`` route (``None`` = profile).
    keep_alive: str | None = None
    timeouts: Timeouts = field(default_factory=Timeouts)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    breaker: BreakerPolicy | None = None
    extra_headers: Mapping[str, str] = field(default_factory=dict)
    usage_hook: Callable[[UsageRecord], None] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", validate_base_url(self.base_url))
        if not _APP_ID.fullmatch(self.app_id):
            raise ConfigurationError("App-ID fehlt oder enthält unzulässige Zeichen.")
        if self.mode is Mode.FLOW_AGENT and self.api_key is None:
            raise ConfigurationError(
                "Flow-Agent-Modus braucht einen appgebundenen Schlüssel (fail-closed)."
            )
        _check_extra_headers(self.extra_headers)
        if self.models is None:
            object.__setattr__(self, "models", self.profile.model_defaults())

    @property
    def model_defaults(self) -> ModelDefaults:
        """Resolved model defaults (never ``None`` after construction)."""
        return self.models or self.profile.model_defaults()

    @property
    def secrets(self) -> tuple[str, ...]:
        """Values that must never leave the client in clear text."""
        return (self.api_key.reveal(),) if self.api_key else ()

    @property
    def app_prefix(self) -> str:
        """Path prefix of the app-bound Flow-Agent routes (empty for the ai-router)."""
        if self.mode is Mode.FLOW_AGENT:
            return f"/api/v1/ai/apps/{self.app_id}"
        return ""
