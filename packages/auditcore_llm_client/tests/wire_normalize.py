"""Normalise recorded httpx requests so legacy and library traffic can be compared.

Shared by ``tools/capture_legacy_clients.py`` (recording) and the parity tests.
Credentials are replaced by ``<key>``; httpx default headers are dropped.
"""

from __future__ import annotations

import hashlib
import json
from email.parser import BytesParser
from email.policy import HTTP

import httpx

#: Headers httpx adds on its own; they carry no client-specific information.
DEFAULT_HEADERS = frozenset(
    {"host", "user-agent", "accept", "accept-encoding", "connection", "content-length"}
)


def _mask(text: str, secrets: tuple[str, ...]) -> str:
    for secret in secrets:
        text = text.replace(secret, "<key>")
    return text


def _multipart(content: bytes, content_type: str) -> dict[str, object]:
    message = BytesParser(policy=HTTP).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + content
    )
    fields: dict[str, object] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        payload = part.get_payload(decode=True) or b""
        filename = part.get_filename()
        if filename is None:
            fields[str(name)] = payload.decode()
        else:
            fields[str(name)] = {
                "filename": filename,
                "content_type": part.get_content_type(),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
    return fields


def _body(request: httpx.Request) -> object:
    content = request.read()
    if not content:
        return None
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        return _multipart(content, content_type)
    try:
        return json.loads(content)
    except ValueError:
        return content.decode("utf-8", "replace")


def normalize_request(request: httpx.Request, secrets: tuple[str, ...]) -> dict[str, object]:
    """Method, URL, relevant headers and parsed body of one request."""
    headers: dict[str, str] = {}
    for key, value in request.headers.items():
        name = key.lower()
        if name in DEFAULT_HEADERS:
            continue
        if name == "content-type" and value.startswith("multipart/form-data"):
            value = "multipart/form-data"
        headers[name] = _mask(value, secrets)
    return {
        "method": request.method,
        "url": _mask(str(request.url), secrets),
        "headers": dict(sorted(headers.items())),
        "body": _body(request),
    }


def response_for(spec: dict[str, object]) -> httpx.Response:
    """Build a canned response from its fixture description."""
    status = int(spec.get("status", 200))  # type: ignore[call-overload]
    headers = dict(spec.get("headers") or {})  # type: ignore[call-overload]
    if "json" in spec:
        return httpx.Response(status, json=spec["json"], headers=headers)
    if "lines" in spec:
        lines = spec["lines"]
        assert isinstance(lines, list)
        body = "".join(str(line) + "\n" for line in lines)
        return httpx.Response(status, text=body, headers=headers)
    return httpx.Response(status, text=str(spec.get("text", "")), headers=headers)


def raise_for(spec: dict[str, object], request: httpx.Request) -> None:
    """Raise the transport error described by ``spec['raise']`` (if any)."""
    kind = spec.get("raise")
    if kind == "connect":
        raise httpx.ConnectError(str(spec.get("message", "connection refused")), request=request)
    if kind == "timeout":
        raise httpx.ReadTimeout(str(spec.get("message", "timed out")), request=request)
