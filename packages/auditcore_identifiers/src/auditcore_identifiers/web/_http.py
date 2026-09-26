"""Framework-neutral request dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass

from .contract import ContractError, Json, Limits, catalogue, check_batch, check_one


@dataclass(frozen=True)
class Reply:
    """Status and JSON body of one response."""

    status: int
    body: bytes
    media_type: str = "application/json"


def _json(status: int, data: object) -> Reply:
    return Reply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"))


def decode(raw: bytes, limits: Limits) -> object:
    """Parsed JSON body within the size limit."""
    if len(raw) > limits.max_body_bytes:
        raise ContractError("Anfrage zu groß.", status=413, code="too_large")
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("Kein gültiges JSON.", status=400, code="invalid_json") from exc


Handler = Callable[[object, Limits], Json]
HANDLERS: dict[str, Handler] = {"check": check_one, "batch": check_batch}


def get_catalogue(limits: Limits) -> Reply:
    """``GET /catalogue``."""
    return _json(200, catalogue(limits))


def handle(name: str, raw: bytes, limits: Limits) -> Reply:
    """Run one POST endpoint and map contract errors to HTTP replies."""
    try:
        return _json(200, HANDLERS[name](decode(raw, limits), limits))
    except ContractError as exc:
        return _json(exc.status, exc.to_dict())
