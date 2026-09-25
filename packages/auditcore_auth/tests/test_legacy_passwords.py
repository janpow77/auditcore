"""Stored hashes of all nine applications verify exactly as in the old code.

Fixture: ``tests/fixtures/legacy_auth_observed.json`` – produced by
``tools/capture_legacy_auth.py`` executing each app's ``core/security.py`` at
the pinned commit with passlib 1.7.4 / bcrypt 4.2.1 / argon2-cffi 23.1.0.
"""

from __future__ import annotations

from typing import Any

import pytest
from conftest import observed, observed_app

from auditcore_auth import APP_PROFILES, PasswordHasher, PasswordPolicyError, identify_hash

APPS = sorted(APP_PROFILES)


def cases(app: str) -> list[dict[str, Any]]:
    passwords = observed_app(app)["passwords"]
    assert isinstance(passwords, dict)
    return list(passwords["cases"])


def test_fixture_covers_all_nine_apps() -> None:
    assert sorted(observed()["apps"]) == APPS  # type: ignore[call-overload]
    assert len(APPS) == 9


@pytest.mark.parametrize("app", APPS)
def test_legacy_hashes_verify_identically(app: str) -> None:
    hasher = PasswordHasher(APP_PROFILES[app].password)
    for case in cases(app):
        stored = case["hash"].get("result")
        if stored is None:
            continue
        password = case["password"]
        assert hasher.verify(password, stored) is case["verify_same"]["result"] is True
        assert hasher.verify("falsch", stored) is case["verify_wrong"]["result"] is False
        prefix = password.encode()[:72].decode(errors="ignore")
        if prefix != password:
            assert hasher.verify(prefix, stored) is case["verify_prefix72"]["result"]


@pytest.mark.parametrize("app", APPS)
def test_nul_passwords_follow_the_profile(app: str) -> None:
    profile = APP_PROFILES[app].password
    nul_case = next(c for c in cases(app) if c["password"] == "a\x00b")
    if "error" in nul_case["hash"]:  # passlib: PasswordValueError
        assert nul_case["hash"]["error"] == "PasswordValueError"
        assert profile.reject_nul
        with pytest.raises(PasswordPolicyError):
            PasswordHasher(profile).hash("a\x00b")
    else:
        assert not profile.reject_nul


@pytest.mark.parametrize("app", APPS)
def test_new_hashes_keep_the_legacy_format(app: str) -> None:
    profile = APP_PROFILES[app].password
    legacy = next(c["hash"]["result"] for c in cases(app) if c["password"] == "geheim123")
    legacy_info, new_info = identify_hash(legacy), identify_hash(
        PasswordHasher(profile).hash("geheim123"))
    assert legacy_info == new_info
    assert legacy[:7] == PasswordHasher(profile).hash("x")[:7]
    assert PasswordHasher(profile).needs_rehash(legacy) is False


def test_any_profile_verifies_every_app_format() -> None:
    """Switching an app to argon2id (or back) never locks out stored users."""
    stored = {app: next(c["hash"]["result"] for c in cases(app) if c["password"] == "geheim123")
              for app in APPS}
    for profile in {p.password for p in APP_PROFILES.values()}:
        hasher = PasswordHasher(profile)
        for value in {stored["regulierung"], stored["versteigerung"], stored["qaaudit"]}:
            check = hasher.check("geheim123", value)
            assert check.valid
            assert check.needs_rehash is (identify_hash(value).scheme is not profile.scheme)  # type: ignore[union-attr]


@pytest.mark.parametrize("app", APPS)
def test_malformed_hashes_are_false_instead_of_errors(app: str) -> None:
    """Deviation D4: the old code raised (ValueError, UnknownHashError, bcrypt panic)."""
    hasher = PasswordHasher(APP_PROFILES[app].password)
    malformed = observed_app(app)["passwords"]["malformed"]  # type: ignore[index]
    for case in malformed:
        assert hasher.verify("geheim123", case["hash"]) is False
        legacy = case["verify"]
        assert legacy.get("result", False) is False
