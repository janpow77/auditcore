"""Redaction patterns and structured errors."""

from __future__ import annotations

import traceback

import pytest

from auditcore_llm_client import (
    ErrorKind,
    LlmClientError,
    RouterHttpError,
    RouterTimeoutError,
    redact,
)
from auditcore_llm_client.redaction import contains_secret

KEY = "k3y-Geheim-4711"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("see http://user:pw@host/x", "see <url>"),
        ("dsn postgresql+asyncpg://u:p@db/x", "dsn <dsn>"),
        ("redis rediss://:pw@r:6379", "redis <dsn>"),
        ("Authorization: Bearer abc.def", "Authorization=<redacted>"),
        ("header bearer abc.def", "header Bearer <token>"),
        ("X-Api-Key: abc", "X-Api-Key=<redacted>"),
        ("x-api-key=abc", "X-Api-Key=<redacted>"),
        ("key sk-live_123", "key <api-key>"),
        ("gh ghp_ABC123", "gh <github-token>"),
        ("q api_key=abc&x=1", "q api_key=<redacted>&x=1"),
        ("token=abc", "token=<redacted>"),
    ],
)
def test_patterns(text: str, expected: str) -> None:
    assert redact(text, max_len=None) == expected


def test_configured_secret_is_removed_before_truncation() -> None:
    text = "x" * 150 + KEY
    redacted = redact(text, secrets=[KEY], max_len=160)
    assert KEY[:5] not in redacted
    assert redact("", secrets=[KEY]) == ""
    assert len(redact("a" * 500)) == 160
    assert contains_secret(f"a{KEY}", [KEY, ""]) and not contains_secret("a", [""])


def test_error_message_is_redacted_and_structured() -> None:
    error = RouterHttpError(f"/x HTTP 403: {KEY}", status_code=403, endpoint="/x",
                            retry_after=2.0, secrets=[KEY])
    assert KEY not in str(error) and error.kind is ErrorKind.HTTP_STATUS
    assert error.to_dict() == {"kind": "http_status", "message": "/x HTTP 403: <redacted>",
                               "status_code": 403, "endpoint": "/x", "retry_after": 2.0}
    assert isinstance(RouterTimeoutError("t"), LlmClientError)


def test_traceback_of_client_error_contains_no_secret() -> None:
    try:
        try:
            raise ValueError(f"inner {KEY}")
        except ValueError:
            raise LlmClientError(f"outer {KEY}", secrets=[KEY]) from None
    except LlmClientError as error:
        rendered = "".join(traceback.format_exception(error))
    assert KEY not in rendered
