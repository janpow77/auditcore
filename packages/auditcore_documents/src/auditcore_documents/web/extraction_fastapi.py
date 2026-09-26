"""FastAPI-Router des Vertrags ``documents_extraction/1`` (Extra ``fastapi``).

Die Endpunkte sind die Starlette-Handler (Antworten byteidentisch);
Anmeldung über ``dependencies`` des Routers.
"""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter, params

from auditcore_documents.web.extraction import ExtractionService
from auditcore_documents.web.extraction_asgi import ExtractionHandlers


def create_extraction_router(
    service: ExtractionService,
    *,
    prefix: str = "",
    tags: Sequence[str] = ("Belegerkennung",),
    dependencies: Sequence[params.Depends] | None = None,
) -> APIRouter:
    """``app.include_router(create_extraction_router(service), prefix="/api/extraction")``."""
    handlers = ExtractionHandlers(service)
    router = APIRouter(prefix=prefix, tags=list(tags), dependencies=list(dependencies or []))
    for path, method, endpoint in handlers.routes():
        router.add_api_route(
            path,
            endpoint,
            methods=[method],
            summary=(endpoint.__doc__ or "").strip().splitlines()[0] or None,
            name=f"extraction_{endpoint.__name__}",
        )
    return router
