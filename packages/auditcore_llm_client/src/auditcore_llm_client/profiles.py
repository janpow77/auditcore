"""App profiles: the characterised differences of the legacy clients as data.

Each profile describes the ai-router dialect of one application (routes,
fallbacks, sampling defaults, environment names). In Flow-Agent mode the
gateway contract is the same for every app; only environment names and the
default app id come from the profile.

Environment names and default app ids are no secrets. Profiles carry **no**
URLs and **no** keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from auditcore_llm_client.jsontypes import JsonValue


class GenerateRoute(StrEnum):
    """How a single prompt (plus optional system prompt) is sent to the ai-router."""

    #: audit_designer: Ollama ``/api/chat`` with fixed options, HTTP 404 → ``/v1/chat/completions``.
    OLLAMA_CHAT = "ollama_chat"
    #: flowinvoice/audit-portal: Ollama ``/api/generate``.
    OLLAMA_GENERATE = "ollama_generate"


class RerankRoute(StrEnum):
    """Reranker route of the ai-router."""

    #: audit_designer: ``/api/reranker`` (``documents``), HTTP 404 → ``/v1/rerank`` (``passages``).
    RERANKER_WITH_FALLBACK = "reranker_with_fallback"
    #: flowinvoice/audit-portal: ``/v1/rerank`` (``passages``).
    OPENAI_RERANK = "openai_rerank"


class EmbedRoute(StrEnum):
    """Embedding route of the ai-router."""

    #: audit_designer: ``/api/embed``, HTTP 404 → ``/v1/embeddings``.
    OLLAMA_EMBED_WITH_FALLBACK = "ollama_embed_with_fallback"
    #: flowinvoice/audit-portal: ``/v1/embeddings``.
    OPENAI_EMBEDDINGS = "openai_embeddings"


class HealthAuth(StrEnum):
    """Headers of the ai-router ``GET /health`` call."""

    #: flowinvoice/audit-portal: the public health check is sent without headers.
    NONE = "none"
    #: audit_designer: full request headers (app id, key, JSON content type).
    FULL = "full"


@dataclass(frozen=True)
class ModelDefaults:
    """Model names used when a call names none (ai-router mode only)."""

    llm: str
    embed: str
    rerank: str


@dataclass(frozen=True)
class EnvNames:
    """Environment variable names read by ``config_from_env``."""

    url: str = "LLM_ROUTER_URL"
    app_id: str = "LLM_ROUTER_APP_ID"
    api_key: str = "LLM_ROUTER_API_KEY"
    llm_models: tuple[str, ...] = ()
    embed_model: str | None = None
    rerank_model: str | None = None
    keep_alive: str | None = None
    flow_agent_url: str | None = None
    flow_agent_app_id: str | None = None
    flow_agent_key: str | None = None
    flow_agent_quality: str | None = None


@dataclass(frozen=True)
class Profile:
    """Dialect of one application."""

    name: str
    default_app_id: str
    env: EnvNames = field(default_factory=EnvNames)
    default_llm_model: str = "qwen3:14b"
    default_embed_model: str = "bge-m3"
    default_rerank_model: str = "bge-reranker-v2-m3"
    generate_route: GenerateRoute = GenerateRoute.OLLAMA_GENERATE
    rerank_route: RerankRoute = RerankRoute.OPENAI_RERANK
    embed_route: EmbedRoute = EmbedRoute.OPENAI_EMBEDDINGS
    health_auth: HealthAuth = HealthAuth.NONE
    #: Sampling values sent when the caller gives none (``None`` = omit).
    default_temperature: float | None = None
    default_max_tokens: int | None = None
    #: Fixed Ollama options of the ``/api/chat`` route (audit_designer).
    chat_options: tuple[tuple[str, JsonValue], ...] = ()
    default_keep_alive: str | None = None
    #: Value of the Ollama ``think`` flag on ``/api/chat`` (``None`` = omit).
    think: bool | None = None
    #: Remove ``<think>…</think>`` blocks from answers.
    strip_think_tags: bool = False
    #: Set for profiles of apps that are being shut down (no further work).
    deprecated: str | None = None

    def model_defaults(self) -> ModelDefaults:
        """The profile's built-in model names."""
        return ModelDefaults(
            llm=self.default_llm_model,
            embed=self.default_embed_model,
            rerank=self.default_rerank_model,
        )


