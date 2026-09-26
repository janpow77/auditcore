"""Starlette routes for the extrapolation REST contract (extra ``web``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from auditcore_common.rest import Reply
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ._http import MAX_BODY_BYTES, dispatch, profiles

#: POST paths below the mount point and their handler names.
POST_PATHS = (
    ("/evaluate", "evaluate"),
    ("/evaluate/export", "export"),
    ("/residual", "residual"),
)


def to_response(reply: Reply) -> Response:
    """Starlette response of a framework-neutral reply."""
    return Response(
        content=reply.body,
        status_code=reply.status,
        headers=dict(reply.headers),
        media_type=reply.media_type,
    )


def _post(name: str, limit: int) -> Callable[[Request], Awaitable[Response]]:
    async def handler(request: Request) -> Response:
        return to_response(dispatch(name, await request.body(), limit))

    return handler


async def _profiles(_: Request) -> Response:
    return to_response(profiles())


def routes(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> list[Route]:
    """Routes below ``prefix`` (e.g. ``/api/extrapolation``)."""
    found = [Route(prefix + "/profiles", _profiles, methods=["GET"])]
    for path, name in POST_PATHS:
        found.append(Route(prefix + path, _post(name, max_body_bytes), methods=["POST"]))
    return found


def create_app(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> Starlette:
    """Standalone ASGI application; authentication and CORS stay with the host."""
    return Starlette(routes=routes(prefix, max_body_bytes=max_body_bytes))
