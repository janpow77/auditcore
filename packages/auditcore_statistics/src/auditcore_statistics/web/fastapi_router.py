"""Optional FastAPI router for the Benford REST contract (requires ``fastapi``)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from ._http import MAX_BODY_BYTES, Reply, handle_analyse, profiles


def _response(reply: Reply) -> Response:
    return Response(reply.body, reply.status, media_type=reply.media_type)


def create_router(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> APIRouter:
    """APIRouter with the same contract; include it with ``app.include_router``."""
    router = APIRouter(prefix=prefix, tags=["Benford"])

    @router.get("/profiles", summary="Tests und Bewertungsprofile")
    async def get_profiles() -> Response:
        return _response(profiles())

    @router.post("/analyze", summary="Benford-Analyse")
    async def post_analyse(request: Request) -> Response:
        return _response(handle_analyse(await request.body(), max_body_bytes))

    return router
