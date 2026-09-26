"""Flow-Agent sensitivity/egress rejections, reasoning_effort, secret references, deprecation.

Contract: flow-agent main 1d49ec3c (``ai_gateway.parse_sensitivity``,
``EgressDeniedError``) and the ai-router think default for ``qwen3.5*``.
"""

from __future__ import annotations

import dataclasses

import pytest
from conftest import KEY, Gateway

from auditcore_llm_client import (
    AUDIT_DESIGNER,
    COCKPIT,
    FLOWINVOICE,
    PROFILES,
    BreakerPolicy,
    ClientConfig,
    ConfigurationError,
    EgressDeniedError,
    ErrorKind,
    LlmClient,
    LlmClientError,
    Mode,
    RetryPolicy,
    RouterHealth,
    RouterHttpError,
    SecretValue,
    Sensitivity,
    SensitivityRejectedError,
    config_from_env,
    is_secret_reference,
    resolve_secret,
)

FLOW = ClientConfig(base_url="https://agent.test", app_id="app", mode=Mode.FLOW_AGENT,
                    api_key=SecretValue(KEY), sensitivity=Sensitivity.RESTRICTED,
                    retry=RetryPolicy(max_attempts=3), breaker=BreakerPolicy(failure_threshold=1))
EGRESS = {"status": 403, "json": {"detail": "Egress: Sensitivität restricted erlaubt nur lokale "
                                            "Modelle; 1 nicht lokale(s) Modell(e) verworfen."}}
INVALID = {"status": 400, "json": {"detail": "Ungültige Sensitivität. Erlaubt: public, internal, "
                                             "confidential, restricted."}}
OK = {"json": {"choices": [{"message": {"content": "ok"}}]}}


@pytest.mark.parametrize(("response", "error_type", "kind"), [
    (EGRESS, EgressDeniedError, ErrorKind.EGRESS_DENIED),
    (INVALID, SensitivityRejectedError, ErrorKind.SENSITIVITY_REJECTED),
])
def test_policy_rejections_are_own_kinds_and_not_retried(
    response: dict[str, object], error_type: type, kind: ErrorKind
) -> None:
    gateway = Gateway([response, OK])
    health = RouterHealth()
    sleeps: list[float] = []
    with LlmClient(FLOW, transport=gateway.transport(), health=health,
                   sleep=sleeps.append) as client:
        with pytest.raises(error_type) as info:
            client.chat([{"role": "user", "content": "x"}])
        assert info.value.kind is kind and info.value.status_code == response["status"]
        assert len(gateway.requests) == 1 and sleeps == []
        assert gateway.requests[0]["headers"]["x-flow-sensitivity"] == "restricted"  # type: ignore[index]
        # Breaker (threshold 1) stayed closed and health counted nothing.
        assert client.chat([]).content == "ok"
    assert health.to_dict()["consecutive_failures"] == 0


def test_other_403_and_router_mode_stay_http_errors() -> None:
    denied = {"status": 403, "json": {"detail": "Capability chat ist nicht freigegeben."}}
    gateway = Gateway([denied, EGRESS])
    with LlmClient(FLOW, transport=gateway.transport()) as client, \
            pytest.raises(RouterHttpError):
        client.chat([])
    router = ClientConfig(base_url="http://r.test", app_id="a")
    with LlmClient(router, transport=gateway.transport()) as client, \
            pytest.raises(RouterHttpError):
        client.chat([])


def test_without_sensitivity_no_header_is_sent() -> None:
    gateway = Gateway([OK])
    config = dataclasses.replace(FLOW, sensitivity=None)
    with LlmClient(config, transport=gateway.transport()) as client:
        client.chat([])
    assert "x-flow-sensitivity" not in gateway.requests[0]["headers"]  # type: ignore[operator]


def test_reasoning_effort_is_passed_through() -> None:
    gateway = Gateway([OK, OK, {"json": {"response": "x"}}, {"json": {"message": {}}}])
    router = ClientConfig(base_url="http://r.test", app_id="a")
    audit = ClientConfig(base_url="http://r.test", app_id="a", profile=AUDIT_DESIGNER)
    with LlmClient(router, transport=gateway.transport()) as client:
        client.chat([], model="qwen3.5:35b", reasoning_effort="low")
        client.chat([], model="qwen3.5:35b")
        client.generate("p", reasoning_effort="none")
    with LlmClient(audit, transport=gateway.transport()) as client:
        client.generate("p", reasoning_effort="high")
    bodies = [r["body"] for r in gateway.requests]
    assert bodies[0]["reasoning_effort"] == "low"  # type: ignore[index]
    assert "reasoning_effort" not in bodies[1]  # type: ignore[operator]
    assert bodies[2]["think"] is False and bodies[3]["think"] is True  # type: ignore[index]


