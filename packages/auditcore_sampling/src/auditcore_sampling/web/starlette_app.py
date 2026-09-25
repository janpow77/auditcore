"""Starlette routes for the sampling REST contract (extra ``web``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ._http import MAX_BODY_BYTES, Reply, handle, profiles

ENDPOINTS = (
    ("/size", "size"),
    ("/allocation", "allocation"),
    ("/selection", "selection"),
    ("/selection/export", "export"),
)


def _response(reply: Reply) -> Response:
    return Response(reply.body, reply.status, reply.headers, reply.media_type)


def routes(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> list[Route]:
    """Routes below ``prefix`` (e.g. ``/api/sampling``) for mounting in an application."""

    async def get_profiles(_: Request) -> Response:
        return _response(profiles())

    def endpoint(name: str) -> Callable[[Request], Awaitable[Response]]:
        async def run(request: Request) -> Response:
            return _response(handle(name, await request.body(), max_body_bytes))

        return run

    result = [Route(f"{prefix}/profiles", get_profiles, methods=["GET"])]
    result += [Route(prefix + path, endpoint(name), methods=["POST"]) for path, name in ENDPOINTS]
    return result


def create_app(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> Starlette:
    """Standalone ASGI application; authentication and CORS stay with the host."""
    return Starlette(routes=routes(prefix, max_body_bytes=max_body_bytes))
