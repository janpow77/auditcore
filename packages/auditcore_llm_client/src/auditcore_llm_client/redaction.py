"""Remove secrets from any text that leaves the client (messages, logs, health).

Starting point is the flowinvoice variant (``_redact_error_message``); the
patterns of audit_designer are a subset. Added: the configured secret values
themselves, URL credentials, ``Authorization`` headers and key/token query
parameters. The rule applies to every exception, log line and health record of
this library.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

#: Default length of cached health messages (flowinvoice/audit_designer: 160).
HEALTH_MESSAGE_LENGTH = 160
#: Default length of exception messages.
ERROR_MESSAGE_LENGTH = 300
#: Replacement for configured secret values.
SECRET_PLACEHOLDER = "<redacted>"

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)authorization\s*[:=]\s*\S+(\s+\S+)?"), "Authorization=<redacted>"),
    (re.compile(r"(?i)x-api-key\s*[:=]\s*\S+"), "X-Api-Key=<redacted>"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer <token>"),
    (re.compile(r"postgresql(\+[a-z]+)?://[^\s'\"]+"), "<dsn>"),
    (re.compile(r"postgres://[^\s'\"]+"), "<dsn>"),
    (re.compile(r"rediss?://[^\s'\"]+"), "<dsn>"),
    (re.compile(r"https?://[^\s'\"]+"), "<url>"),
    (re.compile(r"sk-[A-Za-z0-9_-]+"), "<api-key>"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]+"), "<github-token>"),
    (
        re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|token|secret|password)=[^\s&'\"]+"),
        r"\1=<redacted>",
    ),
)


def _replace_secrets(text: str, secrets: Iterable[str]) -> str:
    for secret in sorted({s for s in secrets if s}, key=len, reverse=True):
        text = text.replace(secret, SECRET_PLACEHOLDER)
    return text


def redact(
    text: str,
    *,
    secrets: Iterable[str] = (),
    max_len: int | None = HEALTH_MESSAGE_LENGTH,
) -> str:
    """Return ``text`` without secrets, URLs, DSNs and tokens, truncated to ``max_len``.

    Configured secret values are removed first and in full (before truncation),
    so a key can never survive half-cut at the end of the message.
    """
    if not text:
        return ""
    text = _replace_secrets(text, secrets)
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text if max_len is None else text[:max_len]


def contains_secret(text: str, secrets: Iterable[str]) -> bool:
    """True if one of the non-empty ``secrets`` occurs in ``text`` (test helper)."""
    return any(secret and secret in text for secret in secrets)
