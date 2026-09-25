"""Parameter checks of the single-invoice rule kinds (``Kind.validate``)."""

from __future__ import annotations

import re

from .base import JsonObject, is_number, need
from .errors import ProfileError
from .rule_checks import Check


def check_numbers(*keys: str) -> Check:
    """Check that each named parameter is a finite number."""

    def check(params: JsonObject, where: str) -> None:
        """Each named parameter must be a finite number."""
        for key in keys:
            need(is_number(params[key]), where, f"{key} muss eine endliche Zahl sein")

    return check


def check_patterns(params: JsonObject, where: str) -> None:
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


def check_split(params: JsonObject, where: str) -> None:
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
    eu = params.get("procurement_eu")
    if eu is not None:
        needed = {"profile", "version", "category", "authority_type", "date_source", "date_field"}
        need(
            isinstance(eu, dict) and set(eu) == needed and eu["date_source"] == "record",
            where,
            f"procurement_eu braucht {sorted(needed)} mit date_source record",
        )


def check_round(params: JsonObject, where: str) -> None:
    check_numbers("min_amount")(params, where)
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


def no_extra_checks(params: JsonObject, where: str) -> None:
    """Kinds whose key set is their whole contract."""
    return None
