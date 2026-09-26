"""Framework-neutral dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal

from auditcore_common.rest import Reply, decode_body, guarded, json_reply

from ._contract import ContractError
from .catalogue import catalogue
from .export import export_evaluation
from .requests import evaluate, residual

MAX_BODY_BYTES = 16 * 1024 * 1024
NO_STORE = {"Cache-Control": "no-store"}

HANDLERS: dict[str, Callable[[object], dict[str, object]]] = {
    "evaluate": evaluate,
    "residual": residual,
}


def profiles() -> Reply:
    """``GET /profiles``."""
    return replace(json_reply(200, catalogue()), headers=NO_STORE)


def _run(name: str, raw: bytes, limit: int) -> Reply:
    payload = decode_body(raw, limit, error=ContractError, parse_float=Decimal)
    if name != "export":
        return replace(json_reply(200, HANDLERS[name](payload)), headers=NO_STORE)
    exported = export_evaluation(payload)
    disposition = f'attachment; filename="{exported.filename}"'
    return Reply(
        200, exported.content, exported.media_type, {"Content-Disposition": disposition, **NO_STORE}
    )


def dispatch(name: str, raw: bytes, limit: int = MAX_BODY_BYTES) -> Reply:
    """Run one POST endpoint; contract errors become JSON error replies."""
    return guarded(lambda: _run(name, raw, limit), error=ContractError)
