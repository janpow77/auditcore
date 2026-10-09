"""Client caches per gateway URL for apps that change the gateway address at runtime.

A client stays bound to exactly one URL (behaviour change B3). The pools build
one client per normalised URL from a template configuration and reuse it, so
every URL keeps its own connection pool, circuit breaker and model cache: an
outage of one gateway never opens the breaker of another. A passed
:class:`RouterHealth` is shared by all clients (one health status per app).
"""

from __future__ import annotations

import dataclasses
import threading
from collections import OrderedDict
from collections.abc import Callable
from typing import Generic, TypeVar

import httpx

from auditcore_llm_client.async_client import AsyncLlmClient
from auditcore_llm_client.config import ClientConfig, validate_base_url
from auditcore_llm_client.errors import ConfigurationError
from auditcore_llm_client.health import RouterHealth
from auditcore_llm_client.sync_client import LlmClient

C = TypeVar("C")

#: Default number of cached clients; the least recently used one is closed beyond it.
DEFAULT_MAX_CLIENTS = 8


class _ClientCache(Generic[C]):
    """Thread-safe LRU map ``normalised URL → client``."""

    def __init__(
        self, config: ClientConfig, factory: Callable[[ClientConfig], C], max_clients: int
    ) -> None:
        if max_clients < 1:
            raise ConfigurationError("max_clients muss mindestens 1 sein.")
        self.config = config
        self._factory = factory
        self._max = max_clients
        self._clients: OrderedDict[str, C] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, base_url: str | None) -> tuple[C, list[C]]:
        """Client for ``base_url`` (``None`` = template URL) and the evicted clients."""
        url = self.config.base_url if base_url is None else validate_base_url(base_url)
        with self._lock:
            client = self._clients.get(url)
            if client is not None:
                self._clients.move_to_end(url)
                return client, []
            client = self._factory(dataclasses.replace(self.config, base_url=url))
            self._clients[url] = client
            evicted: list[C] = []
            while len(self._clients) > self._max:
                evicted.append(self._clients.popitem(last=False)[1])
            return client, evicted

    def urls(self) -> list[str]:
        """Cached URLs, least recently used first."""
        with self._lock:
            return list(self._clients)

    def drain(self) -> list[C]:
        """Remove and return all clients."""
        with self._lock:
            clients = list(self._clients.values())
            self._clients.clear()
            return clients


class _PoolBase(Generic[C]):
    """Shared read access of the sync and async pools."""

    _cache: _ClientCache[C]

    @property
    def config(self) -> ClientConfig:
        """Template configuration (its URL is the default)."""
        return self._cache.config

    @property
    def urls(self) -> list[str]:
        """Normalised URLs with a cached client, least recently used first."""
        return self._cache.urls()


class LlmClientPool(_PoolBase[LlmClient]):
    """One :class:`LlmClient` per gateway URL, built from a template configuration.

    ``client(url)`` validates the URL like :class:`ClientConfig` (no direct Ollama port,
    no credentials, no query) and returns the cached client for it. Beyond
    ``max_clients`` URLs the least recently used client is closed; a caller
    still holding it gets transport errors, so keep ``max_clients`` above the
    number of gateways in use.
    """

    def __init__(
        self,
        config: ClientConfig,
        *,
        transport: httpx.BaseTransport | None = None,
        health: RouterHealth | None = None,
        max_clients: int = DEFAULT_MAX_CLIENTS,
    ) -> None:
        def build(url_config: ClientConfig) -> LlmClient:
            return LlmClient(url_config, transport=transport, health=health)

        self._cache: _ClientCache[LlmClient] = _ClientCache(config, build, max_clients)

    def client(self, base_url: str | None = None) -> LlmClient:
        """Client for ``base_url`` (``None`` = template URL); raises ``ConfigurationError``."""
        client, evicted = self._cache.get(base_url)
        for old in evicted:
            old.close()
        return client

    def close(self) -> None:
        """Close all cached clients."""
        for client in self._cache.drain():
            client.close()

    def __enter__(self) -> LlmClientPool:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AsyncLlmClientPool(_PoolBase[AsyncLlmClient]):
    """Async twin of :class:`LlmClientPool` with :class:`AsyncLlmClient` instances.

    ``close``/eviction close the httpx client of the current event loop only
    (as :meth:`AsyncLlmClient.close`).
    """

    def __init__(
        self,
        config: ClientConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        health: RouterHealth | None = None,
        max_clients: int = DEFAULT_MAX_CLIENTS,
    ) -> None:
        def build(url_config: ClientConfig) -> AsyncLlmClient:
            return AsyncLlmClient(url_config, transport=transport, health=health)

        self._cache: _ClientCache[AsyncLlmClient] = _ClientCache(config, build, max_clients)

    async def client(self, base_url: str | None = None) -> AsyncLlmClient:
        """Client for ``base_url`` (``None`` = template URL); raises ``ConfigurationError``."""
        client, evicted = self._cache.get(base_url)
        for old in evicted:
            await old.close()
        return client

    async def close(self) -> None:
        """Close all cached clients (current event loop)."""
        for client in self._cache.drain():
            await client.close()

    async def __aenter__(self) -> AsyncLlmClientPool:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
