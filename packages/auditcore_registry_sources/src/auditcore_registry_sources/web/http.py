"""Starlette adapter of the review service (extra ``web``).

``create_routes`` returns routes to mount into the consumer's application,
``create_app`` a standalone Starlette app. The consumer supplies
``identify``: it maps a request to the authenticated :class:`Actor` (or
``None`` → 401). Screening runs are CPU-bound and run in the thread pool.
Write requests must be ``application/json``, which keeps plain HTML forms
from other origins out; session-cookie consumers add their own CSRF check.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable
from typing import Any

from .contract import Actor, ReviewError
from .service import ScreeningReviewService

try:  # extra ``web``; the rest of the package works without it
    from starlette.applications import Starlette
    from starlette.concurrency import run_in_threadpool
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route
except ImportError as exc:  # pragma: no cover - exercised without the extra
    raise ImportError(
        "Für die REST-Schnittstelle ist 'auditcore_registry_sources[web]' zu installieren."
    ) from exc

IdentityResolver = Callable[[Request], "Actor | None | Awaitable[Actor | None]"]
MAX_BODY = 256 * 1024


def _error(exc: ReviewError) -> JSONResponse:
    return JSONResponse(exc.to_dict(), status_code=exc.status)


async def _actor(request: Request, identify: IdentityResolver) -> Actor:
    found = identify(request)
    actor = await found if inspect.isawaitable(found) else found
    if actor is None:
        raise ReviewError(401, "unauthenticated", "Anmeldung erforderlich.")
    return actor


async def read_json(request: Request) -> Any:
    """JSON body with content-type and size checks."""
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type != "application/json":
        raise ReviewError(415, "unsupported_media_type", "Anfragen sind als JSON zu senden.")
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BODY:
        raise ReviewError(413, "too_large", "Die Anfrage ist zu groß.")
    raw = await request.body()
    if len(raw) > MAX_BODY:
        raise ReviewError(413, "too_large", "Die Anfrage ist zu groß.")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ReviewError(400, "invalid_json", "Die Anfrage ist kein gültiges JSON.") from exc


Handler = Callable[[Request, Actor], Awaitable[Any]]


def _endpoint(
    handler: Handler, identify: IdentityResolver, *, status: int = 200
) -> Callable[[Request], Awaitable[JSONResponse]]:
    async def endpoint(request: Request) -> JSONResponse:
        try:
            actor = await _actor(request, identify)
            payload = await handler(request, actor)
        except ReviewError as exc:
            return _error(exc)
        return JSONResponse(payload, status_code=status, headers={"Cache-Control": "no-store"})

    return endpoint


def create_routes(service: ScreeningReviewService, identify: IdentityResolver) -> list[Route]:
    """Routes of contract ``auditcore_registry_sources.screening_review/1``."""

    async def settings(_request: Request, _actor: Actor) -> Any:
        return await run_in_threadpool(service.settings)

    async def sources(_request: Request, _actor: Actor) -> Any:
        return await run_in_threadpool(service.sources)

    async def runs(_request: Request, _actor: Actor) -> Any:
        return await run_in_threadpool(service.list_runs)

    async def create_run(request: Request, actor: Actor) -> Any:
        body = await read_json(request)
        return await run_in_threadpool(service.create_run, body, actor)

    async def get_run(request: Request, _actor: Actor) -> Any:
        query = dict(request.query_params)
        return await run_in_threadpool(service.get_run, request.path_params["run_id"], query)

    async def log(request: Request, _actor: Actor) -> Any:
        return await run_in_threadpool(service.log, request.path_params["run_id"])

    async def decide(request: Request, actor: Actor) -> Any:
        body = await read_json(request)
        params = request.path_params
        return await run_in_threadpool(
            service.decide, params["run_id"], params["hit_id"], body, actor
        )

    async def second_review(request: Request, actor: Actor) -> Any:
        body = await read_json(request)
        params = request.path_params
        return await run_in_threadpool(
            service.second_review, params["run_id"], params["hit_id"], body, actor
        )

    def ep(handler: Handler, status: int = 200) -> Callable[[Request], Awaitable[JSONResponse]]:
        return _endpoint(handler, identify, status=status)

    hit = "/runs/{run_id:str}/hits/{hit_id:str}"
    return [
        Route("/settings", ep(settings), methods=["GET"]),
        Route("/sources", ep(sources), methods=["GET"]),
        Route("/runs", ep(runs), methods=["GET"]),
        Route("/runs", ep(create_run, 201), methods=["POST"]),
        Route("/runs/{run_id:str}", ep(get_run), methods=["GET"]),
        Route("/runs/{run_id:str}/log", ep(log), methods=["GET"]),
        Route(f"{hit}/decision", ep(decide), methods=["POST"]),
        Route(f"{hit}/second-review", ep(second_review), methods=["POST"]),
    ]


def create_app(
    service: ScreeningReviewService,
    identify: IdentityResolver,
    *,
    prefix: str = "/api/screening",
) -> Starlette:
    """Standalone Starlette app with the routes mounted under ``prefix``."""
    return Starlette(routes=[Mount(prefix, routes=create_routes(service, identify))])
