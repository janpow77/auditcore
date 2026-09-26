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
from auditcore_llm_client.environment import (
    SecretRefResolver,
    config_from_env,
    is_secret_reference,
    model_defaults_from_env,
    resolve_secret,
)
from auditcore_llm_client.errors import (
    AiRouterError,
    CircuitOpenError,
    ConfigurationError,
    EgressDeniedError,
    ErrorKind,
    InvalidResponseError,
    LlmClientError,
    NotAssignedError,
    RouterHttpError,
    RouterTimeoutError,
    RouterUnavailableError,
    SensitivityRejectedError,
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

__version__ = "0.1.2"

__all__ = [
    "AUDIT_DESIGNER", "AUDIT_PORTAL", "COCKPIT", "FLOWINVOICE", "GENERIC", "PROFILES",
    "AiRouterError", "async_safe_call", "AsyncLlmClient", "BreakerPolicy", "BreakerState",
    "CircuitBreaker", "CircuitOpenError", "ClientConfig", "config_from_env",
    "ConfigurationError", "EgressDeniedError", "EmbedResult", "EmbedRoute", "EnvNames",
    "ErrorKind", "GenerateRoute", "get_profile", "HealthAuth", "InvalidResponseError",
    "is_secret_reference", "LlmClient", "LlmClientError", "LlmResult", "Mode",
    "model_defaults_from_env", "ModelCatalog", "ModelDefaults", "ModelInfo", "ModelSnapshot",
    "NotAssignedError", "OcrResult", "Profile", "Quality", "redact", "RerankResult",
    "RerankRoute", "RerankScore", "resolve_secret", "ResponseTelemetry", "RetryPolicy",
    "RouterHealth", "RouterHttpError", "RouterTimeoutError", "RouterUnavailableError",
    "safe_call", "SecretRefResolver", "SecretValue", "Sensitivity", "SensitivityRejectedError",
    "StreamEvent", "StreamEventKind", "strip_think_tags", "Timeouts",
    "UnsupportedOperationError", "unwrap_secret", "UsageRecord", "validate_base_url",
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
