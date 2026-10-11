"""Cookie session over any transport: cookies survive redirects and follow-up requests.

:class:`SessionTransport` wraps a transport that performs exactly one request
(and does *not* follow redirects itself). It follows redirects hop by hop,
stores every ``Set-Cookie`` of intermediate and final responses in one
:class:`http.cookiejar.CookieJar` and sends the matching cookies with every
later request of the same session (main fetch and follow-up fetches alike).

If the inner transport follows redirects on its own, it should report the
intermediate responses in :attr:`Response.history`; their cookies are then
stored as well, but cannot be sent on those intermediate hops.
"""

from __future__ import annotations

import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .errors import TransportError
from .ports import Response, Transport

if TYPE_CHECKING:  # pragma: no cover - typing only
    import urllib.request
    from http.cookiejar import CookieJar

REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
SENSITIVE_HEADERS = frozenset({"authorization", "cookie", "proxy-authorization"})


@dataclass(frozen=True)
class Hop:
    """One request of a redirect chain."""

    method: str
    url: str
    params: Mapping[str, str] | None
    headers: Mapping[str, str]
    data: bytes | None


class _SetCookieReply:
    """Minimal response object for :meth:`CookieJar.extract_cookies`.

    The standard library's network modules (``http.cookiejar`` pulls in
    ``http.client``, ``socket`` and ``ssl``) are imported only when a session
    is used, so ``import auditcore_harvest`` stays free of them.
    """

    def __init__(self, values: tuple[str, ...]) -> None:
        self._values = list(values)

    def info(self) -> _SetCookieReply:
        """Header container as expected by ``http.cookiejar``."""
        return self

    def get_all(self, name: str, default: list[str]) -> list[str]:
        """Only ``Set-Cookie`` lines are known."""
        return list(self._values) if name.lower() == "set-cookie" else default


def _request(url: str, method: str = "GET") -> urllib.request.Request:
    import urllib.request

    return urllib.request.Request(url, method=method)


def _full_url(url: str, params: Mapping[str, str] | None) -> str:
    if not params:
        return url
    query = urllib.parse.urlencode(sorted(params.items()))
    return f"{url}{'&' if urllib.parse.urlsplit(url).query else '?'}{query}"


def _origin(url: str) -> tuple[str, str]:
    parts = urllib.parse.urlsplit(url)
    return (parts.scheme.lower(), parts.netloc.lower())


class CookieSession:
    """Cookie jar and redirect rules of one session, independent of the transport.

    The same object can be shared by several transports (for example a
    synchronous and an asynchronous one) to keep one cookie state.
    """

    def __init__(self, jar: CookieJar | None = None, *, max_redirects: int = 10) -> None:
        if max_redirects < 0:
            raise ValueError("max_redirects darf nicht negativ sein.")
        if jar is None:
            from http.cookiejar import CookieJar

            jar = CookieJar()
        self.jar = jar
        self.max_redirects = max_redirects

    def cookie_names(self) -> tuple[str, ...]:
        """Names of the stored cookies (values are secrets and never listed)."""
        return tuple(sorted({cookie.name for cookie in self.jar}))

    def headers_for(self, hop: Hop) -> dict[str, str]:
        """Request headers of ``hop`` plus the cookies the jar holds for its URL."""
        headers = dict(hop.headers)
        probe = _request(_full_url(hop.url, hop.params), hop.method)
        self.jar.add_cookie_header(probe)
        stored = probe.get_header("Cookie")
        if stored:
            given = next((v for k, v in headers.items() if k.lower() == "cookie"), None)
            headers = {k: v for k, v in headers.items() if k.lower() != "cookie"}
            headers["Cookie"] = f"{given}; {stored}" if given else stored
        return headers

    def absorb(self, response: Response, hop: Hop) -> None:
        """Store the cookies of ``response`` and of every response in its history."""
        requested = _full_url(hop.url, hop.params)
        for reply in (*response.history, response):
            values = reply.header_values("Set-Cookie")
            if values:
                origin = _request(reply.url or requested)
                self.jar.extract_cookies(_SetCookieReply(values), origin)  # type: ignore[arg-type]

    def next_hop(self, hop: Hop, response: Response) -> Hop | None:
        """The request a redirect asks for, or ``None`` if ``response`` is final."""
        location = response.header("Location")
        if response.status not in REDIRECT_STATUSES or not location:
            return None
        target = urllib.parse.urljoin(response.url or _full_url(hop.url, hop.params), location)
        if urllib.parse.urlsplit(target).scheme.lower() not in ("http", "https"):
            raise TransportError(
                "Weiterleitung auf ein nicht unterstütztes Schema abgelehnt.", retryable=False
            )
        keep_method = response.status in (307, 308) or hop.method == "HEAD"
        to_get = response.status == 303 or (response.status in (301, 302) and hop.method == "POST")
        method = hop.method if keep_method or not to_get else "GET"
        headers = dict(hop.headers)
        if _origin(target) != _origin(hop.url):
            headers = {k: v for k, v in headers.items() if k.lower() not in SENSITIVE_HEADERS}
        data = hop.data if method == hop.method else None
        return Hop(method, target, None, headers, data)

    def too_many(self) -> TransportError:
        """Error for a redirect chain longer than ``max_redirects``."""
        return TransportError(
            f"Mehr als {self.max_redirects} Weiterleitungen; Abruf abgebrochen.", retryable=False
        )

    def step(self, hop: Hop, response: Response, chain: list[Response]) -> Response | Hop:
        """Store cookies, then return the final response or the next request.

        ``chain`` collects the intermediate responses; the final response
        carries them as ``history``.
        """
        self.absorb(response, hop)
        following = self.next_hop(hop, response)
        if following is not None:
            chain.append(response)
            return following
        history: list[Response] = []
        for reply in chain:
            history.extend((*reply.history, replace(reply, history=())))
        return replace(response, history=(*history, *response.history))


class SessionTransport:
    """Transport wrapper keeping cookies across redirects and requests of one session."""

    def __init__(self, inner: Transport, session: CookieSession | None = None) -> None:
        self.inner = inner
        self.session = session or CookieSession()

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
        """Perform the request, follow redirects and keep all cookies."""
        hop = Hop(method, url, params, dict(headers or {}), data)
        chain: list[Response] = []
        for _ in range(self.session.max_redirects + 1):
            response = self.inner.request(
                hop.method,
                hop.url,
                params=hop.params,
                headers=self.session.headers_for(hop),
                data=hop.data,
                timeout=timeout,
            )
            outcome = self.session.step(hop, response, chain)
            if isinstance(outcome, Response):
                return outcome
            hop = outcome
        raise self.session.too_many()
