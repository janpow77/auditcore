"""Request validation shared by the REST contract (framework-free).

Every rejected request raises :class:`ContractError` with an HTTP status and
a German message; nothing is silently replaced by a default.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypeVar

from auditcore_common import rest

MAX_ITEMS = 200_000
MAX_SEED = 2**63 - 1

T = TypeVar("T")


class ContractError(rest.ContractError):
    """Request does not satisfy the sampling REST contract (status, code, ``to_dict``)."""


def as_object(value: object, name: str = "Anfrage") -> Mapping[str, object]:
    """A JSON object with string keys."""
    return rest.json_object(value, name, error=ContractError)


def require(body: Mapping[str, object], key: str) -> object:
    """A mandatory field; missing fields are never defaulted."""
    if key not in body or body[key] is None:
        raise ContractError(f"Pflichtfeld '{key}' fehlt.")
    return body[key]


def number(value: object, name: str) -> float:
    """A finite JSON number (booleans are rejected)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError(f"'{name}' muss eine endliche Zahl sein.")
    return float(value)


def integer(value: object, name: str, *, minimum: int = 0) -> int:
    """A JSON integer ≥ ``minimum``."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"'{name}' muss eine ganze Zahl sein.")
    if value < minimum:
        raise ContractError(f"'{name}' muss mindestens {minimum} sein.")
    return value


def text(value: object, name: str) -> str:
    """A non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"'{name}' muss ein nicht leerer Text sein.")
    return value


def choice(value: object, name: str, allowed: tuple[str, ...]) -> str:
    """One of the explicitly allowed values."""
    return rest.choice(value, name, allowed, error=ContractError)


def optional_seed(value: object) -> int | None:
    """A reproducibility seed in [0, 2⁶³-1] or ``None``."""
    if value is None:
        return None
    seed = integer(value, "seed")
    if seed > MAX_SEED:
        raise ContractError(f"'seed' darf höchstens {MAX_SEED} sein.")
    return seed
