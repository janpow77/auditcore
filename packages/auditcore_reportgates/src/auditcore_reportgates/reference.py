"""Reference value gate: a generated table against its reference table.

Rows are anchored by their normalised label (first column), columns by their
normalised header without unit. Every row is compared, count rows (``Anzahl``)
and total rows included. Values are converted with the column units of both
sides; percent and percentage points never meet. A missing reference value
against a printed ``0,00`` is a deviation, and so is the reverse.

Data vintage: the comparison only counts when both sides declare the same
vintage. Undeclared or different vintages give ``not_run``, never ``passed``.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .numbers import MISSING, PrintedNumber, read_cell, same_value
from .units import Unit, conversion_exponent, unit_of
from .verdict import Finding, GateResult, Verdict, decide

_UNIT_IN_HEADER = re.compile(
    r"\(.*?\)|\bin\s+(?:mio|mrd|tsd)\.?\s*(?:euro|eur)?|%|\b(?:mio|mrd|tsd)\.\s*(?:euro|eur)?"
    r"|\beuro\b|\beur\b|€",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Table:
    """Header row and body rows; the first column holds the row label."""

    headers: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    vintage: str | None = None


def normalise_label(text: object) -> str:
    """Lower case, without soft hyphens, dashes, spaces and punctuation."""
    lowered = str(text or "").lower().replace("\xad", "")
    return re.sub(r"[^0-9a-zäöüß%]+", "", lowered)


def _column_key(header: str) -> str:
    return normalise_label(_UNIT_IN_HEADER.sub(" ", header))


def _row_keys(rows: Sequence[tuple[object, ...]]) -> dict[str, tuple[object, ...]]:
    keyed: dict[str, tuple[object, ...]] = {}
    seen: dict[str, int] = {}
    for row in rows:
        base = normalise_label(row[0] if row else "")
        seen[base] = seen.get(base, 0) + 1
        keyed[f"{base}#{seen[base]}"] = row
    return keyed


@dataclass(frozen=True)
class _Column:
    actual: int
    expected: int
    actual_unit: Unit
    expected_unit: Unit
    header: str


def _columns(actual: Table, expected: Table) -> tuple[list[_Column], list[Finding]]:
    positions = {_column_key(h): i for i, h in enumerate(actual.headers) if i > 0}
    columns: list[_Column] = []
    findings: list[Finding] = []
    for index, header in enumerate(expected.headers):
        if index == 0:
            continue
        found = positions.get(_column_key(header))
        if found is None:
            findings.append(Finding("spalte_fehlt", "Spalte fehlt im Ergebnis", header))
            continue
        units = (unit_of(actual.headers[found]), unit_of(header))
        columns.append(_Column(found, index, units[0], units[1], header))
    return columns, findings


def _cell(row: tuple[object, ...], index: int) -> object:
    return row[index] if index < len(row) else None


def _compare_numbers(
    actual: PrintedNumber, expected: PrintedNumber, column: _Column, where: str
) -> Finding | None:
    exponent = conversion_exponent(column.actual_unit, column.expected_unit)
    if exponent is None:
        return Finding("einheit_unvertraeglich", "Einheiten nicht vergleichbar", where)
    shifted = None if actual.decimals is None else actual.decimals - exponent
    converted = PrintedNumber(actual.value.scaleb(exponent), shifted, actual.text)
    if same_value(converted, expected):
        return None
    return Finding("abweichung", "Wert weicht ab", where, expected.text, actual.text)


def _compare_cell(
    actual_raw: object, expected_raw: object, column: _Column, where: str
) -> Finding | None:
    """``None`` when equal; text cells are not compared and return ``None``."""
    actual, expected = read_cell(actual_raw), read_cell(expected_raw)
    if expected is MISSING:
        if actual is MISSING:
            return None
        return Finding(
            "fehlend_vs_wert",
            "Referenz ohne Wert, Ergebnis mit Wert",
            where,
            "k. A.",
            str(actual_raw),
        )
    if not isinstance(expected, PrintedNumber):
        return None
    if actual is MISSING:
        return Finding("wert_fehlt", "Wert fehlt im Ergebnis", where, expected.text, "k. A.")
    if not isinstance(actual, PrintedNumber):
        return Finding("kein_zahlwert", "Ergebnis ohne Zahlwert", where, expected.text, str(actual))
    return _compare_numbers(actual, expected, column, where)


def _is_number_cell(raw: object) -> bool:
    cell = read_cell(raw)
    return cell is MISSING or isinstance(cell, PrintedNumber)


def _vintage_reason(actual: Table, expected: Table) -> str:
    if actual.vintage is None or expected.vintage is None:
        return "datenstand_nicht_deklariert"
    if actual.vintage != expected.vintage:
        return "datenstand_abweichend"
    return ""


def compare_tables(actual: Table, expected: Table, *, gate: str = "reference_values") -> GateResult:
    """Compare every numeric reference cell; extra and missing rows are findings."""
    reason = _vintage_reason(actual, expected)
    columns, findings = _columns(actual, expected)
    actual_rows, expected_rows = _row_keys(actual.rows), _row_keys(expected.rows)
    checked = 0
    for key, expected_row in expected_rows.items():
        actual_row = actual_rows.get(key)
        label = str(expected_row[0]) if expected_row else key
        if actual_row is None:
            findings.append(Finding("zeile_fehlt", "Zeile fehlt im Ergebnis", label))
            continue
        for column in columns:
            expected_raw = _cell(expected_row, column.expected)
            if not _is_number_cell(expected_raw):
                continue
            checked += 1
            where = f"{label} / {column.header}"
            finding = _compare_cell(_cell(actual_row, column.actual), expected_raw, column, where)
            if finding is not None:
                findings.append(finding)
    extra = [str(row[0]) for key, row in actual_rows.items() if key not in expected_rows and row]
    findings.extend(Finding("zeile_zusaetzlich", "Zeile nicht in der Referenz", x) for x in extra)
    if reason:
        return GateResult(gate, Verdict.NOT_RUN, reason, checked, tuple(findings))
    return decide(gate, checked, findings)
