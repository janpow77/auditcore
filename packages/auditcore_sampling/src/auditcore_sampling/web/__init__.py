"""REST contract and routes for sampling user interfaces (extra ``web``).

The contract functions (:func:`calculate_size`, :func:`allocate`,
:func:`select`, :func:`export_selection`, :func:`catalogue` and the
guidance-based planning :func:`guidance_catalogue`, :func:`guidance_size`,
:func:`guidance_draw`) are framework-free. :func:`create_app`/:func:`routes` need Starlette
(``pip install auditcore_sampling[web]``); :func:`create_router` additionally
needs FastAPI. Contracts: ``docs/ui/sampling-rest.md`` and
``docs/ui/samplesize-rest.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._http import MAX_BODY_BYTES
from ._validate import ContractError
from .derivation import calculate_size
from .draw import allocate, select
from .export import ExportFile, export_selection
from .guidance_catalogue import guidance_catalogue
from .guidance_plan import draw as guidance_draw
from .guidance_plan import plan_size as guidance_size
from .profiles import catalogue

if TYPE_CHECKING:
    from fastapi import APIRouter
    from starlette.applications import Starlette
    from starlette.routing import Route

__all__ = [
    "ContractError",
    "ExportFile",
    "allocate",
    "calculate_size",
    "catalogue",
    "create_app",
    "create_router",
    "export_selection",
    "guidance_catalogue",
    "guidance_draw",
    "guidance_size",
    "routes",
    "select",
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
