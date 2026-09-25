"""Asynchronous client (httpx ``AsyncClient``); transport injectable for tests.

httpx connections are bound to an event loop. As in flowinvoice, the client
keeps one ``AsyncClient`` per running loop so a shared instance can be used
from Celery threads that each run their own loop.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from typing import TypeVar

import httpx

from auditcore_llm_client import operations as ops
from auditcore_llm_client.catalog import ModelCatalog, ModelSnapshot
from auditcore_llm_client.config import ClientConfig
from auditcore_llm_client.engine import (
    NO_RESPONSE,
    Operation,
    Resilience,
    notify_usage,
    status_error,
)
from auditcore_llm_client.errors import LlmClientError
from auditcore_llm_client.health import RouterHealth
from auditcore_llm_client.jsontypes import JsonObject, JsonValue
from auditcore_llm_client.received import ReceivedResponse
from auditcore_llm_client.results import (
    EmbedResult,
    LlmResult,
    ModelInfo,
    OcrResult,
    RerankResult,
    StreamEvent,
)
from auditcore_llm_client.streaming import decoder_for
from auditcore_llm_client.transport import (
    POOL_LIMITS,
    build_request,
    received_from,
    transport_error,
)
from auditcore_llm_client.wire import Messages, PreparedRequest
from auditcore_llm_client.wire_llm import build_stream_chat

T = TypeVar("T")


class AsyncLlmClient:
    """ai-router/Flow-Agent client with async API."""

    def __init__(
        self,
        config: ClientConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        health: RouterHealth | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.config = config
        self._transport = transport
        self._clients: dict[int, tuple[asyncio.AbstractEventLoop, httpx.AsyncClient]] = {}
        self._resilience = Resilience(config, health)
        self._sleep = sleep
        self._catalog = ModelCatalog(config.base_url)
        self._catalog_locks: dict[int, asyncio.Lock] = {}

    def _http(self) -> httpx.AsyncClient:
        loop = asyncio.get_running_loop()
        entry = self._clients.get(id(loop))
        if entry is not None and entry[0] is loop and not entry[1].is_closed:
            return entry[1]
        client = httpx.AsyncClient(
            base_url=self.config.base_url, transport=self._transport, limits=POOL_LIMITS,
            timeout=self.config.timeouts.llm,
        )
        self._clients[id(loop)] = (loop, client)
        return client

    async def close(self) -> None:
        """Close the client of the current loop only (no cross-loop closing)."""
        loop = asyncio.get_running_loop()
        entry = self._clients.pop(id(loop), None)
        if entry is not None and entry[0] is loop and not entry[1].is_closed:
            await entry[1].aclose()

    async def __aenter__(self) -> AsyncLlmClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    # -- transport -------------------------------------------------------

    async def _exchange(self, request: PreparedRequest) -> ReceivedResponse:
        http = self._http()
        try:
            response = await http.send(build_request(http, self.config, request))
        except httpx.HTTPError as exc:
            raise transport_error(exc, request.path) from None
        received = received_from(response, request.path)
        if received.status == 404 and request.fallback_on_404 is not None:
            return await self._exchange(request.fallback_on_404)
        if received.status >= 400:
            raise status_error(self.config, received)
        return received

    async def _send(self, request: PreparedRequest) -> ReceivedResponse:
        attempt = 0
        while True:
            attempt += 1
            try:
                self._resilience.before(request)
                return await self._exchange(request)
            except LlmClientError as error:
                delay = self._resilience.retry_delay(error, attempt)
                if delay is None:
                    raise
                await self._sleep(delay)

    async def _run(self, operation: Operation[T]) -> T:
        if operation.request is None:
            return operation.parse(NO_RESPONSE)
        try:
            result = operation.parse(await self._send(operation.request))
        except LlmClientError as error:
            self._resilience.failed(error)
            raise
        self._resilience.succeeded()
        notify_usage(self.config, operation.request.operation, result)
        return result

    # -- public API ------------------------------------------------------

    async def generate(self, prompt: str, *, system: str | None = None,
                       model: str | None = None, temperature: float | None = None,
                       max_tokens: int | None = None, json_mode: bool = False,
                       seed: int | None = None, options: Mapping[str, JsonValue] | None = None,
                       reasoning_effort: str | None = None,
                       timeout: float | None = None) -> LlmResult:
        """Single prompt with optional system prompt."""
        params = ops.sampling(model=model, temperature=temperature, max_tokens=max_tokens,
                              json_mode=json_mode, seed=seed, options=options,
                              reasoning_effort=reasoning_effort)
        return await self._run(ops.generate_op(self.config, prompt, system, params, timeout))

    async def chat(self, messages: Messages, *, model: str | None = None,
                   temperature: float | None = None, max_tokens: int | None = None,
                   json_mode: bool = False, seed: int | None = None,
                   reasoning_effort: str | None = None, timeout: float | None = None) -> LlmResult:
        """OpenAI-compatible chat completion."""
        params = ops.sampling(model=model, temperature=temperature, max_tokens=max_tokens,
                              json_mode=json_mode, seed=seed,
                              reasoning_effort=reasoning_effort)
        return await self._run(ops.chat_op(self.config, messages, params, timeout))

    async def embed(self, texts: Sequence[str], *, model: str | None = None,
                    timeout: float | None = None) -> EmbedResult:
        """Embedding vectors in input order."""
        return await self._run(ops.embed_op(self.config, texts, model, timeout))

    async def rerank(self, query: str, documents: Sequence[str], *, top_k: int | None = None,
                     model: str | None = None, timeout: float | None = None) -> RerankResult:
        """Scores in document order."""
        return await self._run(
            ops.rerank_op(self.config, query, documents, top_k, model, timeout)
        )

    async def ocr(self, content: bytes, *, filename: str = "upload.bin",
                  content_type: str = "application/octet-stream", model: str = "auto",
                  language: str = "auto", timeout: float | None = None) -> OcrResult:
        """OCR of a PDF or image."""
        return await self._run(ops.ocr_op(self.config, content, filename, content_type, model,
                                          language, timeout))

    async def health(self, *, capability: str = "chat") -> JsonObject:
        """ai-router ``/health`` or Flow-Agent readiness of ``capability``."""
        return await self._run(ops.health_op(self.config, capability))

    async def list_models(self) -> list[ModelInfo]:
        """Models known to the ai-router."""
        return await self._run(ops.models_op(self.config))

    async def model_snapshot(self, *, refresh: bool = False) -> ModelSnapshot:
        """Cached model list with fetch state (cockpit semantics)."""
        lock = self._catalog_locks.setdefault(id(asyncio.get_running_loop()), asyncio.Lock())
        async with lock:
            cached = None if refresh else self._catalog.cached()
            if cached is not None:
                return cached
            try:
                return self._catalog.succeeded(await self.list_models())
            except LlmClientError as error:
                return self._catalog.failed(error)

    async def stream_chat(self, messages: Messages, *, model: str | None = None,
                          options: Mapping[str, JsonValue] | None = None,
                          think: bool | None = None, temperature: float | None = None,
                          max_tokens: int | None = None,
                          reasoning_effort: str | None = None) -> AsyncIterator[StreamEvent]:
        """Streamed chat; HTTP and transport errors raise, in-stream errors are events."""
        params = ops.sampling(model=model, temperature=temperature, max_tokens=max_tokens,
                              options=options, reasoning_effort=reasoning_effort)
        request = build_stream_chat(self.config, messages, params, think)
        try:
            async for event in self._stream(request):
                yield event
        except LlmClientError as error:
            self._resilience.failed(error)
            raise
        self._resilience.succeeded()

    async def _stream(self, request: PreparedRequest) -> AsyncIterator[StreamEvent]:
        self._resilience.before(request)
        http = self._http()
        try:
            response = await http.send(build_request(http, self.config, request), stream=True)
        except httpx.HTTPError as exc:
            raise transport_error(exc, request.path) from None
        try:
            async for event in self._events(response, request.path):
                yield event
        finally:
            await response.aclose()

    async def _events(self, response: httpx.Response, path: str) -> AsyncIterator[StreamEvent]:
        if response.status_code >= 400:
            await response.aread()
            raise status_error(self.config, received_from(response, path))
        decoder = decoder_for(path)
        try:
            async for line in response.aiter_lines():
                for event in decoder.feed(line):
                    yield event
                if decoder.finished:
                    return
        except httpx.HTTPError as exc:
            raise transport_error(exc, path) from None
