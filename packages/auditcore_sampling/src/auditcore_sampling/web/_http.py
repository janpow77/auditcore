"""Framework-neutral request dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

from collections.abc import Callable

from auditcore_common.rest import Reply, decode_body, guarded, json_reply

from ._validate import ContractError
from .derivation import calculate_size
from .draw import allocate, select
from .export import ExportFile, export_selection
from .profiles import catalogue

MAX_BODY_BYTES = 32 * 1024 * 1024


JSON_HANDLERS: dict[str, Callable[[object], dict[str, object]]] = {
    "size": calculate_size,
    "allocation": allocate,
    "selection": select,
}


def decode(raw: bytes, limit: int = MAX_BODY_BYTES) -> object:
    """Parsed JSON body within the size limit."""
    return decode_body(raw, limit, error=ContractError)


def profiles() -> Reply:
    """``GET /profiles``."""
    return json_reply(200, catalogue())


def _run(name: str, raw: bytes, limit: int) -> Reply:
    payload = decode(raw, limit)
    if name == "export":
        exported: ExportFile = export_selection(payload)
        disposition = f'attachment; filename="{exported.filename}"'
        return Reply(
            200, exported.content, exported.media_type, {"Content-Disposition": disposition}
        )
    return json_reply(200, JSON_HANDLERS[name](payload))


def handle(name: str, raw: bytes, limit: int = MAX_BODY_BYTES) -> Reply:
    """Run one POST endpoint and map contract errors to HTTP replies."""
    return guarded(lambda: _run(name, raw, limit), error=ContractError)
