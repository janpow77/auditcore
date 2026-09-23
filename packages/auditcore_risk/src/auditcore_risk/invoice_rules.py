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
from typing import Any

from .base import Context, Kind, Outcome, Table, is_number, need
from .errors import InputError, ProfileError
from .values import as_date, is_missing


def _truthy(value: Any) -> bool:
    return not is_missing(value) and bool(value)


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real | Decimal):
        raise InputError(f"Feld {field!r} erwartet eine Zahl, erhalten: {value!r}.")
    return float(value)


def _amount_or_statistic(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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
            threshold = _number(median, p["median_field"]) + (
                float(p["sigma"]) * _number(std, p["std_field"])
            )
            if amount > threshold:
                out.flags[i], out.variants[i] = True, "relative"
                out.evidence[i] = {
                    "amount": amount,
                    "median": float(median),
                    "threshold": threshold,
                }
                out.reasons[i] = (
                    f"Betrag {amount:.2f} über Median + {p['sigma']}σ = {threshold:.2f}."
                )
    return out


def _share_above(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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


def _all_missing(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        if not any(_truthy(table.value(i, f)) for f in p["fields"]):
            out.flags[i] = True
            out.evidence[i] = {"fields": list(p["fields"])}
            out.reasons[i] = f"Keine Angabe in {', '.join(p['fields'])}."
    return out


def _round_amount_terms(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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


def _date_outside_range(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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
        values = {
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


def _text_patterns(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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


def _names_differ(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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


def _identifier_equal(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)

    def norm(value: Any) -> str:
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


def _split_window(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    minimum = int(p["min_items"])
    window = int(p["window_days"])
    for i in range(len(table)):
        raw = table.value(i, p["items_field"])
        if is_missing(raw) or not raw:
            continue
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
        if len(items) < minimum:
            continue
        for threshold in p["thresholds"]:
            lower = float(threshold) * float(p["proximity"])
            near = [it for it in items if lower <= it[0] <= float(threshold)]
            if len(near) < minimum:
                continue
            ordered = sorted(near, key=lambda it: it[1])
            hit = _first_window(ordered, minimum, window)
            if hit is not None:
                total = sum(it[0] for it in hit)
                out.flags[i] = True
                out.evidence[i] = {
                    "count": len(hit),
                    "lower": lower,
                    "threshold": float(threshold),
                    "total": total,
                    "window_days": window,
                    "dates": [it[1].isoformat() for it in hit],
                }
                out.reasons[i] = (
                    f"{len(hit)} Rechnungen in [{lower:.2f}; {float(threshold):.2f}] "
                    f"innerhalb von {window} Tagen."
                )
                break
    return out


def _first_window(
    ordered: list[tuple[float, date]], minimum: int, window: int
) -> list[tuple[float, date]] | None:
    for start in range(len(ordered) - minimum + 1):
        end = ordered[start][1] + timedelta(days=window)
        inside = [it for it in ordered[start:] if it[1] <= end]
        if len(inside) >= minimum:
            return inside
    return None


# --------------------------------------------------------------------------- validation


def _check_numbers(*keys: str) -> Any:
    def check(params: Mapping[str, Any], where: str) -> None:
        """Each named parameter must be a finite number."""
        for key in keys:
            need(is_number(params[key]), where, f"{key} muss eine endliche Zahl sein")

    return check


def _check_patterns(params: Mapping[str, Any], where: str) -> None:
    need(
        isinstance(params["patterns"], list) and bool(params["patterns"]),
        where,
        "patterns muss eine nicht leere Liste sein",
    )
    for pattern in params["patterns"]:
        try:
            re.compile(pattern)
        except (re.error, TypeError) as exc:
            raise ProfileError(f"{where}: ungültiges Muster {pattern!r}: {exc}") from exc


def _check_split(params: Mapping[str, Any], where: str) -> None:
    need(
        all(is_number(t) and t > 0 for t in params["thresholds"]),
        where,
        "thresholds müssen positive Zahlen sein",
    )
    need(
        is_number(params["proximity"]) and 0 < params["proximity"] < 1,
        where,
        "proximity muss zwischen 0 und 1 liegen",
    )
    need(
        isinstance(params["min_items"], int) and params["min_items"] >= 1,
        where,
        "min_items muss eine positive ganze Zahl sein",
    )
    need(
        isinstance(params["window_days"], int) and params["window_days"] >= 0,
        where,
        "window_days muss eine ganze Zahl ≥ 0 sein",
    )


def _check_round(params: Mapping[str, Any], where: str) -> None:
    _check_numbers("min_amount")(params, where)
    severities = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")
    need(
        params["severity_with_terms"] in severities
        and params["severity_without_terms"] in severities,
        where,
        "unbekannte Schwere",
    )
    need(
        isinstance(params["multiple"], int) and params["multiple"] > 0,
        where,
        "multiple muss eine positive ganze Zahl sein",
    )
    need(isinstance(params["terms"], list), where, "terms muss eine Liste sein")


def _no_extra_checks(params: Mapping[str, Any], where: str) -> None:
    return None


INVOICE_KINDS: dict[str, Kind] = {
    "amount_or_statistic": Kind(
        "record",
        frozenset({"amount_field", "absolute_gt", "median_field", "std_field", "sigma"}),
        frozenset(),
        _amount_or_statistic,
        _check_numbers("absolute_gt", "sigma"),
    ),
    "share_above": Kind(
        "record",
        frozenset({"numerator_field", "denominator_field", "ratio_gt"}),
        frozenset(),
        _share_above,
        _check_numbers("ratio_gt"),
    ),
    "all_missing": Kind(
        "record", frozenset({"fields"}), frozenset(), _all_missing, _no_extra_checks
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
        _check_round,
        derives_severity=True,
    ),
    "date_outside_range": Kind(
        "record",
        frozenset(
            {"start_field", "end_field", "fallback_field", "range_start_field", "range_end_field"}
        ),
        frozenset(),
        _date_outside_range,
        _no_extra_checks,
    ),
    "text_patterns": Kind(
        "record",
        frozenset({"field", "patterns", "lower"}),
        frozenset(),
        _text_patterns,
        _check_patterns,
    ),
    "names_differ": Kind(
        "record",
        frozenset({"left_field", "right_field"}),
        frozenset(),
        _names_differ,
        _no_extra_checks,
    ),
    "identifier_equal": Kind(
        "record",
        frozenset({"left_field", "right_field", "upper", "remove_chars"}),
        frozenset(),
        _identifier_equal,
        _no_extra_checks,
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
        frozenset(),
        _split_window,
        _check_split,
    ),
}
