"""Template profiles: column layouts as data, projected from the canonical bundle.

A profile (``template_data/*.json``) lists tables and columns; a column takes
its values from a canonical field (``field``, optionally through the parent as
``operation.<key>`` or ``claim.<key>``), is a constant (``const``) or stays
empty with a ``note`` saying why. No template has code of its own. ``free``
describes the stand-alone equivalent of a column for the free table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import cache
from importlib.resources import files
from typing import cast

from auditcore_common.hashing import canonical_sha256

from auditcore_dummybundle.amounts import ZERO
from auditcore_dummybundle.bundle import Bundle
from auditcore_dummybundle.errors import BundleError
from auditcore_dummybundle.model import Cell, Column, Row, SolutionEntry, Table

_PARENTS = {"operation": ("operations", "operation_id"), "claim": ("claims", "claim_id")}
#: Sheet names allow 31 characters; four are reserved for a marker prefix.
MAX_NAME = 27
#: Output tables and data row numbers of a canonical row, by ``id`` of the row.
Positions = dict[int, list[tuple[str, int]]]


@dataclass(frozen=True)
class TemplateColumn:
    """One column of a template table."""

    header: str
    kind: str
    field: str | None
    const: str | None
    summed: bool
    note: str
    free: dict[str, object] | None


@dataclass(frozen=True)
class TemplateTable:
    """One table of a template: source table, optional split, filter and total row."""

    name: str
    title: str
    source: str
    columns: tuple[TemplateColumn, ...]
    split_by: str | None
    row_kinds: tuple[str, ...]
    total_row: str | None
    free_start: bool


@dataclass(frozen=True)
class Template:
    """A versioned template profile."""

    id: str
    version: str
    status: str
    public: bool
    title: str
    purpose: str
    legal_basis: str
    sources: tuple[str, ...]
    open_points: tuple[str, ...]
    tables: tuple[TemplateTable, ...]
    content_hash: str = ""
    release: tuple[tuple[str, str], ...] = ()

    @property
    def free_table(self) -> TemplateTable | None:
        """The table that can serve as starting point of a free table, if any."""
        return next((table for table in self.tables if table.free_start), None)


def _column(raw: dict[str, object]) -> TemplateColumn:
    free = raw.get("free")
    return TemplateColumn(
        header=str(raw["header"]),
        kind=str(raw.get("kind", "text")),
        field=None if raw.get("field") is None else str(raw["field"]),
        const=None if raw.get("const") is None else str(raw["const"]),
        summed=bool(raw.get("sum", False)),
        note=str(raw.get("note", "")),
        free=cast(dict[str, object], free) if isinstance(free, dict) else None,
    )


def _table(raw: dict[str, object]) -> TemplateTable:
    columns = cast(list[dict[str, object]], raw["columns"])
    split = raw.get("split_by")
    total = raw.get("total_row")
    return TemplateTable(
        name=str(raw["name"]),
        title=str(raw["title"]),
        source=str(raw["source"]),
        columns=tuple(_column(column) for column in columns),
        split_by=None if split is None else str(split),
        row_kinds=tuple(str(kind) for kind in cast(list[object], raw.get("row_kinds", []))),
        total_row=None if total is None else str(total),
        free_start=bool(raw.get("free_start", False)),
    )


def profile_content(raw: dict[str, object]) -> dict[str, object]:
    """The part of a profile its ``content_hash`` binds: identity, texts and tables."""
    return {key: raw[key] for key in ("id", "version", "title", "purpose", "legal_basis", "tables")}


def _template(raw: dict[str, object]) -> Template:
    if raw.get("content_hash") != canonical_sha256(profile_content(raw)):
        raise BundleError(
            f"Der Inhaltshash der Vorlage '{raw.get('id')}' stimmt nicht.",
            code="profile_hash",
            path="templates",
        )
    review = cast(dict[str, object], raw["review"])
    return Template(
        id=str(raw["id"]),
        version=str(raw["version"]),
        status=str(raw["status"]),
        public=bool(raw["public"]),
        title=str(raw["title"]),
        purpose=str(raw["purpose"]),
        legal_basis=str(raw["legal_basis"]),
        sources=tuple(str(item) for item in cast(list[object], raw["sources"])),
        open_points=tuple(str(item) for item in cast(list[object], raw["open_points"])),
        tables=tuple(_table(table) for table in cast(list[dict[str, object]], raw["tables"])),
        content_hash=str(raw["content_hash"]),
        release=tuple((str(key), str(value)) for key, value in review.items()),
    )


@cache
def templates() -> dict[str, Template]:
    """All packaged template profiles by identifier, in catalogue order."""
    folder = files("auditcore_dummybundle").joinpath("template_data")
    entries = sorted(
        (entry for entry in folder.iterdir() if entry.name.endswith(".json")),
        key=lambda entry: (entry.name[0] != "v", entry.name),
    )
    loaded = [_template(json.loads(entry.read_text(encoding="utf-8"))) for entry in entries]
    return {template.id: template for template in loaded}


def get_template(template_id: str, *, include_private: bool = False) -> Template:
    """Template ``template_id``; non-public profiles only with ``include_private``."""
    template = templates().get(template_id)
    if template is None or not (template.public or include_private):
        raise BundleError(
            f"Die Vorlage '{template_id}' ist nicht verfügbar.",
            code="unknown_template",
            path="templates",
        )
    return template


def _typed(value: str, kind: str) -> Cell:
    if kind in ("amount", "rate"):
        return Decimal(value)
    return int(value) if kind == "int" else value


class _Projector:
    """Resolves column values of one bundle, with parent lookups."""

    def __init__(self, bundle: Bundle) -> None:
        self._bundle = bundle
        self._parents = {
            name: {row[key]: row for row in bundle.table(table)}
            for name, (table, key) in _PARENTS.items()
        }

    def cell(self, row: Row, column: TemplateColumn) -> Cell:
        if column.const is not None:
            return _typed(column.const, column.kind)
        if column.field is None:
            return None
        if "." not in column.field:
            return row[column.field]
        parent, key = column.field.split(".", 1)
        return self._parents[parent][row[_PARENTS[parent][1]]][key]

    def rows(self, table: TemplateTable) -> list[Row]:
        rows = self._bundle.table(table.source)
        if table.row_kinds:
            rows = [row for row in rows if row["row_kind"] in table.row_kinds]
        return rows


def _total(columns: tuple[TemplateColumn, ...], rows: list[tuple[Cell, ...]]) -> tuple[Cell, ...]:
    cells: list[Cell] = []
    for index, column in enumerate(columns):
        if not column.summed:
            cells.append(None)
            continue
        values = [row[index] for row in rows]
        cells.append(sum((v for v in values if isinstance(v, Decimal)), ZERO))
    return tuple(cells)


def _short(value: object) -> str:
    return "-".join(str(value).split("-")[-2:])


def project(bundle: Bundle, template: Template) -> tuple[list[Table], Positions]:
    """Tables of ``template`` for ``bundle`` plus the output position of every source row."""
    projector = _Projector(bundle)
    tables: list[Table] = []
    positions: Positions = {}
    for spec in template.tables:
        source = projector.rows(spec)
        keys = (
            list(dict.fromkeys(row[spec.split_by] for row in source)) if spec.split_by else [None]
        )
        columns = tuple(Column(c.header, c.kind, c.note) for c in spec.columns)
        for key in keys:
            part = [row for row in source if key is None or row[cast(str, spec.split_by)] == key]
            name = spec.name if key is None else f"{spec.name} {_short(key)}"[:MAX_NAME]
            title = spec.title if key is None else f"{spec.title} – {key}"
            body = [tuple(projector.cell(row, column) for column in spec.columns) for row in part]
            offset = 1 if spec.total_row == "top" else 0
            for index, row in enumerate(part, start=1):
                positions.setdefault(id(row), []).append((name, index + offset))
            if spec.total_row == "top":
                body.insert(0, _total(spec.columns, body))
            elif spec.total_row == "bottom":
                body.append(_total(spec.columns, body))
            tables.append(Table(name, title, columns, tuple(body), spec.source))
    return tables, positions


def located(bundle: Bundle, positions: Positions) -> tuple[SolutionEntry, ...]:
    """Solution entries of ``bundle`` with every output table and data row number filled in.

    A row that appears in several output tables is named with each of them; the
    row number is the one in the first table, further ones follow in brackets.
    """
    entries = []
    for entry, row in zip(bundle.solution, bundle.solution_rows, strict=True):
        found = positions.get(id(row), [])
        first = found[0][1] if found else 0
        names = [name if number == first else f"{name} (Zeile {number})" for name, number in found]
        entries.append(
            SolutionEntry(
                entry.code,
                entry.title,
                entry.source,
                entry.row_key,
                entry.changed_field,
                entry.original,
                entry.planted,
                entry.expected_amount,
                entry.reason,
                entry.affected_checks,
                "; ".join(names),
                first,
            )  # fmt: skip
        )
    return tuple(entries)


def template_recipe(
    template: Template, *, seed: int, base_date: date, rows: int, country: str, version: str
) -> dict[str, object]:
    """Recipe document that rebuilds the template's list as a free table to adapt."""
    table = template.free_table
    if table is None:
        raise BundleError(
            f"Die Vorlage '{template.id}' ist kein Ausgangspunkt für eine eigene Tabelle.",
            code="no_free_start",
            path="template",
        )
    fields = []
    for column in table.columns:
        spec = dict(column.free or {"type": "constant", "params": {"value": ""}})
        fields.append({"name": column.header, **spec})
    return {
        "format": "auditcore.dummybundle.recipe",
        "format_version": 1,
        "title": template.title,
        "derived_from": template.id,
        "marking": "SYNTHETISCH",
        "run": {"seed": seed, "base_date": base_date.isoformat(), "rows": rows, "country": country},
        "generator": {"package": "auditcore_dummybundle", "version": version},
        "fields": fields,
    }
