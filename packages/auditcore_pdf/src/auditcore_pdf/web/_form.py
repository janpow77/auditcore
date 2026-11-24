"""Reads the multipart form of ``pdf_redaction/1`` (Starlette request, also used by FastAPI)."""

from __future__ import annotations

from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request

from ._http import FIELDS, Upload
from .contract import ContractError, RedactionService

#: Headroom above file and fields for multipart boundaries and part headers.
OVERHEAD = 64 * 1024


def _declared_length(request: Request) -> int | None:
    value = request.headers.get("content-length")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise ContractError("Ungültige Content-Length.", status=400, code="bad_request") from None


async def read_upload(name: str, request: Request, service: RedactionService) -> Upload:
    """File and the endpoint's fields; 413 above the limits, 400 for broken forms."""
    limits = service.limits
    field_limit = max(limits.max_selection_bytes, limits.max_criteria_bytes)
    declared = _declared_length(request)
    if declared is not None and declared > limits.max_upload_bytes + field_limit + OVERHEAD:
        raise ContractError("Die Anfrage ist zu groß.", status=413, code="too_large")
    wanted = FIELDS[name]
    try:
        parts = request.form(max_files=1, max_fields=len(wanted), max_part_size=field_limit)
        async with parts as form:
            file = form.get("file")
            if not isinstance(file, UploadFile):
                raise ContractError("Feld „file“ fehlt.", status=400, code="missing_file")
            content = await file.read(limits.max_upload_bytes + 1)
            service.check_size(len(content))
            fields = {key: value for key in wanted if isinstance(value := form.get(key), str)}
            return Upload(content, file.filename or "", fields)
    except HTTPException as exc:
        raise ContractError("Die Anfrage ist fehlerhaft.", status=400, code="bad_request") from exc
