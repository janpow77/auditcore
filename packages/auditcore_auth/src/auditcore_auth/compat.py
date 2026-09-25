"""Compatibility profiles of the nine applications (characterised, see docs/app-profiles.md).

Each :class:`AppProfile` reproduces what the application's ``core/security.py``
did at the pinned commit: password scheme, token algorithm, claim order,
default lifetime and the claims its consumers relied on. Tokens issued by the
old code stay valid, and the library issues byte-identical tokens for the same
inputs and instant.

Deliberate tightening compared with the old code (all apps): a token without
``exp`` is rejected, reserved claims cannot be overridden by the caller, and
malformed stored hashes yield ``False`` instead of an exception.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from .errors import ConfigurationError
from .password_profiles import ARGON2ID, BCRYPT, BCRYPT_PASSLIB, PasswordProfile
from .token_profiles import EXTRA_SLOT, TokenProfile


@dataclass(frozen=True)
class AppProfile:
    """Password and token profiles of one application."""

    app: str
    source: str
    password: PasswordProfile
    tokens: dict[str, TokenProfile] = field(default_factory=dict)

    def token(self, kind: str = "access") -> TokenProfile:
        try:
            return self.tokens[kind]
        except KeyError:
            raise ConfigurationError(f"{self.app} kennt kein Token {kind!r}") from None


def _legacy(name: str, lifetime: timedelta, layout: tuple[str, ...],
            required: tuple[str, ...], *, jose: bool = True,
            fixed: tuple[tuple[str, str], ...] = (),
            rejected_types: tuple[str, ...] = ()) -> TokenProfile:
    """Legacy profile: HS256, no leeway, no key-length floor.

    python-jose never rejected an ``iat`` in the future, PyJWT does; the flag
    keeps each application's behaviour.
    """
    return TokenProfile(
        name, lifetime=lifetime, layout=layout, required_claims=required,
        fixed_claims=fixed, rejected_types=rejected_types,
        reject_future_iat=not jose, min_key_bytes=0,
    )


_H = timedelta(hours=1)
_ALL = EXTRA_SLOT

APP_PROFILES: dict[str, AppProfile] = {
    "audit_designer": AppProfile(
        "audit_designer", "backend/app/core/security.py@ccd65245", BCRYPT_PASSLIB,
        # Capability tokens (vpai_notebook/jupyter.py) carry no sub.
        {"access": _legacy("audit_designer", 12 * _H, (_ALL, "exp", "iat"), ("exp", "iat"))},
    ),
    "flownavigator": AppProfile(
        "flownavigator", "apps/backend/app/core/security.py@9dff858d", BCRYPT_PASSLIB,
        {"access": _legacy("flownavigator", 24 * _H, (_ALL, "exp"), ("exp", "sub"))},
    ),
    "flowsearch": AppProfile(
        "flowsearch", "backend/app/core/security.py@9ac5e0dd", BCRYPT,
        {"access": _legacy("flowsearch", timedelta(minutes=30), (_ALL, "exp"), ("exp", "sub"))},
    ),
    "qaaudit": AppProfile(
        "qaaudit", "backend/app/core/security.py@c78be5c8", BCRYPT_PASSLIB,
        {"access": _legacy("qaaudit", 24 * _H, ("sub", "role", "iat", "exp", _ALL),
                           ("exp", "iat", "sub"))},
    ),
    "versteigerung": AppProfile(
        "versteigerung", "backend/app/core/security.py@729f9a10", ARGON2ID,
        {"access": _legacy("versteigerung", timedelta(minutes=30),
                           ("sub", "iat", "exp", "type", _ALL), ("exp", "iat", "sub"),
                           jose=False, fixed=(("type", "access"),))},
    ),
    "regulierung": AppProfile(
        "regulierung", "backend/app/core/security.py@ce76e48c", BCRYPT,
        {
            # 8 h Sachbearbeitung, 24 h Administration: the caller passes the lifetime.
            "access": _legacy("regulierung", 8 * _H, ("sub", "role", "exp", "iat"),
                              ("exp", "iat", "sub"), jose=False, rejected_types=("refresh",)),
            "refresh": _legacy("regulierung-refresh", timedelta(days=7),
                               ("sub", "role", "type", "exp", "iat"), ("exp", "iat", "sub"),
                               jose=False, fixed=(("type", "refresh"),)),
        },
    ),
    "flowinvoice": AppProfile(
        "flowinvoice", "backend/app/api/user_auth.py@5d5d8c5a", BCRYPT,
        {"access": _legacy("flowinvoice", 24 * _H, ("sub", "role", "exp", "iat"),
                           ("exp", "iat", "sub"))},
    ),
    "audit-portal": AppProfile(
        "audit-portal", "backend/app/api/user_auth.py@72cc4b1a", BCRYPT,
        {
            "access": _legacy("audit-portal", 24 * _H, ("sub", "role", "exp", "iat"),
                              ("exp", "iat", "sub")),
            # core/security.py create_access_token: SSE tickets with extra claims first.
            "ticket": _legacy("audit-portal-ticket", 8 * _H, (_ALL, "sub", "exp", "iat"),
                              ("exp", "iat", "sub")),
        },
    ),
    "flowlib": AppProfile(
        "flowlib", "python/flowlib/auth.py@aca2dc6a", BCRYPT_PASSLIB,
        {"access": _legacy("flowlib", 24 * _H, (_ALL, "exp", "iat"), ("exp", "iat"))},
    ),
}


def app_profile(app: str) -> AppProfile:
    """Compatibility profile of ``app`` (e.g. ``"regulierung"``)."""
    try:
        return APP_PROFILES[app]
    except KeyError:
        raise ConfigurationError(f"Kein Kompatibilitätsprofil für {app}") from None
