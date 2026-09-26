"""REST-Anbindung der Synopse-Oberfläche (``<flowaudit-synopsis>``) und der Belegerkennung.

Der Dienst (:class:`SynopsisService`), die Ablage und die Ausgaben kommen mit
der Standardbibliothek aus. ``create_app`` (Starlette, Extra ``web``) und
``create_router`` (FastAPI, Extra ``fastapi``) werden erst beim Zugriff
geladen, damit ``import auditcore_documents.web`` ohne Extras funktioniert.
Vertrag: ``docs/ui/synopsis-rest.md`` im Repository.

Belegerkennung (Vertrag ``documents_extraction/1``, ``docs/ui/extraction-rest.md``):
:class:`ExtractionService` mit den OCR-/Donut-Ports der Anwendung
(:class:`ExtractionEngines`); ``create_extraction_app``/``extraction_routes``
(Extra ``web``) und ``create_extraction_router`` (Extra ``fastapi``).
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
from auditcore_documents.web.extraction import (
    CONTRACT as EXTRACTION_CONTRACT,
)
from auditcore_documents.web.extraction import (
    ExtractionEngines,
    ExtractionError,
    ExtractionService,
    ExtractionSettings,
)
from auditcore_documents.web.extraction_result import Thresholds
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
    from auditcore_documents.web.extraction_asgi import create_extraction_app, extraction_routes
    from auditcore_documents.web.extraction_fastapi import create_extraction_router
    from auditcore_documents.web.fastapi_router import create_router

_LAZY = {
    "create_app": ("auditcore_documents.web.asgi", "web"),
    "single_user": ("auditcore_documents.web.asgi", "web"),
    "create_router": ("auditcore_documents.web.fastapi_router", "fastapi"),
    "create_extraction_app": ("auditcore_documents.web.extraction_asgi", "web"),
    "extraction_routes": ("auditcore_documents.web.extraction_asgi", "web"),
    "create_extraction_router": ("auditcore_documents.web.extraction_fastapi", "fastapi"),
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
    "EXTRACTION_CONTRACT",
    "ExtractionEngines",
    "ExtractionError",
    "ExtractionService",
    "ExtractionSettings",
    "Thresholds",
    "create_extraction_app",
    "create_extraction_router",
    "extraction_routes",
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
