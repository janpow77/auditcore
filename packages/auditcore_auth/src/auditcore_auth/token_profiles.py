"""JWT profiles: algorithm allowlist, claim layout, required claims, lifetime, leeway.

A profile fixes everything that decides whether a token issued today is
accepted tomorrow. Compatibility profiles in :mod:`auditcore_auth.compat`
reproduce the applications' historical tokens byte for byte.

``layout`` lists the claim order of the payload. ``sub``, ``exp``, ``iat``,
``nbf`` and fixed claims are placed where they are listed; any other listed
name is taken from the caller's claims; ``"*"`` stands for the remaining
caller claims in their given order. A profile without ``"*"`` accepts no
additional claims.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta

from .errors import ConfigurationError

HMAC_ALGORITHMS = frozenset({"HS256", "HS384", "HS512"})
ASYMMETRIC_ALGORITHMS = frozenset({
    "RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384", "ES512", "EdDSA",
})
TIME_CLAIMS = frozenset({"exp", "iat", "nbf"})
EXTRA_SLOT = "*"


@dataclass(frozen=True)
class TokenProfile:
    """Issuing and verification rules for one kind of token."""

    name: str
    lifetime: timedelta
    algorithm: str = "HS256"
    accepted_algorithms: tuple[str, ...] = ()
    layout: tuple[str, ...] = ("sub", EXTRA_SLOT, "iat", "exp")
    fixed_claims: tuple[tuple[str, str], ...] = ()
    required_claims: tuple[str, ...] = ("exp", "iat", "sub")
    leeway: timedelta = timedelta(0)
    reject_future_iat: bool = True
    type_claim: str = "type"
    rejected_types: tuple[str, ...] = ()
    min_key_bytes: int = 32
    max_token_bytes: int = 8192

    def __post_init__(self) -> None:
        _check_algorithms(self.algorithm, self.allowed_algorithms)
        _check_layout(self)
        if self.lifetime <= timedelta(0):
            raise ConfigurationError("Die Laufzeit muss positiv sein")
        if self.leeway < timedelta(0):
            raise ConfigurationError("Die Toleranz (leeway) darf nicht negativ sein")
        if self.min_key_bytes < 0 or self.max_token_bytes < 64:
            raise ConfigurationError("Ungültige Schlüssel- oder Tokengrenze")

    @property
    def allowed_algorithms(self) -> tuple[str, ...]:
        """Algorithms accepted on verification (the allowlist)."""
        return self.accepted_algorithms or (self.algorithm,)

    @property
    def uses_hmac(self) -> bool:
        return self.algorithm in HMAC_ALGORITHMS

    @property
    def fixed(self) -> dict[str, str]:
        return dict(self.fixed_claims)

    def with_lifetime(self, lifetime: timedelta) -> TokenProfile:
        """Same profile with another default lifetime (e.g. from app settings)."""
        return replace(self, lifetime=lifetime)


def _check_algorithms(algorithm: str, allowed: tuple[str, ...]) -> None:
    supported = HMAC_ALGORITHMS | ASYMMETRIC_ALGORITHMS
    for name in allowed:
        if name.lower() == "none" or name not in supported:
            raise ConfigurationError(f"Algorithmus nicht zulässig: {name}")
    if algorithm not in allowed:
        raise ConfigurationError("Der Ausstellungsalgorithmus fehlt in der Allowlist")
    families = {name in HMAC_ALGORITHMS for name in allowed}
    if len(families) != 1:
        # Mixing HMAC and public-key algorithms enables key-confusion attacks.
        raise ConfigurationError("HMAC- und Public-Key-Algorithmen nicht mischen")


def _check_layout(profile: TokenProfile) -> None:
    layout = profile.layout
    if len(set(layout)) != len(layout):
        raise ConfigurationError("Claim-Reihenfolge enthält Doppelungen")
    if "exp" not in layout or "exp" not in profile.required_claims:
        raise ConfigurationError("Jedes Token braucht einen Ablauf (exp)")
    for claim in profile.required_claims:
        if claim in TIME_CLAIMS and claim not in layout:
            raise ConfigurationError(f"Pflicht-Claim {claim} wird nie ausgestellt")
    for name, _value in profile.fixed_claims:
        if name not in layout or name in TIME_CLAIMS or name == "sub":
            raise ConfigurationError(f"Fester Claim {name} ist nicht zulässig")


DEFAULT_TOKEN_PROFILE = TokenProfile("default", lifetime=timedelta(minutes=30))
"""Recommended for new code: HS256 only, exp/iat/sub required, 30 minutes, no leeway."""
