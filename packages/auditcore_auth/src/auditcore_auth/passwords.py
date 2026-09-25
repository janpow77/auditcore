"""Password hashing and verification with named profiles.

``PasswordHasher(profile).verify`` accepts every stored format of the nine
applications. ``check`` additionally signals whether a successful login
should re-hash the password under the current profile (rehash on login).
"""

from __future__ import annotations

from dataclasses import dataclass

from . import _hash_backends as backends
from .errors import PasswordPolicyError
from .password_profiles import (
    ARGON2ID,
    BCRYPT_MAX_BYTES,
    HashInfo,
    HashScheme,
    PasswordProfile,
    identify_hash,
)

_DUMMY_PASSWORD = "auditcore-auth: kein Konto"


@dataclass(frozen=True)
class PasswordCheck:
    """Result of :meth:`PasswordHasher.check`."""

    valid: bool
    needs_rehash: bool
    scheme: HashScheme | None


class PasswordHasher:
    """Hash new passwords under one profile; verify hashes of any known format."""

    def __init__(self, profile: PasswordProfile = ARGON2ID) -> None:
        self._profile = profile
        self._dummy: str | None = None

    @property
    def profile(self) -> PasswordProfile:
        return self._profile

    def hash(self, password: str) -> str:
        """Create a new salted hash under the profile."""
        _require_text(password)
        profile = self._profile
        if profile.reject_nul and "\x00" in password:
            raise PasswordPolicyError("Passwörter mit NUL-Zeichen sind nicht zulässig")
        if profile.scheme is HashScheme.ARGON2:
            return backends.argon2_hash(password, profile.argon2)
        secret = password.encode("utf-8")
        if len(secret) > BCRYPT_MAX_BYTES and not profile.truncate_to_72_bytes:
            raise PasswordPolicyError("bcrypt verarbeitet höchstens 72 Byte")
        return backends.bcrypt_hash(secret[:BCRYPT_MAX_BYTES], profile.bcrypt_rounds,
                                    profile.bcrypt_ident)

    def verify(self, password: str, stored: str | None) -> bool:
        """Verify ``password`` against a stored hash of any supported format.

        Unknown, malformed or missing hashes yield ``False`` after a dummy
        verification of the same cost, so a missing account is not faster to
        reject than a wrong password.
        """
        _require_text(password)
        info = identify_hash(stored)
        if info is None or stored is None:
            self._verify_known(password, self._dummy_hash(), identify_hash(self._dummy_hash()))
            return False
        return self._verify_known(password, stored, info)

    def check(self, password: str, stored: str | None) -> PasswordCheck:
        """Verify and report whether the stored hash should be replaced."""
        valid = self.verify(password, stored)
        info = identify_hash(stored)
        return PasswordCheck(
            valid=valid,
            needs_rehash=valid and stored is not None and self.needs_rehash(stored),
            scheme=info.scheme if info else None,
        )

    def verify_and_update(self, password: str, stored: str | None) -> tuple[bool, str | None]:
        """passlib-style helper: ``(valid, new_hash_or_None)``."""
        result = self.check(password, stored)
        if result.valid and result.needs_rehash:
            return True, self.hash(password)
        return result.valid, None

    def needs_rehash(self, stored: str) -> bool:
        """True if ``stored`` is not in the profile's scheme or uses weaker parameters."""
        info = identify_hash(stored)
        profile = self._profile
        if info is None or info.scheme is not profile.scheme:
            return True
        if info.scheme is HashScheme.BCRYPT:
            return (info.bcrypt_rounds or 0) < profile.bcrypt_rounds
        return backends.argon2_needs_rehash(stored, profile.argon2)

    def _verify_known(self, password: str, stored: str, info: HashInfo | None) -> bool:
        if info is not None and info.scheme is HashScheme.ARGON2:
            return backends.argon2_verify(password, stored, self._profile.argon2)
        secret = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
        return backends.bcrypt_verify(secret, stored)

    def _dummy_hash(self) -> str:
        if self._dummy is None:
            self._dummy = self.hash(_DUMMY_PASSWORD)
        return self._dummy


def _require_text(password: object) -> None:
    if not isinstance(password, str):
        raise TypeError("Passwort muss ein str sein")
