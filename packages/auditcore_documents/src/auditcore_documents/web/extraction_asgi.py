"""Starlette-Adapter des Vertrags ``documents_extraction/1`` (Extra ``web``).

``extraction_routes`` liefert die Routen zum Einhängen, ``create_extraction_app``
eine eigenständige ASGI-Anwendung. Anmeldung, CORS und Ratenbegrenzung sind
Sache der Anwendung. Ein Lauf blockiert (OCR, Donut) und läuft deshalb im
Thread-Pool.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from auditcore_documents.web.extraction import ExtractionError, ExtractionService

Endpoint = Callable[[Request], Awaitable[Response]]
MAX_FIELD_BYTES = 1024


def _error(exc: ExtractionError) -> JSONResponse:
    return JSONResponse(exc.to_dict(), status_code=exc.status)


def _declared_length(request: Request) -> int | None:
    value = request.headers.get("content-length")
    try:
        return int(value) if value is not None else None
    except ValueError:
        raise ExtractionError("Ungültige Content-Length.", status=400, code="bad_request") from None


class ExtractionHandlers:
    """Endpunkte als ``(Request) -> Response``; auch für FastAPI nutzbar."""

    def __init__(self, service: ExtractionService) -> None:
        self.service = service

    def routes(self) -> list[tuple[str, str, Endpoint]]:
        """(Pfad, Methode, Endpunkt) relativ zum Einhängepunkt."""
        return [
            ("/profile", "GET", self._guard(self.profile)),
            ("/runs", "POST", self._guard(self.create_run)),
        ]

    @staticmethod
    def _guard(handler: Endpoint) -> Endpoint:
        async def endpoint(request: Request) -> Response:
            try:
                return await handler(request)
            except ExtractionError as exc:
                return _error(exc)

        endpoint.__name__ = handler.__name__
        endpoint.__doc__ = handler.__doc__
        return endpoint

    async def profile(self, _request: Request) -> Response:
        """Profile, angeschlossene Engines, Grenzen, Schwellen und Aufbewahrung."""
        return JSONResponse(self.service.catalogue())

    async def create_run(self, request: Request) -> Response:
        """Dokument hochladen und verarbeiten (multipart/form-data: ``file``, ``profile``)."""
        self.service.ensure_enabled()
        limit = self.service.settings.max_upload_bytes
        declared = _declared_length(request)
        if declared is not None and declared > limit + 64 * 1024:
            raise ExtractionError("Die Datei ist zu groß.", status=413, code="too_large")
        try:
            parts = request.form(max_files=1, max_fields=1, max_part_size=MAX_FIELD_BYTES)
            async with parts as form:
                upload = form.get("file")
                profile = form.get("profile")
                if not isinstance(upload, UploadFile):
                    raise ExtractionError("Feld 'file' fehlt.", code="missing_file")
                content = await upload.read(limit + 1)
                filename = upload.filename or ""
        except HTTPException as exc:
            raise ExtractionError(
                "Die Anfrage ist fehlerhaft.", status=400, code="bad_request"
            ) from exc
        chosen = profile if isinstance(profile, str) and profile else None
        result = await run_in_threadpool(self.service.run, filename, content, chosen)
        return JSONResponse(result)


def extraction_routes(service: ExtractionService, prefix: str = "") -> list[Route]:
    """Routen unter ``prefix`` (z. B. ``/api/extraction``) zum Einhängen."""
    handlers = ExtractionHandlers(service)
    return [
        Route(prefix + path, endpoint, methods=[method])
        for path, method, endpoint in handlers.routes()
    ]


def create_extraction_app(service: ExtractionService, *, debug: bool = False) -> Starlette:
    """Eigenständige ASGI-Anwendung des Vertrags ``docs/ui/extraction-rest.md``."""
    return Starlette(debug=debug, routes=extraction_routes(service))
