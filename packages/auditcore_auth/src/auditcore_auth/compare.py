"""Constant-time comparison for secrets such as CSRF tokens or API keys."""

from __future__ import annotations

import hmac


def constant_time_equals(left: str | bytes, right: str | bytes) -> bool:
    """Compare two secrets without leaking the position of the first difference.

    ``str`` values are compared as UTF-8 (``hmac.compare_digest`` rejects
    non-ASCII ``str``). Differing lengths return ``False``.
    """
    return hmac.compare_digest(_as_bytes(left), _as_bytes(right))


def _as_bytes(value: str | bytes) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, bytes):
        return value
    raise TypeError("Nur str oder bytes vergleichbar")
