"""Excel-Zahlenformate / Excel format selection preserving Flowlib behavior.

Origin: janpow77/flowlib, aca2dc6aad25aea0720312dbcc6da00b0bcba330.
Copyright (c) 2026 Jan Riener. MIT; see LICENSES/flowlib-MIT.txt.
This module selects format strings only and does not import an Office adapter.
"""

from __future__ import annotations

import re
from typing import Any

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Euro amounts
    (
        re.compile(
            r"betrag|summe|kosten|ausgabe|einnahme|foerder|bewillig|auszahl|gesamt|netto|brutto|saldo",
            re.I,
        ),
        '#,##0.00 "EUR"',
    ),
    # Percentages
    (re.compile(r"quote|anteil|prozent|rate|satz|percent", re.I), "0.00%"),
    # Dates
    (re.compile(r"datum|date|von|bis|beginn|ende|stichtag|zeitpunkt", re.I), "DD.MM.YYYY"),
    # Counts / integers
    (re.compile(r"anzahl|count|nummer|nr|pos|lfd", re.I), "#,##0"),
    # Hours / days
    (re.compile(r"stunden|tage|hours|days", re.I), "#,##0.00"),
]

_DEFAULT_FORMAT = "General"


def get_number_format(col_name: str, value: Any = None) -> str:
    """DE: Excel-Zahlenformat anhand der unveränderten Flowlib-Heuristik auswählen.

    EN: Return an Excel number format string based on column name heuristics.

    Parameters
    ----------
    col_name:
        The column header / field name.
    value:
        Optional sample value (currently unused but available for future
        type-based inference).

    Returns
    -------
    str
        An Excel number format string like ``#,##0.00 "EUR"`` or ``General``.

    Raises
    ------
    TypeError
        If col_name is not a string accepted by the legacy regex matching.
    """
    for pattern, fmt in _PATTERNS:
        if pattern.search(col_name):
            return fmt
    return _DEFAULT_FORMAT
