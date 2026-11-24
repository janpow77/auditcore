"""Reads the multipart form of ``pdf_redaction/1`` (Starlette request, also used by FastAPI)."""

from __future__ import annotations

from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request

from ._http import FIELDS, Upload
from .contract import ContractError, Limits, RedactionService

#: Headroom above file and fields for multipart boundaries and part headers.
OVERHEAD = 64 * 1024
#: Size of the ``page`` field of ``/preview`` (a page number).
PAGE_FIELD_BYTES = 64


def field_limit(name: str, limits: Limits) -> int:
    """Largest text field the endpoint ``name`` accepts."""
    return {
        "plan": limits.max_criteria_bytes,
        "apply": limits.max_selection_bytes,
    }.get(name, PAGE_FIELD_BYTES)


def _declared_length(request: Request) -> int:
    """``Content-Length``; without it the body size would only be known after spooling."""
    value = request.headers.get("content-length")
    if value is None:
        raise ContractError("Content-Length fehlt.", status=411, code="length_required")
    try:
        return int(value)
    except ValueError:
        raise ContractError("Ungültige Content-Length.", status=400, code="bad_request") from None


def _form_error(exc: HTTPException) -> ContractError:
    if "maximum size" in str(exc.detail):
        return ContractError("Ein Formularfeld ist zu groß.", status=413, code="too_large")
    return ContractError("Die Anfrage ist fehlerhaft.", status=400, code="bad_request")


async def read_upload(name: str, request: Request, service: RedactionService) -> Upload:
    """File and the endpoint's fields; 411/413 before reading, 400 for broken forms."""
    limits = service.limits
    limit = field_limit(name, limits)
    if _declared_length(request) > limits.max_upload_bytes + limit + OVERHEAD:
        raise ContractError("Die Anfrage ist zu groß.", status=413, code="too_large")
    wanted = FIELDS[name]
    try:
        # +1: ein Feld knapp über der Grenze erreicht decode_json und liefert dort 413.
        parts = request.form(max_files=1, max_fields=len(wanted), max_part_size=limit + 1)
        async with parts as form:
            file = form.get("file")
            if not isinstance(file, UploadFile):
                raise ContractError("Feld „file“ fehlt.", status=400, code="missing_file")
            content = await file.read(limits.max_upload_bytes + 1)
            service.check_size(len(content))
            fields = {key: value for key in wanted if isinstance(value := form.get(key), str)}
            return Upload(content, file.filename or "", fields)
    except HTTPException as exc:
        raise _form_error(exc) from exc
