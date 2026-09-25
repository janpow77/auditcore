"""Optional FastAPI router for the REST contract (extra ``fastapi``).

No ``from __future__ import annotations``: FastAPI resolves the endpoint
annotations at runtime and the framework types are imported locally.

Registered without decorators (``add_api_route``) so the module stays fully
typed. ``current_user`` is an ordinary FastAPI dependency of the consumer (for
example ``get_current_user``); ``user_id_of`` turns its value into the user id.
"""
from collections.abc import Callable

from ..service import BoardService
from .api import METHODS, KanbanApi
from .asgi import parse_json_body


def _str_id(user: object) -> str | None:
    return None if user is None else str(getattr(user, "id", user))


def create_router(
    service: BoardService,
    current_user: Callable[..., object],
    *,
    user_id_of: Callable[[object], str | None] = _str_id,
) -> object:
    """``APIRouter`` with one catch-all route; include it with a prefix."""
    from fastapi import APIRouter, Depends, Request
    from fastapi.responses import JSONResponse, Response

    api = KanbanApi(service)
    router = APIRouter()

    async def endpoint(
        path: str, request: Request, user: object = Depends(current_user)
    ) -> Response:
        ok, body = parse_json_body(await request.body())
        if not ok:
            error = {"error": {"code": "INVALID_REQUEST", "message": "Ungültiges JSON"}}
            return JSONResponse(error, status_code=422)
        result = api.handle(
            request.method, "/" + path.strip("/"), user_id=user_id_of(user),
            query=dict(request.query_params), body=body,
            if_match=request.headers.get("if-match"),
        )
        if result.status == 204:
            return Response(status_code=204, headers=result.headers)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers)

    router.add_api_route("/{path:path}", endpoint, methods=list(METHODS),
                         include_in_schema=False)
    return router
