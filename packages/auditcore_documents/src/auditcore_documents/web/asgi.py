"""Starlette-Adapter des REST-Vertrags (Extra ``web``).

``create_app`` liefert eine eigenständige ASGI-Anwendung, die eine Anwendung
unter einem Pfad einhängt (``app.mount("/api/synopsis", create_app(...))``).
Die Bibliothek authentifiziert nicht: ``identify`` bildet eine Anfrage auf
den Eigentümer ab oder gibt ``None`` zurück (dann 401). Die Vorgabe
:func:`single_user` ist nur für Einzelplatz-Werkzeuge und Demos gedacht.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from urllib.parse import quote

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from auditcore_documents.errors import CompareError
from auditcore_documents.web.options import FORM_FIELDS, RequestError
from auditcore_documents.web.service import SynopsisService, Upload, error_status

Identify = Callable[[Request], str | None]
Endpoint = Callable[[Request], Awaitable[Response]]
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_FIELD_BYTES = 64 * 1024


def single_user(_request: Request) -> str:
    """Alle Anfragen gehören demselben Eigentümer (nur Einzelplatz/Demo)."""
    return "local"


def _problem(status: int, detail: str) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status)


async def _http_problem(_request: Request, exc: Exception) -> Response:
    """Starlette-Fehler (z. B. fehlerhaftes Multipart) in die Vertragsform bringen."""
    if not isinstance(exc, HTTPException):  # pragma: no cover - nur für HTTPException registriert
        raise exc
    if exc.status_code == 400:
        return _problem(400, "Die Anfrage ist fehlerhaft.")
    return _problem(exc.status_code, str(exc.detail))


def _content_length(request: Request) -> int | None:
    value = request.headers.get("content-length")
    try:
        return int(value) if value is not None else None
    except ValueError:
        raise RequestError(400, "Ungültige Content-Length.") from None


async def _limited_body(request: Request, limit: int) -> bytes:
    declared = _content_length(request)
    if declared is not None and declared > limit:
        raise RequestError(413, "Die Anfrage ist zu groß.")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > limit:
            raise RequestError(413, "Die Anfrage ist zu groß.")
    return bytes(body)


async def _json_body(request: Request) -> object:
    raw = await _limited_body(request, MAX_JSON_BYTES)
    try:
        return json.loads(raw or b"null")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RequestError(400, "Der Anfragekörper ist kein gültiges JSON.") from None


async def _upload(value: object, label: str, limit: int) -> Upload:
    if not isinstance(value, UploadFile):
        raise RequestError(422, f"{label}: Datei fehlt.")
    content = await value.read(limit + 1)
    return Upload(value.filename or "", content)


def _attachment(filename: str) -> str:
    ascii_name = filename.encode("ascii", "replace").decode("ascii").replace("?", "_")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


class SynopsisHandlers:
    """Endpunkte als Methoden ``(Request) -> Response``; auch für FastAPI nutzbar."""

    def __init__(self, service: SynopsisService, identify: Identify) -> None:
        self.service = service
        self.identify = identify

    def routes(self) -> list[tuple[str, str, Endpoint]]:
        """(Pfad, Methode, Endpunkt) relativ zum Einhängepunkt."""
        return [
            ("/profiles", "GET", self._guard(self.profiles)),
            ("/comparisons", "GET", self._guard(self.list)),
            ("/comparisons", "POST", self._guard(self.create)),
            ("/comparisons/import", "POST", self._guard(self.import_result)),
            ("/comparisons/{comparison_id}", "GET", self._guard(self.get)),
            ("/comparisons/{comparison_id}", "DELETE", self._guard(self.delete)),
            ("/comparisons/{comparison_id}/rows", "PATCH", self._guard(self.update_rows)),
            ("/comparisons/{comparison_id}/export", "GET", self._guard(self.export)),
        ]

    def _guard(self, handler: Callable[[Request, str], Awaitable[Response]]) -> Endpoint:
        async def endpoint(request: Request) -> Response:
            owner = self.identify(request)
            if not owner:
                return _problem(401, "Anmeldung erforderlich.")
            try:
                return await handler(request, owner)
            except (RequestError, CompareError) as exc:
                detail = exc.detail if isinstance(exc, RequestError) else str(exc)
                return _problem(error_status(exc), detail)

        endpoint.__name__ = handler.__name__
        endpoint.__doc__ = handler.__doc__
        return endpoint

    async def profiles(self, _request: Request, _owner: str) -> Response:
        """Erlaubte Vergleichsprofile."""
        return JSONResponse({"items": self.service.profiles()})

    async def list(self, _request: Request, owner: str) -> Response:
        """Gespeicherte Vergleiche des Eigentümers, neueste zuerst."""
        return JSONResponse({"items": self.service.list(owner)})

    async def create(self, request: Request, owner: str) -> Response:
        """Zwei Fassungen hochladen und vergleichen (multipart/form-data)."""
        limit = self.service.settings.max_upload_bytes
        declared = _content_length(request)
        if declared is not None and declared > 2 * limit + MAX_FIELD_BYTES * len(FORM_FIELDS):
            raise RequestError(413, "Die Anfrage ist zu groß.")
        async with request.form(
            max_files=2, max_fields=len(FORM_FIELDS), max_part_size=MAX_FIELD_BYTES
        ) as form:
            old = await _upload(form.get("old_file"), "Bisherige Fassung", limit)
            new = await _upload(form.get("new_file"), "Neue Fassung", limit)
            fields = {k: v for k, v in form.multi_items() if isinstance(v, str)}
        item = await run_in_threadpool(self.service.create, owner, old, new, fields)
        return JSONResponse(item.envelope(), status_code=201)

    async def import_result(self, request: Request, owner: str) -> Response:
        """Vorhandenes Ergebnisobjekt übernehmen (JSON)."""
        item = self.service.import_result(owner, await _json_body(request))
        return JSONResponse(item.envelope(), status_code=201)

    async def get(self, request: Request, owner: str) -> Response:
        """Einen Vergleich mit vollständigem Ergebnisobjekt lesen."""
        item = self.service.get(owner, request.path_params["comparison_id"])
        return JSONResponse(item.envelope())

    async def delete(self, request: Request, owner: str) -> Response:
        """Vergleich löschen."""
        self.service.delete(owner, request.path_params["comparison_id"])
        return Response(status_code=204)

    async def update_rows(self, request: Request, owner: str) -> Response:
        """Auswahl und Grund je Zeile übernehmen."""
        comparison_id = request.path_params["comparison_id"]
        item = self.service.update_rows(owner, comparison_id, await _json_body(request))
        return JSONResponse(item.envelope())

    async def export(self, request: Request, owner: str) -> Response:
        """Ausgabe als JSON, Markdown, DOCX oder PDF."""
        fmt = request.query_params.get("format", "json")
        comparison_id = request.path_params["comparison_id"]
        file = await run_in_threadpool(self.service.export, owner, comparison_id, fmt)
        headers = {"Content-Disposition": _attachment(file.filename), "Cache-Control": "no-store"}
        return Response(file.content, media_type=file.media_type, headers=headers)


def create_app(
    service: SynopsisService | None = None,
    *,
    identify: Identify = single_user,
    debug: bool = False,
) -> Starlette:
    """ASGI-Anwendung mit allen Endpunkten des Vertrags ``docs/ui/synopsis-rest.md``."""
    handlers = SynopsisHandlers(service or SynopsisService(), identify)
    routes = [
        Route(path, endpoint, methods=[method]) for path, method, endpoint in handlers.routes()
    ]
    return Starlette(debug=debug, routes=routes, exception_handlers={HTTPException: _http_problem})
