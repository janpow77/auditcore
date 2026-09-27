"""FastAPI-Router des Vertrags ``documents_batch_checks/1`` (Extra ``fastapi``).

Die Endpunkte sind die Starlette-Handler (Antworten byteidentisch);
Anmeldung über ``dependencies`` des Routers.
"""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter, params

from auditcore_documents.web.batch_checks import BatchCheckService
from auditcore_documents.web.batch_checks_asgi import BatchCheckHandlers


def create_batch_check_router(
    service: BatchCheckService,
    *,
    prefix: str = "",
    tags: Sequence[str] = ("Bestandsprüfung",),
    dependencies: Sequence[params.Depends] | None = None,
) -> APIRouter:
    """``app.include_router(create_batch_check_router(service), prefix="/api/batch-checks")``."""
    handlers = BatchCheckHandlers(service)
    router = APIRouter(prefix=prefix, tags=list(tags), dependencies=list(dependencies or []))
    for path, method, endpoint in handlers.routes():
        router.add_api_route(
            path,
            endpoint,
            methods=[method],
            summary=(endpoint.__doc__ or "").strip().splitlines()[0] or None,
            name=f"batch_checks_{endpoint.__name__}",
        )
    return router
