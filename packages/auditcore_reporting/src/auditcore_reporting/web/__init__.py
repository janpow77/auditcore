"""REST contract ``reporting_ui/1`` for the table export UI (extras ``web``, ``fastapi``).

:func:`catalogue`, :func:`preview` and :func:`export` are framework-free and
only call :func:`auditcore_reporting.get_profile_format` and
:func:`auditcore_reporting.render_workbook`. :func:`create_app`/:func:`routes`
need Starlette (``pip install auditcore_reporting[web]``), :func:`create_router`
additionally FastAPI (``[fastapi]``); the XLSX export itself needs ``[excel]``.
Contract: ``docs/ui/reporting-rest.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contract import CONTRACT, ContractError, parse_request
from .service import MAX_BODY_BYTES, catalogue, excel_available, export, preview

if TYPE_CHECKING:
    from fastapi import APIRouter
    from starlette.applications import Starlette
    from starlette.routing import Route

__all__ = [
    "CONTRACT",
    "ContractError",
    "catalogue",
    "create_app",
    "create_router",
    "excel_available",
    "export",
    "parse_request",
    "preview",
    "routes",
]


def create_app(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> Starlette:
    """Standalone Starlette application (extra ``web``)."""
    from .starlette_app import create_app as build

    return build(prefix, max_body_bytes=max_body_bytes)


def routes(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> list[Route]:
    """Starlette routes for mounting (extra ``web``)."""
    from .starlette_app import routes as build

    return build(prefix, max_body_bytes=max_body_bytes)


def create_router(prefix: str = "", *, max_body_bytes: int = MAX_BODY_BYTES) -> APIRouter:
    """FastAPI router (extras ``web`` and ``fastapi``)."""
    from .fastapi_router import create_router as build

    return build(prefix, max_body_bytes=max_body_bytes)
