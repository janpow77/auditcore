"""httpx binding: build requests, convert responses, map transport errors.

Only this module and the two client modules import httpx (extra ``http``).
"""

from __future__ import annotations

import httpx

from auditcore_llm_client.config import ClientConfig
from auditcore_llm_client.errors import LlmClientError, RouterTimeoutError, RouterUnavailableError
from auditcore_llm_client.received import ReceivedResponse
from auditcore_llm_client.wire import PreparedRequest, request_headers

#: Connection pool of the legacy flowinvoice client.
POOL_LIMITS = httpx.Limits(max_connections=16, max_keepalive_connections=8)


def timeout_of(request: PreparedRequest) -> httpx.Timeout:
    """Per-request timeout; streams get a shorter connect timeout (cockpit)."""
    if request.connect_timeout is not None:
        return httpx.Timeout(request.timeout, connect=request.connect_timeout)
    return httpx.Timeout(request.timeout)


def build_request(
    client: httpx.Client | httpx.AsyncClient,
    config: ClientConfig,
    request: PreparedRequest,
) -> httpx.Request:
    """httpx request relative to the client's base URL (JSON or multipart body)."""
    files = {f.field: (f.filename, f.content, f.content_type) for f in request.files}
    return client.build_request(
        request.method,
        request.path,
        headers=request_headers(config, request.headers),
        params=dict(request.params) or None,
        json=request.json_body if request.json_body is not None else None,
        data=dict(request.form) or None,
        files=files or None,
        timeout=timeout_of(request),
    )


def received_from(response: httpx.Response, path: str) -> ReceivedResponse:
    """Snapshot of a fully read response."""
    headers = {key.lower(): value for key, value in response.headers.items()}
    return ReceivedResponse(
        status=response.status_code, content=response.content, path=path, headers=headers
    )


def transport_error(exc: httpx.HTTPError, path: str) -> LlmClientError:
    """Map an httpx exception without copying its text (it may contain the URL)."""
    name = type(exc).__name__
    if isinstance(exc, httpx.TimeoutException):
        return RouterTimeoutError(f"{path}: Zeitüberschreitung ({name})", endpoint=path,
                                  cause_type=name)
    return RouterUnavailableError(f"{path}: Gateway nicht erreichbar ({name})", endpoint=path,
                                  cause_type=name)
