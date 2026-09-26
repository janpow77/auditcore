"""REST contract ``identifiers_ui/1`` for "Kennung prüfen" (extras ``web``, ``fastapi``).

:func:`catalogue`, :func:`check_one` and :func:`check_batch` are framework-free.
:func:`create_app`/:func:`routes` need Starlette
(``pip install auditcore_identifiers[web]``), :func:`create_router`
additionally FastAPI (``[fastapi]``). Contract: ``docs/ui/identifiers-rest.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contract import CONTRACT, ContractError, Limits, catalogue, check_batch, check_one

if TYPE_CHECKING:
    from fastapi import APIRouter
    from starlette.applications import Starlette
    from starlette.routing import Route

__all__ = [
    "CONTRACT",
    "ContractError",
    "Limits",
    "catalogue",
    "check_batch",
    "check_one",
    "create_app",
    "create_router",
    "routes",
]


def create_app(prefix: str = "", *, limits: Limits | None = None) -> Starlette:
    """Standalone Starlette application (extra ``web``)."""
    from .starlette_app import create_app as build

    return build(prefix, limits=limits)


def routes(prefix: str = "", *, limits: Limits | None = None) -> list[Route]:
    """Starlette routes for mounting (extra ``web``)."""
    from .starlette_app import routes as build

    return build(prefix, limits=limits)


def create_router(prefix: str = "", *, limits: Limits | None = None) -> APIRouter:
    """FastAPI router (extras ``web`` and ``fastapi``)."""
    from .fastapi_router import create_router as build

    return build(prefix, limits=limits)
