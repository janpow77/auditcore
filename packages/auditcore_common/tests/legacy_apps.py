"""Verbatim copies of application helpers merged into auditcore_common (differential oracle).

Each block names repository, commit, file and symbol; git blobs are listed in
``provenance.json`` (``sources``). Only the names changed (prefixed with the app)
and one method became a function (``self`` removed, marked in the source list).
"""
# ruff: noqa: E501, ANN001, ANN201, SIM103, UP006, UP035

from __future__ import annotations

import asyncio
import math
import os
import re
import threading
from decimal import Decimal
from typing import Any

#: Module state of flowinvoice ``backend/app/worker/tasks.py``.
_async_loop_state = threading.local()


# audit_designer@4b629dd970e5 backend/app/modules/ecohesion/community/metrics.py :: _anteil
def audit_designer_anteil(teil: int, ganzes: int) -> float:
    """Anteil in Prozent, eine Nachkommastelle. Ohne Grundgesamtheit 0,0."""
    if ganzes <= 0:
        return 0.0
    return round(teil * 100.0 / ganzes, 1)


# flowinvoice@5d5d8c5aded2 backend/app/verwk/pipeline/datenqualitaet.py :: _anteil
def flowinvoice_anteil(n: int, gesamt: int) -> float:
    """Anteil in Prozent (0.0-Fallback)."""
    if gesamt <= 0:
        return 0.0
    return round(n / gesamt * 100.0, 2)


# riskanalysis@dace0f66abde backend/app/pipeline/datenqualitaet.py :: _anteil
def riskanalysis_anteil(n: int, gesamt: int) -> float:
    """Anteil in Prozent (0.0-Fallback)."""
    if gesamt <= 0:
        return 0.0
    return round(n / gesamt * 100.0, 2)


# regulierung@ce76e48c8ad7 backend/app/api/kpang/monitoring.py :: _quote_pct
def regulierung_quote_pct(teil: int, gesamt: int) -> float:
    """Prozentquote, robust gegen Division durch Null (leere DB)."""
    if gesamt <= 0:
        return 0.0
    return round(teil / gesamt * 100, 2)


# audit_designer@4b629dd970e5 backend/app/core/shared/research/register/state_aid.py :: _als_float
def audit_designer_als_float(wert: Any) -> float | None:
    if wert is None:
        return None
    if isinstance(wert, Decimal):
        return float(wert)
    try:
        return float(wert)
    except (TypeError, ValueError):
        return None


# audit_designer@4b629dd970e5 backend/app/core/shared/research/register/state_aid.py :: _als_zahl
def audit_designer_als_zahl(wert: Any) -> float | None:
    if wert in (None, ""):
        return None
    try:
        return float(wert)
    except (TypeError, ValueError):
        return None


# audit_designer@4b629dd970e5 backend/app/modules/vp_ai/services/pdb_import_service.py :: _float
def audit_designer_pdb_float(val: Any) -> float | None:
    """Coerce a cell value to float or None."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# audit_designer@4b629dd970e5 backend/app/core/shared/research/register/beneficiaries.py :: _als_float
def audit_designer_beneficiaries_als_float(wert: Any) -> float | None:
    if wert is None:
        return None
    if isinstance(wert, (int, float)):
        zahl = float(wert)
        return None if math.isnan(zahl) else zahl
    try:
        return float(str(wert).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


# audit-portal@72cc4b1a15fd backend/app/modules/company_research/read_model_service.py :: _to_float
def audit_portal_to_float(value: Any) -> float | None:
    """Wandelt einen numerischen Wert in ``float`` (oder None)."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# flowinvoice@5d5d8c5aded2 backend/app/verwk/services/modellguete.py :: _zahl
def flowinvoice_zahl(wert: Any) -> float | None:
    try:
        if wert is None:
            return None
        return float(wert)
    except (TypeError, ValueError):
        return None


