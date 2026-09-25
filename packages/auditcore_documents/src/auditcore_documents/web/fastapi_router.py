"""Optionaler FastAPI-Router (Extra ``fastapi``) mit denselben Endpunkten.

Die Endpunkte sind die Starlette-Handler; FastAPI übergibt ihnen nur das
``Request``-Objekt. Eigene Abhängigkeiten der Anwendung (Anmeldung,
Mandant) werden über ``dependencies`` des Routers und ``identify`` angebunden.
"""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter, params

from auditcore_documents.web.asgi import Identify, SynopsisHandlers, single_user
from auditcore_documents.web.service import SynopsisService


def create_router(
    service: SynopsisService | None = None,
    *,
    identify: Identify = single_user,
    prefix: str = "",
    tags: Sequence[str] = ("Synopse",),
    dependencies: Sequence[params.Depends] | None = None,
) -> APIRouter:
    """``app.include_router(create_router(service, identify=...), prefix="/api/synopsis")``."""
    handlers = SynopsisHandlers(service or SynopsisService(), identify)
    router = APIRouter(prefix=prefix, tags=list(tags), dependencies=list(dependencies or []))
    for path, method, endpoint in handlers.routes():
        router.add_api_route(
            path,
            endpoint,
            methods=[method],
            summary=(endpoint.__doc__ or "").strip() or None,
            name=f"synopsis_{endpoint.__name__}",
        )
    return router
