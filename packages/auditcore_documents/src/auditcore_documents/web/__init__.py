"""REST-Anbindung der Synopse-Oberfläche (``<flowaudit-synopsis>``).

Der Dienst (:class:`SynopsisService`), die Ablage und die Ausgaben kommen mit
der Standardbibliothek aus. ``create_app`` (Starlette, Extra ``web``) und
``create_router`` (FastAPI, Extra ``fastapi``) werden erst beim Zugriff
geladen, damit ``import auditcore_documents.web`` ohne Extras funktioniert.
Vertrag: ``docs/ui/synopsis-rest.md`` im Repository.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from auditcore_documents.web.export import (
    EXPORT_FORMATS,
    ExportFile,
    ExportSettings,
    export_comparison,
    render_markdown,
)
from auditcore_documents.web.options import RequestError
from auditcore_documents.web.service import (
    ServiceSettings,
    SynopsisService,
    Upload,
    error_status,
    safe_filename,
)
from auditcore_documents.web.store import (
    ComparisonStore,
    InMemoryComparisonStore,
    StoredComparison,
)

if TYPE_CHECKING:
    from auditcore_documents.web.asgi import create_app, single_user
    from auditcore_documents.web.fastapi_router import create_router

_LAZY = {
    "create_app": ("auditcore_documents.web.asgi", "web"),
    "single_user": ("auditcore_documents.web.asgi", "web"),
    "create_router": ("auditcore_documents.web.fastapi_router", "fastapi"),
}


def __getattr__(name: str) -> object:
    if name not in _LAZY:
        raise AttributeError(name)
    module_name, extra = _LAZY[name]
    import importlib

    from auditcore_documents.errors import DependencyError

    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise DependencyError(
            f"{name} benötigt das Extra '{extra}' (pip install 'auditcore_documents[{extra}]')."
        ) from exc
    return getattr(module, name)


__all__ = [
    "EXPORT_FORMATS",
    "ComparisonStore",
    "ExportFile",
    "ExportSettings",
    "InMemoryComparisonStore",
    "RequestError",
    "ServiceSettings",
    "StoredComparison",
    "SynopsisService",
    "Upload",
    "create_app",
    "create_router",
    "error_status",
    "export_comparison",
    "render_markdown",
    "safe_filename",
    "single_user",
]