_AUDIT_DESIGNER_OPTIONS: tuple[tuple[str, JsonValue], ...] = (
    ("num_ctx", 16384),
    ("top_p", 0.8),
    ("top_k", 20),
    ("presence_penalty", 0.0),
    ("repeat_penalty", 1.05),
)

AUDIT_DESIGNER = Profile(
    name="audit_designer",
    default_app_id="audit_designer",
    env=EnvNames(
        llm_models=("VP_AI_EGPU_MODEL", "OLLAMA_MODEL"),
        embed_model="LLM_ROUTER_EMBEDDING_MODEL",
        keep_alive="VP_AI_LLM_KEEP_ALIVE",
    ),
    default_llm_model="qwen3:14b",
    default_embed_model="bge-m3",
    default_rerank_model="bge-reranker-v2-m3",
    generate_route=GenerateRoute.OLLAMA_CHAT,
    rerank_route=RerankRoute.RERANKER_WITH_FALLBACK,
    embed_route=EmbedRoute.OLLAMA_EMBED_WITH_FALLBACK,
    health_auth=HealthAuth.FULL,
    default_temperature=0.2,
    default_max_tokens=4000,
    chat_options=_AUDIT_DESIGNER_OPTIONS,
    default_keep_alive="10m",
    think=False,
    strip_think_tags=True,
)

_FLOWINVOICE_ENV = EnvNames(
    llm_models=("OLLAMA_DEFAULT_MODEL",),
    embed_model="EMBEDDING_MODEL",
    rerank_model="RERANKER_MODEL",
    flow_agent_url="FLOW_AGENT_URL",
    flow_agent_app_id="FLOW_AGENT_APP_ID",
    flow_agent_key="FLOW_AGENT_APP_KEY",
    flow_agent_quality="FLOW_AGENT_QUALITY",
)

FLOWINVOICE = Profile(
    name="flowinvoice",
    default_app_id="flowinvoice",
    env=_FLOWINVOICE_ENV,
    default_rerank_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
)

AUDIT_PORTAL = Profile(
    name="audit_portal",
    default_app_id="audit-portal",
    env=EnvNames(
        llm_models=("OLLAMA_DEFAULT_MODEL",),
        embed_model="EMBEDDING_MODEL",
        rerank_model="RERANKER_MODEL",
    ),
    default_rerank_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
)

COCKPIT = Profile(
    name="cockpit",
    default_app_id="cockpit",
    deprecated="abgekündigt: cockpit wird abgeschaltet, Funktionen gehen in flow-agent #50",
    env=EnvNames(url="AI_ROUTER_URL", app_id="AI_ROUTER_APP_ID", api_key="AI_ROUTER_API_KEY"),
)

#: Neutral profile for new consumers: OpenAI-compatible routes, no fixed options.
GENERIC = Profile(
    name="generic",
    default_app_id="auditcore",
    env=EnvNames(
        url="AI_ROUTER_URL",
        app_id="AI_ROUTER_APP_ID",
        api_key="AI_ROUTER_API_KEY",
        flow_agent_url="FLOW_AGENT_URL",
        flow_agent_app_id="FLOW_AGENT_APP_ID",
        flow_agent_key="FLOW_AGENT_APP_KEY",
        flow_agent_quality="FLOW_AGENT_QUALITY",
    ),
)

PROFILES: dict[str, Profile] = {
    p.name: p for p in (AUDIT_DESIGNER, FLOWINVOICE, AUDIT_PORTAL, COCKPIT, GENERIC)
}


def get_profile(name: str) -> Profile:
    """Look up a profile by name (``audit_designer``, ``flowinvoice``, …)."""
    try:
        return PROFILES[name]
    except KeyError:
        known = ", ".join(sorted(PROFILES))
        raise KeyError(f"Unbekanntes Profil {name!r}; bekannt: {known}") from None
