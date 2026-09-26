"""Framework-neutral request dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from urllib.parse import quote

from .contract import ContractError
from .service import MAX_BODY_BYTES, catalogue, export, preview

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass(frozen=True)
class Reply:
    """Status, body, media type and extra headers of one response."""

    status: int
    body: bytes
    media_type: str = "application/json"
    headers: dict[str, str] = field(default_factory=dict)


def _json(status: int, data: object) -> Reply:
    return Reply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"))


def _reject(_: str) -> object:
    raise ValueError("non-finite number")


def decode(raw: bytes, limit: int = MAX_BODY_BYTES) -> object:
    """Parsed JSON body within the size limit; NaN/Infinity are not JSON."""
    if len(raw) > limit:
        raise ContractError("Anfrage zu groß.", status=413, code="too_large")
    try:
        return json.loads(raw, parse_constant=_reject)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ContractError("Kein gültiges JSON.", status=400, code="invalid_json") from exc


def disposition(filename: str) -> str:
    """``attachment`` header: ASCII fallback (non-ASCII, ``"`` and ``\\`` replaced) and RFC 5987 name."""
    fallback = re.sub(r'[^\x20-\x7e]|["\\]', "_", filename)
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename, safe='')}"


def profiles() -> Reply:
    """``GET /profiles``."""
    return _json(200, catalogue())


def handle_preview(raw: bytes, limit: int = MAX_BODY_BYTES) -> Reply:
    """``POST /preview`` with contract errors mapped to HTTP replies."""
    try:
        return _json(200, preview(decode(raw, limit)))
    except ContractError as exc:
        return _json(exc.status, exc.to_dict())


def handle_export(raw: bytes, limit: int = MAX_BODY_BYTES) -> Reply:
    """``POST /export``: the XLSX file as attachment."""
    try:
        content, filename = export(decode(raw, limit))
    except ContractError as exc:
        return _json(exc.status, exc.to_dict())
    return Reply(200, content, XLSX, {"Content-Disposition": disposition(filename)})
