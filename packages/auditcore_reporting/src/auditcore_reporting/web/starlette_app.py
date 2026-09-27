"""Starlette routes for contract ``reporting_ui/1`` (extra ``web``)."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ._http import Reply, handle_export, handle_preview, profiles
from ._templates_http import (
    handle_detail,
    handle_list,
    handle_template_preview,
    handle_template_render,
)
from .service import MAX_BODY_BYTES
from .templates_service import TemplateCatalogue, default_catalogue


def _response(reply: Reply) -> Response:
    return Response(reply.body, reply.status, headers=reply.headers, media_type=reply.media_type)


async def read_limited(request: Request, limit: int) -> bytes:
    """Request body; reading stops once it exceeds ``limit`` (the handler then rejects it)."""
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > limit:
            break
    return bytes(body)


def _template_routes(prefix: str, limit: int, catalogue: TemplateCatalogue) -> list[Route]:
    async def get_templates(_: Request) -> Response:
        return _response(handle_list(catalogue))

    async def get_template(request: Request) -> Response:
        template_id = request.path_params["template_id"]
        return _response(handle_detail(catalogue, template_id, request.url.query))

    async def post_template_preview(request: Request) -> Response:
        raw = await read_limited(request, limit)
        return _response(
            handle_template_preview(catalogue, request.path_params["template_id"], raw, limit)
        )

    async def post_template_render(request: Request) -> Response:
        raw = await read_limited(request, limit)
        return _response(
            handle_template_render(catalogue, request.path_params["template_id"], raw, limit)
        )

    return [
        Route(f"{prefix}/templates", get_templates, methods=["GET"]),
        Route(f"{prefix}/templates/{{template_id}}", get_template, methods=["GET"]),
        Route(
            f"{prefix}/templates/{{template_id}}/preview", post_template_preview, methods=["POST"]
        ),
        Route(f"{prefix}/templates/{{template_id}}/render", post_template_render, methods=["POST"]),
    ]


def routes(
    prefix: str = "",
    *,
    max_body_bytes: int = MAX_BODY_BYTES,
    templates: TemplateCatalogue | None = None,
) -> list[Route]:
    """Routes below ``prefix`` (e.g. ``/api/reporting``) for mounting in an application."""

    async def get_profiles(_: Request) -> Response:
        return _response(profiles())

    async def post_preview(request: Request) -> Response:
        raw = await read_limited(request, max_body_bytes)
        return _response(handle_preview(raw, max_body_bytes))

    async def post_export(request: Request) -> Response:
        raw = await read_limited(request, max_body_bytes)
        return _response(handle_export(raw, max_body_bytes))

    return [
        Route(f"{prefix}/profiles", get_profiles, methods=["GET"]),
        Route(f"{prefix}/preview", post_preview, methods=["POST"]),
        Route(f"{prefix}/export", post_export, methods=["POST"]),
        *_template_routes(prefix, max_body_bytes, templates or default_catalogue()),
    ]


def create_app(
    prefix: str = "",
    *,
    max_body_bytes: int = MAX_BODY_BYTES,
    templates: TemplateCatalogue | None = None,
) -> Starlette:
    """Standalone ASGI application; authentication and CORS stay with the host."""
    return Starlette(routes=routes(prefix, max_body_bytes=max_body_bytes, templates=templates))
