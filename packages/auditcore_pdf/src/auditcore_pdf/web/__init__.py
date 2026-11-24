"""REST contract ``pdf_redaction/1`` for "PDF schwärzen" (extras ``web``, ``fastapi``).

:class:`RedactionService` is framework-free. :func:`create_app`/:func:`routes`
need Starlette (``pip install auditcore_pdf[web]``), :func:`create_router`
additionally FastAPI (``[fastapi]``). Contract: ``docs/ui/redaction-rest.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contract import CONTRACT, Applied, ContractError, Limits, RedactionService

if TYPE_CHECKING:
    from fastapi import APIRouter
    from starlette.applications import Starlette
    from starlette.routing import Route

__all__ = [
    "CONTRACT",
    "Applied",
    "ContractError",
    "Limits",
    "RedactionService",
    "create_app",
    "create_router",
    "routes",
]


def create_app(service: RedactionService, prefix: str = "") -> Starlette:
    """Standalone Starlette application (extra ``web``)."""
    from .starlette_app import create_app as build

    return build(service, prefix)


def routes(service: RedactionService, prefix: str = "") -> list[Route]:
    """Starlette routes for mounting (extra ``web``)."""
    from .starlette_app import routes as build

    return build(service, prefix)


def create_router(service: RedactionService, prefix: str = "") -> APIRouter:
    """FastAPI router (extras ``web`` and ``fastapi``)."""
    from .fastapi_router import create_router as build

    return build(service, prefix)
