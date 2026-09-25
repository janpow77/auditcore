"""Configuration, secrets, profiles and environment."""

from __future__ import annotations

import dataclasses

import pytest

from auditcore_llm_client import (
    AUDIT_DESIGNER,
    COCKPIT,
    FLOWINVOICE,
    GENERIC,
    PROFILES,
    ClientConfig,
    ConfigurationError,
    Mode,
    Quality,
    SecretValue,
    config_from_env,
    get_profile,
    unwrap_secret,
    validate_base_url,
)

KEY = "k3y-Geheim-4711"


class FakeSecretStr:
    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value


class BrokenSecret:
    def get_secret_value(self) -> str:
        raise RuntimeError(KEY)


@pytest.mark.parametrize(
    "url",
    [
        "ftp://router:7842",
        "router:7842",
        "http://user:pw@router:7842",
        "http://router:7842/?key=1",
        "http://router:7842#x",
        "http://localhost:11434",
        "",
    ],
)
def test_unsafe_urls_are_refused(url: str) -> None:
    with pytest.raises(ConfigurationError):
        validate_base_url(url)


def test_url_is_normalised() -> None:
    assert validate_base_url(" https://agent.test/prefix/ ") == "https://agent.test/prefix"


def test_secret_value_never_shows_itself() -> None:
    secret = SecretValue(KEY)
    config = ClientConfig(base_url="http://r.test", app_id="x", api_key=secret)
    for text in (repr(secret), str(secret), repr(config), str(config), f"{secret}"):
        assert KEY not in text
    assert secret.reveal() == KEY
    assert secret == SecretValue(KEY) and hash(secret) == hash(SecretValue(KEY))
    with pytest.raises(ConfigurationError):
        SecretValue("")


def test_unwrap_secret_accepts_legacy_types() -> None:
    assert unwrap_secret(None) is None
    assert unwrap_secret("") is None
    assert unwrap_secret(FakeSecretStr("")) is None
    assert unwrap_secret(BrokenSecret()) is None
    assert unwrap_secret(FakeSecretStr(KEY)) == SecretValue(KEY)
    assert unwrap_secret(KEY) == SecretValue(KEY)
    same = SecretValue(KEY)
    assert unwrap_secret(same) is same


def test_flow_agent_mode_is_fail_closed_without_key() -> None:
    with pytest.raises(ConfigurationError) as info:
        ClientConfig(base_url="https://agent.test", app_id="app", mode=Mode.FLOW_AGENT)
    assert "Schlüssel" in str(info.value)


@pytest.mark.parametrize("name", ["X-Api-Key", "authorization", "X-App-Id", "Cookie"])
def test_extra_headers_cannot_carry_credentials(name: str) -> None:
    with pytest.raises(ConfigurationError):
        ClientConfig(base_url="http://r.test", app_id="a", extra_headers={name: "v"})


@pytest.mark.parametrize("app_id", ["", "a/b", "../x", "a b", "x" * 65])
def test_app_id_must_be_a_path_segment(app_id: str) -> None:
    with pytest.raises(ConfigurationError):
        ClientConfig(base_url="http://r.test", app_id=app_id)


def test_models_default_to_profile() -> None:
    config = ClientConfig(base_url="http://r.test", app_id="a", profile=AUDIT_DESIGNER)
    assert config.model_defaults == AUDIT_DESIGNER.model_defaults()
    assert config.app_prefix == ""
    assert config.secrets == ()


def test_env_requires_a_url_and_has_no_default_key() -> None:
    with pytest.raises(ConfigurationError) as info:
        config_from_env(AUDIT_DESIGNER, {})
    assert "LLM_ROUTER_URL" in str(info.value)
    config = config_from_env(AUDIT_DESIGNER, {"LLM_ROUTER_URL": "http://r.test:7842"})
    assert config.api_key is None and config.app_id == "audit_designer"
    assert config.mode is Mode.AI_ROUTER


def test_env_model_chain_and_keep_alive() -> None:
    env = {"LLM_ROUTER_URL": "http://r.test", "OLLAMA_MODEL": "o", "VP_AI_LLM_KEEP_ALIVE": "3m",
           "LLM_ROUTER_EMBEDDING_MODEL": "e"}
    config = config_from_env(AUDIT_DESIGNER, env)
    assert (config.model_defaults.llm, config.model_defaults.embed) == ("o", "e")
    assert config.keep_alive == "3m"
    env["VP_AI_EGPU_MODEL"] = "egpu"
    assert config_from_env(AUDIT_DESIGNER, env).model_defaults.llm == "egpu"


def test_flow_agent_url_switches_mode() -> None:
    env = {"LLM_ROUTER_URL": "http://r.test", "FLOW_AGENT_URL": "https://agent.test/",
           "FLOW_AGENT_APP_KEY": KEY, "FLOW_AGENT_QUALITY": "Fast"}
    config = config_from_env(FLOWINVOICE, env)
    assert config.mode is Mode.FLOW_AGENT and config.base_url == "https://agent.test"
    assert config.quality is Quality.FAST and config.app_prefix == "/api/v1/ai/apps/flowinvoice"
    env["FLOW_AGENT_QUALITY"] = "ultra"
    assert config_from_env(FLOWINVOICE, env).quality is Quality.HIGH
    del env["FLOW_AGENT_APP_KEY"]
    with pytest.raises(ConfigurationError):
        config_from_env(FLOWINVOICE, env)


def test_profiles_without_flow_agent_ignore_its_url() -> None:
    env = {"AI_ROUTER_URL": "http://r.test", "FLOW_AGENT_URL": "https://agent.test"}
    assert config_from_env(COCKPIT, env).mode is Mode.AI_ROUTER
    env["FLOW_AGENT_APP_KEY"] = KEY
    assert config_from_env(GENERIC, env).mode is Mode.FLOW_AGENT


def test_profiles_carry_no_urls_or_keys() -> None:
    for profile in PROFILES.values():
        text = repr(dataclasses.asdict(profile))
        assert "http" not in text and "7842" not in text and "100." not in text
    assert get_profile("cockpit") is COCKPIT
    with pytest.raises(KeyError):
        get_profile("unbekannt")
