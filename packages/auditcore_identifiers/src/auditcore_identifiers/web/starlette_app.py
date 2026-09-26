"""Starlette routes for the ``identifiers_ui/1`` contract (extra ``web``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ._http import Reply, get_catalogue, handle
from .contract import Limits


def response(reply: Reply) -> Response:
    """Starlette response of a framework-neutral reply."""
    return Response(reply.body, reply.status, media_type=reply.media_type)


def routes(prefix: str = "", *, limits: Limits | None = None) -> list[Route]:
    """Routes below ``prefix`` (e.g. ``/api/identifiers``) for mounting in an application."""
    active = limits or Limits()

    async def get(_: Request) -> Response:
        return response(get_catalogue(active))

    def post(name: str) -> Callable[[Request], Awaitable[Response]]:
        async def run(request: Request) -> Response:
            return response(handle(name, await request.body(), active))

        return run

    return [
        Route(f"{prefix}/catalogue", get, methods=["GET"]),
        Route(f"{prefix}/check", post("check"), methods=["POST"]),
        Route(f"{prefix}/check/batch", post("batch"), methods=["POST"]),
    ]


def create_app(prefix: str = "", *, limits: Limits | None = None) -> Starlette:
    """Standalone ASGI application; authentication and CORS stay with the host."""
    return Starlette(routes=routes(prefix, limits=limits))
