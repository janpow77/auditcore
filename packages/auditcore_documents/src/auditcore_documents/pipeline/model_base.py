"""Gemeinsame Grundlage der Pipeline-Modelle: Uhr, Kennungen, Wertebereiche, Serialisierung."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields
from datetime import datetime
from typing import Any

from auditcore_common.clock import utc_now
from auditcore_common.ids import new_uuid

from auditcore_documents.pipeline.jsonfmt import dumps_compact

#: Pipeline names of the shared helpers (same objects as in ``auditcore_common``).
new_id = new_uuid
__all__ = ["Clock", "PipelineValueError", "new_id", "utc_now"]

Clock = Callable[[], datetime]


class PipelineValueError(ValueError):
    """Ungültiger Wert für ein Pipeline-Modell (entspricht pydantic ``ValidationError``)."""


def _range(owner: object, name: str, low: float | None, high: float | None) -> None:
    value = getattr(owner, name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PipelineValueError(f"{type(owner).__name__}.{name}: Zahl erwartet")
    if low is not None and value < low:
        raise PipelineValueError(f"{type(owner).__name__}.{name}: größer oder gleich {low}")
    if high is not None and value > high:
        raise PipelineValueError(f"{type(owner).__name__}.{name}: kleiner oder gleich {high}")


def _dump(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_dump(item) for item in value]
    return value


class _Model:
    """Gemeinsame Serialisierung in Feldreihenfolge (ohne interne Uhr)."""

    def to_dict(self) -> dict[str, Any]:
        return {f.name: _dump(getattr(self, f.name)) for f in fields(self) if f.name != "clock"}  # type: ignore[arg-type]

    def to_json(self) -> str:
        return dumps_compact(self.to_dict())
