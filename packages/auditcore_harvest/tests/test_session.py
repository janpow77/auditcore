"""Issue #236: cookies of redirect intermediate responses survive into follow-up requests."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from auditcore_harvest import CookieSession, Response, SessionTransport, TransportError

_spec = importlib.util.spec_from_file_location(
    "urllib_transport_session",
    Path(__file__).parents[1] / "docs" / "examples" / "urllib_transport.py",
)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
sys.modules["urllib_transport_session"] = _module
_spec.loader.exec_module(_module)
UrllibTransport = _module.UrllibTransport


class CookieHandler(BaseHTTPRequestHandler):
    """``/start`` → 302 (cookie a) → ``/step`` → 303 (cookie b) → ``/data`` echoes cookies."""

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        path = self.path.split("?")[0]
        if path == "/start":
            self._redirect(302, "/step", ("sid=a1; Path=/", "lang=de; Path=/"))
        elif path == "/step":
            self._redirect(303, "/data", ("token=b2; Path=/",))
        else:
            body = json.dumps({"path": path, "cookie": self.headers.get("Cookie", "")})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode())

    def _redirect(self, status: int, target: str, cookies: tuple[str, ...]) -> None:
        self.send_response(status)
        for cookie in cookies:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Location", target)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args: object) -> None:
        return None


@pytest.fixture(scope="module")
def server() -> Iterator[str]:
    httpd = HTTPServer(("127.0.0.1", 0), CookieHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def cookies_of(response: Response) -> set[str]:
    sent = json.loads(response.body)["cookie"]
    return {part.strip() for part in sent.split(";") if part.strip()}


def test_cookies_of_intermediate_redirects_reach_main_and_follow_up_requests(server: str) -> None:
    transport = SessionTransport(UrllibTransport(follow_redirects=False))
    final = transport.request("GET", f"{server}/start", timeout=5)
    assert final.status == 200 and json.loads(final.body)["path"] == "/data"
    assert cookies_of(final) == {"sid=a1", "lang=de", "token=b2"}
    assert [r.status for r in final.history] == [302, 303]
    follow_up = transport.request("GET", f"{server}/anderes", timeout=5)
    assert cookies_of(follow_up) == {"sid=a1", "lang=de", "token=b2"}
    assert transport.session.cookie_names() == ("lang", "sid", "token")


def test_plain_urllib_redirects_lose_intermediate_cookies(server: str) -> None:
    """Characterizes the defect the session fixes (urllib follows on its own)."""
    final = UrllibTransport().request("GET", f"{server}/start", timeout=5)
    assert cookies_of(final) == set()


@dataclass
class Scripted:
    """Inner transport with scripted responses; records every request."""

    replies: list[Response]
    seen: list[dict[str, object]] = field(default_factory=list)

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
        self.seen.append(
            {"method": method, "url": url, "headers": dict(headers or {}), "data": data}
        )
        return self.replies.pop(0)


def redirect(status: int, location: str, url: str, *cookies: str) -> Response:
    lines = (("Location", location), *(("Set-Cookie", c) for c in cookies))
    return Response(status, b"", dict(lines), url, raw_headers=lines)


def test_post_redirect_becomes_get_and_cross_origin_drops_secrets() -> None:
    inner = Scripted(
        [
            redirect(303, "/weiter", "https://a.invalid/form", "s=1; Path=/"),
            redirect(307, "https://b.invalid/ziel", "https://a.invalid/weiter"),
            Response(200, b"ok", {}, "https://b.invalid/ziel"),
        ]
    )
    transport = SessionTransport(inner)
    final = transport.request(
        "POST",
        "https://a.invalid/form",
        headers={"Authorization": "Bearer geheim", "Accept": "x"},
        data=b"q=1",
        timeout=1,
    )
    assert final.body == b"ok" and len(final.history) == 2
    second, third = inner.seen[1], inner.seen[2]
    assert second["method"] == "GET" and second["data"] is None
    assert second["headers"] == {"Authorization": "Bearer geheim", "Accept": "x", "Cookie": "s=1"}
    assert third["method"] == "GET" and third["headers"] == {"Accept": "x"}


def test_307_keeps_method_and_body_and_caller_cookie_is_merged() -> None:
    inner = Scripted(
        [
            redirect(307, "/b", "https://a.invalid/a", "s=1; Path=/"),
            Response(200, b"", {}, "https://a.invalid/b"),
        ]
    )
    SessionTransport(inner).request(
        "PUT", "https://a.invalid/a", headers={"cookie": "eigen=1"}, data=b"x", timeout=1
    )
    assert inner.seen[1]["method"] == "PUT" and inner.seen[1]["data"] == b"x"
    assert inner.seen[1]["headers"] == {"Cookie": "eigen=1; s=1"}


def test_cookies_from_history_of_a_following_inner_transport_are_kept() -> None:
    hop = redirect(302, "/z", "https://a.invalid/x", "early=1; Path=/")
    inner = Scripted(
        [
            Response(200, b"", {}, "https://a.invalid/z", history=(hop,)),
            Response(200, b"", {}, "https://a.invalid/next"),
        ]
    )
    transport = SessionTransport(inner)
    first = transport.request("GET", "https://a.invalid/x", params={"q": "1"}, timeout=1)
    assert first.history == (hop,)
    transport.request("GET", "https://a.invalid/next", timeout=1)
    assert inner.seen[1]["headers"] == {"Cookie": "early=1"}


def test_redirect_limits_and_schemes() -> None:
    loop = [redirect(302, "/a", "https://a.invalid/a") for _ in range(3)]
    with pytest.raises(TransportError) as too_many:
        SessionTransport(Scripted(loop), CookieSession(max_redirects=1)).request(
            "GET", "https://a.invalid/a", timeout=1
        )
    assert not too_many.value.retryable
    bad = Scripted([redirect(301, "file:///etc/passwd", "https://a.invalid/")])
    with pytest.raises(TransportError):
        SessionTransport(bad).request("GET", "https://a.invalid/", timeout=1)
    with pytest.raises(ValueError):
        CookieSession(max_redirects=-1)
    plain = Scripted([Response(301, b"", {}, "https://a.invalid/")])
    assert SessionTransport(plain).request("GET", "https://a.invalid/", timeout=1).status == 301


def test_session_can_be_shared_between_transports() -> None:
    session = CookieSession()
    first = Scripted([Response(200, b"", {"Set-Cookie": "k=v; Path=/"}, "https://a.invalid/")])
    SessionTransport(first, session).request("GET", "https://a.invalid/", timeout=1)
    second = Scripted([Response(200, b"", {}, "https://a.invalid/p")])
    SessionTransport(second, session).request("GET", "https://a.invalid/p", timeout=1)
    assert second.seen[0]["headers"] == {"Cookie": "k=v"}
