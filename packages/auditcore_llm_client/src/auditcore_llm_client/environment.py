"""Build a :class:`ClientConfig` from environment variables of a profile.

Mode selection follows flowinvoice: a non-empty Flow-Agent URL switches the
whole client to the app-bound Flow-Agent routes; otherwise the ai-router URL is
used. Unlike the legacy clients there is **no** default URL and **no** default
key – a missing URL is a :class:`ConfigurationError`.

Keys are preferably kept as Flow-Agent secret references
(``secret://<anbieter>/<name>``) and resolved at start through
``POST /api/v1/secrets/use``. Pass a resolver, e.g.
``flow_agent_client.secret_refs.SecretResolver.from_env().resolve``; this
library has no dependency on ``flow_agent_client``. A reference without a
resolver is a :class:`ConfigurationError` – it is never sent as a key.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping

from auditcore_llm_client.config import ClientConfig, Mode, Quality, SecretValue
from auditcore_llm_client.errors import ConfigurationError
from auditcore_llm_client.profiles import EnvNames, ModelDefaults, Profile

#: Resolves a ``secret://`` reference to the plain value (injected, e.g. flow-agent client).
SecretRefResolver = Callable[[str], str]
SECRET_REFERENCE_PREFIX = "secret://"


def is_secret_reference(value: str) -> bool:
    """True for Flow-Agent secret references (``secret://<anbieter>/<name>``)."""
    return value.strip().startswith(SECRET_REFERENCE_PREFIX)


def resolve_secret(value: str, resolver: SecretRefResolver | None) -> SecretValue | None:
    """Plain value or resolved ``secret://`` reference; the value never enters messages."""
    if not value:
        return None
    if not is_secret_reference(value):
        return SecretValue(value)
    if resolver is None:
        raise ConfigurationError(f"{value.strip()} braucht einen Secret-Resolver.")
    try:
        plain = resolver(value.strip())
    except Exception as exc:  # noqa: BLE001 - resolver errors must not carry values
        raise ConfigurationError(
            f"{value.strip()} konnte nicht aufgelöst werden ({type(exc).__name__})."
        ) from None
    if not plain:
        raise ConfigurationError(f"{value.strip()} lieferte keinen Wert.")
    return SecretValue(plain)


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


def _secret(environ: Mapping[str, str], name: str | None,
            resolver: SecretRefResolver | None) -> SecretValue | None:
    return resolve_secret(_read(environ, name), resolver)


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
    profile: Profile, environ: Mapping[str, str], url: str, resolver: SecretRefResolver | None
) -> ClientConfig:
    env: EnvNames = profile.env
    return ClientConfig(
        base_url=url,
        app_id=_read(environ, env.flow_agent_app_id) or profile.default_app_id,
        mode=Mode.FLOW_AGENT,
        api_key=_secret(environ, env.flow_agent_key, resolver),
        profile=profile,
        models=model_defaults_from_env(profile, environ),
        quality=_quality(_read(environ, env.flow_agent_quality)),
    )


def config_from_env(
    profile: Profile,
    environ: Mapping[str, str] | None = None,
    *,
    secret_resolver: SecretRefResolver | None = None,
) -> ClientConfig:
    """Read URL, app id, key, quality and model names for ``profile``.

    A key given as ``secret://…`` is resolved with ``secret_resolver``.
    """
    source = os.environ if environ is None else environ
    env = profile.env
    flow_agent_url = _read(source, env.flow_agent_url)
    if flow_agent_url:
        return _flow_agent_config(profile, source, flow_agent_url, secret_resolver)
    url = _read(source, env.url)
    if not url:
        raise ConfigurationError(f"{env.url} ist nicht gesetzt; es gibt keine Standard-URL.")
    return ClientConfig(
        base_url=url,
        app_id=_read(source, env.app_id) or profile.default_app_id,
        mode=Mode.AI_ROUTER,
        api_key=_secret(source, env.api_key, secret_resolver),
        profile=profile,
        models=model_defaults_from_env(profile, source),
        keep_alive=_read(source, env.keep_alive) or None,
    )

