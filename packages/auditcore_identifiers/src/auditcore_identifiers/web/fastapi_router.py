"""Optional FastAPI router for the ``identifiers_ui/1`` contract (extra ``fastapi``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import Response

from ._http import Reply, get_catalogue, handle
from .contract import Limits


def _response(reply: Reply) -> Response:
    return Response(reply.body, reply.status, media_type=reply.media_type)


def create_router(prefix: str = "", *, limits: Limits | None = None) -> APIRouter:
    """APIRouter with the same contract; include it with ``app.include_router``."""
    active = limits or Limits()
    router = APIRouter(prefix=prefix, tags=["Kennungen"])

    async def get() -> Response:
        return _response(get_catalogue(active))

    def post(name: str) -> Callable[[Request], Awaitable[Response]]:
        async def run(request: Request) -> Response:
            return _response(handle(name, await request.body(), active))

        return run

    router.add_api_route("/catalogue", get, methods=["GET"], summary="Kennungsarten und Profile")
    router.add_api_route("/check", post("check"), methods=["POST"], summary="Kennung prüfen")
    router.add_api_route("/check/batch", post("batch"), methods=["POST"], summary="Stapelprüfung")
    return router
