"""Password hashing: profiles, rehash signal, 72-byte rule, malformed input, timing."""

from __future__ import annotations

import pytest
from conftest import FAST_BCRYPT

import auditcore_auth._hash_backends as backends
from auditcore_auth import (
    ARGON2ID,
    BCRYPT,
    BCRYPT_PASSLIB,
    Argon2Parameters,
    ConfigurationError,
    HashScheme,
    PasswordHasher,
    PasswordPolicyError,
    PasswordProfile,
    identify_hash,
    password_profile,
)

FAST_ARGON = PasswordProfile("fast-argon", HashScheme.ARGON2,
                             argon2=Argon2Parameters(time_cost=1, memory_cost=1024, parallelism=1))


def test_named_profiles() -> None:
    assert password_profile("argon2id") is ARGON2ID
    assert password_profile("bcrypt") is BCRYPT
    assert password_profile("bcrypt-passlib") is BCRYPT_PASSLIB
    with pytest.raises(ConfigurationError):
        password_profile("md5")


@pytest.mark.parametrize("profile", [FAST_BCRYPT, FAST_ARGON])
def test_hash_and_verify_roundtrip(profile: PasswordProfile) -> None:
    hasher = PasswordHasher(profile)
    stored = hasher.hash("Prüfbehörde-2026")
    assert stored != hasher.hash("Prüfbehörde-2026")  # salted
    assert hasher.verify("Prüfbehörde-2026", stored)
    assert not hasher.verify("Prüfbehörde-2027", stored)
    assert identify_hash(stored).scheme is profile.scheme  # type: ignore[union-attr]


def test_bcrypt_long_passwords_use_the_first_72_bytes_even_with_bcrypt_5() -> None:
    hasher = PasswordHasher(FAST_BCRYPT)
    stored = hasher.hash("x" * 100)
    assert hasher.verify("x" * 72, stored)
    assert hasher.verify("x" * 72 + "anything", stored)
    assert not hasher.verify("x" * 71, stored)


def test_bcrypt_without_truncation_refuses_long_passwords() -> None:
    strict = PasswordProfile("strict", HashScheme.BCRYPT, bcrypt_rounds=4,
                             truncate_to_72_bytes=False)
    with pytest.raises(PasswordPolicyError):
        PasswordHasher(strict).hash("ä" * 37)
    assert PasswordHasher(strict).hash("ä" * 36)


def test_argon2_has_no_length_limit() -> None:
    hasher = PasswordHasher(FAST_ARGON)
    stored = hasher.hash("x" * 100)
    assert not hasher.verify("x" * 72, stored)


def test_passlib_profile_refuses_nul_bytes() -> None:
    fast_passlib = PasswordProfile("p", HashScheme.BCRYPT, bcrypt_rounds=4, reject_nul=True)
    with pytest.raises(PasswordPolicyError):
        PasswordHasher(fast_passlib).hash("a\x00b")
    stored = PasswordHasher(FAST_BCRYPT).hash("a\x00b")
    assert PasswordHasher(fast_passlib).verify("a\x00b", stored)  # verifying never raises
    assert not PasswordHasher(fast_passlib).verify("a\x00c", stored)


@pytest.mark.parametrize("stored", [
    None, "", "garbage", "$2b$12$short", "$2b$03$" + "a" * 53, "$2x$12$" + "a" * 53,
    "$argon2id$v=19$m=65536,t=3,p=4$abc", "$argon2id$v=19$m=65536,t=3,p=4$$",
    "$1$md5$crypt", "plaintext-password",
])
def test_malformed_or_unknown_hashes_are_false(stored: str | None) -> None:
    assert PasswordHasher(FAST_BCRYPT).verify("geheim", stored) is False
    assert PasswordHasher(FAST_BCRYPT).check("geheim", stored).valid is False


