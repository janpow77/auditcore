"""Client for the ai-router and the Flow-Agent inference gateway.

FlowAgent (with the ai-router in front) is the only GPU path: the library never
talks to Ollama, vLLM or GPU hosts directly. The configuration, request
builders, parsers, redaction, health tracking, retry policy and circuit breaker
need only the standard library; the HTTP clients :class:`LlmClient` and
:class:`AsyncLlmClient` need the extra ``http`` (httpx) and are imported lazily.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from auditcore_llm_client.catalog import ModelCatalog, ModelSnapshot
from auditcore_llm_client.config import (
    ClientConfig,
    Mode,
    Quality,
    SecretValue,
    Sensitivity,
    Timeouts,
    unwrap_secret,
    validate_base_url,
)
from auditcore_llm_client.environment import config_from_env, model_defaults_from_env
from auditcore_llm_client.errors import (
    AiRouterError,
    CircuitOpenError,
    ConfigurationError,
    ErrorKind,
    InvalidResponseError,
    LlmClientError,
    NotAssignedError,
    RouterHttpError,
    RouterTimeoutError,
    RouterUnavailableError,
    UnsupportedOperationError,
)
from auditcore_llm_client.health import RouterHealth, async_safe_call, safe_call
from auditcore_llm_client.parsing import strip_think_tags
from auditcore_llm_client.profiles import (
    AUDIT_DESIGNER,
    AUDIT_PORTAL,
    COCKPIT,
    FLOWINVOICE,
    GENERIC,
    PROFILES,
    EmbedRoute,
    EnvNames,
    GenerateRoute,
    HealthAuth,
    ModelDefaults,
    Profile,
    RerankRoute,
    get_profile,
)
from auditcore_llm_client.redaction import redact
from auditcore_llm_client.resilience import BreakerPolicy, BreakerState, CircuitBreaker, RetryPolicy
from auditcore_llm_client.results import (
    EmbedResult,
    LlmResult,
    ModelInfo,
    OcrResult,
    RerankResult,
    RerankScore,
    ResponseTelemetry,
    StreamEvent,
    StreamEventKind,
    UsageRecord,
)

if TYPE_CHECKING:
    from auditcore_llm_client.async_client import AsyncLlmClient
    from auditcore_llm_client.sync_client import LlmClient

__version__ = "0.1.0"

__all__ = [
    "AUDIT_DESIGNER", "AUDIT_PORTAL", "COCKPIT", "FLOWINVOICE", "GENERIC", "PROFILES",
    "AiRouterError", "AsyncLlmClient", "BreakerPolicy", "BreakerState", "CircuitBreaker",
    "CircuitOpenError", "ClientConfig", "ConfigurationError", "EmbedResult", "EmbedRoute",
    "EnvNames", "ErrorKind", "GenerateRoute", "HealthAuth", "InvalidResponseError",
    "LlmClient", "LlmClientError", "LlmResult", "Mode", "ModelCatalog", "ModelDefaults",
    "ModelInfo", "ModelSnapshot", "NotAssignedError", "OcrResult", "Profile", "Quality",
    "RerankResult", "RerankRoute", "RerankScore", "ResponseTelemetry", "RetryPolicy",
    "RouterHealth", "RouterHttpError", "RouterTimeoutError", "RouterUnavailableError",
    "SecretValue", "Sensitivity", "StreamEvent", "StreamEventKind", "Timeouts",
    "UnsupportedOperationError", "UsageRecord", "async_safe_call", "config_from_env",
    "get_profile", "model_defaults_from_env", "redact", "safe_call", "strip_think_tags",
    "unwrap_secret", "validate_base_url",
]


def __getattr__(name: str) -> object:
    """Import the httpx-based clients on first use (extra ``http``)."""
    if name == "LlmClient":
        from auditcore_llm_client.sync_client import LlmClient

        return LlmClient
    if name == "AsyncLlmClient":
        from auditcore_llm_client.async_client import AsyncLlmClient

        return AsyncLlmClient
    raise AttributeError(f"module 'auditcore_llm_client' has no attribute {name!r}")
