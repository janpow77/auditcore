"""Optional FastAPI router for the ``pdf_redaction/1`` contract (extra ``fastapi``)."""

from __future__ import annotations

from fastapi import APIRouter

from .contract import RedactionService
from .starlette_app import endpoints

SUMMARIES = {
    "/catalogue": "Suchmuster und Grenzen",
    "/plan": "Fundstellen suchen (ändert nichts)",
    "/preview": "Seitenvorschau als PNG",
    "/apply": "Bestätigte Auswahl schwärzen und nachprüfen",
}


def create_router(service: RedactionService, prefix: str = "") -> APIRouter:
    """APIRouter with the same contract; include it with ``app.include_router``."""
    router = APIRouter(prefix=prefix, tags=["Schwärzung"])
    for path, method, run in endpoints(service):
        router.add_api_route(path, run, methods=[method], summary=SUMMARIES[path])
    return router
