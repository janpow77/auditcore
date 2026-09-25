"""Execute the four legacy ai-router clients and record their traffic.

The client modules are taken from the pinned commits (``git show``), loaded
with small stubs for the app settings, and run against an ``httpx.MockTransport``
that answers with the canned responses of ``legacy_cases.py``. Recorded per
case: every request (method, URL, relevant headers, parsed body), the result or
the raised error, the legacy health record, the usage hook calls (audit-portal)
and whether the configured key showed up in errors, return values, health or
logs.

Usage (from the package directory)::

    python tools/capture_legacy_clients.py --projects ~/Projekte

Writes ``tests/fixtures/legacy_clients_observed.json``. Needs httpx; runs no
network access.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import functools
import hashlib
import importlib.util
import io
import json
import logging
import subprocess
import sys
import tempfile
import types
from collections.abc import Callable
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "tests")]

import legacy_cases as cases  # noqa: E402
from wire_normalize import normalize_request, raise_for, response_for  # noqa: E402

SOURCES = {
    "audit_designer": ("janpow77/audit_designer", "audit_designer",
                       "ccd65245182982af3ef885a7a6d43583f4f72cbb",
                       "backend/app/utils/ai_router_client.py"),
    "flowinvoice": ("janpow77/flowinvoice", "flowinvoice",
                    "fb2d18568d2eaf64574d131ceae51a936b9aac02",
                    "backend/app/clients/ai_router_client.py"),
    "audit_portal": ("janpow77/audit-portal", "audit-portal",
                     "d8eefa426826bdecb67036774f3128ae05e7d0d0",
                     "backend/app/clients/ai_router_client.py"),
    "cockpit": ("janpow77/cockpit", "cockpit", "df203d4c33e786eb8a8ad3fe53b3b7eb9241d406",
                "src/cockpit/services/ai_router_client.py"),
}
SECRETS = (cases.KEY,)
ENV_NAMES = ("LLM_ROUTER_URL", "LLM_ROUTER_APP_ID", "LLM_ROUTER_API_KEY", "FLOW_AGENT_URL",
             "FLOW_AGENT_APP_ID", "FLOW_AGENT_APP_KEY", "FLOW_AGENT_QUALITY", "RERANKER_MODEL",
             "EMBEDDING_MODEL", "AI_ROUTER_URL", "AI_ROUTER_APP_ID", "AI_ROUTER_API_KEY")


class Secret:
    """Minimal pydantic ``SecretStr`` stand-in."""

    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value


def _source(projects: Path, app: str) -> tuple[str, dict[str, str]]:
    repository, folder, commit, path = SOURCES[app]
    repo = projects / folder
    text = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], check=True,
                          capture_output=True, text=True).stdout
    blob = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{commit}:{path}"], check=True,
                          capture_output=True, text=True).stdout.strip()
    return text, {"repository": repository, "commit": commit, "path": path, "git_blob": blob,
                  "sha256": hashlib.sha256(text.encode()).hexdigest()}


def _stub_modules(settings: object, usage: list[dict[str, object]]) -> None:
    for name in ("app", "app.core"):
        sys.modules[name] = types.ModuleType(name)
    config = types.ModuleType("app.config")
    config.get_settings = lambda: settings  # type: ignore[attr-defined]
    core_config = types.ModuleType("app.core.config")
    core_config.settings = settings  # type: ignore[attr-defined]
    metrics = types.ModuleType("app.core.request_metrics")
    metrics.record_llm_usage = lambda **kw: usage.append(kw)  # type: ignore[attr-defined]
    sys.modules.update({"app.config": config, "app.core.config": core_config,
                        "app.core.request_metrics": metrics})


def _load(text: str, name: str) -> types.ModuleType:
    folder = Path(tempfile.mkdtemp(prefix="legacy-client-"))
    path = folder / f"{name}.py"
    path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _mock_httpx(module: types.ModuleType, transport: httpx.MockTransport) -> None:
    fake = types.SimpleNamespace(**{k: getattr(httpx, k) for k in dir(httpx)
                                    if not k.startswith("_")})
    sync = httpx.Client(transport=transport)
    fake.post = sync.post
    fake.get = sync.get
    fake.Client = functools.partial(httpx.Client, transport=transport)
    fake.AsyncClient = functools.partial(httpx.AsyncClient, transport=transport)
    module.httpx = fake  # type: ignore[attr-defined]


def _decode(value: object) -> object:
    if isinstance(value, dict) and set(value) == {"$bytes"}:
        return str(value["$bytes"]).encode("latin-1")
    return value


def _plain(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, tuple):
        return [_plain(v) for v in value]
    return value


class Recorder:
    """Mock gateway: answers from the case, records normalised requests."""

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, object]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(normalize_request(request, SECRETS))
        spec = self.responses.pop(0)
        raise_for(spec, request)
        return response_for(spec)


def _leaks(text: str) -> bool:
    return any(secret in text for secret in SECRETS)


def _error(exc: BaseException) -> dict[str, object]:
    message = str(exc)
    return {"type": type(exc).__name__, "status_code": getattr(exc, "status_code", None),
            "message": message.replace(cases.KEY, "<key>"), "key_in_message": _leaks(message)}


async def _invoke(target: Callable[..., object], legacy: dict[str, object]) -> object:
    args = [_decode(a) for a in legacy["args"]]  # type: ignore[attr-defined]
    kwargs = {k: _decode(v) for k, v in legacy["kwargs"].items()}  # type: ignore[attr-defined]
    result = target(*args, **kwargs)
    if asyncio.iscoroutine(result):
        return await result
    if hasattr(result, "__aiter__"):
        return [event async for event in result]  # type: ignore[attr-defined]
    return result


def _health_record(module: types.ModuleType) -> dict[str, object] | None:
    health = getattr(module, "router_health", None)
    if health is None:
        return None
    record = health().to_dict()
    message = str(record.get("last_error_message") or "")
    return {"consecutive_failures": record["consecutive_failures"],
            "last_error_message": message.replace(cases.KEY, "<key>") or None,
            "key_in_health": _leaks(message)}


def _resolve(module: types.ModuleType, fn: str, client_class: bool) -> Callable[..., object]:
    if client_class and not fn.startswith("safe_") and fn != "_fetch_models":
        return getattr(module.AiRouterClient(), fn)  # type: ignore[no-any-return]
    return getattr(module, fn)  # type: ignore[no-any-return]


def run_case(module: types.ModuleType, case: dict[str, object], client_class: bool,
             usage: list[dict[str, object]]) -> dict[str, object]:
    recorder = Recorder(case["responses"])  # type: ignore[arg-type]
    _mock_httpx(module, httpx.MockTransport(recorder))
    _reset(module)
    usage.clear()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    legacy = case["legacy"]
    outcome: dict[str, object] = {}
    try:
        target = _resolve(module, str(legacy["fn"]), client_class)  # type: ignore[index]
        result = asyncio.run(_invoke(target, legacy))  # type: ignore[arg-type]
        outcome["result"] = _plain(result)
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], str):
            outcome["key_in_result"] = _leaks(result[1])
            outcome["result"] = [_plain(result[0]), result[1].replace(cases.KEY, "<key>")]
        if isinstance(result, list):
            outcome["key_in_result"] = _leaks(json.dumps(result))
            outcome["result"] = json.loads(json.dumps(result).replace(cases.KEY, "<key>"))
    except Exception as exc:  # noqa: BLE001 - legacy errors are the observation
        outcome["error"] = _error(exc)
    finally:
        logging.getLogger().removeHandler(handler)
    logs = stream.getvalue()
    return {**case, "requests": recorder.requests, **outcome, "health": _health_record(module),
            "usage": list(usage), "key_in_logs": _leaks(logs),
            "unused_responses": len(recorder.responses)}


def _reset(module: types.ModuleType) -> None:
    health_class = getattr(module, "RouterHealth", None)
    if health_class is not None:
        health_class._instance = None
    if hasattr(module, "_singleton"):
        module._singleton = None
    for name in ("_cache", "_resolved"):
        if hasattr(module, name):
            getattr(module, name).clear()


def _settings_audit_designer() -> object:
    return types.SimpleNamespace(LLM_ROUTER_URL=cases.ROUTER, LLM_ROUTER_APP_ID="audit_designer",
                                 LLM_ROUTER_API_KEY=cases.KEY, VP_AI_EGPU_MODEL="qwen3.5:35b",
                                 OLLAMA_MODEL="qwen3:14b", VP_AI_LLM_KEEP_ALIVE="10m")


def _settings_flowinvoice(app_id: str, flow_agent: bool) -> object:
    return types.SimpleNamespace(
        llm_router_url=cases.ROUTER, llm_router_app_id=app_id, llm_router_api_key=Secret(cases.KEY),
        flow_agent_url=cases.AGENT if flow_agent else "", flow_agent_app_id=app_id,
        flow_agent_app_key=Secret(cases.KEY), flow_agent_quality="balanced",
        ollama_default_model="qwen3:14b",
    )


GROUPS: list[dict[str, object]] = [
    {"group": "audit_designer", "app": "audit_designer", "profile": "audit_designer",
     "settings": _settings_audit_designer, "cases": cases.AUDIT_DESIGNER_CASES,
     "client_class": False,
     "env": {"LLM_ROUTER_URL": cases.ROUTER, "LLM_ROUTER_APP_ID": "audit_designer",
             "LLM_ROUTER_API_KEY": cases.KEY, "VP_AI_EGPU_MODEL": "qwen3.5:35b",
             "OLLAMA_MODEL": "qwen3:14b", "VP_AI_LLM_KEEP_ALIVE": "10m"}},
    {"group": "flowinvoice_router", "app": "flowinvoice", "profile": "flowinvoice",
     "settings": lambda: _settings_flowinvoice("flowinvoice", False),
     "cases": cases.FLOWINVOICE_CASES, "client_class": True,
     "env": {"LLM_ROUTER_URL": cases.ROUTER, "LLM_ROUTER_APP_ID": "flowinvoice",
             "LLM_ROUTER_API_KEY": cases.KEY, "OLLAMA_DEFAULT_MODEL": "qwen3:14b"}},
    {"group": "flowinvoice_flow_agent", "app": "flowinvoice", "profile": "flowinvoice",
     "settings": lambda: _settings_flowinvoice("flowinvoice", True),
     "cases": cases.FLOW_AGENT_CASES, "client_class": True,
     "env": {"FLOW_AGENT_URL": cases.AGENT, "FLOW_AGENT_APP_ID": "flowinvoice",
             "FLOW_AGENT_APP_KEY": cases.KEY, "FLOW_AGENT_QUALITY": "balanced",
             "OLLAMA_DEFAULT_MODEL": "qwen3:14b"}},
    {"group": "audit_portal", "app": "audit_portal", "profile": "audit_portal",
     "settings": lambda: _settings_flowinvoice("audit-portal", False),
     "cases": cases.AUDIT_PORTAL_CASES, "client_class": True,
     "env": {"LLM_ROUTER_URL": cases.ROUTER, "LLM_ROUTER_APP_ID": "audit-portal",
             "LLM_ROUTER_API_KEY": cases.KEY, "OLLAMA_DEFAULT_MODEL": "qwen3:14b"}},
    {"group": "cockpit", "app": "cockpit", "profile": "cockpit", "settings": lambda: None,
     "cases": cases.COCKPIT_CASES, "client_class": False,
     "env": {"AI_ROUTER_URL": cases.ROUTER, "AI_ROUTER_API_KEY": cases.KEY}},
]


def capture_group(projects: Path, group: dict[str, object]) -> dict[str, object]:
    import os

    for name in ENV_NAMES:
        os.environ.pop(name, None)
    if group["app"] == "cockpit":
        os.environ.update(group["env"])  # type: ignore[arg-type]
    usage: list[dict[str, object]] = []
    _stub_modules(group["settings"](), usage)  # type: ignore[operator]
    text, source = _source(projects, str(group["app"]))
    module = _load(text, f"legacy_{group['group']}")
    observed = [run_case(module, case, bool(group["client_class"]), usage)
                for case in group["cases"]]  # type: ignore[attr-defined]
    for name in ENV_NAMES:
        os.environ.pop(name, None)
    return {"group": group["group"], "profile": group["profile"], "source": source,
            "env": group["env"], "cases": observed}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projects", type=Path, default=Path.home() / "Projekte")
    parser.add_argument("--output", type=Path,
                        default=HERE.parent / "tests/fixtures/legacy_clients_observed.json")
    args = parser.parse_args()
    groups = [capture_group(args.projects, group) for group in GROUPS]
    document = {"schema": "auditcore_llm_client.legacy_observed/1", "key_placeholder": "<key>",
                "tool": "tools/capture_legacy_clients.py", "httpx": httpx.__version__,
                "python": sys.version.split()[0], "groups": groups}
    text = json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True)
    args.output.write_text(text.replace(cases.KEY, "<key>") + "\n", encoding="utf-8")
    total = sum(len(g["cases"]) for g in groups)  # type: ignore[arg-type]
    print(f"{total} Fälle in {len(groups)} Gruppen -> {args.output}")


if __name__ == "__main__":
    main()
