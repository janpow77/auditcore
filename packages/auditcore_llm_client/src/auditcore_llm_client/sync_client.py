"""Synchronous client (httpx ``Client``); transport injectable for tests."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
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


class LlmClient:
    """ai-router/Flow-Agent client with sync API."""

    def __init__(
        self,
        config: ClientConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        health: RouterHealth | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self._http = httpx.Client(
            base_url=config.base_url, transport=transport, limits=POOL_LIMITS,
            timeout=config.timeouts.llm,
        )
        self._resilience = Resilience(config, health)
        self._sleep = sleep
        self._catalog = ModelCatalog(config.base_url)
        self._catalog_lock = threading.Lock()

    def close(self) -> None:
        """Close the connection pool."""
        self._http.close()

    def __enter__(self) -> LlmClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # -- transport -------------------------------------------------------

    def _exchange(self, request: PreparedRequest) -> ReceivedResponse:
        try:
            response = self._http.send(build_request(self._http, self.config, request))
        except httpx.HTTPError as exc:
            raise transport_error(exc, request.path) from None
        received = received_from(response, request.path)
        if received.status == 404 and request.fallback_on_404 is not None:
            return self._exchange(request.fallback_on_404)
        if received.status >= 400:
            raise status_error(self.config, received)
        return received

    def _send(self, request: PreparedRequest) -> ReceivedResponse:
        attempt = 0
        while True:
            attempt += 1
            try:
                self._resilience.before(request)
                return self._exchange(request)
            except LlmClientError as error:
                delay = self._resilience.retry_delay(error, attempt)
                if delay is None:
                    raise
                self._sleep(delay)

    def _run(self, operation: Operation[T]) -> T:
        if operation.request is None:
            return operation.parse(NO_RESPONSE)
        try:
            result = operation.parse(self._send(operation.request))
        except LlmClientError as error:
            self._resilience.failed(error)
            raise
        self._resilience.succeeded()
        notify_usage(self.config, operation.request.operation, result)
        return result

    # -- public API ------------------------------------------------------

    def generate(self, prompt: str, *, system: str | None = None, model: str | None = None,
                 temperature: float | None = None, max_tokens: int | None = None,
                 json_mode: bool = False, seed: int | None = None,
                 options: Mapping[str, JsonValue] | None = None,
                 reasoning_effort: str | None = None,
                 timeout: float | None = None) -> LlmResult:
        """Single prompt with optional system prompt."""
        params = ops.sampling(model=model, temperature=temperature, max_tokens=max_tokens,
                              json_mode=json_mode, seed=seed, options=options,
                              reasoning_effort=reasoning_effort)
        return self._run(ops.generate_op(self.config, prompt, system, params, timeout))

    def chat(self, messages: Messages, *, model: str | None = None,
             temperature: float | None = None, max_tokens: int | None = None,
             json_mode: bool = False, seed: int | None = None,
             reasoning_effort: str | None = None, timeout: float | None = None) -> LlmResult:
        """OpenAI-compatible chat completion."""
        params = ops.sampling(model=model, temperature=temperature, max_tokens=max_tokens,
                              json_mode=json_mode, seed=seed,
                              reasoning_effort=reasoning_effort)
        return self._run(ops.chat_op(self.config, messages, params, timeout))

    def embed(self, texts: Sequence[str], *, model: str | None = None,
              timeout: float | None = None) -> EmbedResult:
        """Embedding vectors in input order."""
        return self._run(ops.embed_op(self.config, texts, model, timeout))

    def rerank(self, query: str, documents: Sequence[str], *, top_k: int | None = None,
               model: str | None = None, timeout: float | None = None) -> RerankResult:
        """Scores in document order."""
        return self._run(ops.rerank_op(self.config, query, documents, top_k, model, timeout))

    def ocr(self, content: bytes, *, filename: str = "upload.bin",
            content_type: str = "application/octet-stream", model: str = "auto",
            language: str = "auto", timeout: float | None = None) -> OcrResult:
        """OCR of a PDF or image."""
        return self._run(ops.ocr_op(self.config, content, filename, content_type, model,
                                    language, timeout))

    def health(self, *, capability: str = "chat") -> JsonObject:
        """ai-router ``/health`` or Flow-Agent readiness of ``capability``."""
        return self._run(ops.health_op(self.config, capability))

    def list_models(self) -> list[ModelInfo]:
        """Models known to the ai-router."""
        return self._run(ops.models_op(self.config))

    def model_snapshot(self, *, refresh: bool = False) -> ModelSnapshot:
        """Cached model list with fetch state (cockpit semantics)."""
        with self._catalog_lock:
            cached = None if refresh else self._catalog.cached()
            if cached is not None:
                return cached
            try:
                return self._catalog.succeeded(self.list_models())
            except LlmClientError as error:
                return self._catalog.failed(error)

    def stream_chat(self, messages: Messages, *, model: str | None = None,
                    options: Mapping[str, JsonValue] | None = None, think: bool | None = None,
                    temperature: float | None = None,
                    max_tokens: int | None = None,
                    reasoning_effort: str | None = None) -> Iterator[StreamEvent]:
        """Streamed chat; HTTP and transport errors raise, in-stream errors are events."""
        params = ops.sampling(model=model, temperature=temperature, max_tokens=max_tokens,
                              options=options, reasoning_effort=reasoning_effort)
        request = build_stream_chat(self.config, messages, params, think)
        try:
            yield from self._stream(request)
        except LlmClientError as error:
            self._resilience.failed(error)
            raise
        self._resilience.succeeded()

    def _stream(self, request: PreparedRequest) -> Iterator[StreamEvent]:
        self._resilience.before(request)
        try:
            response = self._http.send(build_request(self._http, self.config, request),
                                       stream=True)
        except httpx.HTTPError as exc:
            raise transport_error(exc, request.path) from None
        try:
            yield from self._events(response, request.path)
        finally:
            response.close()

    def _events(self, response: httpx.Response, path: str) -> Iterator[StreamEvent]:
        if response.status_code >= 400:
            response.read()
            raise status_error(self.config, received_from(response, path))
        decoder = decoder_for(path)
        try:
            for line in response.iter_lines():
                yield from decoder.feed(line)
                if decoder.finished:
                    return
        except httpx.HTTPError as exc:
            raise transport_error(exc, path) from None
