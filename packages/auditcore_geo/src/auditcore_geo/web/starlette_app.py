"""Starlette routes for the geo REST contract (extra ``web``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ._http import Reply, get_profile, get_sources, handle, handle_gpkg, handle_source
from .settings import Settings

ENDPOINTS = (
    ("/umkreis", "umkreis"),
    ("/lage", "lage"),
    ("/utm", "utm"),
    ("/utm/geographisch", "utm_geographisch"),
    ("/vereinfachung", "vereinfachung"),
    ("/geocode", "geocode"),
)


def response(reply: Reply) -> Response:
    """Starlette response of a framework-neutral reply."""
    return Response(reply.body, reply.status, media_type="application/json")


async def read_limited(request: Request, limit: int) -> bytes:
    """Request body, read at most one byte beyond ``limit`` (the handler rejects it)."""
    chunks, size = [], 0
    async for chunk in request.stream():
        chunks.append(chunk)
        size += len(chunk)
        if size > limit:
            break
    return b"".join(chunks)


def routes(prefix: str = "", *, settings: Settings | None = None) -> list[Route]:
    """Routes below ``prefix`` (e.g. ``/api/geo``) for mounting in an application."""
    settings = settings or Settings()

    async def catalogue(_: Request) -> Response:
        return response(get_profile(settings))

    async def sources(_: Request) -> Response:
        return response(get_sources(settings))

    async def source(request: Request) -> Response:
        name = str(request.path_params["name"])
        return response(handle_source(name, settings, request.query_params.get("tabelle")))

    async def upload(request: Request) -> Response:
        raw = await read_limited(request, settings.max_gpkg_bytes)
        return response(handle_gpkg(raw, settings, request.query_params.get("tabelle")))

    def endpoint(name: str) -> Callable[[Request], Awaitable[Response]]:
        async def run(request: Request) -> Response:
            raw = await read_limited(request, settings.max_body_bytes)
            return response(handle(name, raw, settings))

        return run

    result = [
        Route(f"{prefix}/profile", catalogue, methods=["GET"]),
        Route(f"{prefix}/gpkg", upload, methods=["POST"]),
        Route(f"{prefix}/gpkg/quellen", sources, methods=["GET"]),
        Route(f"{prefix}/gpkg/quellen/{{name}}", source, methods=["GET"]),
    ]
    result += [Route(prefix + path, endpoint(name), methods=["POST"]) for path, name in ENDPOINTS]
    return result


def create_app(prefix: str = "", *, settings: Settings | None = None) -> Starlette:
    """Standalone ASGI application; authentication and CORS stay with the host."""
    return Starlette(routes=routes(prefix, settings=settings))
