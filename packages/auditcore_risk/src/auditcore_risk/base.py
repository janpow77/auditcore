"""Shared building blocks of the rule kinds (records, context, outcomes, helpers)."""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from importlib.util import find_spec
from typing import Any, TypedDict, cast

from .errors import DependencyError, InputError, ProfileError
from .values import as_date, coerce_number, strict_amount, text

#: A JSON object of a profile (rule parameters, assessment, summary) or a consumer's
#: result mapping. Its values stay ``Any`` on purpose: their type depends on the key,
#: and the profile checks (``validate_params`` and friends) fix it when loading.
JsonObject = Mapping[str, Any]

WHEN_MISSING = ("error", "skip", "all_false", "undetermined")
# Betragsregeln, die einen fehlenden Betrag als „unbestimmt“ ausweisen können
# (Parameter ``missing_amount_reason``), mit dem Schlüssel ihres Betragsfelds.
MISSING_AMOUNT_FIELD = {"near_threshold": "field", "missing_procurement": "amount_field"}
#: Grouping key of a missing value (distinct from every real value).
MISSING_KEY = object()


@dataclass
class Table:
    """Records with an explicit column set (a key absent in one record is missing)."""

    rows: Sequence[Mapping[str, object]]
    columns: tuple[str, ...]

    def __len__(self) -> int:
        return len(self.rows)

    def has(self, *names: str) -> bool:
        """Whether every named column is part of the column set."""
        return all(n in self.columns for n in names)

    def value(self, index: int, name: str) -> object:
        """Cell value; a key absent in the record reads as ``None`` (missing)."""
        return self.rows[index].get(name)


@dataclass
class Context:
    """Per-evaluation settings and caches (loaded dependent profiles)."""

    reference_date: date | None = None
    #: Loaded profiles of optional dependencies by ``(library, profile, version)``;
    #: their types belong to lazily imported extras, hence ``Any``.
    cache: dict[tuple[str, str, str], Any] = field(default_factory=dict)


class DatasetOutcome(TypedDict, total=False):
    """Result of a dataset-wide rule kind (``evidence`` only when triggered or evaluated)."""

    triggered: bool
    value: float | None
    reason: str
    evidence: dict[str, object]


@dataclass
class Outcome:
    """Result of one rule over all records."""

    flags: list[bool | None]
    reasons: list[str | None]
    evidence: list[dict[str, object] | None]
    matches: list[int] | None = None
    values: dict[str, Sequence[object]] = field(default_factory=dict)
    dataset: DatasetOutcome | None = None
    #: Message variant per record (key into the rule's ``messages``), if the kind has several.
    variants: list[str | None] | None = None
    #: Severity per record, if the kind derives it (otherwise the rule's fixed severity).
    severities: list[str | None] | None = None

    @classmethod
    def constant(cls, n: int, flag: bool | None) -> Outcome:
        """Outcome with the same flag for all ``n`` records and no evidence."""
        return cls([flag] * n, [None] * n, [None] * n)


#: Implementation of a rule kind: validated profile parameters, records, evaluation context.
KindRun = Callable[[JsonObject, Table, Context], Outcome]


@dataclass(frozen=True)
class Kind:
    """Parameter contract and implementation of one rule kind."""

    scope: str
    required: frozenset[str]
    optional: frozenset[str]
    run: KindRun
    #: Kind-specific parameter checks beyond the key set.
    validate: Callable[[JsonObject, str], None] | None = None
    #: The kind sets the severity per record (e.g. from terms in the description).
    derives_severity: bool = False


# --------------------------------------------------------------------------- helpers


