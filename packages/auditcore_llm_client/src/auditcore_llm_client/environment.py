"""Build a :class:`ClientConfig` from environment variables of a profile.

Mode selection follows flowinvoice: a non-empty Flow-Agent URL switches the
whole client to the app-bound Flow-Agent routes; otherwise the ai-router URL is
used. Unlike the legacy clients there is **no** default URL and **no** default
key – a missing URL is a :class:`ConfigurationError`.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from auditcore_llm_client.config import ClientConfig, Mode, Quality, SecretValue
from auditcore_llm_client.errors import ConfigurationError
from auditcore_llm_client.profiles import EnvNames, ModelDefaults, Profile


def _read(environ: Mapping[str, str], name: str | None) -> str:
    return (environ.get(name) or "").strip() if name else ""


def _first(environ: Mapping[str, str], names: tuple[str, ...], default: str) -> str:
    for name in names:
        value = _read(environ, name)
        if value:
            return value
    return default


def _quality(raw: str) -> Quality:
    """Legacy: unknown or empty values fall back to ``high``."""
    try:
        return Quality(raw.lower())
    except ValueError:
        return Quality.HIGH


def _secret(environ: Mapping[str, str], name: str | None) -> SecretValue | None:
    value = _read(environ, name)
    return SecretValue(value) if value else None


def model_defaults_from_env(profile: Profile, environ: Mapping[str, str]) -> ModelDefaults:
    """Model names from the profile's environment chain, else the profile defaults."""
    env = profile.env
    return ModelDefaults(
        llm=_first(environ, env.llm_models, profile.default_llm_model),
        embed=_first(environ, _names(env.embed_model), profile.default_embed_model),
        rerank=_first(environ, _names(env.rerank_model), profile.default_rerank_model),
    )


def _names(name: str | None) -> tuple[str, ...]:
    return (name,) if name else ()


def _flow_agent_config(
    profile: Profile, environ: Mapping[str, str], url: str
) -> ClientConfig:
    env: EnvNames = profile.env
    return ClientConfig(
        base_url=url,
        app_id=_read(environ, env.flow_agent_app_id) or profile.default_app_id,
        mode=Mode.FLOW_AGENT,
        api_key=_secret(environ, env.flow_agent_key),
        profile=profile,
        models=model_defaults_from_env(profile, environ),
        quality=_quality(_read(environ, env.flow_agent_quality)),
    )


def config_from_env(
    profile: Profile,
    environ: Mapping[str, str] | None = None,
) -> ClientConfig:
    """Read URL, app id, key, quality and model names for ``profile``."""
    source = os.environ if environ is None else environ
    env = profile.env
    flow_agent_url = _read(source, env.flow_agent_url)
    if flow_agent_url:
        return _flow_agent_config(profile, source, flow_agent_url)
    url = _read(source, env.url)
    if not url:
        raise ConfigurationError(f"{env.url} ist nicht gesetzt; es gibt keine Standard-URL.")
    return ClientConfig(
        base_url=url,
        app_id=_read(source, env.app_id) or profile.default_app_id,
        mode=Mode.AI_ROUTER,
        api_key=_secret(source, env.api_key),
        profile=profile,
        models=model_defaults_from_env(profile, source),
        keep_alive=_read(source, env.keep_alive) or None,
    )

