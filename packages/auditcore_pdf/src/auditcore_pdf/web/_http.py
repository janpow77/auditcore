"""Framework-neutral dispatch of ``pdf_redaction/1`` shared by the Starlette and FastAPI adapters.

Both adapters read the multipart form into :class:`Upload` and hand it to
:func:`dispatch`; everything after that needs no web framework.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from auditcore_common import rest
from auditcore_common.rest import Reply

from .contract import ContractError, RedactionService, decode_json

PNG = "image/png"
PDF = "application/pdf"


@dataclass(frozen=True)
class Upload:
    """File and text fields of one multipart request."""

    content: bytes = b""
    filename: str = ""
    fields: dict[str, str] = field(default_factory=dict)


def _field(upload: Upload, name: str) -> str:
    value = upload.fields.get(name)
    if value is None:
        raise ContractError(f"Feld „{name}“ fehlt.", status=400, code="missing_field")
    return value


def _plan(service: RedactionService, upload: Upload) -> Reply:
    limit = service.limits.max_criteria_bytes
    criteria = decode_json(_field(upload, "criteria"), limit, "criteria")
    return rest.json_reply(200, service.plan(upload.content, criteria))


def _preview(service: RedactionService, upload: Upload) -> Reply:
    image = service.preview(upload.content, _field(upload, "page"))
    return Reply(200, image, PNG, {"Cache-Control": "no-store"})


def _apply(service: RedactionService, upload: Upload) -> Reply:
    limit = service.limits.max_selection_bytes
    selection = decode_json(_field(upload, "selection"), limit, "selection")
    applied = service.apply(upload.content, upload.filename, selection)
    return Reply(200, applied.content, PDF, applied.headers)


HANDLERS: dict[str, Callable[[RedactionService, Upload], Reply]] = {
    "plan": _plan,
    "preview": _preview,
    "apply": _apply,
}

#: Fields each endpoint accepts besides ``file``.
FIELDS: dict[str, tuple[str, ...]] = {
    "plan": ("criteria",),
    "preview": ("page",),
    "apply": ("selection",),
}


def get_catalogue(service: RedactionService) -> Reply:
    """``GET /catalogue``."""
    return rest.json_reply(200, service.catalogue())


def dispatch(name: str, service: RedactionService, upload: Upload) -> Reply:
    """Run one POST endpoint and map contract errors to JSON replies."""
    return rest.guarded(lambda: HANDLERS[name](service, upload), error=ContractError)


def error_reply(exc: ContractError) -> Reply:
    """JSON reply of a contract error raised while reading the form."""
    return rest.json_reply(exc.status, exc.to_dict())
