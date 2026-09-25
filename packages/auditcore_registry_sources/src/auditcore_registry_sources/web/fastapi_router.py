"""Optional FastAPI router of the review service (extra ``fastapi``).

Same paths, bodies and errors as the Starlette adapter; the endpoints appear
in the consumer's OpenAPI document. ``identify`` is the same resolver as for
:func:`~.http.create_routes` (FastAPI requests are Starlette requests). The
resolver runs inside each endpoint, so an unauthenticated request gets the
contract's 401 body before anything else is read.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from .contract import ReviewError
from .http import IdentityResolver, _actor, read_json
from .service import ScreeningReviewService

try:
    from fastapi import APIRouter, Request
    from fastapi.concurrency import run_in_threadpool
    from fastapi.responses import JSONResponse
except ImportError as exc:  # pragma: no cover - exercised without FastAPI
    raise ImportError(
        "Für den FastAPI-Router ist 'auditcore_registry_sources[fastapi]' zu installieren."
    ) from exc

Call = Callable[..., object]
Endpoint = Callable[..., Awaitable[JSONResponse]]


class _Responder:
    """Authenticate, optionally read the body, call the service, map errors."""

    def __init__(self, identify: IdentityResolver) -> None:
        self.identify = identify

    async def __call__(
        self, request: Request, call: Call, *args: object, status: int = 200, write: bool = False
    ) -> JSONResponse:
        try:
            actor = await _actor(request, self.identify)
            if write:
                args = (*args, await read_json(request), actor)
            payload = await run_in_threadpool(call, *args)
        except ReviewError as exc:
            return JSONResponse(exc.to_dict(), status_code=exc.status)
        return JSONResponse(payload, status_code=status, headers={"Cache-Control": "no-store"})


def _read_endpoints(
    service: ScreeningReviewService, respond: _Responder
) -> list[tuple[str, str, Endpoint]]:
    async def settings(request: Request) -> JSONResponse:
        return await respond(request, service.settings)

    async def sources(request: Request) -> JSONResponse:
        return await respond(request, service.sources)

    async def runs(request: Request) -> JSONResponse:
        return await respond(request, service.list_runs)

    async def get_run(run_id: str, request: Request) -> JSONResponse:
        return await respond(request, service.get_run, run_id, dict(request.query_params))

    async def log(run_id: str, request: Request) -> JSONResponse:
        return await respond(request, service.log, run_id)

    return [
        ("/settings", "Profile und Prüfregeln", settings),
        ("/sources", "Quellenstand der Listen", sources),
        ("/runs", "Prüfläufe", runs),
        ("/runs/{run_id}", "Prüflauf mit Treffern", get_run),
        ("/runs/{run_id}/log", "Protokoll eines Prüflaufs", log),
    ]


def _write_endpoints(
    service: ScreeningReviewService, respond: _Responder
) -> list[tuple[str, str, Endpoint]]:
    async def create_run(request: Request) -> JSONResponse:
        return await respond(request, service.create_run, status=201, write=True)

    async def decide(run_id: str, hit_id: str, request: Request) -> JSONResponse:
        return await respond(request, service.decide, run_id, hit_id, write=True)

    async def second_review(run_id: str, hit_id: str, request: Request) -> JSONResponse:
        return await respond(request, service.second_review, run_id, hit_id, write=True)

    hit = "/runs/{run_id}/hits/{hit_id}"
    return [
        ("/runs", "Prüflauf anlegen", create_run),
        (f"{hit}/decision", "Treffer entscheiden", decide),
        (f"{hit}/second-review", "Zweitprüfung", second_review),
    ]


def create_router(
    service: ScreeningReviewService,
    identify: IdentityResolver,
    *,
    prefix: str = "/api/screening",
    tags: list[str] | None = None,
) -> APIRouter:
    """APIRouter of contract ``auditcore_registry_sources.screening_review/1``."""
    router = APIRouter(prefix=prefix, tags=list(tags or ["Screening-Trefferprüfung"]))
    respond = _Responder(identify)
    for path, summary, endpoint in _read_endpoints(service, respond):
        router.add_api_route(path, endpoint, methods=["GET"], summary=summary)
    for path, summary, endpoint in _write_endpoints(service, respond):
        status = 201 if path == "/runs" else 200
        router.add_api_route(path, endpoint, methods=["POST"], summary=summary, status_code=status)
    return router
