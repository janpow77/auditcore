"""Replay transport for page-based POST searches: matches the JSON body ``page``.

``auditcore_harvest.ReplayTransport`` matches method, URL and query parameters
only; TED v3 sends the page in the JSON body. Fixture exchanges carry
``request.json_page``. Unmatched requests raise, they are never empty data.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from auditcore_harvest import Response, TransportError


@dataclass
class PageReplay:
    exchanges: list[dict[str, Any]]
    calls: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> PageReplay:
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
        body = json.loads(data or b"{}")
        self.calls.append({"method": method, "url": url, "body": body, "timeout": timeout})
        for exchange in self.exchanges:
            wanted = exchange["request"]
            if (wanted["method"], wanted["url"], wanted["json_page"]) == (
                method,
                url,
                body.get("page"),
            ):
                reply = exchange["response"]
                raw = (
                    json.dumps(reply["body_json"]).encode()
                    if "body_json" in reply
                    else base64.b64decode(reply.get("body_b64", ""))
                )
                return Response(int(reply["status"]), raw, dict(reply.get("headers", {})), url)
        raise TransportError(f"Keine aufgezeichnete Antwort für Seite {body.get('page')}.")
