"""Cached model list with explicit fetch state (cockpit ``model_snapshot``).

Semantics taken from cockpit: a successful list is cached for 60 s; a failed
fetch is cached between 5 s and 60 s (``Retry-After``); after a failure the
last good list is served as ``stale`` for at most 300 s. Unlike cockpit the
client knows exactly one gateway URL – the hard-coded Tailscale fallback
address is not adopted.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, replace

from auditcore_llm_client.errors import ErrorKind, LlmClientError
from auditcore_llm_client.results import ModelInfo

CACHE_TTL_S = 60.0
ERROR_TTL_S = 5.0
STALE_TTL_S = 300.0


@dataclass(frozen=True)
class ModelSnapshot:
    """Model list plus the state of the last fetch."""

    ok: bool
    reachable: bool
    state: str
    message: str
    url: str
    models: tuple[ModelInfo, ...]
    stale: bool
    http_status: int | None
    retry_after: int | None
    cache_ttl: float

    def to_dict(self) -> dict[str, object]:
        """cockpit shape (``models`` as list of dicts)."""
        return {
            "ok": self.ok, "reachable": self.reachable, "state": self.state,
            "message": self.message, "url": self.url,
            "models": [m.to_dict() for m in self.models], "stale": self.stale,
            "http_status": self.http_status, "retry_after": self.retry_after,
            "cache_ttl": self.cache_ttl,
        }


def _retry_after(error: LlmClientError) -> int:
    return max(1, int(error.retry_after)) if error.retry_after is not None else 1


def classify(error: LlmClientError) -> tuple[str, str, int | None, bool]:
    """(state, message, retry_after, reachable) of a failed model fetch."""
    code = error.status_code
    if error.kind is ErrorKind.HTTP_STATUS and code == 429:
        return ("overloaded", "ai-router überlastet (HTTP 429) – Modellabruf gedrosselt",
                _retry_after(error), True)
    if error.kind is ErrorKind.HTTP_STATUS and code in (401, 403):
        return "auth_error", f"ai-router: Zugriff verweigert (HTTP {code})", None, True
    if error.kind is ErrorKind.HTTP_STATUS:
        return "http_error", f"ai-router: Modellabruf fehlgeschlagen (HTTP {code})", None, True
    if error.kind is ErrorKind.INVALID_RESPONSE:
        return "invalid_response", "ai-router: ungültige Antwort auf den Modellabruf", None, True
    return "unreachable", "ai-router nicht erreichbar", None, False


class ModelCatalog:
    """Cache logic only; the client supplies the fetch and the lock."""

    def __init__(self, url: str, clock: Callable[[], float] = time.monotonic) -> None:
        self.url = url
        self._clock = clock
        self._snapshot: tuple[float, ModelSnapshot] | None = None
        self._last_models: tuple[float, tuple[ModelInfo, ...]] | None = None

    def _age(self, stamp: float) -> float:
        return self._clock() - stamp

    def cached(self) -> ModelSnapshot | None:
        """The cached snapshot while it is valid, else ``None``."""
        if self._snapshot is None:
            return None
        stamp, snapshot = self._snapshot
        if self._age(stamp) >= min(CACHE_TTL_S, snapshot.cache_ttl):
            return None
        if snapshot.stale and self._stale_models() is None:
            return replace(snapshot, models=(), stale=False)
        return snapshot

    def _stale_models(self) -> tuple[ModelInfo, ...] | None:
        if self._last_models is None or self._age(self._last_models[0]) >= STALE_TTL_S:
            return None
        return self._last_models[1]

    def succeeded(self, models: list[ModelInfo]) -> ModelSnapshot:
        """Store and return the snapshot of a successful fetch."""
        found = tuple(models)
        self._last_models = (self._clock(), found)
        snapshot = ModelSnapshot(
            ok=bool(found), reachable=True, state="ok" if found else "empty",
            message="Router bereit" if found else "ai-router erreichbar, meldet aber keine Modelle",
            url=self.url, models=found, stale=False, http_status=200, retry_after=None,
            cache_ttl=CACHE_TTL_S,
        )
        self._snapshot = (self._clock(), snapshot)
        return snapshot

    def failed(self, error: LlmClientError) -> ModelSnapshot:
        """Store and return the snapshot of a failed fetch (last good list as stale)."""
        state, message, retry_after, reachable = classify(error)
        models = self._stale_models() or ()
        status = error.status_code if error.kind is ErrorKind.HTTP_STATUS else None
        if error.kind is ErrorKind.INVALID_RESPONSE:
            status = 200
        snapshot = ModelSnapshot(
            ok=False, reachable=reachable, state=state, message=message, url=self.url,
            models=models, stale=bool(models), http_status=status, retry_after=retry_after,
            cache_ttl=min(CACHE_TTL_S, max(ERROR_TTL_S, float(retry_after or 0))),
        )
        self._snapshot = (self._clock(), snapshot)
        return snapshot
