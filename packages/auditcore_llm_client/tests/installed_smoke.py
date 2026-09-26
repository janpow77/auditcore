"""Run with python -I against an installed wheel or Debian package; no pytest needed.

Without the extra ``http`` only the stdlib core is available; the smoke test
then checks that the HTTP clients fail with a clear import error. With httpx
installed it additionally runs one call through ``httpx.MockTransport``.
"""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_llm_client import (
    AUDIT_DESIGNER,
    FLOWINVOICE,
    BreakerPolicy,
    CircuitBreaker,
    ConfigurationError,
    Mode,
    RouterHttpError,
    config_from_env,
    redact,
)
from auditcore_llm_client.received import ReceivedResponse
from auditcore_llm_client.wire import request_headers
from auditcore_llm_client.wire_llm import Sampling, build_generate

KEY = "k3y-Geheim-4711"


def _core() -> None:
    config = config_from_env(AUDIT_DESIGNER, {"LLM_ROUTER_URL": "http://router.test:7842",
                                              "LLM_ROUTER_API_KEY": KEY})
    request = build_generate(config, "Frage", "System", Sampling())
    assert request.path == "/api/chat" and request.fallback_on_404 is not None
    assert request.json_body is not None and request.json_body["think"] is False
    assert request_headers(config, request.headers)["X-Api-Key"] == KEY
    assert KEY not in repr(config)
    flow = config_from_env(FLOWINVOICE, {"FLOW_AGENT_URL": "https://agent.test",
                                         "FLOW_AGENT_APP_KEY": KEY})
    assert flow.mode is Mode.FLOW_AGENT and flow.app_prefix == "/api/v1/ai/apps/flowinvoice"
    try:
        config_from_env(AUDIT_DESIGNER, {"LLM_ROUTER_URL": "http://gpu.test:11434"})
    except ConfigurationError:
        pass
    else:
        raise AssertionError("direct Ollama host accepted")
    assert redact(f"Bearer {KEY} http://x.test", secrets=[KEY]) == "Bearer <redacted> <url>"
    received = ReceivedResponse(403, f"echo {KEY}".encode(), "/api/chat")
    from auditcore_llm_client.received import error_for_status

    error = error_for_status(received, config.secrets)
    assert isinstance(error, RouterHttpError) and KEY not in str(error)
    breaker = CircuitBreaker(BreakerPolicy(failure_threshold=1))
    breaker.record_failure(error)
    assert breaker.snapshot()["state"] == "closed"


def _http() -> None:
    import httpx

    from auditcore_llm_client import LlmClient

    def answer(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-app-id"] == "audit_designer"
        return httpx.Response(200, json={"message": {"content": "<think>x</think>Antwort"}})

    config = config_from_env(AUDIT_DESIGNER, {"LLM_ROUTER_URL": "http://router.test:7842"})
    with LlmClient(config, transport=httpx.MockTransport(answer)) as client:
        assert client.generate("Frage", system="System").content == "Antwort"


def main() -> None:
    package = distribution("auditcore_llm_client")
    assert package.version == "0.1.1"
    assert [r for r in package.requires or [] if "extra ==" not in r] == []
    assert find_spec("auditcore") is None
    _core()
    if find_spec("httpx") is None:
        try:
            from auditcore_llm_client import LlmClient  # noqa: F401
        except ModuleNotFoundError as exc:
            assert exc.name == "httpx"
        else:
            raise AssertionError("LlmClient importable without httpx")
    else:
        _http()
    print("auditcore_llm_client smoke OK")


if __name__ == "__main__":
    main()
