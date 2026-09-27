"""Optional FastAPI router for contract ``reporting_ui/1`` (requires ``fastapi``)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import Response

from ._http import Reply, handle_export, handle_preview, profiles
from ._templates_http import (
    handle_detail,
    handle_list,
    handle_template_preview,
    handle_template_render,
)
from .service import MAX_BODY_BYTES
from .starlette_app import read_limited
from .templates_service import TemplateCatalogue, default_catalogue

Handler = Callable[[bytes, int], Reply]
TemplateHandler = Callable[[TemplateCatalogue, str, bytes, int], Reply]


def _response(reply: Reply) -> Response:
    return Response(reply.body, reply.status, headers=reply.headers, media_type=reply.media_type)


def _post(handler: Handler, limit: int) -> Callable[[Request], Awaitable[Response]]:
    async def run(request: Request) -> Response:
        return _response(handler(await read_limited(request, limit), limit))

    return run


def _template_post(
    handler: TemplateHandler, catalogue: TemplateCatalogue, limit: int
) -> Callable[[Request], Awaitable[Response]]:
    async def run(request: Request) -> Response:
        raw = await read_limited(request, limit)
        return _response(handler(catalogue, request.path_params["template_id"], raw, limit))

    return run


async def _profiles() -> Response:
    return _response(profiles())


def _add_templates(router: APIRouter, catalogue: TemplateCatalogue, limit: int) -> None:
    async def templates() -> Response:
        return _response(handle_list(catalogue))

    async def template(request: Request) -> Response:
        return _response(
            handle_detail(catalogue, request.path_params["template_id"], request.url.query)
        )

    router.add_api_route("/templates", templates, methods=["GET"], summary="Berichtsvorlagen")
    router.add_api_route(
        "/templates/{template_id}", template, methods=["GET"], summary="Datenvertrag"
    )
    router.add_api_route(
        "/templates/{template_id}/preview",
        _template_post(handle_template_preview, catalogue, limit),
        methods=["POST"],
        summary="Vorlagenvorschau",
    )
    router.add_api_route(
        "/templates/{template_id}/render",
        _template_post(handle_template_render, catalogue, limit),
        methods=["POST"],
        summary="Bericht erzeugen",
    )


def create_router(
    prefix: str = "",
    *,
    max_body_bytes: int = MAX_BODY_BYTES,
    templates: TemplateCatalogue | None = None,
) -> APIRouter:
    """APIRouter with the same contract; include it with ``app.include_router``."""
    router = APIRouter(prefix=prefix, tags=["Berichtsexport"])
    router.add_api_route("/profiles", _profiles, methods=["GET"], summary="Formatprofile")
    router.add_api_route(
        "/preview", _post(handle_preview, max_body_bytes), methods=["POST"], summary="Vorschau"
    )
    router.add_api_route(
        "/export", _post(handle_export, max_body_bytes), methods=["POST"], summary="XLSX-Export"
    )
    _add_templates(router, templates or default_catalogue(), max_body_bytes)
    return router
