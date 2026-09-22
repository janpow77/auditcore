"""Standard-library-only workbook contracts with an optional Excel adapter."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TypeAlias

CellValue: TypeAlias = str | int | float | bool | date | datetime | None
ReportRow: TypeAlias = Sequence[CellValue] | Mapping[str, CellValue]


@dataclass(frozen=True)
class ReportTable:
    """A named sheet with ordered columns and caller-supplied rows, consumed once.

    Mapping rows must have exactly the declared column keys. Sequence rows must
    match the column count. Formats override individual columns explicitly.
    """

    name: str
    columns: Sequence[str]
    rows: Iterable[ReportRow]
    start_row: int = 1
    profile: str = "flowlib-legacy-v1"
    formats: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkbookLimits:
    """Per-export resource limits; row count excludes headers, cells include them."""

    max_rows_per_sheet: int = 100_000
    max_columns: int = 256
    max_sheets: int = 32
    max_cells: int = 500_000
    max_text_characters: int = 5_000_000
    max_output_bytes: int = 32 * 1024 * 1024


@dataclass(frozen=True)
class ExcelOptions:
    """Formatting and resource controls; formulas are never accepted as cell data."""

    zebra: bool = True
    border: bool = True
    freeze_header: bool = True
    auto_filter: bool = True
    min_width: float = 8.0
    max_width: float = 50.0
    limits: WorkbookLimits = field(default_factory=WorkbookLimits)


class ExcelDependencyError(ImportError):
    """The optional openpyxl adapter dependency is not installed."""


class WorkbookLimitError(ValueError):
    """Input or output exceeds an explicit workbook resource limit."""


def render_workbook(tables: Iterable[ReportTable], options: ExcelOptions | None = None) -> bytes:
    """Render supplied tables as XLSX bytes without filesystem/network/application access.

    String values, including leading '=', are always literal text. The adapter
    never evaluates formulas, reads an existing workbook or creates hyperlinks.
    Args:
        tables: One or more ReportTable objects; generators are consumed once.
        options: Optional formatting and limits; defaults are bounded.
    Returns:
        A complete XLSX document. No partial artifact is returned on failure.
    Raises:
        ExcelDependencyError: Install auditcore_reporting[excel].
        WorkbookLimitError: Configured or XLSX format limits are exceeded.
        ValueError: Invalid sheet/column names, row shape, dates or text.
        TypeError: Unsupported values or malformed model fields.
    """
    if options is not None and not isinstance(options, ExcelOptions):
        raise TypeError("options must be ExcelOptions or None")
    try:
        from auditcore_reporting._excel import render
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.split(".")[0] in {"openpyxl", "defusedxml"}:
            raise ExcelDependencyError(
                "Install auditcore_reporting[excel] for XLSX export"
            ) from exc
        raise
    return render(tables, options or ExcelOptions())
