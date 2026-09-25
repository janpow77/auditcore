"""Report data and dependency-free renderers (JSON, HTML).

Report builders return plain JSON-compatible dictionaries so any consumer
renderer can use them. Excel and PDF output are optional extras in
:mod:`auditcore_dataprotection.excel` and :mod:`auditcore_dataprotection.pdf`.

The report data lives in :mod:`.report_data`, the HTML views in
:mod:`.assessment_html` and :mod:`.register_html`; every name stays
importable from here.
"""

from __future__ import annotations

from .assessment_html import ANSWER_TEXT, render_assessment_html
from .register_html import (
    COVER_TITLES,
    DECISION_TEXT,
    DSFA_STATUS_TEXT,
    REGISTER_STATUS_TEXT,
    render_register_html,
)
from .report_data import (
    REPORT_SCHEMA,
    SNAPSHOT_FIELDS,
    assessment_report,
    overview_rows,
    register_report,
    to_json_bytes,
)

__all__ = [
    "ANSWER_TEXT",
    "COVER_TITLES",
    "DECISION_TEXT",
    "DSFA_STATUS_TEXT",
    "REGISTER_STATUS_TEXT",
    "REPORT_SCHEMA",
    "SNAPSHOT_FIELDS",
    "assessment_report",
    "overview_rows",
    "register_report",
    "render_assessment_html",
    "render_register_html",
    "to_json_bytes",
]
