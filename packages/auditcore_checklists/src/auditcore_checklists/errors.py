"""Fehlerklassen und JSON-Typverträge für den Checklisten-Kern."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias

JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def to_json_value(value: object) -> JsonValue:
    """Konvertiert beliebige Objekte typsicher in JsonValue."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Mapping):
        return {str(k): to_json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_value(v) for v in value]
    return str(value)


def to_json_object(value: object) -> JsonObject:
    """Konvertiert eine Zuordnung typsicher in ein JsonObject."""
    if not isinstance(value, Mapping):
        return {}
    return {str(k): to_json_value(v) for k, v in value.items()}


def to_int(value: object, default: int = 0) -> int:
    """Wandelt einen Wert sicher in einen Integer um."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


STATUS_BY_CODE: Mapping[str, int] = {
    "TREE_ERROR": 400,
    "NODE_NOT_FOUND": 404,
    "ROOT_DELETION_FORBIDDEN": 400,
    "CYCLE_DETECTED": 409,
    "INVALID_PARENT": 400,
    "INVALID_BRANCH": 400,
    "INVALID_PACKAGE": 422,
    "UNSUPPORTED_PACKAGE_VERSION": 422,
    "CHECKSUM_MISMATCH": 422,
    "VALIDATION_FAILED": 422,
}


class ChecklistError(Exception):
    """Basis-Ausnahme für alle fachlichen Fehler im Checklisten-Kern."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.details: dict[str, JsonValue] = dict(details or {})

    @property
    def status(self) -> int:
        """HTTP-Statuscode für diesen Fehler."""
        return STATUS_BY_CODE.get(self.code, 400)

    def to_json(self) -> JsonObject:
        """JSON-Repräsentation des Fehlers."""
        res: JsonObject = {"code": self.code, "message": self.message}
        if self.details:
            res["details"] = self.details
        return {"error": res}


class NodeNotFoundError(ChecklistError):
    """Knoten wurde im Baum nicht gefunden."""

    def __init__(self, node_id: str) -> None:
        super().__init__("NODE_NOT_FOUND", f"Knoten '{node_id}' wurde nicht gefunden.")
        self.node_id = node_id


class TreeStructureError(ChecklistError):
    """Verletzung der Baumstruktur-Regeln."""

    def __init__(self, message: str, code: str = "TREE_ERROR") -> None:
        super().__init__(code, message)


class CycleDetectedError(TreeStructureError):
    """Zyklische Abhängigkeit in der Knoten-Hierarchie erkannt."""

    def __init__(self, node_id: str, target_parent_id: str) -> None:
        super().__init__(
            f"Verschieben von Knoten '{node_id}' unter '{target_parent_id}' "
            "würde einen Zyklus erzeugen.",
            code="CYCLE_DETECTED",
        )
        self.node_id = node_id
        self.target_parent_id = target_parent_id


class InvalidBranchError(TreeStructureError):
    """Ungültiger Zweig für einen Unterknoten."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="INVALID_BRANCH")


class PackageFormatError(ChecklistError):
    """Fehler beim Lesen oder Schreiben eines Checklisten-Pakets."""

    def __init__(self, message: str, code: str = "INVALID_PACKAGE") -> None:
        super().__init__(code, message)
