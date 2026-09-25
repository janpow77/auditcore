"""Starlette ASGI app for the REST contract (extra ``ui``).

Starlette is imported only inside :func:`create_app`; the core stays stdlib-only.
The consumer injects the identity: a function from the request headers
(lower-case names) to a user id or None. ``ui_directory`` is the prepared
mount point for the embedded board UI (served under ``/ui``); no assets ship yet.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

from ..service import BoardService
from .api import METHODS, KanbanApi

Identity = Callable[[Mapping[str, str]], str | None]


def parse_json_body(raw: bytes) -> tuple[bool, object]:
    """(ok, value); an empty body is ``None``."""
    if not raw.strip():
        return True, None
    try:
        return True, json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, None


def create_app(
    service: BoardService,
    identity: Identity,
    *,
    ui_directory: Path | None = None,
) -> object:
    """Starlette application; mount it under any prefix (e.g. ``/api/kanban``)."""
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Mount, Route
    from starlette.staticfiles import StaticFiles

    api = KanbanApi(service)

    async def endpoint(request: Request) -> Response:
        ok, body = parse_json_body(await request.body())
        if not ok:
            error = {"error": {"code": "INVALID_REQUEST", "message": "Ungültiges JSON"}}
            return JSONResponse(error, status_code=422)
        headers = {k.lower(): v for k, v in request.headers.items()}
        result = api.handle(
            request.method, "/" + request.path_params["path"].strip("/"),
            user_id=identity(headers), query=dict(request.query_params), body=body,
            if_match=headers.get("if-match"),
        )
        if result.status == 204:
            return Response(status_code=204, headers=result.headers)
        return JSONResponse(result.body, status_code=result.status, headers=result.headers)

    routes: list[Route | Mount] = []
    if ui_directory is not None:
        routes.append(Mount("/ui", app=StaticFiles(directory=ui_directory, html=True)))
    routes.append(Route("/{path:path}", endpoint, methods=list(METHODS)))
    return Starlette(routes=routes)
