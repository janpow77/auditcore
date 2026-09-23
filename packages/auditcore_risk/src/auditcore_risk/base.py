"""Shared building blocks of the rule kinds (records, context, outcomes, helpers)."""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .errors import InputError, ProfileError
from .values import coerce_number, strict_amount, text

WHEN_MISSING = ("error", "skip", "all_false")
_MISSING_KEY = object()


@dataclass
class Table:
    """Records with an explicit column set (a key absent in one record is missing)."""

    rows: Sequence[Mapping[str, Any]]
    columns: tuple[str, ...]

    def __len__(self) -> int:
        return len(self.rows)

    def has(self, *names: str) -> bool:
        """Whether every named column is part of the column set."""
        return all(n in self.columns for n in names)

    def value(self, index: int, name: str) -> Any:
        """Cell value; a key absent in the record reads as ``None`` (missing)."""
        return self.rows[index].get(name)


@dataclass
class Context:
    """Per-evaluation settings and caches (loaded dependent profiles)."""

    reference_date: date | None = None
    cache: dict[Any, Any] = field(default_factory=dict)


@dataclass
class Outcome:
    """Result of one rule over all records."""

    flags: list[bool | None]
    reasons: list[str | None]
    evidence: list[dict[str, Any] | None]
    matches: list[int] | None = None
    values: dict[str, list[Any]] = field(default_factory=dict)
    dataset: dict[str, Any] | None = None
    #: Message variant per record (key into the rule's ``messages``), if the kind has several.
    variants: list[str | None] | None = None
    #: Severity per record, if the kind derives it (otherwise the rule's fixed severity).
    severities: list[str | None] | None = None

    @classmethod
    def constant(cls, n: int, flag: bool | None) -> Outcome:
        """Outcome with the same flag for all ``n`` records and no evidence."""
        return cls([flag] * n, [None] * n, [None] * n)


@dataclass(frozen=True)
class Kind:
    """Parameter contract and implementation of one rule kind."""

    scope: str
    required: frozenset[str]
    optional: frozenset[str]
    run: Callable[[Mapping[str, Any], Table, Context], Outcome]
    #: Kind-specific parameter checks beyond the key set.
    validate: Callable[[Mapping[str, Any], str], None] | None = None
    #: The kind sets the severity per record (e.g. from terms in the description).
    derives_severity: bool = False


# --------------------------------------------------------------------------- helpers


def _amounts(table: Table, params: Mapping[str, Any], name_key: str = "field") -> list[Any]:
    """Amount per record by ``parse`` (``strict``/``coerce``) and ``missing_value``."""
    name = params[name_key]
    missing = params["missing_value"]
    if not table.has(name):
        return [missing] * len(table)
    out: list[Any] = []
    for i in range(len(table)):
        raw = table.value(i, name)
        if params["parse"] == "strict":
            out.append(strict_amount(raw, name, missing))
        else:
            number = coerce_number(raw, name)
            out.append(missing if number is None else number)
    return out


def seq_sum(values: Iterable[Any], start: Any = 0) -> Any:
    """Plain left-to-right addition, i.e. Python ≤ 3.11 ``sum``.

    Python 3.12 compensates float sums in ``sum``; the source applications run
    on Python 3.11 (their Dockerfiles), so legacy profiles must not depend on
    the interpreter the library happens to run on.
    """
    total = start
    for value in values:
        total = total + value
    return total


def _sum(values: Sequence[float]) -> float:
    """Correctly rounded sum; non-finite values follow IEEE arithmetic."""
    if all(math.isfinite(v) for v in values):
        return math.fsum(values)
    return float(seq_sum(values))


def _relevance(table: Table, spec: Mapping[str, Any] | None) -> list[bool]:
    """``True`` unless the cost type matches the exclusion pattern (missing = relevant)."""
    if spec is None:
        return [True] * len(table)
    name = spec["field"]
    if not table.has(name):
        if spec["column_missing"] != "relevant":
            raise InputError(f"Spalte {name!r} fehlt.")
        return [True] * len(table)
    pattern = re.compile(spec["exclude_pattern"], re.IGNORECASE if spec["ignore_case"] else 0)
    out = []
    for i in range(len(table)):
        value = text(table.value(i, name))
        out.append(value is None or pattern.search(value) is None)
    return out


def _compare(left: float, op: str, right: float) -> bool:
    return {
        "gt": left > right,
        "ge": left >= right,
        "lt": left < right,
        "le": left <= right,
    }[op]


_OPS = {"gt": ">", "ge": "≥", "lt": "<", "le": "≤"}


def need(condition: bool, where: str, message: str) -> None:
    """Raise ``ProfileError`` with location unless ``condition`` holds."""
    if not condition:
        raise ProfileError(f"{where}: {message}")


def is_number(value: Any) -> bool:
    """Finite ``int``/``float`` (booleans excluded)."""
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)
