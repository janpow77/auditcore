"""Reverse direction, run live only where passlib and python-jose are installed.

The applications that are migrated later may keep old instances running next
to new ones: hashes and tokens made by the library must be accepted by the old
code. CI skips this module (the unmaintained libraries are no dev dependency);
run it in the capture environment of ``tools/capture_legacy_auth.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

passlib_context = pytest.importorskip("passlib.context")
jose_jwt = pytest.importorskip("jose.jwt")

from auditcore_auth import APP_PROFILES, PasswordHasher, TokenIssuer  # noqa: E402

KEY = "live-legacy-secret-0123456789abcdef"
SCHEMES = {"bcrypt": "bcrypt", "bcrypt-passlib": "bcrypt", "argon2id": "argon2"}


@pytest.mark.parametrize("app", sorted(APP_PROFILES))
def test_passlib_accepts_library_hashes(app: str) -> None:
    profile = APP_PROFILES[app].password
    context = passlib_context.CryptContext(schemes=[SCHEMES[profile.name]])
    for password in ("geheim123", "Prüfung-ÄÖÜß", "x" * 80):
        stored = PasswordHasher(profile).hash(password)
        assert context.verify(password, stored)
        assert not context.verify("falsch", stored)
        assert not context.needs_update(stored)


@pytest.mark.parametrize("app", sorted(APP_PROFILES))
def test_jose_accepts_library_tokens(app: str) -> None:
    profile = APP_PROFILES[app].token("access")
    now = datetime.now(UTC)
    token = TokenIssuer(profile, KEY, clock=lambda: now).issue(
        {"sub": "7", "role": "pruefer"} if "role" in profile.layout else {"sub": "7"},
        lifetime=timedelta(minutes=5),
    ).token
    claims = jose_jwt.decode(token, KEY, algorithms=["HS256"])
    assert claims["sub"] == "7"
    assert claims["exp"] - int(now.timestamp()) == 300
