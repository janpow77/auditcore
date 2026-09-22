"""Framework-independent format rules and optional Excel workbook export."""

from auditcore_reporting.formats import get_number_format
from auditcore_reporting.profiles import PROFILE_IDS, get_profile_format, get_profile_metadata
from auditcore_reporting.workbook import (
    ExcelDependencyError,
    ExcelOptions,
    ReportTable,
    WorkbookLimitError,
    WorkbookLimits,
    render_workbook,
)

__all__ = [
    "get_number_format",
    "PROFILE_IDS",
    "get_profile_format",
    "get_profile_metadata",
    "ExcelDependencyError",
    "ExcelOptions",
    "ReportTable",
    "WorkbookLimitError",
    "WorkbookLimits",
    "render_workbook",
]
