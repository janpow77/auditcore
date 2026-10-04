"""PDF output: only inline ``data:`` resources, no file or network access (#234)."""

from __future__ import annotations

import socket
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from auditcore_dataprotection.pdf import _refusing_url_fetcher, _require_data_url, render_pdf

# 1×1 PNG, synthetic.
PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg=="
)


class _CountingHandler(BaseHTTPRequestHandler):
    """Records the path and answers every request with a redirect."""

    requests: list[str] = []

    def do_GET(self) -> None:  # noqa: N802 - name given by http.server
        self.requests.append(self.path)
        self.send_response(302)
        self.send_header("Location", "/umgeleitet.png")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Keep test output quiet."""


@pytest.fixture
def local_server() -> Iterator[tuple[str, list[str]]]:
    """Local HTTP server that counts every incoming request."""
    seen: list[str] = []
    handler = type("Handler", (_CountingHandler,), {"requests": seen})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", seen
    finally:
        server.shutdown()
        server.server_close()


def _closed_port() -> int:
    """A local port with no listener."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
    return port


def test_external_references_are_skipped_without_fetch(
    local_server: tuple[str, list[str]],
) -> None:
    pytest.importorskip("weasyprint")
    base, seen = local_server
    html = (
        f'<html><head><link rel="stylesheet" href="{base}/stil.css"></head>'
        f'<body><p>Bericht</p><img src="{base}/bild.png">'
        f'<img src="https://127.0.0.1:{_closed_port()}/a.png">'
        '<img src="file:///etc/hostname"></body></html>'
    )

    assert render_pdf(html)[:5] == b"%PDF-"
    assert seen == []


def test_closed_port_reference_does_not_abort() -> None:
    pytest.importorskip("weasyprint")
    html = f'<p>x</p><img src="http://127.0.0.1:{_closed_port()}/a.png">'

    assert render_pdf(html)[:5] == b"%PDF-"


def test_data_image_is_embedded() -> None:
    pytest.importorskip("weasyprint")
    with_image = render_pdf(f'<p>x</p><img src="{PIXEL}" style="width:2cm">')
    without_image = render_pdf('<p>x</p><img src="http://127.0.0.1:9/a.png" style="width:2cm">')

    assert with_image[:5] == b"%PDF-"
    assert b"/Image" in with_image
    assert b"/Image" not in without_image


@pytest.mark.parametrize(
    "url",
    ["http://127.0.0.1:9/a.png", "https://example.invalid/a", "file:///etc/passwd", "bild.png"],
)
def test_require_data_url_refuses_everything_else(url: str) -> None:
    with pytest.raises(ValueError, match="nicht zulässig"):
        _require_data_url(url)


def test_require_data_url_accepts_data() -> None:
    _require_data_url(PIXEL)
    _require_data_url("DATA:text/plain,x")


class _LegacyWeasyPrint:
    """Stand-in for WeasyPrint < 68: no ``URLFetcher``, only ``default_url_fetcher``."""

    def __init__(self) -> None:
        self.fetched: list[str] = []

    def default_url_fetcher(self, url: str) -> dict[str, str]:
        self.fetched.append(url)
        return {"string": "ok"}


def test_legacy_fallback_resolves_only_data_urls() -> None:
    legacy = _LegacyWeasyPrint()
    fetcher = _refusing_url_fetcher(legacy)  # type: ignore[arg-type]
    assert callable(fetcher)

    assert fetcher(PIXEL) == {"string": "ok"}
    with pytest.raises(ValueError, match="nicht zulässig"):
        fetcher("http://127.0.0.1:9/a.png")
    assert legacy.fetched == [PIXEL]


def test_current_weasyprint_gets_url_fetcher_instance() -> None:
    weasyprint = pytest.importorskip("weasyprint")
    if not hasattr(weasyprint, "URLFetcher"):
        pytest.skip("WeasyPrint < 68 nutzt den Funktionsabrufer")
    fetcher = _refusing_url_fetcher(weasyprint)

    assert isinstance(fetcher, weasyprint.URLFetcher)
    with pytest.raises(ValueError):
        fetcher.fetch("http://127.0.0.1:9/a.png")
