"""HTTP dispatch of the template endpoints (shared by the Starlette and FastAPI adapters)."""

from __future__ import annotations

import json
from collections.abc import Callable
from urllib.parse import parse_qs

from ._http import Reply, decode, disposition
from .contract import ContractError
from .service import MAX_BODY_BYTES
from .templates_service import (
    TemplateCatalogue,
    template_detail,
    template_list,
    template_preview,
    template_render,
)


def _json(status: int, data: object) -> Reply:
    return Reply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"))


def _guard(action: Callable[[], Reply]) -> Reply:
    try:
        return action()
    except ContractError as exc:
        return _json(exc.status, exc.to_dict())


def handle_list(catalogue: TemplateCatalogue) -> Reply:
    """``GET /templates``."""
    return _json(200, template_list(catalogue))


def handle_detail(catalogue: TemplateCatalogue, template_id: str, query: str = "") -> Reply:
    """``GET /templates/{id}?version=…``."""
    version = parse_qs(query).get("version", [None])[0]
    return _guard(lambda: _json(200, template_detail(catalogue, template_id, version)))


def handle_template_preview(
    catalogue: TemplateCatalogue, template_id: str, raw: bytes, limit: int = MAX_BODY_BYTES
) -> Reply:
    """``POST /templates/{id}/preview``."""
    return _guard(lambda: _json(200, template_preview(catalogue, template_id, decode(raw, limit))))


def handle_template_render(
    catalogue: TemplateCatalogue, template_id: str, raw: bytes, limit: int = MAX_BODY_BYTES
) -> Reply:
    """``POST /templates/{id}/render``: the document as attachment with provenance headers."""

    def run() -> Reply:
        content, filename, media_type, headers = template_render(
            catalogue, template_id, decode(raw, limit)
        )
        return Reply(
            200, content, media_type, {"Content-Disposition": disposition(filename), **headers}
        )

    return _guard(run)
