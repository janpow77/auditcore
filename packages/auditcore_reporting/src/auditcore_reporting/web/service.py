"""Catalogue, preview and export of contract ``reporting_ui/1`` (framework-free)."""

from __future__ import annotations

import importlib.util
from collections.abc import Sequence
from dataclasses import asdict
from datetime import date
from importlib.metadata import PackageNotFoundError, version

from ..profiles import PROFILE_IDS, get_profile_format, get_profile_metadata
from ..workbook import (
    CellValue,
    ExcelDependencyError,
    WorkbookLimitError,
    WorkbookLimits,
    render_workbook,
)
from .contract import COLUMN_TYPES, CONTRACT, ContractError, TableRequest, parse_request


def _library() -> str:
    try:
        return f"auditcore_reporting {version('auditcore_reporting')}"
    except PackageNotFoundError:  # pragma: no cover - source tree without installation
        return "auditcore_reporting"


LIBRARY = _library()
SAMPLE_ROWS = 20
MAX_BODY_BYTES = 16 * 1024 * 1024

PROFILE_TEXTS = {
    "flowlib-legacy-v1": (
        "Flowlib-Formate nach Spaltennamen",
        "Zahlenformat aus dem Spaltennamen (Betrag vor Prozent vor Datum vor Anzahl vor "
        "Stunden/Tagen, sonst Standard), unverändert aus flowlib übernommen.",
    ),
    "plain-v1": (
        "Ohne Formatregeln",
        "Keine Heuristik: jede Spalte im Standardformat; Datumswerte behalten die "
        "Datumsdarstellung von openpyxl.",
    ),
}


def excel_available() -> bool:
    """Whether the ``[excel]`` extra (openpyxl, defusedxml) is installed."""
    return all(importlib.util.find_spec(name) is not None for name in ("openpyxl", "defusedxml"))


def _source(source: object) -> str | None:
    """Origin as one line: ``repository@commit`` or the recorded kind."""
    if not isinstance(source, dict):
        return None
    if "repository" in source and "commit" in source:
        return f"{source['repository']}@{source['commit']}"
    kind = source.get("kind")
    return str(kind) if kind else None


def _profile(profile_id: str) -> dict[str, object]:
    meta = get_profile_metadata(profile_id)
    label, description = PROFILE_TEXTS[profile_id]
    return {
        "id": profile_id,
        "label": label,
        "description": description,
        "version": meta["version"],
        "status": meta["status"],
        "source": _source(meta.get("source")),
    }


def catalogue() -> dict[str, object]:
    """``GET /profiles``: format profiles, column types, limits and Excel availability."""
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "excel_available": excel_available(),
        "profiles": [_profile(p) for p in PROFILE_IDS],
        "column_types": list(COLUMN_TYPES),
        "limits": {
            **asdict(WorkbookLimits()),
            "max_body_bytes": MAX_BODY_BYTES,
            "sample_rows": SAMPLE_ROWS,
        },
    }


def _json_cell(value: CellValue) -> object:
    return value.isoformat() if isinstance(value, date) else value


def _sample(rows: Sequence[Sequence[CellValue]]) -> list[list[object]]:
    return [[_json_cell(v) for v in row] for row in rows[:SAMPLE_ROWS]]


def _table_preview(entry: TableRequest) -> dict[str, object]:
    table = entry.table
    columns = [
        {
            "name": column,
            "type": entry.types[column],
            "format": table.formats.get(column) or get_profile_format(table.profile, column),
            "source": "override" if column in table.formats else "profile",
        }
        for column in table.columns
    ]
    return {
        "name": table.name,
        "rows": len(entry.rows),
        "columns": columns,
        "sample": _sample(entry.rows),
    }


def _render(tables: Sequence[TableRequest]) -> bytes:
    try:
        return render_workbook([entry.table for entry in tables])
    except ExcelDependencyError as exc:
        raise ContractError(
            "XLSX-Export nicht verfügbar: Extra auditcore_reporting[excel] fehlt.",
            status=501,
            code="excel_unavailable",
        ) from exc
    except WorkbookLimitError as exc:
        raise ContractError(f"Grenze überschritten: {exc}", status=413, code="too_large") from exc
    except (ValueError, TypeError) as exc:
        raise ContractError(f"Arbeitsmappe abgelehnt: {exc}", code="workbook_rejected") from exc


def preview(payload: object) -> dict[str, object]:
    """``POST /preview``: formats per column, sample rows and a trial rendering."""
    request = parse_request(payload)
    workbook: dict[str, object] | None = None
    if excel_available():
        workbook = {"bytes": len(_render(request.tables)), "filename": request.filename}
    return {
        "contract": CONTRACT,
        "profile": request.profile,
        "tables": [_table_preview(entry) for entry in request.tables],
        "workbook": workbook,
    }


def export(payload: object) -> tuple[bytes, str]:
    """``POST /export``: XLSX bytes and the sanitised download name."""
    request = parse_request(payload)
    return _render(request.tables), request.filename