def test_reasoning_effort_in_streams_and_flow_generate() -> None:
    gateway = Gateway([{"lines": ["data: [DONE]"]}, {"lines": ['{"done": true}']},
                       {"json": {"content": "x"}}])
    router = ClientConfig(base_url="http://r.test", app_id="a")
    with LlmClient(FLOW, transport=gateway.transport()) as client:
        list(client.stream_chat([], reasoning_effort="none"))
    with LlmClient(router, transport=gateway.transport()) as client:
        list(client.stream_chat([], reasoning_effort="medium"))
    with LlmClient(FLOW, transport=gateway.transport()) as client:
        client.generate("p", reasoning_effort="none")
    bodies = [r["body"] for r in gateway.requests]
    assert bodies[0]["reasoning_effort"] == "none"  # type: ignore[index]
    assert bodies[1]["think"] is True  # type: ignore[index]
    assert "reasoning_effort" not in bodies[2] and "think" not in bodies[2]  # type: ignore[operator]


def test_secret_references_need_a_resolver() -> None:
    reference = "secret://ai-router/flowinvoice-key"
    env = {"LLM_ROUTER_URL": "http://r.test", "LLM_ROUTER_API_KEY": reference}
    assert is_secret_reference(reference) and not is_secret_reference(KEY)
    with pytest.raises(ConfigurationError) as info:
        config_from_env(FLOWINVOICE, env)
    assert reference in str(info.value)
    seen: list[str] = []

    def resolver(ref: str) -> str:
        seen.append(ref)
        return KEY

    config = config_from_env(FLOWINVOICE, env, secret_resolver=resolver)
    assert config.api_key == SecretValue(KEY) and seen == [reference]
    flow = {"FLOW_AGENT_URL": "https://agent.test", "FLOW_AGENT_APP_KEY": reference}
    assert config_from_env(FLOWINVOICE, flow, secret_resolver=resolver).api_key is not None


def test_resolver_failures_do_not_leak() -> None:
    def broken(ref: str) -> str:
        raise RuntimeError(f"denied {KEY}")

    for resolver in (broken, lambda ref: ""):
        with pytest.raises(ConfigurationError) as info:
            resolve_secret("secret://x/y", resolver)
        assert KEY not in str(info.value) and info.value.__cause__ is None
    assert resolve_secret("", None) is None
    assert resolve_secret(KEY, None) == SecretValue(KEY)


def test_cockpit_profile_is_deprecated_but_kept() -> None:
    assert COCKPIT.deprecated and "flow-agent #50" in COCKPIT.deprecated
    assert [p.name for p in PROFILES.values() if p.deprecated] == ["cockpit"]


HEADER_CASES = [
    # (status, header, detail, expected type)
    (403, "egress-denied", "irgendein Text", EgressDeniedError),
    (400, "invalid-sensitivity", "irgendein Text", SensitivityRejectedError),
    (403, "EGRESS-DENIED ", "x", EgressDeniedError),
    (400, "egress-denied", "Ungültige Sensitivität", RouterHttpError),
    (403, "invalid-sensitivity", "Egress: kein Modell", RouterHttpError),
    (500, "egress-denied", "Egress", RouterHttpError),
    (403, "unbekannt", "Egress: kein Modell", RouterHttpError),
    (403, None, "Egress: Sensitivität restricted", EgressDeniedError),
    (400, None, "Ungültige Sensitivität.", SensitivityRejectedError),
    (403, None, "Capability chat ist nicht freigegeben.", RouterHttpError),
]


@pytest.mark.parametrize(("status", "header", "detail", "expected"), HEADER_CASES)
def test_error_header_is_primary_and_text_is_fallback(
    status: int, header: str | None, detail: str, expected: type
) -> None:
    headers = {"X-Flow-Agent-Error": header} if header is not None else {}
    gateway = Gateway([{"status": status, "json": {"detail": detail}, "headers": headers}])
    with LlmClient(FLOW, transport=gateway.transport(), sleep=lambda _: None) as client, \
            pytest.raises(LlmClientError) as info:
        client.chat([])
    assert type(info.value) is expected


def test_error_header_is_ignored_in_router_mode() -> None:
    gateway = Gateway([{"status": 403, "json": {"detail": "x"},
                        "headers": {"X-Flow-Agent-Error": "egress-denied"}}])
    router = ClientConfig(base_url="http://r.test", app_id="a")
    with LlmClient(router, transport=gateway.transport()) as client, \
            pytest.raises(RouterHttpError):
        client.chat([])
