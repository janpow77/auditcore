"""Starlette-Adapter des Vertrags ``documents_batch_checks/1`` (Extra ``web``).

``batch_check_routes`` liefert die Routen zum Einhängen,
``create_batch_check_app`` eine eigenständige ASGI-Anwendung. Anmeldung, CORS
und Ratenbegrenzung sind Sache der Anwendung. Ein Prüflauf über viele Belege
läuft im Thread-Pool.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from auditcore_common.rest import Reply, decode_body, guarded, json_reply
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from auditcore_documents.web.batch_checks import BatchCheckService
from auditcore_documents.web.batch_input import BatchCheckError

Endpoint = Callable[[Request], Awaitable[Response]]


def reply_response(reply: Reply) -> Response:
    """Framework-Antwort einer :class:`Reply` (auch für den FastAPI-Router)."""
    return Response(reply.body, reply.status, dict(reply.headers), reply.media_type)


class BatchCheckHandlers:
    """Endpunkte als ``(Request) -> Response``; auch für FastAPI nutzbar."""

    def __init__(self, service: BatchCheckService) -> None:
        self.service = service

    def routes(self) -> list[tuple[str, str, Endpoint]]:
        """(Pfad, Methode, Endpunkt) relativ zum Einhängepunkt."""
        return [
            ("/catalogue", "GET", self.catalogue),
            ("/runs", "POST", self.create_run),
            ("/export", "POST", self.export),
        ]

    def _payload(self, raw: bytes) -> object:
        return decode_body(raw, self.service.settings.max_body_bytes, error=BatchCheckError)

    def _run(self, raw: bytes) -> Reply:
        return json_reply(200, self.service.check(self._payload(raw)))

    def _export(self, raw: bytes) -> Reply:
        exported = self.service.export(self._payload(raw))
        disposition = f'attachment; filename="{exported.filename}"'
        return Reply(
            200, exported.content, exported.media_type, {"Content-Disposition": disposition}
        )

    async def catalogue(self, _request: Request) -> Response:
        """Regeln, Felder, Vorgaben, Stufen, Grenzen und Exportformate."""
        return reply_response(json_reply(200, self.service.catalogue()))

    async def create_run(self, request: Request) -> Response:
        """Bestand prüfen (JSON: ``documents``, optional ``options``)."""
        raw = await request.body()
        reply = await run_in_threadpool(guarded, lambda: self._run(raw), error=BatchCheckError)
        return reply_response(reply)

    async def export(self, request: Request) -> Response:
        """Prüflauf als Datei (JSON wie ``/runs`` plus ``format``: ``json`` oder ``csv``)."""
        raw = await request.body()
        reply = await run_in_threadpool(guarded, lambda: self._export(raw), error=BatchCheckError)
        return reply_response(reply)


def batch_check_routes(service: BatchCheckService, prefix: str = "") -> list[Route]:
    """Routen unter ``prefix`` (z. B. ``/api/batch-checks``) zum Einhängen."""
    handlers = BatchCheckHandlers(service)
    return [
        Route(prefix + path, endpoint, methods=[method])
        for path, method, endpoint in handlers.routes()
    ]


def create_batch_check_app(service: BatchCheckService, *, debug: bool = False) -> Starlette:
    """Eigenständige ASGI-Anwendung des Vertrags ``docs/ui/batch-checks-rest.md``."""
    return Starlette(debug=debug, routes=batch_check_routes(service))
