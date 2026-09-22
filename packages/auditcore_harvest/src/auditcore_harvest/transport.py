"""Transports: stdlib HTTP, confined local files and fixture replay."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ConfigError, RateLimitError, TransportError
from .ports import Response

MAX_BODY_BYTES = 50 * 1024 * 1024
SAFE_REQUEST_HEADERS = frozenset({"accept", "content-type", "user-agent", "accept-language"})


def raise_for_status(response: Response) -> Response:
    """Map HTTP status codes to structured errors; 2xx is returned unchanged."""
    if response.status == 429:
        retry = response.header("Retry-After")
        seconds = float(retry) if retry and retry.strip().isdigit() else None
        raise RateLimitError("Quelle meldet Rate-Limit (HTTP 429).", retry_after=seconds)
    if response.status in (401, 403):
        from .errors import AuthError

        raise AuthError(f"Zugriff verweigert (HTTP {response.status}).")
    if 500 <= response.status < 600 or response.status == 408:
        raise TransportError(f"Serverfehler HTTP {response.status}.")
    if not 200 <= response.status < 300:
        raise TransportError(f"Unerwarteter Status HTTP {response.status}.", retryable=False)
    return response


class UrllibTransport:
    """Standard-library HTTP(S) transport with timeout and size limit."""

    def __init__(self, user_agent: str = "auditcore-harvest/1.0") -> None:
        self.user_agent = user_agent

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
        """One HTTP request; network failures become ``TransportError``."""
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ConfigError("Nur http(s)-Adressen sind zulässig.")
        if params:
            query = urllib.parse.urlencode(sorted(params.items()))
            url = f"{url}{'&' if parsed.query else '?'}{query}"
        request = urllib.request.Request(url, data=data, method=method)  # noqa: S310
        request.add_header("User-Agent", self.user_agent)
        for key, value in (headers or {}).items():
            request.add_header(key, value)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as reply:  # noqa: S310
                body = reply.read(MAX_BODY_BYTES + 1)
                status = reply.status
                reply_headers = dict(reply.headers.items())
                final_url = reply.url
        except urllib.error.HTTPError as error:
            body = error.read(MAX_BODY_BYTES + 1)
            status, reply_headers, final_url = error.code, dict(error.headers.items()), url
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise TransportError(f"Verbindung fehlgeschlagen: {type(error).__name__}") from error
        if len(body) > MAX_BODY_BYTES:
            raise TransportError("Antwort überschreitet die Größenbegrenzung.", retryable=False)
        return Response(status, body, reply_headers, final_url)


class FileTransport:
    """Reads ``file:`` locators confined to one root directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

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
        """Return the file as body; paths outside the root are rejected."""
        if method != "GET" or not url.startswith("file:"):
            raise ConfigError("FileTransport unterstützt nur GET auf file:-Adressen.")
        relative = urllib.parse.unquote(url[len("file:") :]).lstrip("/")
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root) or path.is_symlink():
            raise ConfigError("Pfad liegt außerhalb des freigegebenen Verzeichnisses.")
        if not path.is_file():
            return Response(404, b"", {}, url)
        if path.stat().st_size > MAX_BODY_BYTES:
            raise TransportError("Datei überschreitet die Größenbegrenzung.", retryable=False)
        return Response(200, path.read_bytes(), {"content-type": "application/octet-stream"}, url)


@dataclass
class ReplayTransport:
    """Serves recorded responses; unmatched requests are errors, not empty data.

    Each exchange matches on method, URL (without query) and exactly the
    recorded query parameters; parameters named in ``ignore_params`` (secrets
    such as API keys) are excluded from matching and never recorded.
    Exchanges are consumed in order when ``ordered``.
    """

    exchanges: Sequence[Mapping[str, Any]]
    ordered: bool = False
    ignore_params: frozenset[str] = frozenset({"apikey", "api_key", "key", "token", "password"})
    calls: list[dict[str, Any]] = field(default_factory=list)
    _used: set[int] = field(default_factory=set)

    @classmethod
    def from_file(cls, path: Path, *, ordered: bool = False) -> ReplayTransport:
        """Load ``{"exchanges": [...]}`` fixture JSON."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(tuple(data["exchanges"]), ordered=ordered)

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
        """Answer from the fixture or raise ``TransportError`` (non-retryable)."""
        params = {k: str(v) for k, v in (params or {}).items() if k not in self.ignore_params}
        self.calls.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "header_names": sorted(k.lower() for k in (headers or {})),
            }
        )
        for index, exchange in enumerate(self.exchanges):
            if index in self._used and (self.ordered or exchange.get("once", False)):
                continue
            match = exchange["request"]
            if match.get("method", "GET") != method or match["url"] != url:
                continue
            wanted = {k: str(v) for k, v in match.get("params", {}).items()}
            if params != wanted:
                continue
            self._used.add(index)
            reply = exchange["response"]
            if reply.get("raise") == "timeout":
                raise TransportError("Zeitüberschreitung (aufgezeichnet).")
            if "body_json" in reply:
                body = json.dumps(reply["body_json"], ensure_ascii=False).encode("utf-8")
            elif "body_b64" in reply:
                body = base64.b64decode(reply["body_b64"])
            else:
                body = str(reply.get("body_text", "")).encode("utf-8")
            return Response(
                int(reply.get("status", 200)), body, dict(reply.get("headers", {})), url
            )
        raise TransportError(
            f"Keine aufgezeichnete Antwort für {method} {url} {params}.", retryable=False
        )