def test_truncated_bcrypt_hash_never_reaches_the_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """bcrypt 4.x panics (BaseException) on '$2b$12$short'; the syntax check prevents that."""
    seen: list[str] = []
    original = backends.bcrypt_verify
    monkeypatch.setattr(backends, "bcrypt_verify",
                        lambda secret, stored: seen.append(stored) or original(secret, stored))
    hasher = PasswordHasher(FAST_BCRYPT)
    assert hasher.verify("pw", "$2b$12$short") is False
    assert "$2b$12$short" not in seen


def test_missing_account_costs_a_real_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    original = backends.bcrypt_verify
    monkeypatch.setattr(backends, "bcrypt_verify",
                        lambda secret, stored: calls.append(stored) or original(secret, stored))
    hasher = PasswordHasher(FAST_BCRYPT)
    assert hasher.verify("geheim", None) is False
    assert hasher.verify("geheim", "kein-hash") is False
    assert len(calls) == 2 and identify_hash(calls[0]) is not None


def test_rehash_signal() -> None:
    old_bcrypt = PasswordHasher(FAST_BCRYPT).hash("pw")
    stronger = PasswordProfile("strong", HashScheme.BCRYPT, bcrypt_rounds=5)
    assert PasswordHasher(stronger).check("pw", old_bcrypt).needs_rehash
    assert not PasswordHasher(FAST_BCRYPT).check("pw", old_bcrypt).needs_rehash
    migrate = PasswordHasher(FAST_ARGON)
    check = migrate.check("pw", old_bcrypt)
    assert check.valid and check.needs_rehash and check.scheme is HashScheme.BCRYPT
    assert not migrate.check("wrong", old_bcrypt).needs_rehash
    valid, new_hash = migrate.verify_and_update("pw", old_bcrypt)
    assert valid and new_hash and identify_hash(new_hash).scheme is HashScheme.ARGON2  # type: ignore[union-attr]
    assert migrate.verify_and_update("pw", new_hash) == (True, None)
    assert migrate.verify_and_update("wrong", new_hash) == (False, None)


def test_argon2_parameter_change_signals_rehash() -> None:
    stored = PasswordHasher(FAST_ARGON).hash("pw")
    assert not PasswordHasher(FAST_ARGON).needs_rehash(stored)
    tuned = PasswordProfile("tuned", HashScheme.ARGON2,
                            argon2=Argon2Parameters(time_cost=2, memory_cost=1024, parallelism=1))
    assert PasswordHasher(tuned).needs_rehash(stored)
    assert PasswordHasher(tuned).verify("pw", stored)
    assert PasswordHasher(tuned).needs_rehash("kaputt")


def test_argon2i_and_2y_bcrypt_are_recognised() -> None:
    assert identify_hash("$2y$10$" + "a" * 53).variant == "2y"  # type: ignore[union-attr]
    stored = PasswordHasher(PasswordProfile(
        "i", HashScheme.ARGON2, argon2=Argon2Parameters(1, 1024, 1, variant="i"))).hash("pw")
    assert stored.startswith("$argon2i$")
    assert PasswordHasher(FAST_BCRYPT).verify("pw", stored)


@pytest.mark.parametrize("kwargs", [
    {"bcrypt_rounds": 3}, {"bcrypt_rounds": 32}, {"bcrypt_ident": "2y"},
])
def test_invalid_bcrypt_profiles(kwargs: dict[str, object]) -> None:
    with pytest.raises(ConfigurationError):
        PasswordProfile("bad", HashScheme.BCRYPT, **kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("kwargs", [
    {"variant": "x"}, {"time_cost": 0}, {"memory_cost": 4}, {"hash_len": 8}, {"salt_len": 8},
])
def test_invalid_argon2_parameters(kwargs: dict[str, object]) -> None:
    with pytest.raises(ConfigurationError):
        Argon2Parameters(**kwargs)  # type: ignore[arg-type]


def test_password_must_be_text() -> None:
    with pytest.raises(TypeError):
        PasswordHasher(FAST_BCRYPT).hash(b"bytes")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        PasswordHasher(FAST_BCRYPT).verify(None, "x")  # type: ignore[arg-type]
