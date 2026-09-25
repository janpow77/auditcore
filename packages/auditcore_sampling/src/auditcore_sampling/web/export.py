"""Export of a reproduced selection as CSV or JSON (framework-free).

The export repeats the draw from the request, so a seed is mandatory: the
exported file is the selection that the same request always yields, not a
copy of client state.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Any

from ._validate import ContractError, as_object, choice, require
from .draw import select

_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
CSV_COLUMNS = ("Lfd. Nr.", "Position", "Kennung", "Wert", "Schicht", "Treffer")


@dataclass(frozen=True)
class ExportFile:
    """Rendered export with media type and download name."""

    content: bytes
    media_type: str
    filename: str


def _cell(value: object) -> str:
    """Spreadsheet-safe text; formula prefixes are neutralised with an apostrophe."""
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value).replace(".", ",")
    text = str(value)
    return "'" + text if text.startswith(_FORMULA_START) else text


def _csv(result: dict[str, Any]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for row in result["rows"]:
        writer.writerow(
            [_cell(row[k]) for k in ("order", "position", "id", "value", "stratum", "hits")]
        )
    return ("﻿" + buffer.getvalue()).encode("utf-8")


def export_selection(payload: object) -> ExportFile:
    """``POST /selection/export``: CSV (Excel, Semikolon, UTF-8 mit BOM) or JSON."""
    body = as_object(payload)
    fmt = choice(require(body, "format"), "format", ("csv", "json"))
    if body.get("seed") is None:
        raise ContractError("Für den Export ist der Seed der Auswahl anzugeben.")
    result = select({k: v for k, v in body.items() if k != "format"})
    stem = f"stichprobe-{result['method']}-seed-{result['seed']}"
    if fmt == "csv":
        return ExportFile(_csv(result), "text/csv; charset=utf-8", f"{stem}.csv")
    content = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
    return ExportFile(content, "application/json", f"{stem}.json")
