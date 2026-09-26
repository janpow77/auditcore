"""REST interface of the VVT and DSFA UI (``<flowaudit-vvt>``, ``<flowaudit-dsfa>``).

Handlers (:class:`DataProtectionApi`), views and exports need only the
standard library. :func:`create_app`/:func:`routes` (Starlette, extra ``web``)
and :func:`create_router` (FastAPI, extra ``fastapi``) import their framework
lazily. Persistence stays with the consumer: :class:`Storage` bundles the
repository and audit ports of :mod:`auditcore_dataprotection.ports`.
Contract ``dataprotection_ui/1``: ``docs/ui/dataprotection-rest.md``.
"""

from __future__ import annotations

from importlib.util import find_spec
from typing import TYPE_CHECKING

from .backend import Backend, InMemoryStorage, Storage, SystemClock, UuidIds, create_backend
from .contract import CONTRACT, ApiError, JsonObject, Principal, library_error
from .export import (
    EXPORT_FORMATS,
    ExportFile,
    assessment_export,
    csv_cell,
    csv_document,
    register_export,
)
from .service import DataProtectionApi
from .views import profile_view, register_columns

if TYPE_CHECKING:
    from .fastapi_router import create_router
    from .http import MAX_BODY_BYTES, Identify, create_app, read_json, routes

_LAZY = {
    "create_app": ("http", "starlette", "web"),
    "routes": ("http", "starlette", "web"),
    "read_json": ("http", "starlette", "web"),
    "Identify": ("http", "starlette", "web"),
    "MAX_BODY_BYTES": ("http", "starlette", "web"),
    "create_router": ("fastapi_router", "fastapi", "fastapi"),
}


def __getattr__(name: str) -> object:
    if name not in _LAZY:
        raise AttributeError(name)
    module_name, requirement, extra = _LAZY[name]
    if find_spec(requirement) is None:
        raise ImportError(
            f"{name} benötigt das Extra '{extra}' "
            f"(pip install 'auditcore_dataprotection[{extra}]')."
        )
    import importlib

    module = importlib.import_module(f"{__name__}.{module_name}")
    return getattr(module, name)


__all__ = [
    "CONTRACT",
    "EXPORT_FORMATS",
    "MAX_BODY_BYTES",
    "ApiError",
    "Backend",
    "DataProtectionApi",
    "ExportFile",
    "Identify",
    "InMemoryStorage",
    "JsonObject",
    "Principal",
    "Storage",
    "SystemClock",
    "UuidIds",
    "assessment_export",
    "create_app",
    "create_backend",
    "create_router",
    "csv_cell",
    "csv_document",
    "library_error",
    "profile_view",
    "read_json",
    "register_columns",
    "register_export",
    "routes",
]
