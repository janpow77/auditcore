"""Framework-neutral request dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass

from ..errors import GeoError
from ._contract import Body, ContractError
from .calculations import catalogue, from_utm, locate, radius_search, to_utm
from .geocoding import GeocoderError
from .geopackage import read_geopackage, read_source
from .settings import Settings
from .simplification import simplify


@dataclass(frozen=True)
class Reply:
    """Status and JSON body of one response."""

    status: int
    body: bytes


def _clean(value: object) -> object:
    """Non-finite floats become text so every body stays valid JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def _json(status: int, data: object) -> Reply:
    return Reply(status, json.dumps(_clean(data), ensure_ascii=False).encode("utf-8"))


def decode(raw: bytes, limit: int) -> object:
    """Parsed JSON body within the size limit."""
    if len(raw) > limit:
        raise ContractError("Anfrage zu groß.", status=413, code="zu_gross")
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("Kein gültiges JSON.", status=400, code="ungueltiges_json") from exc


def _geocode(payload: object, settings: Settings) -> dict[str, object]:
    geocoder = settings.geocoder
    if geocoder is None:
        raise ContractError(
            "Adresssuche ist abgeschaltet (kein Geocoder angeschlossen).",
            status=404,
            code="geocoder_abgeschaltet",
        )
    query = Body.of(payload).text("anfrage", max_length=300)
    return {"treffer": geocoder.search(query), "namensnennung": geocoder.attribution}


Handler = Callable[[object, Settings], dict[str, object]]

JSON_HANDLERS: dict[str, Handler] = {
    "umkreis": radius_search,
    "lage": lambda payload, _: locate(payload),
    "utm": lambda payload, _: to_utm(payload),
    "utm_geographisch": lambda payload, _: from_utm(payload),
    "vereinfachung": simplify,
    "geocode": _geocode,
}


def _guarded(task: Callable[[], dict[str, object]]) -> Reply:
    try:
        return _json(200, task())
    except ContractError as exc:
        return _json(exc.status, exc.to_dict())
    except GeocoderError as exc:
        return _json(exc.status, {"error": {"code": exc.code, "message": str(exc)}})
    except GeoError as exc:
        return _json(422, {"error": {"code": exc.code, "message": str(exc)}})


def get_profile(settings: Settings) -> Reply:
    """``GET /profile``."""
    return _json(200, catalogue(settings))


def get_sources(settings: Settings) -> Reply:
    """``GET /gpkg/quellen``."""
    return _json(200, {"quellen": sorted(settings.gpkg_sources)})


def handle(name: str, raw: bytes, settings: Settings) -> Reply:
    """Run one JSON POST endpoint and map errors to HTTP replies."""
    return _guarded(lambda: JSON_HANDLERS[name](decode(raw, settings.max_body_bytes), settings))


def handle_gpkg(raw: bytes, settings: Settings, table: str | None) -> Reply:
    """``POST /gpkg``: the request body is the GeoPackage file itself."""
    return _guarded(lambda: read_geopackage(raw, settings, table))


def handle_source(name: str, settings: Settings, table: str | None) -> Reply:
    """``GET /gpkg/quellen/{name}``."""
    return _guarded(lambda: read_source(name, settings, table))
