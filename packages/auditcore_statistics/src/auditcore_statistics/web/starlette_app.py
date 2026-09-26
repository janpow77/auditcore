"""Starlette routes for the Benford REST contract (extra ``web``)."""

from __future__ import annotations

from auditcore_common.rest import Reply
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ._http import MAX_BODY_BYTES, handle_analyse, profiles


def response(reply: Reply) -> Response:
    """The framework response of a reply (also used by the FastAPI router)."""
    return Response(reply.body, reply.status, dict(reply.headers), reply.media_type)


def routes(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> list[Route]:
    """Routes below ``prefix`` (e.g. ``/api/benford``) for mounting in an application."""

    async def get_profiles(_: Request) -> Response:
        return response(profiles())

    async def post_analyse(request: Request) -> Response:
        return response(handle_analyse(await request.body(), max_body_bytes))

    return [
        Route(f"{prefix}/profiles", get_profiles, methods=["GET"]),
        Route(f"{prefix}/analyze", post_analyse, methods=["POST"]),
    ]


def create_app(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> Starlette:
    """Standalone ASGI application; authentication and CORS stay with the host."""
    return Starlette(routes=routes(prefix, max_body_bytes=max_body_bytes))
