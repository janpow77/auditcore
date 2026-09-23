"""Source snapshots: a transport decorator that keeps every response body with its hash.

Adapters stay pure (one page → records). The consumer wraps its own network
transport in :class:`RecordingTransport` when it must archive the raw
response or compute the package hash it logs per run. Secret query
parameters are never recorded.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from auditcore_harvest import Response, Transport, TransportError

SECRET_PARAMS = frozenset({"apikey", "api_key", "key", "token", "password"})


@dataclass(frozen=True)
class SourceSnapshot:
    """One response as received: request identity without secrets, status, bytes, digest."""

    method: str
    url: str
    params: Mapping[str, str]
    status: int
    content_type: str | None
    sha256: str
    body: bytes

    def to_dict(self) -> dict[str, Any]:
        """JSON view without the body."""
        return {
            "method": self.method,
            "url": self.url,
            "params": dict(self.params),
            "status": self.status,
            "content_type": self.content_type,
            "sha256": self.sha256,
            "length": len(self.body),
        }


@dataclass
class RecordingTransport:
    """Wraps a transport and records bounded snapshots of all responses."""

    inner: Transport
    max_body_bytes: int = 50 * 1024 * 1024
    snapshots: list[SourceSnapshot] = field(default_factory=list)

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        timeout: float,
    ) -> Response:
        """Delegate and record; oversized bodies are an error, not a truncated snapshot."""
        response = self.inner.request(
            method, url, params=params, headers=headers, data=data, timeout=timeout
        )
        if len(response.body) > self.max_body_bytes:
            raise TransportError("Antwort überschreitet die Snapshot-Grenze.", retryable=False)
        self.snapshots.append(
            SourceSnapshot(
                method=method,
                url=url,
                params={k: str(v) for k, v in (params or {}).items() if k not in SECRET_PARAMS},
                status=response.status,
                content_type=response.header("content-type"),
                sha256=hashlib.sha256(response.body).hexdigest(),
                body=response.body,
            )
        )
        return response


def canonical_json_bytes(body: bytes) -> bytes:
    """``json.dumps(payload, sort_keys=True)`` of a JSON body (regulierung's package bytes).

    Raises ``ValueError`` if the body is not JSON.
    """
    return json.dumps(json.loads(body), sort_keys=True).encode()


def package_sha256(body: bytes, *, canonical_json: bool) -> str:
    """Digest of a response as regulierung logs it (canonical JSON or raw bytes)."""
    data = canonical_json_bytes(body) if canonical_json else body
    return hashlib.sha256(data).hexdigest()
