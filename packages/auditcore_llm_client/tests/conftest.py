"""Shared helpers: fixture loading, mock gateway and library call dispatch."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import sys
from collections.abc import Callable
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))

from wire_normalize import normalize_request, raise_for, response_for  # noqa: E402

from auditcore_llm_client import (  # noqa: E402
    AsyncLlmClient,
    ClientConfig,
    LlmClient,
    async_safe_call,
    safe_call,
)

KEY = "k3y-Geheim-4711"
FIXTURES = Path(__file__).parent / "fixtures"


def load_observed() -> dict[str, object]:
    """Legacy observations with the placeholder replaced by the test key."""
    text = (FIXTURES / "legacy_clients_observed.json").read_text(encoding="utf-8")
    loaded: dict[str, object] = json.loads(text.replace("<key>", KEY))
    return loaded


class Gateway:
    """Mock gateway answering with canned responses; records normalised requests."""

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, object]] = []
        self.raw: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.raw.append(request)
        self.requests.append(normalize_request(request, ()))
        spec = self.responses.pop(0)
        raise_for(spec, request)
        return response_for(spec)

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)


def decode(value: object) -> object:
    if isinstance(value, dict) and set(value) == {"$bytes"}:
        return str(value["$bytes"]).encode("latin-1")
    return value


def plain(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    return value


def _sync_call(client: LlmClient, fn: str, args: list[object],
               kwargs: dict[str, object]) -> object:
    if fn == "snapshot":
        return client.model_snapshot(refresh=True).to_dict()
    if fn == "stream":
        return [event.to_dict() for event in client.stream_chat(*args, **kwargs)]  # type: ignore[arg-type]
    if fn.startswith("safe:"):
        return list(safe_call(getattr(client, fn[5:]), *args, **kwargs))
    method: Callable[..., object] = getattr(client, fn)
    return method(*args, **kwargs)


async def _async_call(client: AsyncLlmClient, fn: str, args: list[object],
                      kwargs: dict[str, object]) -> object:
    if fn == "snapshot":
        return (await client.model_snapshot(refresh=True)).to_dict()
    if fn == "stream":
        return [e.to_dict() async for e in client.stream_chat(*args, **kwargs)]  # type: ignore[arg-type]
    if fn.startswith("safe:"):
        return list(await async_safe_call(getattr(client, fn[5:]), *args, **kwargs))
    method: Callable[..., object] = getattr(client, fn)
    return await method(*args, **kwargs)  # type: ignore[misc]


def call_library(config: ClientConfig, gateway: Gateway, spec: dict[str, object],
                 variant: str, **client_kwargs: object) -> object:
    """Execute the library twin of a case with the sync or async client."""
    fn = str(spec["fn"])
    args = [decode(a) for a in spec["args"]]  # type: ignore[attr-defined]
    kwargs = {k: decode(v) for k, v in spec["kwargs"].items()}  # type: ignore[attr-defined]
    if variant == "sync":
        with LlmClient(config, transport=gateway.transport(), **client_kwargs) as client:  # type: ignore[arg-type]
            return _sync_call(client, fn, args, kwargs)

    async def run() -> object:
        async with AsyncLlmClient(config, transport=gateway.transport(), **client_kwargs) as client:  # type: ignore[arg-type]
            return await _async_call(client, fn, args, kwargs)

    return asyncio.run(run())
