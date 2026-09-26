"""Optional FastAPI router for contract ``reporting_ui/1`` (requires ``fastapi``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import Response

from ._http import Reply, handle_export, handle_preview, profiles
from .service import MAX_BODY_BYTES
from .starlette_app import read_limited

Handler = Callable[[bytes, int], Reply]


def _response(reply: Reply) -> Response:
    return Response(reply.body, reply.status, headers=reply.headers, media_type=reply.media_type)


def _post(handler: Handler, limit: int) -> Callable[[Request], Awaitable[Response]]:
    async def run(request: Request) -> Response:
        return _response(handler(await read_limited(request, limit), limit))

    return run


async def _profiles() -> Response:
    return _response(profiles())


def create_router(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> APIRouter:
    """APIRouter with the same contract; include it with ``app.include_router``."""
    router = APIRouter(prefix=prefix, tags=["Berichtsexport"])
    router.add_api_route("/profiles", _profiles, methods=["GET"], summary="Formatprofile")
    router.add_api_route(
        "/preview", _post(handle_preview, max_body_bytes), methods=["POST"], summary="Vorschau"
    )
    router.add_api_route(
        "/export", _post(handle_export, max_body_bytes), methods=["POST"], summary="XLSX-Export"
    )
    return router
