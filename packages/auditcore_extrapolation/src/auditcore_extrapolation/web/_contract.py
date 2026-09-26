"""Request reading for the REST contract (framework-free).

Every rejected request raises :class:`ContractError` with an HTTP status and a
German message; missing fields are never filled with defaults, except where
the contract documents one (materiality 2 %, zero amounts).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal

from auditcore_common.rest import ContractError as RestContractError
from auditcore_common.rest import bounded_list, json_object

CONTRACT = "auditcore_extrapolation.evaluation/1"
MAX_UNITS = 100_000
MAX_STRATA = 200
MAX_TEXT = 2_000


class ContractError(RestContractError):
    """Request does not satisfy the extrapolation REST contract."""


class Reader:
    """Typed access to one JSON object; ``where`` prefixes the messages."""

    def __init__(self, raw: object, where: str = "Anfrage") -> None:
        self.body: Mapping[str, object] = json_object(raw, where, error=ContractError)
        self.where = where

    def _name(self, key: str) -> str:
        return key if self.where == "Anfrage" else f"{self.where}.{key}"

    def has(self, key: str) -> bool:
        """Field present and not null."""
        return self.body.get(key) is not None

    def decimal(self, key: str, default: Decimal | None = None) -> Decimal:
        """A finite JSON number as exact Decimal."""
        value = self.body.get(key)
        if value is None and default is not None:
            return default
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            raise ContractError(f"'{self._name(key)}' muss eine Zahl sein.")
        exact = Decimal(repr(value)) if isinstance(value, float) else Decimal(value)
        if not exact.is_finite():
            raise ContractError(f"'{self._name(key)}' muss endlich sein.")
        return exact

    def number(self, key: str, default: float | None = None) -> float:
        """A finite JSON number as float."""
        fallback = None if default is None else Decimal(repr(default))
        result = float(self.decimal(key, fallback))
        if not math.isfinite(result):
            raise ContractError(f"'{self._name(key)}' ist zu groß.")
        return result

    def optional_number(self, key: str) -> float | None:
        """A number or ``None`` when absent."""
        return self.number(key) if self.has(key) else None

    def whole(self, key: str, *, minimum: int = 0) -> int:
        """A JSON integer ≥ ``minimum``."""
        value = self.body.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ContractError(f"'{self._name(key)}' muss eine ganze Zahl ≥ {minimum} sein.")
        return value

    def optional_whole(self, key: str, *, minimum: int = 0) -> int | None:
        """An integer or ``None`` when absent."""
        return self.whole(key, minimum=minimum) if self.has(key) else None

    def text(self, key: str, *, required: bool = True) -> str:
        """A string (non-empty if required), at most :data:`MAX_TEXT` characters."""
        value = self.body.get(key)
        if value is None and not required:
            return ""
        if not isinstance(value, str) or (required and not value.strip()):
            raise ContractError(f"'{self._name(key)}' muss ein nicht leerer Text sein.")
        if len(value) > MAX_TEXT:
            raise ContractError(f"'{self._name(key)}' ist länger als {MAX_TEXT} Zeichen.")
        return value

    def flag(self, key: str) -> bool:
        """A JSON boolean, ``false`` when absent."""
        value = self.body.get(key, False)
        if not isinstance(value, bool):
            raise ContractError(f"'{self._name(key)}' muss true oder false sein.")
        return value

    def items(self, key: str, limit: int) -> list[Reader]:
        """A non-empty list of objects, at most ``limit`` entries."""
        value = bounded_list(
            self.body.get(key), self._name(key), limit, "Einträge", error=ContractError
        )
        return [Reader(entry, f"{key}[{index}]") for index, entry in enumerate(value)]
