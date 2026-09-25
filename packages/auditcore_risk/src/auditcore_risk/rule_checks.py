"""Parameter value checks of the rule kinds that have no own ``Kind.validate``.

:func:`auditcore_risk.rules.validate_params` first checks the exact key set,
then the common checks (amount parsing, finite numbers, patterns, relevance)
and finally the check of the kind itself from :data:`KIND_CHECKS`.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from .base import OPERATOR_SYMBOLS, JsonObject, is_number, need
from .errors import ProfileError

#: Parameters that must be finite numbers wherever a kind has them.
NUMBER_KEYS = (
    "multiple",
    "amount_gt",
    "tolerance",
    "ratio_gt",
    "total_min",
    "rate_gt",
    "percent_factor",
    "share_ge",
    "threshold",
    "scale",
    "containment_score",
)
PATTERN_KEYS = ("placeholder_pattern", "marker_pattern")
RELEVANCE_KEYS = frozenset({"field", "exclude_pattern", "ignore_case", "column_missing"})
SCORERS = ("ratio", "token_set_ratio", "token_sort_ratio", "WRatio")
EU_THRESHOLD_KEYS = frozenset({"profile", "version", "category", "authority_type", "date_source"})

Check = Callable[[JsonObject, str], None]


def _check_amount_parsing(params: JsonObject, where: str) -> None:
    if "parse" not in params:
        return
    need(params["parse"] in ("strict", "coerce"), where, "parse muss strict/coerce sein")
    reason = params.get("missing_amount_reason")
    if reason is None:
        need(is_number(params["missing_value"]), where, "missing_value muss eine Zahl sein")
        return
    need(
        isinstance(reason, str) and bool(reason.strip()),
        where,
        "missing_amount_reason muss ein nichtleerer Text sein",
    )
    need(
        params["missing_value"] is None,
        where,
        "missing_amount_reason verlangt missing_value null (kein Ersatzbetrag)",
    )


def _check_numbers(params: JsonObject, where: str) -> None:
    for key in NUMBER_KEYS:
        if key in params:
            need(is_number(params[key]), where, f"{key} muss eine endliche Zahl sein")


def _check_patterns(params: JsonObject, where: str) -> None:
    for key in PATTERN_KEYS:
        if params.get(key):
            try:
                re.compile(params[key])
            except re.error as exc:
                raise ProfileError(f"{where}: ungültiges Muster {key}: {exc}") from exc


def _check_relevance(params: JsonObject, where: str) -> None:
    relevance = params.get("relevance")
    if relevance is None:
        return
    need(
        isinstance(relevance, dict) and set(relevance) == RELEVANCE_KEYS,
        where,
        f"relevance braucht genau {sorted(RELEVANCE_KEYS)}",
    )
    need(
        relevance["column_missing"] in ("relevant", "error"),
        where,
        "relevance.column_missing muss relevant/error sein",
    )
    try:
        re.compile(relevance["exclude_pattern"])
    except (re.error, TypeError) as exc:
        raise ProfileError(f"{where}: ungültiges Ausschlussmuster: {exc}") from exc


#: Checks every kind without its own ``Kind.validate`` passes, in this order.
COMMON_CHECKS: tuple[Check, ...] = (
    _check_amount_parsing,
    _check_numbers,
    _check_patterns,
    _check_relevance,
)


def _check_eu_threshold(eu: JsonObject, where: str) -> None:
    need(
        isinstance(eu, dict) and set(eu) >= EU_THRESHOLD_KEYS,
        where,
        f"procurement_eu braucht {sorted(EU_THRESHOLD_KEYS)}",
    )
    need(
        eu["date_source"] in ("record", "reference_date"),
        where,
        "date_source muss record/reference_date sein",
    )
    need(
        eu["date_source"] != "record" or isinstance(eu.get("date_field"), str),
        where,
        "date_source record verlangt date_field",
    )


def _check_near_threshold(params: JsonObject, where: str) -> None:
    thresholds = params["thresholds"]
    need(
        isinstance(thresholds, dict) and "static" in thresholds,
        where,
        "thresholds braucht 'static'",
    )
    need(
        set(thresholds) <= {"static", "procurement_eu", "annotations"},
        where,
        "unbekannter Schwellenschlüssel",
    )
    need(
        all(is_number(t) and t > 0 for t in thresholds["static"]),
        where,
        "statische Schwellen müssen positive Zahlen sein",
    )
    eu = thresholds.get("procurement_eu")
    if eu is not None:
        _check_eu_threshold(eu, where)
    lower = params["lower"]
    need(
        isinstance(lower, dict) and len(lower) == 1 and set(lower) <= {"proximity", "factor"},
        where,
        "lower braucht genau proximity oder factor",
    )
    value = next(iter(lower.values()))
    need(is_number(value) and 0 < value < 1, where, "lower muss zwischen 0 und 1 liegen")
    need(params["count"] in ("first", "all"), where, "count muss first/all sein")


def _check_propagation(params: JsonObject, where: str) -> None:
    if "propagation" in params:
        need(
            params["propagation"] in ("case_any_group", "same_group"),
            where,
            "propagation muss case_any_group/same_group sein",
        )


def _check_numeric_compare(params: JsonObject, where: str) -> None:
    need(
        params["op"] in OPERATOR_SYMBOLS,
        where,
        f"op muss eine von {sorted(OPERATOR_SYMBOLS)} sein",
    )


def _check_missing_procurement(params: JsonObject, where: str) -> None:
    need(
        params["id_column_missing"] in ("counts_as_missing", "error"),
        where,
        "id_column_missing muss counts_as_missing/error sein",
    )


def _check_name_similarity(params: JsonObject, where: str) -> None:
    norm = params["normalization"]
    need(
        isinstance(norm, dict) and set(norm) == {"profile", "version"},
        where,
        "normalization braucht profile und version",
    )
    need(params["scorer"] in SCORERS, where, "unbekannter Scorer")


def _check_concentration(params: JsonObject, where: str) -> None:
    need(set(params["pair"]) == {"count_gt", "sum_gt"}, where, "pair braucht count_gt, sum_gt")
    need(set(params["group"]) == {"cases_gt", "sum_gt"}, where, "group braucht cases_gt, sum_gt")


#: Kind-specific checks after the common ones (kinds absent here have none).
KIND_CHECKS: dict[str, Check] = {
    "near_threshold": _check_near_threshold,
    "leave_one_out_rate": _check_propagation,
    "numeric_compare": _check_numeric_compare,
    "missing_procurement": _check_missing_procurement,
    "name_similarity": _check_name_similarity,
    "counterparty_concentration": _check_concentration,
}
