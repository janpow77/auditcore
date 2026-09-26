"""Payload layout for issuing and claim checks for verification (no cryptography)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta

from .clock import to_epoch
from .errors import (
    ExpiredTokenError,
    ImmatureTokenError,
    InvalidClaimError,
    MissingClaimError,
    TokenTypeError,
)
from .token_profiles import EXTRA_SLOT, TIME_CLAIMS, TokenProfile


def build_payload(profile: TokenProfile, claims: Mapping[str, object] | None,
                  subject: str | None, now: datetime, lifetime: timedelta) -> dict[str, object]:
    """Place caller claims, fixed claims and time claims in the profile's order."""
    caller = _caller_claims(profile, claims, subject)
    named = set(profile.layout) - {EXTRA_SLOT}
    extras = {name: value for name, value in caller.items() if name not in named}
    if extras and EXTRA_SLOT not in profile.layout:
        raise ValueError(f"Profil {profile.name} erlaubt keine weiteren Claims: {sorted(extras)}")
    timing: dict[str, object] = {"exp": to_epoch(now + lifetime), "iat": to_epoch(now),
                                 "nbf": to_epoch(now)}
    fixed = profile.fixed
    payload: dict[str, object] = {}
    for slot in profile.layout:
        if slot == EXTRA_SLOT:
            payload.update(extras)
        elif slot in TIME_CLAIMS:
            payload[slot] = timing[slot]
        elif slot in fixed:
            payload[slot] = fixed[slot]
        elif slot in caller:
            payload[slot] = caller[slot]
    return payload


def _caller_claims(profile: TokenProfile, claims: Mapping[str, object] | None,
                   subject: str | None) -> dict[str, object]:
    caller = dict(claims or {})
    if subject is not None:
        if "sub" in caller:
            raise ValueError("sub doppelt angegeben (subject und claims)")
        caller = {"sub": subject, **caller}
    reserved = (TIME_CLAIMS | set(profile.fixed)) & set(caller)
    if reserved:
        raise ValueError(f"Claims werden von der Bibliothek gesetzt: {sorted(reserved)}")
    sub = caller.get("sub")
    if sub is not None and not isinstance(sub, str):
        raise ValueError("sub muss ein String sein")
    if "sub" in profile.required_claims and not sub:
        raise ValueError(f"Profil {profile.name} verlangt ein sub")
    return caller


def check_claims(claims: Mapping[str, object], profile: TokenProfile, now: datetime,
                 expected_type: str | None) -> None:
    """Presence, time window, claim types and token type."""
    for claim in profile.required_claims:
        if claim not in claims:
            raise MissingClaimError(claim)
    current = now.timestamp()
    leeway = profile.leeway.total_seconds()
    expires = _numeric(claims, "exp")
    if expires is not None and expires <= current - leeway:
        raise ExpiredTokenError("Token ist abgelaufen")
    issued = _numeric(claims, "iat")
    if issued is not None and profile.reject_future_iat and issued > current + leeway:
        raise ImmatureTokenError("Ausstellungszeit liegt in der Zukunft")
    not_before = _numeric(claims, "nbf")
    if not_before is not None and not_before > current + leeway:
        raise ImmatureTokenError("Token ist noch nicht gültig")
    for name in ("sub", "jti"):
        if name in claims and not isinstance(claims[name], str):
            raise InvalidClaimError(name, f"{name} muss ein String sein")
    _check_type(claims, profile, expected_type)


def _numeric(claims: Mapping[str, object], name: str) -> float | None:
    if name not in claims:
        return None
    value = claims[name]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidClaimError(name, f"{name} muss eine Zahl sein")
    return float(value)


def _check_type(claims: Mapping[str, object], profile: TokenProfile,
                expected_type: str | None) -> None:
    token_type = claims.get(profile.type_claim)
    if token_type is not None and token_type in profile.rejected_types:
        raise TokenTypeError(f"Tokentyp {token_type!r} ist hier nicht zulässig")
    if expected_type is not None and token_type != expected_type:
        raise TokenTypeError(f"Tokentyp {expected_type!r} erwartet")
