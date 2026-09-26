"""Optional FastAPI router for the sampling REST contract (requires ``fastapi``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import Response

from ._http import MAX_BODY_BYTES, handle, profiles
from .starlette_app import ENDPOINTS, response


def _endpoint(name: str, max_body_bytes: int) -> Callable[[Request], Awaitable[Response]]:
    async def run(request: Request) -> Response:
        return response(handle(name, await request.body(), max_body_bytes))

    return run


async def _profiles() -> Response:
    return response(profiles())


def create_router(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> APIRouter:
    """APIRouter with the same contract; include it with ``app.include_router``."""
    router = APIRouter(prefix=prefix, tags=["Stichprobe"])
    router.add_api_route("/profiles", _profiles, methods=["GET"], summary="Methodenprofile")
    for path, name in ENDPOINTS:
        router.add_api_route(
            path, _endpoint(name, max_body_bytes), methods=["POST"], name=f"sampling_{name}"
        )
    return router
