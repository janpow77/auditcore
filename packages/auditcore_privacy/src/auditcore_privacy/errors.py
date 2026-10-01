"""Fehlerklassen und JSON-Typverträge für auditcore_privacy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias

from auditcore_common.rest import ContractError

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

STATUS_BY_CODE: Mapping[str, int] = {
    "PRIVACY_ERROR": 400,
    "SCOPE_NOT_FOUND": 404,
    "COLLISION_ERROR": 409,
    "INVALID_SCOPE": 400,
    "INVALID_MAPPING": 422,
}


class PrivacyError(ContractError):
    """Basis-Ausnahme für Fehler im Pseudonymisierungs- und Datenschutzmodul."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "PRIVACY_ERROR",
        status: int | None = None,
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        effective_status = status if status is not None else STATUS_BY_CODE.get(code, 400)
        super().__init__(message, status=effective_status, code=code)
        self.message = message
        self.details: dict[str, JsonValue] = dict(details or {})

    def to_dict(self) -> dict[str, object]:
        """JSON-Fehlerobjekt nach REST-Konvention."""
        payload = super().to_dict()
        if self.details:
            err = payload.get("error")
            if isinstance(err, dict):
                err["details"] = self.details
        return payload

    def to_json(self) -> JsonObject:
        """JSON-Repräsentation des Fehlers."""
        return self.to_dict()  # type: ignore[return-value]


class ScopeError(PrivacyError):
    """Fehler bei der Verwaltung des Pseudonymisierungs-Scopes."""

    def __init__(self, message: str, code: str = "INVALID_SCOPE") -> None:
        super().__init__(message, code=code)


class CollisionError(PrivacyError):
    """Kollision bei der Pseudonym-Erzeugung konnte nicht aufgelöst werden."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="COLLISION_ERROR")
