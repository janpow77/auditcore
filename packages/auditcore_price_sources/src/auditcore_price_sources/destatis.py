"""Destatis GENESIS-Online table files (ffcsv), default: fuel price tables.

Moved from regulierung ``external_apis/destatis_genesis.py`` (adapter
``DestatisTabellenAdapter``, which already ran on ``auditcore_harvest`` 0.1.0):
one page per table, cursor = table index, the raw table is kept byte-exact
(base64). A table answered with an HTTP status other than 200 is skipped as
an issue (``partial``) and not retried, exactly as before; a non-UTF-8 or
binary answer is a parser error.

Added in adapter version 1.1.0: the normalized record states the time values,
units and missing-value markers found in the ffcsv (``parse_ffcsv``), so the
time reference and unit of the table are explicit. The paging profile
(``2026.09.1``) is unchanged, so checkpoints stay compatible.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from auditcore_harvest import (
    JSON,
    AuthKind,
    Capabilities,
    ConfigError,
    Cursor,
    FetchContext,
    PageResult,
    ParserError,
    RecordIssue,
    SnapshotSemantics,
    Source,
    page_result,
)

KRAFTSTOFF_TABELLEN = ("61243-0001", "61241-0004")
#: GENESIS markers for missing or suppressed values
MISSING_MARKERS = frozenset({"", "-", ".", "...", "/", "x"})

QUELLE = Source(
    source_id="price.destatis_genesis",
    title="Destatis GENESIS (Kraftstofftabellen)",
    family="price",
    adapter_version="1.1.0",
    profile_version="2026.09.1",
    data_format="text/csv (ffcsv)",
    auth=AuthKind.TOKEN,
    capabilities=Capabilities(
        pagination=True, incremental=False, full_snapshot=True, deletions=False
    ),
    snapshot_semantics=SnapshotSemantics.APPEND_ONLY,
)


@dataclass(frozen=True)
class FfcsvRow:
    """One ffcsv value row: time, month/period code, exact value or missing marker, unit."""

    time: str
    period_code: str | None
    value: Decimal | None
    marker: str | None
    unit: str | None


@dataclass(frozen=True)
class FfcsvTable:
    """Parsed ffcsv table (structure ``unbekannt`` if ``time``/``value`` columns are absent)."""

    columns: tuple[str, ...]
    structure: str
    rows: tuple[FfcsvRow, ...]
    unreadable: int

    def summary(self) -> dict[str, JSON]:
        """Explicit time reference and units of the table."""
        return {
            "struktur": self.structure,
            "zeitangaben": sorted({r.time for r in self.rows}),
            "periodencodes": sorted({r.period_code for r in self.rows if r.period_code}),
            "einheiten": sorted({r.unit for r in self.rows if r.unit}),
            "werte": sum(1 for r in self.rows if r.value is not None),
            "fehlwerte": sum(1 for r in self.rows if r.value is None),
            "nicht_lesbar": self.unreadable,
        }


def parse_ffcsv(text: str) -> FfcsvTable:
    """Parse GENESIS ffcsv (semicolon separated, German decimal comma, BOM tolerated).

    As in regulierung ``genesis_sync._parse_ffcsv_to_values`` only the decimal
    comma is converted; a value with both ``.`` and ``,`` is counted as unreadable.

    Missing/suppressed markers stay markers (never 0); ``time`` values of the
    form ``2025-P1Y`` keep their source text. Aggregation to quarters or
    index series is consumer logic and not done here.
    """
    lines = [line for line in text.replace("\ufeff", "").splitlines() if line.strip()]
    if not lines:
        return FfcsvTable((), "leer", (), 0)
    columns = tuple(c.strip() for c in lines[0].split(";"))
    index = {name: i for i, name in enumerate(columns)}
    if "time" not in index or "value" not in index:
        return FfcsvTable(columns, "unbekannt", (), len(lines) - 1)
    rows: list[FfcsvRow] = []
    unreadable = 0
    for line in lines[1:]:
        parts = [p.strip().strip('"') for p in line.split(";")]
        if len(parts) != len(columns):
            unreadable += 1
            continue
        raw = parts[index["value"]]
        value: Decimal | None = None
        marker: str | None = None
        if raw in MISSING_MARKERS:
            marker = raw
        else:
            try:
                if "." in raw and "," in raw:
                    raise InvalidOperation(raw)
                value = Decimal(raw.replace(",", "."))
            except InvalidOperation:
                unreadable += 1
                continue
        period = index.get("1_variable_attribute_code")
        unit_index = index.get("value_unit")
        rows.append(
            FfcsvRow(
                time=parts[index["time"]],
                period_code=None if period is None else parts[period] or None,
                value=value,
                marker=marker,
                unit=None if unit_index is None else parts[unit_index] or None,
            )
        )
    return FfcsvTable(columns, "ffcsv", tuple(rows), unreadable)


class DestatisTabellenAdapter:
    """One page per GENESIS table; raw data kept byte-exact."""

    source = QUELLE

    def __init__(self, tables: Sequence[str] = KRAFTSTOFF_TABELLEN) -> None:
        if not tables:
            raise ConfigError("Mindestens eine Tabelle angeben.")
        self.tables = tuple(tables)

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """``url`` (``…/data/tablefile``) and ``username`` are required."""
        if not isinstance(config.get("url"), str) or not isinstance(config.get("username"), str):
            raise ConfigError("url und username sind anzugeben.")

    def fetch_page(self, context: FetchContext, cursor: Cursor | None) -> PageResult:
        """Fetch one table; the secret ``token`` goes into the ``password`` parameter."""
        index = int((cursor or {}).get("tabelle", 0))
        table = self.tables[index]
        params = {
            "username": str(context.config["username"]),
            "password": context.secret(QUELLE.source_id, "token"),
            "name": table,
            "area": "all",
            "compress": "false",
            "transpose": "false",
            "format": "ffcsv",
            "language": "de",
        }
        response = context.transport.request(
            "GET", str(context.config["url"]), params=params, timeout=context.timeout
        )
        next_cursor = {"tabelle": index + 1} if index + 1 < len(self.tables) else None
        if response.status != 200:
            return page_result((), (RecordIssue(table, f"HTTP {response.status}"),), next_cursor)
        try:
            text = response.body.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ParserError(f"Tabelle {table}: Antwort ist kein UTF-8-Text.") from exc
        if "\x00" in text:
            raise ParserError(f"Tabelle {table}: Antwort enthält Binärdaten statt ffcsv.")
        lines = text.splitlines()
        raw = {"tabelle": table, "inhalt_b64": base64.b64encode(response.body).decode()}
        normalized = {
            "tabelle": table,
            "datensaetze": max(0, len(lines) - 1),
            "inhalt": parse_ffcsv(text).summary(),
        }
        return page_result([context.record(QUELLE, table, raw, normalized, table)], (), next_cursor)
