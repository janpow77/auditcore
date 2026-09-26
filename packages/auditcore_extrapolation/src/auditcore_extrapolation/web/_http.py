"""Framework-neutral dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

from ._contract import ContractError
from .catalogue import catalogue
from .export import export_evaluation
from .requests import evaluate, residual

MAX_BODY_BYTES = 16 * 1024 * 1024
JSON_TYPE = "application/json"


@dataclass(frozen=True)
class Reply:
    """Status, body, media type and extra headers of one response."""

    status: int
    body: bytes
    media_type: str = JSON_TYPE
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def of(cls, status: int, data: object) -> Reply:
        """JSON reply; responses are never cached by intermediaries."""
        text = json.dumps(data, ensure_ascii=False)
        return cls(status, text.encode("utf-8"), headers={"Cache-Control": "no-store"})


HANDLERS: dict[str, Callable[[object], dict[str, object]]] = {
    "evaluate": evaluate,
    "residual": residual,
}


def profiles() -> Reply:
    """``GET /profiles``."""
    return Reply.of(200, catalogue())


def _payload(raw: bytes, limit: int) -> object:
    if len(raw) > limit:
        raise ContractError("Anfrage zu groß.", status=413, code="too_large")
    try:
        text = raw.decode("utf-8")
        return json.loads(text, parse_float=Decimal)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("Kein gültiges JSON.", status=400, code="invalid_json") from exc


def dispatch(name: str, raw: bytes, limit: int = MAX_BODY_BYTES) -> Reply:
    """Run one POST endpoint; contract errors become JSON error replies."""
    try:
        payload = _payload(raw, limit)
        if name != "export":
            return Reply.of(200, HANDLERS[name](payload))
        exported = export_evaluation(payload)
        headers = {
            "Content-Disposition": f'attachment; filename="{exported.filename}"',
            "Cache-Control": "no-store",
        }
        return Reply(200, exported.content, exported.media_type, headers)
    except ContractError as exc:
        return Reply.of(exc.status, exc.to_dict())
