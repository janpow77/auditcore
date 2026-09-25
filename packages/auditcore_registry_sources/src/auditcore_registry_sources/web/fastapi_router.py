"""Optional FastAPI router of the review service (FastAPI installed by the consumer).

Same paths, bodies and errors as the Starlette adapter; the endpoints appear
in the consumer's OpenAPI document. ``identify`` is the same resolver as for
:func:`~.http.create_routes` (FastAPI requests are Starlette requests).

No ``from __future__ import annotations`` here: FastAPI evaluates the
endpoint annotations, which refer to the local dependency of the router.
"""

from typing import Annotated, Any

from .contract import Actor, ReviewError
from .http import IdentityResolver, _actor, read_json
from .service import ScreeningReviewService

try:
    from fastapi import APIRouter, Depends, Request
    from fastapi.concurrency import run_in_threadpool
    from fastapi.responses import JSONResponse
except ImportError as exc:  # pragma: no cover - exercised without FastAPI
    raise ImportError("Für den FastAPI-Router ist FastAPI zu installieren.") from exc


async def _respond(
    found: Actor | ReviewError,
    call: Any,
    *args: Any,
    status: int = 200,
    request: Request | None = None,
) -> JSONResponse:
    """Run a service call; write endpoints (``request`` given) get body and actor appended."""
    try:
        if isinstance(found, ReviewError):
            raise found
        if request is not None:
            args = (*args, await read_json(request), found)
        payload = await run_in_threadpool(call, *args)
    except ReviewError as exc:
        return JSONResponse(exc.to_dict(), status_code=exc.status)
    return JSONResponse(payload, status_code=status, headers={"Cache-Control": "no-store"})


def _read_routes(router: APIRouter, service: ScreeningReviewService, found_actor: Any) -> None:
    @router.get("/settings", summary="Profile und Prüfregeln")
    async def settings(found: found_actor) -> Any:
        return await _respond(found, service.settings)

    @router.get("/sources", summary="Quellenstand der Listen")
    async def sources(found: found_actor) -> Any:
        return await _respond(found, service.sources)

    @router.get("/runs", summary="Prüfläufe")
    async def runs(found: found_actor) -> Any:
        return await _respond(found, service.list_runs)

    @router.get("/runs/{run_id}", summary="Prüflauf mit Treffern")
    async def get_run(run_id: str, request: Request, found: found_actor) -> Any:
        return await _respond(found, service.get_run, run_id, dict(request.query_params))

    @router.get("/runs/{run_id}/log", summary="Protokoll eines Prüflaufs")
    async def log(run_id: str, found: found_actor) -> Any:
        return await _respond(found, service.log, run_id)


def _write_routes(router: APIRouter, service: ScreeningReviewService, found_actor: Any) -> None:
    @router.post("/runs", status_code=201, summary="Prüflauf anlegen")
    async def create_run(request: Request, found: found_actor) -> Any:
        return await _respond(found, service.create_run, status=201, request=request)

    @router.post("/runs/{run_id}/hits/{hit_id}/decision", summary="Treffer entscheiden")
    async def decide(run_id: str, hit_id: str, request: Request, found: found_actor) -> Any:
        return await _respond(found, service.decide, run_id, hit_id, request=request)

    @router.post("/runs/{run_id}/hits/{hit_id}/second-review", summary="Zweitprüfung")
    async def second_review(run_id: str, hit_id: str, request: Request, found: found_actor) -> Any:
        return await _respond(found, service.second_review, run_id, hit_id, request=request)


def create_router(
    service: ScreeningReviewService,
    identify: IdentityResolver,
    *,
    prefix: str = "/api/screening",
    tags: list[str] | None = None,
) -> APIRouter:
    """APIRouter of contract ``auditcore_registry_sources.screening_review/1``."""
    router = APIRouter(prefix=prefix, tags=list(tags or ["Screening-Trefferprüfung"]))

    async def actor(request: Request) -> Actor | ReviewError:
        try:
            return await _actor(request, identify)
        except ReviewError as exc:
            return exc

    found_actor = Annotated[Any, Depends(actor)]
    _read_routes(router, service, found_actor)
    _write_routes(router, service, found_actor)
    return router
