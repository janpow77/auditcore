"""REST contract ``reporting_ui/1``: error answer and request checks (framework-free).

Every rejected request raises :class:`ContractError` with an HTTP status, a
code and a German message naming the field; nothing is silently defaulted.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime

from auditcore_common import rest

from ..profiles import PROFILE_IDS
from ..workbook import CellValue, ReportTable

CONTRACT = "reporting_ui/1"
COLUMN_TYPES = ("json", "text", "number", "boolean", "date", "datetime")
MAX_SHEETS_PER_REQUEST = 32
_FILENAME = re.compile(r"[^\w .()-]", re.UNICODE)


class ContractError(rest.ContractError):
    """Request does not satisfy the ``reporting_ui/1`` contract (status, code, ``to_dict``)."""


@dataclass(frozen=True)
class TableRequest:
    """One validated sheet: the library table plus the declared column types."""

    table: ReportTable
    types: Mapping[str, str]
    rows: Sequence[Sequence[CellValue]]


@dataclass(frozen=True)
class WorkbookRequest:
    """A validated preview or export request."""

    profile: str
    tables: Sequence[TableRequest]
    filename: str


def _text_map(value: object, path: str) -> dict[str, str]:
    if value is None:
        return {}
    data = rest.json_object(value, path, error=ContractError)
    if not all(isinstance(v, str) for v in data.values()):
        raise ContractError(f"'{path}' darf nur Texte enthalten.")
    return {k: str(v) for k, v in data.items()}


def _columns(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"'{path}' muss eine nicht leere Liste von Spaltennamen sein.")
    if not all(isinstance(name, str) and name.strip() for name in value):
        raise ContractError(f"'{path}' darf nur nicht leere Texte enthalten.")
    if len(set(value)) != len(value):
        raise ContractError(f"'{path}' enthält doppelte Spaltennamen.")
    return [str(name) for name in value]


def _temporal(raw: object, kind: str, path: str) -> CellValue:
    if not isinstance(raw, str):
        raise ContractError(f"'{path}' muss ein ISO-{kind} als Text oder null sein.")
    try:
        parsed: date = date.fromisoformat(raw) if kind == "Datum" else datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ContractError(f"'{path}' ist kein gültiges ISO-{kind}: {raw!r}.") from exc
    if isinstance(parsed, datetime) and parsed.tzinfo is not None:
        raise ContractError(f"'{path}' enthält eine Zeitzone; bitte vorher umrechnen.")
    return parsed


def _cell(raw: object, kind: str, path: str) -> CellValue:
    """Cell value by declared column type (``json``: as sent); no guessing from text."""
    if raw is None:
        return None
    if kind in ("date", "datetime"):
        return _temporal(raw, "Datum" if kind == "date" else "Datum mit Uhrzeit", path)
    if kind == "boolean" and not isinstance(raw, bool):
        raise ContractError(f"'{path}' muss true, false oder null sein.")
    if kind == "number" and (isinstance(raw, bool) or not isinstance(raw, (int, float))):
        raise ContractError(f"'{path}' muss eine Zahl oder null sein.")
    if kind == "text" and not isinstance(raw, str):
        raise ContractError(f"'{path}' muss ein Text oder null sein.")
    if isinstance(raw, float) and not math.isfinite(raw):
        raise ContractError(f"'{path}' muss eine endliche Zahl sein.")
    if isinstance(raw, (str, int, float, bool)):
        return raw
    raise ContractError(f"'{path}' muss Text, Zahl, true/false oder null sein.")


def _types(value: object, columns: list[str], path: str) -> dict[str, str]:
    given = _text_map(value, path)
    for column, kind in given.items():
        if column not in columns:
            raise ContractError(f"'{path}' nennt die unbekannte Spalte {column!r}.")
        if kind not in COLUMN_TYPES:
            raise ContractError(
                f"'{path}.{column}' muss einer der Werte {', '.join(COLUMN_TYPES)} sein."
            )
    return {column: given.get(column, "json") for column in columns}


def _rows(
    value: object, columns: list[str], types: Mapping[str, str], path: str
) -> list[list[CellValue]]:
    if not isinstance(value, list):
        raise ContractError(f"'{path}' muss eine Liste von Zeilen sein.")
    rows: list[list[CellValue]] = []
    for index, row in enumerate(value):
        where = f"{path}[{index}]"
        if not isinstance(row, list) or len(row) != len(columns):
            raise ContractError(f"'{where}' muss eine Liste mit {len(columns)} Werten sein.")
        rows.append(
            [
                _cell(raw, types[column], f"{where}[{position}]")
                for position, (raw, column) in enumerate(zip(row, columns, strict=True))
            ]
        )
    return rows


def _table(value: object, profile: str, path: str) -> TableRequest:
    data = rest.json_object(value, path, error=ContractError)
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ContractError(f"'{path}.name' muss ein nicht leerer Blattname sein.")
    columns = _columns(data.get("columns"), f"{path}.columns")
    types = _types(data.get("types"), columns, f"{path}.types")
    formats = _text_map(data.get("formats"), f"{path}.formats")
    rows = _rows(data.get("rows"), columns, types, f"{path}.rows")
    table = ReportTable(name, columns, rows, profile=profile, formats=formats)
    return TableRequest(table, types, rows)


def filename_of(value: object) -> str:
    """Download name: safe characters only, ``.xlsx`` appended, default ``bericht.xlsx``."""
    if value is None:
        return "bericht.xlsx"
    if not isinstance(value, str):
        raise ContractError("'filename' muss ein Text sein.")
    stem = _FILENAME.sub("_", value.strip()).strip(" .")[:100]
    stem = stem[:-5].rstrip(" .") if stem.lower().endswith(".xlsx") else stem
    return f"{stem or 'bericht'}.xlsx"


def parse_request(payload: object) -> WorkbookRequest:
    """Validate ``{"profile", "tables", "filename"?}``; the profile is always explicit."""
    body = rest.json_object(payload, "Anfrage", error=ContractError)
    profile = body.get("profile")
    if profile not in PROFILE_IDS:
        raise ContractError(
            f"'profile' muss einer der Werte {', '.join(PROFILE_IDS)} sein.", code="unknown_profile"
        )
    tables = body.get("tables")
    if not isinstance(tables, list) or not tables:
        raise ContractError("'tables' muss eine nicht leere Liste sein.")
    if len(tables) > MAX_SHEETS_PER_REQUEST:
        raise ContractError(
            f"Höchstens {MAX_SHEETS_PER_REQUEST} Blätter je Anfrage.", status=413, code="too_large"
        )
    parsed = [_table(entry, str(profile), f"tables[{i}]") for i, entry in enumerate(tables)]
    return WorkbookRequest(str(profile), parsed, filename_of(body.get("filename")))