# regulierung@ce76e48c8ad7 backend/scripts/import_tankerkoenig_history.py :: _safe_float
def regulierung_safe_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


# versteigerung@729f9a10bc54 backend/app/api/routers/auctions.py :: _money_float
def versteigerung_money_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# versteigerung@729f9a10bc54 backend/app/services/data_quality.py :: _to_float
def versteigerung_to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# audit_designer@4b629dd970e5 backend/app/api/document_comparisons.py :: _safe_filename
def audit_designer_comparison_filename(filename: str | None) -> str:
    value = os.path.basename(filename or "datei")
    value = re.sub(r"[^\w.()\- äöüÄÖÜß]", "_", value).strip(" .")
    return value[:255] or "datei"


# audit_designer@4b629dd970e5 backend/app/api/vpai_notebook/jupyter.py :: _safe_filename
def audit_designer_jupyter_filename(filename: str | None, fallback: str = "download") -> str:
    """Strip directories/control characters from browser supplied filenames."""
    candidate = (filename or fallback).replace("\\", "/").split("/")[-1]
    candidate = "".join(char for char in candidate if ord(char) >= 32).strip()
    if candidate in ("", ".", ".."):
        candidate = fallback
    return candidate[:255]


# audit_designer@4b629dd970e5 backend/app/services/presentation_export_service.py :: _safe_filename
def audit_designer_presentation_filename(filename: str) -> str:
    """Entfernt unsichere Zeichen aus Dateinamen."""
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, "_")
    return filename.strip()


# audit-portal@72cc4b1a15fd backend/app/api/vvt_templates.py :: _safe_filename
def audit_portal_vvt_filename(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    safe = "_".join(part for part in safe.split("_") if part)
    return safe[:80] or "vvt"


# audit-portal@72cc4b1a15fd backend/app/services/help_export_service.py :: safe_filename
def audit_portal_help_filename(slug: str, ext: str) -> str:
    """Erzeugt einen dateisystemsicheren Exportnamen."""
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", slug).strip("_") or "export"
    return f"{base}.{ext}"


# regulierung@ce76e48c8ad7 backend/app/api/kpang/vollzug.py :: _safe_filename_part
def regulierung_filename_part(value: str) -> str:
    allowed = []
    for char in value.lower():
        if char.isalnum():
            allowed.append(char)
        elif char in {" ", "-", "_"}:
            allowed.append("-")
    return "".join(allowed).strip("-")[:48] or "tankstelle"


# audit_designer@4b629dd970e5 backend/app/modules/vp_ai/api/runs.py :: _run_async_in_thread
def audit_designer_run_async_in_thread(coro):
    """
    Safely run an async coroutine from a thread pool executor.

    Creates a new event loop for the thread if one doesn't exist,
    instead of calling asyncio.run() multiple times.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


# flowaudit@d8107f6b4287 backend/flowaudit/modules/module_converter/api/protocol.py :: run_async
def flowaudit_run_async(coro):
    """Hilfsfunktion zum Ausfuehren von async Code in Flask"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# flowinvoice@5d5d8c5aded2 backend/app/worker/tasks.py :: run_async
def flowinvoice_run_async(coro):
    """Fuehrt Coroutines auf einem stabilen Loop je Worker-Thread aus.

    HTTPX-, Redis- und SQLAlchemy-Async-Clients binden Verbindungen an den
    Event-Loop ihres ersten Aufrufs. Ein neuer Loop pro Celery-Task machte
    diese gecachten Clients beim naechsten Task unbrauchbar.
    """
    process_id = os.getpid()
    loop = getattr(_async_loop_state, "loop", None)
    owner_process_id = getattr(_async_loop_state, "process_id", None)
    if loop is None or loop.is_closed() or owner_process_id != process_id:
        loop = asyncio.new_event_loop()
        _async_loop_state.loop = loop
        _async_loop_state.process_id = process_id
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
