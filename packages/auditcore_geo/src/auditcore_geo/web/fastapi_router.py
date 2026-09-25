"""Optional FastAPI router for the geo REST contract (requires ``fastapi``)."""

from __future__ import annotations

from fastapi import APIRouter

from .settings import Settings
from .starlette_app import routes


def create_router(prefix: str = "", *, settings: Settings | None = None) -> APIRouter:
    """APIRouter with the unchanged Starlette endpoints (byte-identical answers).

    The endpoints do not appear in FastAPI's OpenAPI schema; the contract is
    ``docs/ui/geo-rest.md``.
    """
    router = APIRouter(tags=["Geo"])
    router.routes.extend(routes(prefix, settings=settings))
    return router
