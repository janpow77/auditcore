"""REST contract ``auditcore_extrapolation.evaluation/1`` (extra ``web``).

The contract functions (:func:`catalogue`, :func:`evaluate`, :func:`residual`,
:func:`export_evaluation`) are framework-free. :func:`create_app` and
:func:`routes` need Starlette (``pip install auditcore_extrapolation[web]``);
:func:`create_router` additionally needs FastAPI. Contract:
``docs/ui/extrapolation-rest.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._contract import CONTRACT, ContractError
from ._http import MAX_BODY_BYTES
from .catalogue import catalogue
from .export import ExportFile, export_evaluation
from .requests import evaluate, fingerprint, residual

if TYPE_CHECKING:
    from fastapi import APIRouter
    from starlette.applications import Starlette
    from starlette.routing import Route

__all__ = [
    "CONTRACT",
    "ContractError",
    "ExportFile",
    "catalogue",
    "create_app",
    "create_router",
    "evaluate",
    "export_evaluation",
    "fingerprint",
    "residual",
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
    """FastAPI router (extra ``web`` plus ``fastapi``)."""
    from .fastapi_router import create_router as build

    return build(prefix, max_body_bytes=max_body_bytes)
