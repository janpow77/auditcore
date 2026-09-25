"""Adapter over PyJWT (imported lazily). Signing and signature checks happen here only.

Time-based claims are *not* checked by PyJWT but by :mod:`auditcore_auth._claims`
against the injectable clock; PyJWT still enforces the algorithm allowlist,
the signature, the presence of required claims and the audience rule.
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, NoReturn

from .errors import (
    BackendUnavailableError,
    ConfigurationError,
    DisallowedAlgorithmError,
    ExpiredTokenError,
    ImmatureTokenError,
    InvalidClaimError,
    InvalidSignatureError,
    MalformedTokenError,
    MissingClaimError,
    TokenError,
)

if TYPE_CHECKING:
    from types import ModuleType

Key = str | bytes


def _jwt() -> ModuleType:
    try:
        return importlib.import_module("jwt")
    except ImportError:
        raise BackendUnavailableError("PyJWT", "jwt") from None


def encode(payload: Mapping[str, object], key: Key, algorithm: str,
           headers: Mapping[str, str] | None = None) -> str:
    token: str = _jwt().encode(dict(payload), key, algorithm=algorithm,
                               headers=dict(headers) if headers else None)
    return token


def unverified_algorithm(token: str) -> str:
    """Read ``alg`` from the header before any key is used."""
    module = _jwt()
    try:
        header = module.get_unverified_header(token)
    except module.PyJWTError:
        raise MalformedTokenError("Token ist nicht lesbar") from None
    algorithm = header.get("alg")
    if not isinstance(algorithm, str):
        raise MalformedTokenError("Kopfzeile ohne Algorithmus")
    return algorithm


def decode(token: str, key: Key, algorithms: Sequence[str],
           required: Sequence[str]) -> dict[str, object]:
    module = _jwt()
    options = {
        "verify_signature": True,
        "verify_exp": False,
        "verify_iat": False,
        "verify_nbf": False,
        "require": list(required),
    }
    try:
        claims: dict[str, object] = module.decode(
            token, key, algorithms=list(algorithms), options=options
        )
    except module.PyJWTError as error:
        _translate(module, error)
    return claims


def _translate(module: ModuleType, error: Exception) -> NoReturn:
    """Map PyJWT errors onto the auditcore_auth contract (most specific first)."""
    if isinstance(error, module.MissingRequiredClaimError):
        raise MissingClaimError(error.claim) from None
    table: tuple[tuple[type[Exception], type[TokenError]], ...] = (
        (module.InvalidSignatureError, InvalidSignatureError),
        (module.InvalidAlgorithmError, DisallowedAlgorithmError),
        (module.ExpiredSignatureError, ExpiredTokenError),
        (module.ImmatureSignatureError, ImmatureTokenError),
        (module.DecodeError, MalformedTokenError),
    )
    for source, target in table:
        if isinstance(error, source):
            raise target() from None
    if isinstance(error, module.InvalidKeyError):
        raise ConfigurationError("Schlüssel passt nicht zum Algorithmus") from None
    raise InvalidClaimError("token", "Token abgelehnt") from None
