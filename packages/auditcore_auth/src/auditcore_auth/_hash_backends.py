"""Thin adapters over bcrypt and argon2-cffi; both are imported lazily.

No cryptography is implemented here: hashing, salt generation and the
constant-time comparison are done by the established libraries.
"""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import TYPE_CHECKING

from .errors import BackendUnavailableError

if TYPE_CHECKING:
    from types import ModuleType

    import argon2

    from .password_profiles import Argon2Parameters


def _load(module: str, distribution: str, extra: str) -> ModuleType:
    try:
        return importlib.import_module(module)
    except ImportError:
        raise BackendUnavailableError(distribution, extra) from None


def _bcrypt() -> ModuleType:
    return _load("bcrypt", "bcrypt", "bcrypt")


def _argon2() -> ModuleType:
    return _load("argon2", "argon2-cffi", "argon2")


def bcrypt_hash(secret: bytes, rounds: int, ident: str) -> str:
    module = _bcrypt()
    salt = module.gensalt(rounds=rounds, prefix=ident.encode("ascii"))
    hashed: bytes = module.hashpw(secret, salt)
    return hashed.decode("ascii")


def bcrypt_verify(secret: bytes, stored: str) -> bool:
    module = _bcrypt()
    try:
        return bool(module.checkpw(secret, stored.encode("ascii")))
    except ValueError:
        return False


@lru_cache(maxsize=16)
def _argon2_hasher(parameters: Argon2Parameters) -> argon2.PasswordHasher:
    module = _argon2()
    variants = {"id": module.Type.ID, "i": module.Type.I, "d": module.Type.D}
    hasher: argon2.PasswordHasher = module.PasswordHasher(
        time_cost=parameters.time_cost,
        memory_cost=parameters.memory_cost,
        parallelism=parameters.parallelism,
        hash_len=parameters.hash_len,
        salt_len=parameters.salt_len,
        type=variants[parameters.variant],
    )
    return hasher


def argon2_hash(password: str, parameters: Argon2Parameters) -> str:
    return str(_argon2_hasher(parameters).hash(password))


def argon2_verify(password: str, stored: str, parameters: Argon2Parameters) -> bool:
    module = _argon2()
    try:
        return bool(_argon2_hasher(parameters).verify(stored, password))
    except (module.exceptions.VerificationError, module.exceptions.InvalidHash, ValueError):
        return False


def argon2_needs_rehash(stored: str, parameters: Argon2Parameters) -> bool:
    try:
        return bool(_argon2_hasher(parameters).check_needs_rehash(stored))
    except ValueError:  # InvalidHash derives from ValueError
        return True
