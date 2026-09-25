"""Optional FastAPI router (extra ``fastapi``) with the same endpoints.

The endpoints are the plain Starlette handlers of :mod:`.http`: FastAPI
injects nothing, the answers are byte-identical to :func:`~.http.create_app`
and the endpoints do not appear in the OpenAPI schema (the contract is
``docs/ui/dataprotection-rest.md``). Authentication and tenant come from
``identify``; ``add_route`` ignores router dependencies, so application checks
such as CSRF belong into ``identify`` or a middleware.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .http import MAX_BODY_BYTES, Identify, endpoints
from .service import DataProtectionApi

if TYPE_CHECKING:
    from fastapi import APIRouter


def create_router(
    api: DataProtectionApi,
    *,
    identify: Identify,
    prefix: str = "",
    max_body_bytes: int = MAX_BODY_BYTES,
) -> APIRouter:
    """``app.include_router(create_router(api, identify=..., prefix="/api/dataprotection"))``."""
    from fastapi import APIRouter

    router = APIRouter(tags=["Datenschutz"])
    for path, method, endpoint in endpoints(api, identify, max_body_bytes):
        router.add_route(
            prefix + path,
            endpoint,
            methods=[method],
            name=f"dataprotection_{endpoint.__name__}_{method.lower()}",
        )
    return router
