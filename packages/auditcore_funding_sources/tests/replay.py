"""Replay transport that also matches the JSON request body (POST paging in the body).

``auditcore_harvest.ReplayTransport`` matches method, URL and query only; the
eAidRegister pages through the request body, so this test transport compares
the body as well. Fixture format: ``{"exchanges": [{"request": {"method", "url",
"json"}, "response": {"status", "headers", "body_json" | "body_b64"}}]}``.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from auditcore_harvest import Response, TransportError


class BodyReplayTransport:
    def __init__(self, exchanges: list[dict[str, Any]]) -> None:
        self.exchanges = exchanges
        self.calls: list[dict[str, Any]] = []

    @classmethod
    def from_file(cls, path: Path) -> BodyReplayTransport:
        return cls(json.loads(path.read_text(encoding="utf-8"))["exchanges"])

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Any = None,
        headers: Any = None,
        data: bytes | None = None,
        timeout: float,
    ) -> Response:
        body = json.loads(data) if data else None
        self.calls.append({"method": method, "url": url, "json": body})
        for exchange in self.exchanges:
            wanted = exchange["request"]
            if wanted["method"] == method and wanted["url"] == url and wanted.get("json") == body:
                reply = exchange["response"]
                if "body_json" in reply:
                    raw = json.dumps(reply["body_json"], ensure_ascii=False).encode("utf-8")
                elif "body_b64" in reply:
                    raw = base64.b64decode(reply["body_b64"])
                else:
                    raw = str(reply.get("body_text", "")).encode("utf-8")
                return Response(
                    int(reply.get("status", 200)), raw, dict(reply.get("headers", {})), url
                )
        raise TransportError(f"Keine aufgezeichnete Antwort für {method} {url}", retryable=False)
