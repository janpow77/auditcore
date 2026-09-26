"""Starlette routes for contract ``reporting_ui/1`` (extra ``web``)."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ._http import Reply, handle_export, handle_preview, profiles
from .service import MAX_BODY_BYTES


def _response(reply: Reply) -> Response:
    return Response(reply.body, reply.status, headers=reply.headers, media_type=reply.media_type)


async def read_limited(request: Request, limit: int) -> bytes:
    """Request body; reading stops once it exceeds ``limit`` (the handler then rejects it)."""
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > limit:
            break
    return bytes(body)


def routes(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> list[Route]:
    """Routes below ``prefix`` (e.g. ``/api/reporting``) for mounting in an application."""

    async def get_profiles(_: Request) -> Response:
        return _response(profiles())

    async def post_preview(request: Request) -> Response:
        raw = await read_limited(request, max_body_bytes)
        return _response(handle_preview(raw, max_body_bytes))

    async def post_export(request: Request) -> Response:
        raw = await read_limited(request, max_body_bytes)
        return _response(handle_export(raw, max_body_bytes))

    return [
        Route(f"{prefix}/profiles", get_profiles, methods=["GET"]),
        Route(f"{prefix}/preview", post_preview, methods=["POST"]),
        Route(f"{prefix}/export", post_export, methods=["POST"]),
    ]


def create_app(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> Starlette:
    """Standalone ASGI application; authentication and CORS stay with the host."""
    return Starlette(routes=routes(prefix, max_body_bytes=max_body_bytes))
