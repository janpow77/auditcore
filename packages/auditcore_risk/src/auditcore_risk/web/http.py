"""HTTP binding of the risk API for Starlette (extra ``web``) and FastAPI (extra ``fastapi``).

``create_app()`` returns a standalone Starlette application; ``routes()`` the
same endpoints for mounting into an existing Starlette app;
``build_fastapi_router()`` an ``APIRouter`` with identical paths and answers.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from importlib.util import find_spec
from typing import TYPE_CHECKING

from ..errors import DependencyError
from .jsontypes import JsonObject
from .service import (
    MAX_RECORDS,
    ApiError,
    Limits,
    handle_check_columns,
    handle_evaluate,
    handle_profile,
    handle_profiles,
)

if TYPE_CHECKING:
    from fastapi import APIRouter
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route

#: Default upper bound of a request body in bytes.
MAX_BODY_BYTES = 20 * 1024 * 1024


def _require(module: str, extra: str) -> None:
    if find_spec(module) is None:
        raise DependencyError(f"Die Web-Schnittstelle verlangt 'auditcore_risk[{extra}]'.")


def _json(data: JsonObject, status: int = 200) -> JSONResponse:
    from starlette.responses import JSONResponse

    return JSONResponse(data, status_code=status)


async def _body(request: Request, max_bytes: int) -> object:
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > max_bytes:
        raise ApiError(413, "body_too_large", f"Anfrage größer als {max_bytes} Byte.")
    raw = await request.body()
    if len(raw) > max_bytes:
        raise ApiError(413, "body_too_large", f"Anfrage größer als {max_bytes} Byte.")
    try:
        decoded: object = json.loads(raw)
        return decoded
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(400, "invalid_json", "Anfrage ist kein gültiges JSON.") from exc


Handler = Callable[["Request"], Awaitable["JSONResponse"]]


def _guarded(handler: Callable[[Request], Awaitable[JsonObject]]) -> Handler:
    async def endpoint(request: Request) -> JSONResponse:
        try:
            return _json(await handler(request))
        except ApiError as exc:
            return _json(exc.to_dict(), exc.status)

    return endpoint


def routes(max_records: int = MAX_RECORDS, max_body_bytes: int = MAX_BODY_BYTES) -> list[Route]:
    """Starlette routes (paths relative to the mount point)."""
    _require("starlette", "web")
    from starlette.concurrency import run_in_threadpool
    from starlette.routing import Route

    limits = Limits(max_records=max_records)

    async def profiles(request: Request) -> JsonObject:
        return handle_profiles()

    async def profile(request: Request) -> JsonObject:
        params = request.path_params
        return handle_profile(params["profile_id"], params["version"])

    async def check_columns(request: Request) -> JsonObject:
        params = request.path_params
        body = await _body(request, max_body_bytes)
        return handle_check_columns(params["profile_id"], params["version"], body)

    async def evaluate(request: Request) -> JsonObject:
        body = await _body(request, max_body_bytes)
        # CPU-bound evaluation off the event loop.
        result: JsonObject = await run_in_threadpool(handle_evaluate, body, limits)
        return result

    base = "/profiles/{profile_id}/{version}"
    return [
        Route("/profiles", _guarded(profiles), methods=["GET"]),
        Route(base, _guarded(profile), methods=["GET"]),
        Route(f"{base}/check-columns", _guarded(check_columns), methods=["POST"]),
        Route("/evaluate", _guarded(evaluate), methods=["POST"]),
    ]


def create_app(
    prefix: str = "/risk",
    *,
    max_records: int = MAX_RECORDS,
    max_body_bytes: int = MAX_BODY_BYTES,
) -> Starlette:
    """Standalone Starlette app with the API under ``prefix`` (``""`` = root)."""
    _require("starlette", "web")
    from starlette.applications import Starlette
    from starlette.routing import Mount

    inner = routes(max_records, max_body_bytes)
    return Starlette(routes=[Mount(prefix, routes=inner)] if prefix else inner)


def build_fastapi_router(
    prefix: str = "/risk",
    *,
    max_records: int = MAX_RECORDS,
    max_body_bytes: int = MAX_BODY_BYTES,
) -> APIRouter:
    """FastAPI ``APIRouter`` with the same endpoints (for ``app.include_router``).

    The endpoints are documented in ``docs/ui/risk-rest.md``, not in FastAPI's
    OpenAPI schema.
    """
    _require("fastapi", "fastapi")
    from fastapi import APIRouter

    router = APIRouter(tags=["risk"])
    # Plain Starlette endpoints (Request in, JSONResponse out): FastAPI injects nothing,
    # answers are byte-identical to create_app(); they do not appear in the OpenAPI schema.
    # ``add_route`` ignores the router prefix, so the prefix is part of each path.
    for route in routes(max_records, max_body_bytes):
        router.add_route(prefix + route.path, route.endpoint, methods=sorted(route.methods or ()))
    return router