def amount_values(table: Table, params: JsonObject, name_key: str = "field") -> list[float | None]:
    """Amount per record by ``parse`` (``strict``/``coerce``) and ``missing_value``.

    ``missing_value`` ``None`` (only with ``missing_amount_reason``) keeps a
    missing amount — or an absent column — as ``None`` instead of a substitute.
    """
    name = params[name_key]
    missing = params["missing_value"]
    if not table.has(name):
        return [missing] * len(table)
    out: list[float | None] = []
    for i in range(len(table)):
        raw = table.value(i, name)
        if params["parse"] == "strict":
            out.append(strict_amount(raw, name, missing))
        else:
            number = coerce_number(raw, name)
            out.append(missing if number is None else number)
    return out


def present_amounts(table: Table, params: JsonObject, name_key: str = "field") -> list[float]:
    """:func:`amount_values` of a kind whose profile check demands a numeric ``missing_value``.

    Only ``near_threshold`` and ``missing_procurement`` accept
    ``missing_amount_reason`` (``missing_value`` null); every other amount kind
    therefore always receives a number.
    """
    return cast(list[float], amount_values(table, params, name_key))


def seq_sum(values: Iterable[float], start: float = 0) -> float:
    """Plain left-to-right addition, i.e. Python ≤ 3.11 ``sum``.

    Python 3.12 compensates float sums in ``sum``; the source applications run
    on Python 3.11 (their Dockerfiles), so legacy profiles must not depend on
    the interpreter the library happens to run on.
    """
    total = start
    for value in values:
        total = total + value
    return total


def correct_sum(values: Sequence[float]) -> float:
    """Correctly rounded sum; non-finite values follow IEEE arithmetic."""
    if all(math.isfinite(v) for v in values):
        return math.fsum(values)
    return float(seq_sum(values))


def relevance(table: Table, spec: JsonObject | None) -> list[bool]:
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


def compare(left: float, op: str, right: float) -> bool:
    """``left <op> right`` for the profile operators ``gt``/``ge``/``lt``/``le``."""
    return {
        "gt": left > right,
        "ge": left >= right,
        "lt": left < right,
        "le": left <= right,
    }[op]


#: Display symbol of each comparison operator.
OPERATOR_SYMBOLS = {"gt": ">", "ge": "≥", "lt": "<", "le": "≤"}


def need(condition: bool, where: str, message: str) -> None:
    """Raise ``ProfileError`` with location unless ``condition`` holds."""
    if not condition:
        raise ProfileError(f"{where}: {message}")


def is_number(value: object) -> bool:
    """Finite ``int``/``float`` (booleans excluded)."""
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def procurement_threshold(
    spec: JsonObject, table: Table, index: int, ctx: Context
) -> tuple[float | None, dict[str, object]]:
    """Year-bound EU threshold from ``auditcore_procurement``; never a neighbouring year."""
    if find_spec("auditcore_procurement") is None:
        raise DependencyError(
            "Jahresbezogene Vergabeschwellen verlangen 'auditcore_risk[procurement]'."
        )
    from auditcore_procurement import prechecks

    key = ("procurement", spec["profile"], spec["version"])
    if key not in ctx.cache:
        ctx.cache[key] = prechecks.load_profile(spec["profile"], spec["version"])
    profile = ctx.cache[key]
    if spec["date_source"] == "record":
        on = as_date(table.value(index, spec["date_field"]), spec["date_field"])
    else:
        on = ctx.reference_date
        if on is None:
            raise InputError("Das Profil verlangt einen ausdrücklichen Stichtag (reference_date).")
    source = {
        "profile": spec["profile"],
        "version": spec["version"],
        "category": spec["category"],
        "authority_type": spec["authority_type"],
        "date": None if on is None else on.isoformat(),
    }
    if on is None:
        return None, {**source, "unavailable": "Datum fehlt"}
    try:
        period = prechecks.eu_period(profile, on)
        threshold = prechecks.eu_threshold(
            profile, spec["category"], period, spec["authority_type"]
        )
    except prechecks.ThresholdUnavailable as exc:
        return None, {**source, "unavailable": str(exc)}
    return float(threshold.value), {
        **source,
        **threshold.to_dict(),
        "fingerprint": profile.fingerprint,
    }
