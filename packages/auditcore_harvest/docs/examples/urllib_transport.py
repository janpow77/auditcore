"""Beispiel eines Netzwerktransports für ``auditcore_harvest`` (nur Standardbibliothek).

Nicht Teil der Distribution: Netzwerkzugriff ist Infrastruktur des Consumers.
Die Klasse erfüllt das Protokoll ``auditcore_harvest.Transport`` und wird dem
``HarvestEngine`` injiziert.

Mit ``follow_redirects=False`` folgt der Transport keinen Weiterleitungen und
liefert jede Antwort samt aller ``Set-Cookie``-Zeilen (``raw_headers``). So
umschlossen von ``auditcore_harvest.SessionTransport`` bleiben Cookies aus
Weiterleitungs-Zwischenantworten für Folgeabrufe erhalten.
"""

from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping

from auditcore_harvest import ConfigError, ErrorKind, Response, TransportError

MAX_BODY_BYTES = 50 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Hands every redirect response back to the caller unchanged."""

    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


class UrllibTransport:
    """Standard-library HTTP(S) transport with timeout and size limit."""

    def __init__(
        self, user_agent: str = "auditcore-harvest/1.0", *, follow_redirects: bool = True
    ) -> None:
        self.user_agent = user_agent
        handlers = () if follow_redirects else (_NoRedirect(),)
        self._opener = urllib.request.build_opener(*handlers)

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
            with self._opener.open(request, timeout=timeout) as reply:
                body = reply.read(MAX_BODY_BYTES + 1)
                status = reply.status
                lines = tuple(reply.headers.items())
                final_url = reply.url
        except urllib.error.HTTPError as error:
            body = error.read(MAX_BODY_BYTES + 1)
            status, lines, final_url = error.code, tuple(error.headers.items()), url
        except TimeoutError as error:
            raise TransportError("Zeitüberschreitung.", kind=ErrorKind.TIMEOUT) from error
        except (urllib.error.URLError, OSError) as error:
            raise TransportError(f"Verbindung fehlgeschlagen: {type(error).__name__}") from error
        if len(body) > MAX_BODY_BYTES:
            raise TransportError("Antwort überschreitet die Größenbegrenzung.", retryable=False)
        return Response(status, body, dict(lines), final_url, raw_headers=lines)
