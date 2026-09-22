"""Transports, status mapping and reference adapters against real and recorded I/O."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest

from auditcore_harvest import (
    AuthError,
    ConfigError,
    FetchContext,
    HarvestRequest,
    ParserError,
    RateLimitError,
    Response,
    TransportError,
    raise_for_status,
)
from auditcore_harvest.memory import FixedClock, StaticCredentials
from auditcore_harvest.reference import (
    FeedAdapter,
    JsonApiAdapter,
    example_feed_source,
    example_json_source,
)
from auditcore_harvest.transport import FileTransport, ReplayTransport

_spec = importlib.util.spec_from_file_location(
    "urllib_transport", Path(__file__).parents[1] / "docs" / "examples" / "urllib_transport.py"
)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
sys.modules["urllib_transport"] = _module
_spec.loader.exec_module(_module)
UrllibTransport = _module.UrllibTransport


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server API
        if self.path.startswith("/slow"):
            time.sleep(1.0)
        status = {"/429": 429, "/500": 500}.get(self.path.split("?")[0], 200)
        self.send_response(status)
        if status == 429:
            self.send_header("Retry-After", "7")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"path": self.path}).encode())

    def log_message(self, *args: Any) -> None:
        return None


@pytest.fixture(scope="module")
def server() -> Iterator[str]:
    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_urllib_transport_real_http(server: str) -> None:
    transport = UrllibTransport()
    ok = transport.request("GET", f"{server}/ok", params={"b": "2", "a": "1"}, timeout=5)
    assert ok.status == 200 and json.loads(ok.body)["path"] == "/ok?a=1&b=2"
    with pytest.raises(RateLimitError) as limited:
        raise_for_status(transport.request("GET", f"{server}/429", timeout=5))
    assert limited.value.retry_after == 7
    with pytest.raises(TransportError) as failed:
        raise_for_status(transport.request("GET", f"{server}/500", timeout=5))
    assert failed.value.retryable
    with pytest.raises(TransportError):
        transport.request("GET", f"{server}/slow", timeout=0.2)
    with pytest.raises(ConfigError):
        transport.request("GET", "ftp://example.invalid/x", timeout=1)


def test_status_mapping() -> None:
    assert raise_for_status(Response(204, b"")).status == 204
    with pytest.raises(AuthError):
        raise_for_status(Response(401, b""))
    with pytest.raises(TransportError) as not_found:
        raise_for_status(Response(404, b""))
    assert not not_found.value.retryable


def test_file_transport_confinement(tmp_path: Path) -> None:
    (tmp_path / "a.xml").write_text("<x/>")
    (tmp_path.parent / "outside.txt").write_text("nein")
    (tmp_path / "link").symlink_to(tmp_path.parent / "outside.txt")
    transport = FileTransport(tmp_path)
    assert transport.request("GET", "file:a.xml", timeout=1).body == b"<x/>"
    assert transport.request("GET", "file:fehlt.xml", timeout=1).status == 404
    for bad in ("file:../outside.txt", "file:link"):
        with pytest.raises(ConfigError):
            transport.request("GET", bad, timeout=1)


def test_replay_transport_exact_matching_and_secrets() -> None:
    replay = ReplayTransport(
        [
            {
                "request": {"url": "https://x.invalid/a", "params": {"p": "1"}},
                "response": {"status": 200, "body_text": "eins"},
            },
            {"request": {"url": "https://x.invalid/t"}, "response": {"raise": "timeout"}},
        ]
    )
    response = replay.request(
        "GET", "https://x.invalid/a", params={"p": "1", "apikey": "geheim"}, timeout=1
    )
    assert response.text() == "eins" and "geheim" not in repr(replay.calls)
    with pytest.raises(TransportError) as unmatched:
        replay.request("GET", "https://x.invalid/a", params={"p": "2"}, timeout=1)
    assert not unmatched.value.retryable
    with pytest.raises(TransportError):
        replay.request("GET", "https://x.invalid/t", timeout=1)


def context(transport: Any, config: dict[str, Any], **kw: Any) -> FetchContext:
    return FetchContext(
        HarvestRequest("example.feed", "r", **kw),
        config,
        transport,
        StaticCredentials({("example.json_api", "api_key"): "k-123"}),
        FixedClock(),
        5.0,
        1,
    )


def feed(body: str) -> ReplayTransport:
    return ReplayTransport(
        [{"request": {"url": "https://f.invalid/"}, "response": {"status": 200, "body_text": body}}]
    )


def test_feed_adapter_formats_and_safety() -> None:
    adapter = FeedAdapter(example_feed_source())
    cfg = {"url": "https://f.invalid/"}
    atom = (
        '<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>urn:1</id><title>A</title>'
        '<link href="https://a"/><updated>2026-01-01</updated></entry></feed>'
    )
    page = adapter.fetch_page(context(feed(atom), cfg), None)
    assert [r.record_id for r in page.records] == ["urn:1"] and page.complete
    empty = adapter.fetch_page(
        context(feed("<rss><channel><title>t</title></channel></rss>"), cfg), None
    )
    assert empty.records == () and empty.complete and not empty.issues
    missing = adapter.fetch_page(
        context(feed("<rss><channel><item><title>x</title></item></channel></rss>"), cfg), None
    )
    assert missing.issues and missing.status.value == "partial"
    for bad in ('<?xml version="1.0"?><!DOCTYPE r [<!ENTITY e "x">]><rss/>', "kein xml", "<html/>"):
        with pytest.raises(ParserError):
            adapter.fetch_page(context(feed(bad), cfg), None)
    with pytest.raises(ConfigError):
        adapter.validate_config({"url": "gopher://x"})


def test_json_adapter_filters_issues_and_secret_handling() -> None:
    adapter = JsonApiAdapter(example_json_source(), api_key_param="apikey")
    body = {"items": [{"id": "1", "land": "DE"}, {"name": "ohne id"}], "next": None}
    replay = ReplayTransport(
        [
            {
                "request": {"url": "https://j.invalid/", "params": {"land": "DE"}},
                "response": {"status": 200, "body_json": body},
            }
        ]
    )
    page = adapter.fetch_page(
        context(replay, {"url": "https://j.invalid/"}, filters={"land": "DE", "unbekannt": "x"}),
        None,
    )
    assert [r.record_id for r in page.records] == ["1"] and len(page.issues) == 1
    assert "k-123" not in repr(page)
    for payload in ("nicht json", json.dumps({"daten": []})):
        broken = ReplayTransport(
            [
                {
                    "request": {"url": "https://j.invalid/"},
                    "response": {"status": 200, "body_text": payload},
                }
            ]
        )
        with pytest.raises(ParserError):
            adapter.fetch_page(context(broken, {"url": "https://j.invalid/"}), None)
    for config in ({"url": "https://j.invalid", "page_size": 0}, {"url": 5}, {}):
        with pytest.raises(ConfigError):
            adapter.validate_config(config)
    no_key = FetchContext(
        HarvestRequest("example.json_api", "r"),
        {"url": "https://j.invalid/"},
        replay,
        StaticCredentials(),
        FixedClock(),
        5.0,
        1,
    )
    with pytest.raises(AuthError):
        adapter.fetch_page(no_key, None)
