"""Error and decision contract shared by commands, the service and the REST handler."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TypeAlias

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)
JsonObject: TypeAlias = dict[str, JsonValue]

#: HTTP status per error code; the REST contract (docs/kanban/rest-api.md) uses this table.
STATUS_BY_CODE: Mapping[str, int] = {
    "VALIDATION_ERROR": 400,
    "INVALID_PERMISSION": 400,
    "SELF_SHARE": 400,
    "UNKNOWN_COLUMN": 400,
    "UNAUTHENTICATED": 401,
    "FORBIDDEN": 403,
    "NOT_VISIBLE": 404,
    "BOARD_NOT_FOUND": 404,
    "CARD_NOT_FOUND": 404,
    "SHARE_NOT_FOUND": 404,
    "USER_NOT_FOUND": 404,
    "ROUTE_NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "TRANSITION_NOT_ALLOWED": 409,
    "COLUMN_LOCKED": 409,
    "ORDER_FIXED": 409,
    "WIP_LIMIT_REACHED": 409,
    "VERSION_CONFLICT": 409,
    "BOARD_EXISTS": 409,
    "INVALID_REQUEST": 422,
    "INVALID_DOCUMENT": 422,
}


class KanbanError(Exception):
    """A rejected operation with a stable machine code and a German message."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message

    @property
    def status(self) -> int:
        """HTTP status of the REST contract for this code (400 if unknown)."""
        return STATUS_BY_CODE.get(self.code, 400)

    def to_json(self) -> JsonObject:
        """Error body of the REST contract."""
        return {"error": {"code": self.code, "message": self.message}}


@dataclass(frozen=True)
class Decision:
    """Outcome of a rule check; ``warnings`` carries non-blocking codes (WIP warn mode)."""

    allowed: bool
    code: str = "OK"
    message: str = ""
    warnings: tuple[str, ...] = field(default=())

    def raise_if_denied(self) -> None:
        """Turn a denial into a :class:`KanbanError`."""
        if not self.allowed:
            raise KanbanError(self.code, self.message)

    def to_json(self) -> JsonObject:
        """Serialized decision (used by the parity fixtures)."""
        return {
            "allowed": self.allowed,
            "code": None if self.allowed and self.code == "OK" else self.code,
            "warnings": list(self.warnings),
        }


ALLOWED = Decision(True)


def deny(code: str, message: str) -> Decision:
    """Shorthand for a blocking decision."""
    return Decision(False, code, message)
