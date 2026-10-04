"""Transports shipped with the core: confined local files and fixture replay.

Network transports are infrastructure and are injected by the consumer (for
example an httpx client wrapped in the :class:`~auditcore_harvest.ports.Transport`
protocol); ``docs/examples/urllib_transport.py`` shows a standard-library
implementation.
"""

from __future__ import annotations

import base64
import json
import urllib.parse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .errors import AuthError, ConfigError, ParserError, RateLimitError, TransportError
from .kinds import ErrorKind
from .model import JSON
from .ports import Response

MAX_BODY_BYTES = 50 * 1024 * 1024


@dataclass(frozen=True)
class StatusPolicy:
    """How :func:`raise_for_status` maps HTTP status codes; the default is the contract-1 mapping.

    * ``check=False`` returns every response unchanged (the adapter decides).
    * ``accept`` lists further statuses returned unchanged (for example ``404``
      for a source where "not found" is a valid answer).
    * ``rate_limited``, ``auth`` and ``retryable`` select the error class;
      ``retry_server_errors`` treats every 5xx as retryable.
    """

    check: bool = True
    accept: frozenset[int] = frozenset()
    rate_limited: frozenset[int] = frozenset({429})
    auth: frozenset[int] = frozenset({401, 403})
    retryable: frozenset[int] = frozenset({408})
    retry_server_errors: bool = True

    def passes(self, status: int) -> bool:
        """True if a response with ``status`` is returned unchanged."""
        return not self.check or 200 <= status < 300 or status in self.accept

    def is_retryable(self, status: int) -> bool:
        """True for statuses that end in a retryable ``TransportError``."""
        return status in self.retryable or (self.retry_server_errors and 500 <= status < 600)


DEFAULT_STATUS_POLICY = StatusPolicy()


def _retry_after(response: Response) -> float | None:
    """``Retry-After`` in whole seconds; HTTP dates and garbage give ``None``."""
    value = response.header("Retry-After")
    return float(value) if value and value.strip().isdigit() else None


def raise_for_status(response: Response, policy: StatusPolicy | None = None) -> Response:
    """Map HTTP status codes to structured errors; passing responses are returned unchanged.

    Every raised error carries ``http_status`` and an :class:`ErrorKind`.
    """
    rules = policy or DEFAULT_STATUS_POLICY
    status = response.status
    if rules.passes(status):
        return response
    if status in rules.rate_limited:
        raise RateLimitError(
            f"Quelle meldet Rate-Limit (HTTP {status}).",
            retry_after=_retry_after(response),
            http_status=status,
        )
    if status in rules.auth:
        raise AuthError(f"Zugriff verweigert (HTTP {status}).", http_status=status)
    if rules.is_retryable(status):
        raise TransportError(
            f"Serverfehler HTTP {status}.", http_status=status, kind=ErrorKind.HTTP_STATUS
        )
    raise TransportError(
        f"Unerwarteter Status HTTP {status}.",
        retryable=False,
        http_status=status,
        kind=ErrorKind.HTTP_STATUS,
    )


def decode_json(body: bytes, message: str = "Antwort ist kein JSON.") -> JSON:
    """Parse a JSON response body; undecodable bodies are a :class:`ParserError`.

    ``message`` is the source-specific error text; the decoding error is chained.
    """
    try:
        return json.loads(body)
    except ValueError as exc:
        raise ParserError(message) from exc


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

    exchanges: Sequence[Mapping[str, JSON]]
    ordered: bool = False
    ignore_params: frozenset[str] = frozenset({"apikey", "api_key", "key", "token", "password"})
    calls: list[dict[str, JSON]] = field(default_factory=list)
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
                raise TransportError("Zeitüberschreitung (aufgezeichnet).", kind=ErrorKind.TIMEOUT)
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
