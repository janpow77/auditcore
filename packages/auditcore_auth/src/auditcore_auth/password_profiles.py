"""Named password hashing profiles and hash-format recognition (stdlib only).

Profiles describe *how new hashes are made*. Verification accepts every
format the applications ever stored (bcrypt ``$2a$``/``$2b$``/``$2y$`` and
argon2 ``$argon2id$``/``$argon2i$``/``$argon2d$``) regardless of the profile,
so switching profiles never locks out existing users.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

from .errors import ConfigurationError

BCRYPT_MAX_BYTES = 72

_BCRYPT_HASH = re.compile(r"\$(2[aby])\$(\d\d)\$[./A-Za-z0-9]{53}")
_ARGON2_HASH = re.compile(
    r"\$argon2(id|i|d)\$v=\d+\$m=\d+,t=\d+,p=\d+\$[A-Za-z0-9+/]+={0,2}\$[A-Za-z0-9+/]+={0,2}"
)


class HashScheme(StrEnum):
    """Hash families the library can produce and verify."""

    BCRYPT = "bcrypt"
    ARGON2 = "argon2"


@dataclass(frozen=True)
class Argon2Parameters:
    """argon2 cost parameters; the defaults equal argon2-cffi's RFC 9106 low-memory profile.

    passlib 1.7.4 delegates to argon2-cffi, so versteigerung's stored hashes use
    exactly these values (``m=65536,t=3,p=4``, 16-byte salt, 32-byte digest).
    """

    time_cost: int = 3
    memory_cost: int = 65536
    parallelism: int = 4
    hash_len: int = 32
    salt_len: int = 16
    variant: str = "id"

    def __post_init__(self) -> None:
        if self.variant not in {"id", "i", "d"}:
            raise ConfigurationError(f"Unbekannte argon2-Variante: {self.variant}")
        if min(self.time_cost, self.parallelism) < 1 or self.memory_cost < 8 * self.parallelism:
            raise ConfigurationError("argon2-Parameter zu klein")
        if self.hash_len < 16 or self.salt_len < 16:
            raise ConfigurationError("argon2: Digest und Salt brauchen mindestens 16 Byte")


@dataclass(frozen=True)
class PasswordProfile:
    """How new password hashes are created.

    ``truncate_to_72_bytes`` reproduces the historical bcrypt behaviour (bcrypt
    < 5 and passlib silently used only the first 72 bytes). With it, hashes and
    verification stay compatible with stored hashes and work unchanged under
    bcrypt 5, which raises for longer input.

    ``reject_nul`` reproduces passlib, which refuses passwords containing NUL.
    """

    name: str
    scheme: HashScheme
    bcrypt_rounds: int = 12
    bcrypt_ident: str = "2b"
    truncate_to_72_bytes: bool = True
    reject_nul: bool = False
    argon2: Argon2Parameters = field(default_factory=Argon2Parameters)

    def __post_init__(self) -> None:
        if not 4 <= self.bcrypt_rounds <= 31:
            raise ConfigurationError("bcrypt-Kostenfaktor muss zwischen 4 und 31 liegen")
        if self.bcrypt_ident not in {"2a", "2b"}:
            raise ConfigurationError("bcrypt-Kennung muss 2a oder 2b sein")


BCRYPT = PasswordProfile("bcrypt", HashScheme.BCRYPT)
"""bcrypt called directly (regulierung, flowinvoice, audit-portal, flowsearch)."""

BCRYPT_PASSLIB = PasswordProfile("bcrypt-passlib", HashScheme.BCRYPT, reject_nul=True)
"""bcrypt as passlib's ``CryptContext(schemes=["bcrypt"])`` produced it
(audit_designer, flownavigator, qaaudit, flowlib): same ``$2b$12$`` format,
NUL bytes refused."""

ARGON2ID = PasswordProfile("argon2id", HashScheme.ARGON2)
"""argon2id with argon2-cffi defaults; also passlib's ``argon2`` scheme (versteigerung).
Recommended for new applications."""

PASSWORD_PROFILES: dict[str, PasswordProfile] = {
    profile.name: profile for profile in (BCRYPT, BCRYPT_PASSLIB, ARGON2ID)
}


@dataclass(frozen=True)
class HashInfo:
    """What a stored hash string declares about itself."""

    scheme: HashScheme
    variant: str
    bcrypt_rounds: int | None = None


def identify_hash(stored: str | None) -> HashInfo | None:
    """Recognise a stored hash by its full syntax; ``None`` if it is not well-formed.

    The strict check matters: bcrypt 4.x aborts with a Rust panic (a
    ``BaseException``) on truncated ``$2b$`` strings.
    """
    if not isinstance(stored, str):
        return None
    bcrypt_match = _BCRYPT_HASH.fullmatch(stored)
    if bcrypt_match:
        rounds = int(bcrypt_match.group(2))
        if not 4 <= rounds <= 31:
            return None
        return HashInfo(HashScheme.BCRYPT, bcrypt_match.group(1), rounds)
    argon2_match = _ARGON2_HASH.fullmatch(stored)
    if argon2_match:
        return HashInfo(HashScheme.ARGON2, argon2_match.group(1))
    return None


def password_profile(name: str) -> PasswordProfile:
    """Look up a named profile."""
    try:
        return PASSWORD_PROFILES[name]
    except KeyError:
        raise ConfigurationError(f"Unbekanntes Passwortprofil: {name}") from None
