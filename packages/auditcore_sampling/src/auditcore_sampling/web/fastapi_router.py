"""Optional FastAPI router for the sampling REST contract (requires ``fastapi``)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from ._http import MAX_BODY_BYTES, Reply, handle, profiles
from .starlette_app import ENDPOINTS


def _response(reply: Reply) -> Response:
    return Response(reply.body, reply.status, reply.headers, reply.media_type)


def create_router(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> APIRouter:
    """APIRouter with the same contract; include it with ``app.include_router``."""
    router = APIRouter(prefix=prefix, tags=["Stichprobe"])

    @router.get("/profiles", summary="Methodenprofile")
    async def get_profiles() -> Response:
        return _response(profiles())

    for path, name in ENDPOINTS:

        async def run(request: Request, _name: str = name) -> Response:
            return _response(handle(_name, await request.body(), max_body_bytes))

        router.add_api_route(path, run, methods=["POST"], name=f"sampling_{name}")
    return router
