"""Starlette routes for the ``pdf_redaction/1`` contract (extra ``web``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from auditcore_common.rest import Reply
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ._form import read_upload
from ._http import dispatch, error_reply, get_catalogue
from .contract import ContractError, RedactionService

Endpoint = Callable[[Request], Awaitable[Response]]


def response(reply: Reply) -> Response:
    """Starlette response of a framework-neutral reply."""
    return Response(
        reply.body, reply.status, headers=dict(reply.headers), media_type=reply.media_type
    )


def endpoints(service: RedactionService) -> list[tuple[str, str, Endpoint]]:
    """(path, method, endpoint) relative to the mount point; also used by FastAPI."""

    async def catalogue(_: Request) -> Response:
        return response(get_catalogue(service))

    def post(name: str) -> Endpoint:
        async def run(request: Request) -> Response:
            try:
                upload = await read_upload(name, request, service)
            except ContractError as exc:
                return response(error_reply(exc))
            # Suche und Schwärzung blockieren (PyMuPDF, spaCy): im Thread-Pool.
            return response(await run_in_threadpool(dispatch, name, service, upload))

        run.__name__ = name
        return run

    return [
        ("/catalogue", "GET", catalogue),
        ("/plan", "POST", post("plan")),
        ("/preview", "POST", post("preview")),
        ("/apply", "POST", post("apply")),
    ]


def routes(service: RedactionService, prefix: str = "") -> list[Route]:
    """Routes below ``prefix`` (e.g. ``/api/redaction``) for mounting in an application."""
    return [Route(prefix + path, run, methods=[method]) for path, method, run in endpoints(service)]


def create_app(service: RedactionService, prefix: str = "") -> Starlette:
    """Standalone ASGI application; authentication, CORS and rate limits stay with the host."""
    return Starlette(routes=routes(service, prefix))
