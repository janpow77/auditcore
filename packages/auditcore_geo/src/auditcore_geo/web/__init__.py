"""REST-Vertrag und Routen für Geo-Oberflächen (Extras ``web`` und ``fastapi``).

Die Vertragsfunktionen (:func:`catalogue`, :func:`radius_search`,
:func:`locate`, :func:`to_utm`, :func:`from_utm`, :func:`simplify`,
:func:`read_geopackage`, :func:`read_source`) sind framework-frei und rufen
nur die bestehende, deutsch benannte Geo-API auf (Entscheidungen D1–D6); die
Web-Schicht selbst trägt wie alle auditcore-Web-Module englische Namen.
:func:`create_app`/:func:`routes` brauchen Starlette
(``pip install auditcore_geo[web]``), :func:`create_router` zusätzlich FastAPI
(``[fastapi]``). Adresssuche nur mit ausdrücklich übergebenem
:class:`Geocoder` (:class:`NominatimGeocoder` braucht ``[geocoder]``).
Vertrag: ``docs/ui/geo-rest.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._contract import ContractError
from .calculations import catalogue, from_utm, locate, radius_search, standard_zone, to_utm
from .geocoding import Geocoder, GeocoderError, NominatimGeocoder
from .geopackage import read_geopackage, read_source
from .settings import Settings
from .simplification import simplify

if TYPE_CHECKING:
    from fastapi import APIRouter
    from starlette.applications import Starlette
    from starlette.routing import Route

__all__ = [
    "ContractError",
    "Geocoder",
    "GeocoderError",
    "NominatimGeocoder",
    "Settings",
    "catalogue",
    "create_app",
    "create_router",
    "from_utm",
    "locate",
    "radius_search",
    "read_geopackage",
    "read_source",
    "routes",
    "simplify",
    "standard_zone",
    "to_utm",
]


def create_app(prefix: str = "", *, settings: Settings | None = None) -> Starlette:
    """Eigenständige Starlette-Anwendung (Extra ``web``)."""
    from .starlette_app import create_app as build

    return build(prefix, settings=settings)


def routes(prefix: str = "", *, settings: Settings | None = None) -> list[Route]:
    """Starlette-Routen zum Einhängen (Extra ``web``)."""
    from .starlette_app import routes as build

    return build(prefix, settings=settings)


def create_router(prefix: str = "", *, settings: Settings | None = None) -> APIRouter:
    """FastAPI-Router (Extras ``web`` und ``fastapi``)."""
    from .fastapi_router import create_router as build

    return build(prefix, settings=settings)
