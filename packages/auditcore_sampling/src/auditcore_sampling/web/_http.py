"""Framework-neutral request dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ._validate import ContractError
from .derivation import calculate_size
from .draw import allocate, select
from .export import ExportFile, export_selection
from .profiles import catalogue

MAX_BODY_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class Reply:
    """Status, body and headers of one response."""

    status: int
    body: bytes
    media_type: str
    headers: dict[str, str]


JSON_HANDLERS: dict[str, Callable[[object], dict[str, Any]]] = {
    "size": calculate_size,
    "allocation": allocate,
    "selection": select,
}


def _json(status: int, data: object) -> Reply:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return Reply(status, body, "application/json", {})


def decode(raw: bytes, limit: int = MAX_BODY_BYTES) -> object:
    """Parsed JSON body within the size limit."""
    if len(raw) > limit:
        raise ContractError("Anfrage zu groß.", status=413, code="too_large")
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("Kein gültiges JSON.", status=400, code="invalid_json") from exc


def profiles() -> Reply:
    """``GET /profiles``."""
    return _json(200, catalogue())


def handle(name: str, raw: bytes, limit: int = MAX_BODY_BYTES) -> Reply:
    """Run one POST endpoint and map contract errors to HTTP replies."""
    try:
        payload = decode(raw, limit)
        if name == "export":
            exported: ExportFile = export_selection(payload)
            disposition = f'attachment; filename="{exported.filename}"'
            return Reply(200, exported.content, exported.media_type,
                         {"Content-Disposition": disposition})
        return _json(200, JSON_HANDLERS[name](payload))
    except ContractError as exc:
        return _json(exc.status, exc.to_dict())
