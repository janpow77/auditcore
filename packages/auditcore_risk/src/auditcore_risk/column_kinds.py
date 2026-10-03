"""Vectorised rule kinds over columns (same decisions as the record-wise kinds).

Each function returns a :class:`VectorOutcome` or ``None`` when the
parameters or the column types need the record-wise kind (for example
year-bound thresholds, missing amounts that stay undetermined, text dates);
:func:`auditcore_risk.columns.evaluate_columns` then runs the record kind
over the same columns. Amount comparisons stay in float64 exactly like the
record kinds; only ``balance_mismatch`` and ``top_share`` compute in whole
cents through ``auditcore_compute``.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from auditcore_compute.validation import DEVIATION, reconcile

from .amount_rules import _lower_bound, identifier_state
from .base import CENT_LIMIT, Context, DatasetOutcome, JsonObject, relevance, tolerance_cents
from .column_values import (
    Bools,
    ColumnData,
    ColumnTable,
    Floats,
    Ints,
    amounts,
    cents,
    key_codes,
    missing_mask,
    numbers,
    text_flags,
)
from .errors import InputError
from .group_rules import top_share_outcome, top_share_undecided

#: Largest product of group counts combined into one int64 key without compacting.
_RADIX_LIMIT = 2**62
#: Above this many rows int64 cent sums could overflow; Python integers are used then.
_SAFE_SUM_ROWS = 9_000_000


@dataclass
class VectorOutcome:
    """Result of one rule over all records as arrays."""

    flags: Bools
    undetermined: Bools
    matches: Ints | None = None
    values: dict[str, Floats] = field(default_factory=dict)
    dataset: DatasetOutcome | None = None

    @classmethod
    def from_flags(cls, flags: Bools) -> VectorOutcome:
        """Decided flags without undetermined records."""
        return cls(flags, np.zeros(flags.shape, dtype=np.bool_))


VectorRun = Callable[[JsonObject, ColumnData, Context], VectorOutcome | None]


def _amounts(p: JsonObject, data: ColumnData, key: str) -> Floats | None:
    """Amounts with the profile substitute; ``None`` if a missing amount stays undetermined.

    Only ``near_threshold`` and ``missing_procurement`` accept ``missing_value``
    null (profile check); every other amount kind uses :func:`_present`.
    """
    if p["missing_value"] is None:
        return None
    return _present(p, data, key)


def _present(p: JsonObject, data: ColumnData, key: str) -> Floats:
    return amounts(data, p[key], p["parse"], p["missing_value"])


def round_multiple(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """Exact multiple of ``multiple`` (Python ``%`` and ``np.remainder`` agree)."""
    values = _present(p, data, "field")
    with np.errstate(invalid="ignore"):
        multiple = np.remainder(values, float(p["multiple"])) == 0
    sign = values > 0 if p["positive_only"] else np.ones(values.shape, dtype=np.bool_)
    return VectorOutcome.from_flags(sign & multiple)


def near_threshold(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """Hits per static threshold in ``[lower bound; threshold)`` (count ``all``/``first``)."""
    values = _amounts(p, data, "field")
    if values is None or "procurement_eu" in p["thresholds"]:
        return None
    valid = np.isfinite(values) & (values > 0)
    matches = np.zeros(values.shape, dtype=np.int64)
    for raw in p["thresholds"]["static"]:
        threshold = float(raw)
        bound = _lower_bound(p["lower"], threshold)
        matches += valid & (bound <= values) & (values < threshold)
    if p["count"] == "first":
        matches = np.minimum(matches, 1)
    outcome = VectorOutcome.from_flags(matches > 0)
    outcome.matches = matches
    return outcome


def missing_value(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """The field is missing."""
    return VectorOutcome.from_flags(missing_mask(data, p["field"]))


def date_before(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """``field`` before ``before_field`` for two ``datetime64`` columns (else record kind)."""
    early, late = data.array(p["field"]), data.array(p["before_field"])
    if early is None or late is None or early.dtype.kind != "M" or late.dtype.kind != "M":
        return None
    present = ~np.isnat(early) & ~np.isnat(late)
    return VectorOutcome.from_flags(present & np.less(early, late))


def _group_ids(data: ColumnData, name: str) -> tuple[Ints, int]:
    """Group number per record in any order (missing values form one group) and the count."""
    array = data.array(name) if data.has(name) else None
    if array is None or array.dtype.kind not in "biuf":
        codes, keys = key_codes(data, name)
        return codes, len(keys)
    missing = missing_mask(data, name)
    present, inverse = np.unique(array[~missing], return_inverse=True)
    ids = np.full(data.size, present.shape[0], dtype=np.int64)
    ids[~missing] = inverse.reshape(-1)
    return ids, present.shape[0] + 1


def duplicate_key(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """The combination of ``fields`` occurs more than once (missing values compare equal).

    Equal values share a group exactly as in the record kind (``np.unique``
    treats ``-0.0`` and ``0.0`` as equal like ``dict``); groups of all fields
    are combined in mixed radix, compacted whenever the product could overflow.
    """
    combined, size = np.zeros(data.size, dtype=np.int64), 1
    for name in p["fields"]:
        ids, count = _group_ids(data, name)
        if size * count >= _RADIX_LIMIT:
            unique, inverse = np.unique(combined, return_inverse=True)
            combined, size = inverse.reshape(-1).astype(np.int64), unique.shape[0]
        combined, size = combined * count + ids, size * max(count, 1)
    _, inverse, counts = np.unique(combined, return_inverse=True, return_counts=True)
    return VectorOutcome.from_flags(counts[inverse.reshape(-1)] > 1)


def nonzero_without_text(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """Non-zero amount without the explaining text (texts read only where the amount is set)."""
    values = _present(p, data, "amount_field")
    rows = np.flatnonzero(values != 0)
    flags = np.zeros(data.size, dtype=np.bool_)
    flags[rows] = text_flags(data, p["text_field"], rows, _blank)
    return VectorOutcome.from_flags(flags)


def _blank(note: str | None) -> bool:
    return note is None or note.strip() == ""


def balance_mismatch(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """Minuend minus subtrahends in whole cents beyond the tolerance (``reconcile``)."""
    names = [p["minuend"], *p["subtrahends"]]
    converted = [cents(amounts(data, name, p["parse"], p["missing_value"])) for name in names]
    decidable = np.logical_and.reduce([ok for _, ok in converted])
    subtracted = np.zeros(data.size, dtype=np.int64)
    for value, _ in converted[1:]:
        subtracted += value
    decidable &= np.abs(subtracted) <= CENT_LIMIT
    minuend = np.where(decidable, converted[0][0], 0)
    result = reconcile(
        minuend,
        np.where(decidable, subtracted, 0),
        tolerance_cents=tolerance_cents(p["tolerance"]),
    )
    return VectorOutcome(decidable & (result.status == DEVIATION), ~decidable)


def _relevant(p: JsonObject, data: ColumnData) -> Bools:
    spec = p["relevance"]
    if spec is None:
        return np.ones(data.size, dtype=np.bool_)
    return np.array(relevance(ColumnTable(data), spec), dtype=np.bool_).reshape(data.size)


def missing_procurement(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """Amount above the limit without a genuine identifier (identifiers read only there)."""
    values = _amounts(p, data, "amount_field")
    if values is None:
        return None
    relevant = _relevant(p, data)
    has_ids = data.has(p["id_field"])
    if not has_ids and p["id_column_missing"] != "counts_as_missing":
        raise InputError(f"Spalte {p['id_field']!r} fehlt.")
    rows = np.flatnonzero((values > float(p["amount_gt"])) & relevant)
    flags = np.zeros(data.size, dtype=np.bool_)
    if has_ids:
        flags[rows] = text_flags(
            data, p["id_field"], rows, lambda raw: bool(identifier_state(p, raw))
        )
    else:
        flags[rows] = True
    return VectorOutcome.from_flags(flags)


def amount_with_marker(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """Amount above the limit with a marker matching the pattern (markers read only there)."""
    values = _present(p, data, "amount_field")
    pattern = re.compile(p["marker_pattern"])
    rows = np.flatnonzero(values > float(p["amount_gt"]))

    def marked(raw: str | None) -> bool:
        marker = raw or ""
        return pattern.search(marker.lower() if p["lowercase"] else marker) is not None

    flags = np.zeros(data.size, dtype=np.bool_)
    flags[rows] = text_flags(data, p["marker_field"], rows, marked)
    return VectorOutcome.from_flags(flags)


def _int_sum(values: Ints) -> int:
    return int(values.sum()) if values.shape[0] <= _SAFE_SUM_ROWS else sum(values.tolist())


def _group_sums(codes: Ints, values: Ints, groups: int) -> list[int]:
    if values.shape[0] > _SAFE_SUM_ROWS:
        sums = [0] * groups
        for code, value in zip(codes.tolist(), values.tolist(), strict=True):
            sums[code] += value
        return sums
    totals = np.zeros(groups, dtype=np.int64)
    np.add.at(totals, codes, values)
    return [int(v) for v in totals.tolist()]


def top_share(p: JsonObject, data: ColumnData, ctx: Context) -> VectorOutcome | None:
    """Share of the largest group in the total amount, summed in whole cents."""
    name = p["amount_field"]
    if data.has(name):
        values, missing = numbers(data, name, "coerce")
    else:
        values, missing = np.zeros(data.size), np.ones(data.size, dtype=np.bool_)
    converted, ok = cents(np.where(missing, 0.0, values))
    unconvertible = np.flatnonzero(~missing & ~ok)
    outcome = VectorOutcome(np.zeros(data.size, np.bool_), np.ones(data.size, np.bool_))
    total = _int_sum(converted)
    if unconvertible.size or not total > 0:
        first = int(unconvertible[0]) if unconvertible.size else None
        outcome.dataset = top_share_undecided(first)
        return outcome
    codes, keys = key_codes(data, p["group_field"])
    sums = _group_sums(codes, converted, len(keys))
    top = max(sums)
    outcome.dataset = top_share_outcome(p, total, top, keys[sums.index(top)])
    return outcome


VECTOR_KINDS: dict[str, VectorRun] = {
    "round_multiple": round_multiple,
    "near_threshold": near_threshold,
    "missing_value": missing_value,
    "date_before": date_before,
    "duplicate_key": duplicate_key,
    "nonzero_without_text": nonzero_without_text,
    "balance_mismatch": balance_mismatch,
    "missing_procurement": missing_procurement,
    "amount_with_marker": amount_with_marker,
    "top_share": top_share,
}

__all__ = ["VECTOR_KINDS", "VectorOutcome", "VectorRun"]
