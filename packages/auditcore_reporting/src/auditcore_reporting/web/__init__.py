"""REST contract ``reporting_ui/1``: table export and report templates (``web``, ``fastapi``).

:func:`catalogue`, :func:`preview` and :func:`export` are framework-free and
only call :func:`auditcore_reporting.get_profile_format` and
:func:`auditcore_reporting.render_workbook`; the template endpoints
(:func:`template_list`, :func:`template_detail`, :func:`template_preview`,
:func:`template_render`) call :mod:`auditcore_reporting.templates`.
:func:`create_app`/:func:`routes` need Starlette
(``pip install auditcore_reporting[web]``), :func:`create_router` additionally
FastAPI (``[fastapi]``); the XLSX export itself needs ``[excel]``, PDF output
``[pdf]`` and Word templates ``[docx]``.
Contract: ``docs/ui/reporting-rest.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contract import CONTRACT, ContractError, parse_request
from .service import MAX_BODY_BYTES, catalogue, excel_available, export, preview
from .templates_service import (
    DataContractError,
    TemplateCatalogue,
    template_detail,
    template_list,
    template_preview,
    template_render,
)

if TYPE_CHECKING:
    from fastapi import APIRouter
    from starlette.applications import Starlette
    from starlette.routing import Route

__all__ = [
    "CONTRACT",
    "ContractError",
    "DataContractError",
    "TemplateCatalogue",
    "catalogue",
    "create_app",
    "create_router",
    "excel_available",
    "export",
    "parse_request",
    "preview",
    "routes",
    "template_detail",
    "template_list",
    "template_preview",
    "template_render",
]


def create_app(
    prefix: str = "",
    *,
    max_body_bytes: int = MAX_BODY_BYTES,
    templates: TemplateCatalogue | None = None,
) -> Starlette:
    """Standalone Starlette application (extra ``web``); ``templates`` defaults to the built-ins."""
    from .starlette_app import create_app as build

    return build(prefix, max_body_bytes=max_body_bytes, templates=templates)


def routes(
    prefix: str = "",
    *,
    max_body_bytes: int = MAX_BODY_BYTES,
    templates: TemplateCatalogue | None = None,
) -> list[Route]:
    """Starlette routes for mounting (extra ``web``)."""
    from .starlette_app import routes as build

    return build(prefix, max_body_bytes=max_body_bytes, templates=templates)


def create_router(
    prefix: str = "",
    *,
    max_body_bytes: int = MAX_BODY_BYTES,
    templates: TemplateCatalogue | None = None,
) -> APIRouter:
    """FastAPI router (extras ``web`` and ``fastapi``)."""
    from .fastapi_router import create_router as build

    return build(prefix, max_body_bytes=max_body_bytes, templates=templates)
