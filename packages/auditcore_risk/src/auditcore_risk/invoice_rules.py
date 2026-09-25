"""Rule kinds for single-invoice risk indicators (flowinvoice/audit-portal ``RiskChecker``).

Each record is one invoice. Context values (median, vendor statistics,
project period, other invoices of the same vendor) are ordinary record fields,
typically flattened with :func:`auditcore_risk.flatten_record`
(``context.median_amount`` …). Truthiness rules of the source are kept where
they decide whether a check runs (a median of ``0.0`` counts as "not given").
Each kind names a message *variant*; the texts live in the profile.
"""

from __future__ import annotations

import math
import numbers
import re
from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal

from .amount_rules import unavailable_threshold_reason
from .base import Context, JsonObject, Kind, Outcome, Table, procurement_threshold, seq_sum
from .errors import InputError
from .invoice_checks import (
    check_numbers,
    check_patterns,
    check_round,
    check_split,
    no_extra_checks,
)
from .values import as_date, is_missing


def _truthy(value: object) -> bool:
    return not is_missing(value) and bool(value)


def _number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real | Decimal):
        raise InputError(f"Feld {field!r} erwartet eine Zahl, erhalten: {value!r}.")
    return float(value)


def _amount_or_statistic(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    out.variants = [None] * len(table)
    for i in range(len(table)):
        amount = _number(table.value(i, p["amount_field"]), p["amount_field"])
        limit = float(p["absolute_gt"])
        if amount > limit:
            out.flags[i], out.variants[i] = True, "absolute"
            out.evidence[i] = {"amount": amount, "limit": limit}
            out.reasons[i] = f"Betrag {amount:.2f} über {limit:.2f}."
            continue
        median, std = table.value(i, p["median_field"]), table.value(i, p["std_field"])
        if _truthy(median) and _truthy(std):
            median_value = _number(median, p["median_field"])
            threshold = median_value + (float(p["sigma"]) * _number(std, p["std_field"]))
            if amount > threshold:
                out.flags[i], out.variants[i] = True, "relative"
                out.evidence[i] = {
                    "amount": amount,
                    "median": median_value,
                    "threshold": threshold,
                }
                out.reasons[i] = (
                    f"Betrag {amount:.2f} über Median + {p['sigma']}σ = {threshold:.2f}."
                )
    return out


def _share_above(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        num, den = table.value(i, p["numerator_field"]), table.value(i, p["denominator_field"])
        if not _truthy(num) or not _truthy(den):
            continue
        ratio = _number(num, p["numerator_field"]) / _number(den, p["denominator_field"])
        if ratio > float(p["ratio_gt"]):
            out.flags[i] = True
            out.evidence[i] = {"numerator": num, "denominator": den, "ratio": ratio}
            out.reasons[i] = f"Anteil {num}/{den} = {ratio:.4f} > {p['ratio_gt']}."
    return out


def _all_missing(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        if not any(_truthy(table.value(i, f)) for f in p["fields"]):
            out.flags[i] = True
            out.evidence[i] = {"fields": list(p["fields"])}
            out.reasons[i] = f"Keine Angabe in {', '.join(p['fields'])}."
    return out


def _round_amount_terms(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    out.variants = [None] * len(table)
    out.severities = [None] * len(table)
    multiple = int(p["multiple"])
    for i in range(len(table)):
        amount = _number(table.value(i, p["amount_field"]), p["amount_field"])
        if amount < float(p["min_amount"]):
            continue
        if not math.isfinite(amount):
            raise InputError(f"Feld {p['amount_field']!r}: Betrag {amount!r} ist nicht endlich.")
        if amount == int(amount) and int(amount) % multiple == 0:
            description = table.value(i, p["text_field"])
            lowered = "" if is_missing(description) else str(description).lower()
            matched = any(term in lowered for term in p["terms"])
            out.flags[i] = True
            out.variants[i] = "with_terms" if matched else "without_terms"
            out.severities[i] = p["severity_with_terms"] if matched else p["severity_without_terms"]
            out.evidence[i] = {"amount": amount, "terms_found": matched}
            out.reasons[i] = f"Betrag {amount:.2f} ist ein glattes Vielfaches von {multiple}."
    return out


def _date_outside_range(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    out.variants = [None] * len(table)
    for i in range(len(table)):
        low = table.value(i, p["range_start_field"])
        high = table.value(i, p["range_end_field"])
        if not _truthy(low) or not _truthy(high):
            continue
        range_start = as_date(low, p["range_start_field"])
        range_end = as_date(high, p["range_end_field"])
        fallback = table.value(i, p["fallback_field"])
        start_raw = table.value(i, p["start_field"])
        end_raw = table.value(i, p["end_field"])
        check_start = as_date(start_raw if _truthy(start_raw) else fallback, p["start_field"])
        check_end = as_date(end_raw if _truthy(end_raw) else fallback, p["end_field"])
        if check_start is None or check_end is None or range_start is None or range_end is None:
            raise InputError("Datumsvergleich ohne Rechnungsdatum nicht möglich.")
        values: dict[str, object] = {
            "check_start": check_start,
            "check_end": check_end,
            "range_start": range_start,
            "range_end": range_end,
        }
        if check_start < range_start:
            out.flags[i], out.variants[i] = True, "before_start"
        elif check_end > range_end:
            out.flags[i], out.variants[i] = True, "after_end"
        if out.flags[i]:
            out.evidence[i] = values
            out.reasons[i] = (
                f"Zeitraum {check_start}–{check_end} außerhalb {range_start}–{range_end}."
            )
    return out


def _text_patterns(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    compiled = [re.compile(pattern) for pattern in p["patterns"]]
    for i in range(len(table)):
        raw = table.value(i, p["field"])
        value = "" if is_missing(raw) else str(raw)
        if p["lower"]:
            value = value.lower()
        for pattern in compiled:
            if pattern.search(value):
                out.flags[i] = True
                shown = pattern.pattern.replace(chr(92), "")
                out.evidence[i] = {"pattern": pattern.pattern, "pattern_display": shown}
                out.reasons[i] = f"Muster {pattern.pattern!r} in {p['field']}."
                break
    return out


def _names_differ(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        left, right = table.value(i, p["left_field"]), table.value(i, p["right_field"])
        if not _truthy(left) or not _truthy(right):
            continue
        a, b = str(left).lower().strip(), str(right).lower().strip()
        if a != b and b not in a and a not in b:
            out.flags[i] = True
            out.evidence[i] = {"left": left, "right": right}
            out.reasons[i] = f"{left!r} und {right!r} stimmen nicht überein."
    return out


def _identifier_equal(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)

    def norm(value: object) -> str:
        """Identifier comparison form: upper case, stripped, separators removed."""
        text = str(value).upper().strip() if p["upper"] else str(value).strip()
        for char in p["remove_chars"]:
            text = text.replace(char, "")
        return text

    for i in range(len(table)):
        left, right = table.value(i, p["left_field"]), table.value(i, p["right_field"])
        if not _truthy(left) or not _truthy(right):
            continue
        if norm(left) == norm(right):
            out.flags[i] = True
            out.evidence[i] = {"left": left, "right": right, "normalized": norm(left)}
            out.reasons[i] = f"Kennungen gleich ({norm(left)})."
    return out


Item = tuple[float, date]


def _split_items(raw: object, p: JsonObject) -> list[Item]:
    """Amount and date of every listed invoice of the same vendor."""
    if not isinstance(raw, list | tuple):
        raise InputError(f"Feld {p['items_field']!r} erwartet eine Liste.")
    items = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise InputError(f"Feld {p['items_field']!r}: Einträge müssen Zuordnungen sein.")
        amount = _number(item.get(p["amount_key"]), p["amount_key"])
        day = as_date(item.get(p["date_key"]), p["date_key"])
        if day is None:
            raise InputError(f"Feld {p['items_field']!r}: Datum fehlt.")
        items.append((amount, day))
    return items


def _split_thresholds(
    p: JsonObject, table: Table, index: int, ctx: Context
) -> tuple[list[float], dict[str, object] | None]:
    """Profile thresholds plus the year-bound EU threshold, if the profile names one."""
    thresholds = [float(t) for t in p["thresholds"]]
    eu_spec = p.get("procurement_eu")
    if eu_spec is None:
        return thresholds, None
    value, eu_info = procurement_threshold(eu_spec, table, index, ctx)
    if value is not None:
        thresholds = sorted({*thresholds, value})
    return thresholds, eu_info


def _split_hit(
    items: list[Item], thresholds: list[float], p: JsonObject
) -> tuple[float, float, list[Item]] | None:
    """First threshold with ``min_items`` invoices near it inside the window."""
    minimum = int(p["min_items"])
    for threshold in thresholds:
        lower = float(threshold) * float(p["proximity"])
        near = [it for it in items if lower <= it[0] <= float(threshold)]
        if len(near) < minimum:
            continue
        ordered = sorted(near, key=lambda it: it[1])
        hit = _first_window(ordered, minimum, int(p["window_days"]))
        if hit is not None:
            return lower, float(threshold), hit
    return None


def _split_window(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    window = int(p["window_days"])
    for i in range(len(table)):
        raw = table.value(i, p["items_field"])
        if is_missing(raw) or not raw:
            continue
        items = _split_items(raw, p)
        if len(items) < int(p["min_items"]):
            continue
        thresholds, eu_info = _split_thresholds(p, table, i, ctx)
        found = _split_hit(items, thresholds, p)
        if found is not None:
            lower, threshold, hit = found
            out.flags[i] = True
            out.evidence[i] = {
                "count": len(hit),
                "lower": lower,
                "threshold": threshold,
                "total": seq_sum(it[0] for it in hit),
                "window_days": window,
                "dates": [it[1].isoformat() for it in hit],
                "eu_threshold": eu_info,
            }
            out.reasons[i] = (
                f"{len(hit)} Rechnungen in [{lower:.2f}; {threshold:.2f}] "
                f"innerhalb von {window} Tagen."
            )
        elif eu_info is not None and "unavailable" in eu_info:
            out.flags[i] = None
            out.evidence[i] = {"eu_threshold": eu_info}
            out.reasons[i] = unavailable_threshold_reason(eu_info)
    return out


def _first_window(ordered: list[Item], minimum: int, window: int) -> list[Item] | None:
    for start in range(len(ordered) - minimum + 1):
        end = ordered[start][1] + timedelta(days=window)
        inside = [it for it in ordered[start:] if it[1] <= end]
        if len(inside) >= minimum:
            return inside
    return None


INVOICE_KINDS: dict[str, Kind] = {
    "amount_or_statistic": Kind(
        "record",
        frozenset({"amount_field", "absolute_gt", "median_field", "std_field", "sigma"}),
        frozenset(),
        _amount_or_statistic,
        check_numbers("absolute_gt", "sigma"),
    ),
    "share_above": Kind(
        "record",
        frozenset({"numerator_field", "denominator_field", "ratio_gt"}),
        frozenset(),
        _share_above,
        check_numbers("ratio_gt"),
    ),
    "all_missing": Kind(
        "record", frozenset({"fields"}), frozenset(), _all_missing, no_extra_checks
    ),
    "round_amount_terms": Kind(
        "record",
        frozenset(
            {
                "amount_field",
                "min_amount",
                "multiple",
                "text_field",
                "terms",
                "severity_with_terms",
                "severity_without_terms",
            }
        ),
        frozenset(),
        _round_amount_terms,
        check_round,
        derives_severity=True,
    ),
    "date_outside_range": Kind(
        "record",
        frozenset(
            {"start_field", "end_field", "fallback_field", "range_start_field", "range_end_field"}
        ),
        frozenset(),
        _date_outside_range,
        no_extra_checks,
    ),
    "text_patterns": Kind(
        "record",
        frozenset({"field", "patterns", "lower"}),
        frozenset(),
        _text_patterns,
        check_patterns,
    ),
    "names_differ": Kind(
        "record",
        frozenset({"left_field", "right_field"}),
        frozenset(),
        _names_differ,
        no_extra_checks,
    ),
    "identifier_equal": Kind(
        "record",
        frozenset({"left_field", "right_field", "upper", "remove_chars"}),
        frozenset(),
        _identifier_equal,
        no_extra_checks,
    ),
    "split_window": Kind(
        "record",
        frozenset(
            {
                "items_field",
                "amount_key",
                "date_key",
                "thresholds",
                "proximity",
                "min_items",
                "window_days",
            }
        ),
        frozenset({"procurement_eu"}),
        _split_window,
        check_split,
    ),
}
