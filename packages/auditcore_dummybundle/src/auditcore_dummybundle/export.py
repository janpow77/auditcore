"""JSON-ready form of a result: metadata first, exact amounts as text."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from auditcore_dummybundle.model import Cell, Result, Table


def plain(cell: Cell) -> str | int | bool | None:
    """Cell for JSON: decimals as text (exact), dates as ISO text."""
    if isinstance(cell, Decimal):
        return str(cell)
    if isinstance(cell, date):
        return cell.isoformat()
    return cell


def table_document(table: Table, max_rows: int | None = None) -> dict[str, object]:
    """One table with column descriptions; ``max_rows`` shortens the rows for a preview."""
    rows = table.rows if max_rows is None else table.rows[:max_rows]
    return {
        "name": table.name,
        "title": table.title,
        "source": table.source,
        "row_count": len(table.rows),
        "columns": [
            {"header": column.header, "kind": column.kind, "note": column.note}
            for column in table.columns
        ],
        "rows": [[plain(cell) for cell in row] for row in rows],
    }


def document(result: Result, max_rows: int | None = None) -> dict[str, object]:
    """Whole result as JSON document: ``_meta``, ``tables`` and, if requested, ``solution``."""
    data: dict[str, object] = {
        "_meta": dict(result.meta),
        "tables": [table_document(table, max_rows) for table in result.tables],
    }
    if result.solution is not None:
        data["solution"] = [
            {key: plain(value) for key, value in entry.as_row().items()}
            for entry in result.solution
        ]
    return data
