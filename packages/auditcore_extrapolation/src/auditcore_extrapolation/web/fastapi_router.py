"""Optional FastAPI router for the extrapolation REST contract (requires ``fastapi``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import Response

from ._http import MAX_BODY_BYTES, dispatch, profiles
from .starlette_app import POST_PATHS


def create_router(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> APIRouter:
    """APIRouter with the same contract; include it with ``app.include_router``."""
    router = APIRouter(prefix=prefix, tags=["Hochrechnung"])

    async def get_profiles() -> Response:
        reply = profiles()
        return Response(reply.body, reply.status, reply.headers, reply.media_type)

    def post(name: str) -> Callable[[Request], Awaitable[Response]]:
        async def handler(request: Request) -> Response:
            reply = dispatch(name, await request.body(), max_body_bytes)
            return Response(reply.body, reply.status, reply.headers, reply.media_type)

        return handler

    router.add_api_route("/profiles", get_profiles, methods=["GET"], summary="Methoden und Profile")
    for path, name in POST_PATHS:
        router.add_api_route(path, post(name), methods=["POST"], name=f"extrapolation_{name}")
    return router
