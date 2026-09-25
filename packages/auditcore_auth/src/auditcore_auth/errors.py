"""Error contract of auditcore_auth.

Token errors carry a stable ``reason`` for logs and metrics. The message is
meant for operators; HTTP responses should not echo it to clients.
"""

from __future__ import annotations


class AuthError(Exception):
    """Base class of every error raised by auditcore_auth."""


class ConfigurationError(AuthError, ValueError):
    """A profile, key or parameter is unusable or unsafe."""


class BackendUnavailableError(AuthError, ImportError):
    """An optional backend (bcrypt, argon2-cffi, PyJWT, FastAPI) is not installed."""

    def __init__(self, backend: str, extra: str) -> None:
        super().__init__(
            f"{backend} ist nicht installiert; auditcore_auth[{extra}] installieren"
        )
        self.backend = backend
        self.extra = extra


class PasswordPolicyError(AuthError, ValueError):
    """The password cannot be hashed under the selected profile."""


class TokenError(AuthError):
    """A token was rejected; ``reason`` is a stable machine-readable code."""

    reason = "invalid"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.reason)


class MalformedTokenError(TokenError):
    reason = "malformed"


class InvalidSignatureError(TokenError):
    reason = "signature"


class DisallowedAlgorithmError(TokenError):
    reason = "algorithm"


class ExpiredTokenError(TokenError):
    reason = "expired"


class ImmatureTokenError(TokenError):
    reason = "not_yet_valid"


class MissingClaimError(TokenError):
    reason = "missing_claim"

    def __init__(self, claim: str) -> None:
        super().__init__(f"Pflicht-Claim fehlt: {claim}")
        self.claim = claim


class InvalidClaimError(TokenError):
    reason = "invalid_claim"

    def __init__(self, claim: str, message: str | None = None) -> None:
        super().__init__(message or f"Claim ungültig: {claim}")
        self.claim = claim


class TokenTypeError(TokenError):
    reason = "token_type"
