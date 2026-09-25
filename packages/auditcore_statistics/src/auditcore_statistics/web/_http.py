"""Framework-neutral request dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal

from .analysis import ContractError, analyse, catalogue

MAX_BODY_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True)
class Reply:
    """Status, JSON body and media type of one response."""

    status: int
    body: bytes
    media_type: str = "application/json"


def _json(status: int, data: object) -> Reply:
    return Reply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"))


def decode(raw: bytes, limit: int = MAX_BODY_BYTES) -> object:
    """JSON body with numbers as exact Decimal/int, within the size limit."""
    if len(raw) > limit:
        raise ContractError("Anfrage zu groß.", status=413, code="too_large")
    try:
        return json.loads(raw, parse_float=Decimal)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("Kein gültiges JSON.", status=400, code="invalid_json") from exc


def profiles() -> Reply:
    """``GET /profiles``."""
    return _json(200, catalogue())


def handle_analyse(raw: bytes, limit: int = MAX_BODY_BYTES) -> Reply:
    """``POST /analyze`` with contract errors mapped to HTTP replies."""
    try:
        return _json(200, analyse(decode(raw, limit)))
    except ContractError as exc:
        return _json(exc.status, exc.to_dict())
