"""Value types shared by the bundle, the free table and the exports."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from auditcore_dummybundle.errors import BudgetExceededError

#: One cell of a generated table.
Cell = str | int | Decimal | date | bool | None
#: One canonical row: English field keys, typed cells.
Row = dict[str, Cell]
#: Marker carried by every output.
MARKING = "SYNTHETISCH"


def amount(row: Row, key: str) -> Decimal:
    """Decimal cell ``key`` of ``row``."""
    value = row[key]
    if not isinstance(value, Decimal):
        raise TypeError(f"{key} is not an amount")
    return value


def day(row: Row, key: str) -> date:
    """Date cell ``key`` of ``row``."""
    value = row[key]
    if not isinstance(value, date):
        raise TypeError(f"{key} is not a date")
    return value


def text(row: Row, key: str) -> str:
    """Text cell ``key`` of ``row``."""
    value = row[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} is not a text")
    return value


def number(row: Row, key: str) -> int:
    """Integer cell ``key`` of ``row``."""
    value = row[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} is not an integer")
    return value


@dataclass(frozen=True)
class Column:
    """One output column: header as shown, value kind for exporters."""

    header: str
    kind: str = "text"
    note: str = ""


@dataclass(frozen=True)
class Table:
    """One output table with ordered columns and positional rows."""

    name: str
    title: str
    columns: tuple[Column, ...]
    rows: tuple[tuple[Cell, ...], ...]
    source: str = ""


@dataclass(frozen=True)
class SolutionEntry:
    """One planted anomaly; every key of :meth:`as_row` carries the ``gt_`` prefix."""

    code: str
    title: str
    source: str
    row_key: str
    changed_field: str
    original: Cell
    planted: Cell
    expected_amount: Decimal
    reason: str
    affected_checks: tuple[int, ...] = ()
    table: str = ""
    row_number: int = 0

    def as_row(self) -> Row:
        """Flat row for the separate solution file."""
        return {
            "gt_code": self.code,
            "gt_title": self.title,
            "gt_table": self.table or self.source,
            "gt_row_number": self.row_number,
            "gt_row_key": self.row_key,
            "gt_field": self.changed_field,
            "gt_original": self.original,
            "gt_planted": self.planted,
            "gt_expected_amount": self.expected_amount,
            "gt_reason": self.reason,
            "gt_affected_checks": ", ".join(str(check) for check in self.affected_checks),
        }


@dataclass(frozen=True)
class Result:
    """Generated tables, run metadata and (only on request) the solution."""

    tables: tuple[Table, ...]
    meta: dict[str, object]
    solution: tuple[SolutionEntry, ...] | None = None


@dataclass
class Budget:
    """Cooperative time limit; generators call :meth:`tick` in their loops."""

    seconds: float | None = None
    _started: float = field(default_factory=time.monotonic)
    _calls: int = 0

    def tick(self) -> None:
        """Raise :class:`BudgetExceededError` once the limit has passed."""
        self._calls += 1
        if self.seconds is None or self._calls % 64:
            return
        if time.monotonic() - self._started > self.seconds:
            raise BudgetExceededError
