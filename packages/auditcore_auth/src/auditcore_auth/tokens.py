"""Issue and verify JWTs under a :class:`TokenProfile` (PyJWT backend)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from types import MappingProxyType

from . import _jwt_backend as backend
from ._claims import build_payload, check_claims
from .clock import Clock, from_epoch, require_aware, system_clock
from .errors import ConfigurationError, DisallowedAlgorithmError, MalformedTokenError, TokenError
from .token_profiles import TokenProfile

Key = str | bytes


@dataclass(frozen=True)
class IssuedToken:
    """A freshly signed token and its validity window."""

    token: str
    issued_at: datetime
    expires_at: datetime

    @property
    def expires_in(self) -> int:
        """Lifetime in whole seconds (``expires_in`` of OAuth2 token responses)."""
        return int((self.expires_at - self.issued_at).total_seconds())


@dataclass(frozen=True)
class VerifiedToken:
    """Claims of a token whose signature, algorithm and time window were checked."""

    claims: Mapping[str, object]
    algorithm: str

    @property
    def subject(self) -> str | None:
        value = self.claims.get("sub")
        return value if isinstance(value, str) else None

    @property
    def expires_at(self) -> datetime | None:
        return _instant(self.claims.get("exp"))

    @property
    def issued_at(self) -> datetime | None:
        return _instant(self.claims.get("iat"))

    def as_dict(self) -> dict[str, object]:
        return dict(self.claims)


def _instant(value: object) -> datetime | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return from_epoch(value)
    return None


def _check_key(profile: TokenProfile, key: Key) -> None:
    if not isinstance(key, str | bytes) or not key:
        raise ConfigurationError("Ein nicht leerer Schlüssel ist erforderlich")
    size = len(key.encode("utf-8") if isinstance(key, str) else key)
    if profile.uses_hmac and size < profile.min_key_bytes:
        raise ConfigurationError(
            f"HMAC-Schlüssel zu kurz: {size} Byte, Profil {profile.name} verlangt "
            f"mindestens {profile.min_key_bytes}"
        )


class TokenIssuer:
    """Sign tokens; the payload order follows ``profile.layout``."""

    def __init__(self, profile: TokenProfile, key: Key, *, clock: Clock = system_clock,
                 key_id: str | None = None) -> None:
        _check_key(profile, key)
        self._profile = profile
        self._key = key
        self._clock = clock
        self._headers = {"kid": key_id} if key_id else None

    @property
    def profile(self) -> TokenProfile:
        return self._profile

    def issue(self, claims: Mapping[str, object] | None = None, *, subject: str | None = None,
              lifetime: timedelta | None = None) -> IssuedToken:
        """Sign ``claims`` (plus ``sub``) with ``exp``/``iat`` from the clock.

        ``exp``, ``iat``, ``nbf`` and the profile's fixed claims cannot be
        supplied by the caller.
        """
        duration = self._profile.lifetime if lifetime is None else lifetime
        if duration <= timedelta(0):
            raise ValueError("Die Laufzeit muss positiv sein")
        now = require_aware(self._clock())
        payload = build_payload(self._profile, claims, subject, now, duration)
        token = backend.encode(payload, self._key, self._profile.algorithm, self._headers)
        issued = from_epoch(now.timestamp() // 1)
        return IssuedToken(token, issued_at=issued, expires_at=issued + duration)


class TokenVerifier:
    """Verify tokens: allowlisted algorithm, signature, required claims, time window."""

    def __init__(self, profile: TokenProfile, key: Key, *, clock: Clock = system_clock) -> None:
        _check_key(profile, key)
        self._profile = profile
        self._key = key
        self._clock = clock

    @property
    def profile(self) -> TokenProfile:
        return self._profile

    def verify(self, token: str, *, expected_type: str | None = None) -> VerifiedToken:
        """Return the verified claims or raise a :class:`~auditcore_auth.errors.TokenError`."""
        profile = self._profile
        if not isinstance(token, str) or not token or len(token) > profile.max_token_bytes:
            raise MalformedTokenError("Token fehlt oder ist zu lang")
        algorithm = backend.unverified_algorithm(token)
        if algorithm not in profile.allowed_algorithms:
            raise DisallowedAlgorithmError(f"Algorithmus {algorithm!r} nicht zugelassen")
        claims = backend.decode(token, self._key, profile.allowed_algorithms,
                                profile.required_claims)
        check_claims(claims, profile, require_aware(self._clock()), expected_type)
        return VerifiedToken(MappingProxyType(claims), algorithm)

    def verify_or_none(self, token: str | None, *,
                       expected_type: str | None = None) -> VerifiedToken | None:
        """Like :meth:`verify` but ``None`` for any rejected token (legacy ``decode_token``)."""
        if token is None:
            return None
        try:
            return self.verify(token, expected_type=expected_type)
        except TokenError:
            return None
