"""Predicate kinds for point scores (WIBANK-RBVK criteria, ex-ante indicators).

Each rule is one named criterion that is true or false for a record; its
points live in the rule (``points``) and are summed by the profile's
``points_stages`` assessment. The predicates reproduce the source semantics:
``_bool``-style truthy texts, ``str(value) in {...}``, ``float(value or 0)``
ranges and membership in a set of earlier finding families.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import Context, Kind, Outcome, Table, is_number, need
from .errors import InputError
from .values import is_missing


def _truthy(value: Any, truthy: frozenset[str]) -> bool:
    if isinstance(value, bool):
        return value
    if is_missing(value):
        return False
    return str(value).strip().lower() in truthy


def _truthy_all(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    truthy = frozenset(p["truthy_values"])
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        values = [table.value(i, f) for f in p["fields"]]
        if all(_truthy(v, truthy) for v in values):
            out.flags[i] = True
            out.evidence[i] = {"values": dict(zip(p["fields"], values, strict=True))}
            out.reasons[i] = f"{' und '.join(p['fields'])} zutreffend."
    return out


def _text_in_set(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    allowed = frozenset(p["values"])
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        row = table.rows[i]
        text = str(row[p["field"]]) if p["field"] in row else p["missing_text"]
        if text in allowed:
            out.flags[i] = True
            out.evidence[i] = {"value": text}
            out.reasons[i] = f"{p['field']} = {text!r}."
    return out


def _as_number(value: Any, field: str, missing: float) -> float:
    """``float(value or missing)`` exactly like the sources (``NaN`` stays ``NaN``)."""
    try:
        return float(value or missing)
    except (TypeError, ValueError) as exc:
        raise InputError(f"Feld {field!r} erwartet eine Zahl, erhalten {value!r}.") from exc


def _number_range(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    low, high = p["lower"], p["upper"]
    for i in range(len(table)):
        row = table.rows[i]
        raw = row.get(p["field"]) if p["field"] in row else None
        x = _as_number(raw, p["field"], float(p["missing_value"]))
        above = low is None or (x >= low if p["lower_inclusive"] else x > low)
        below = high is None or (x <= high if p["upper_inclusive"] else x < high)
        if above and below:
            out.flags[i] = True
            out.evidence[i] = {"value": x}
            out.reasons[i] = f"{p['field']} = {x:g} im Bereich."
    return out


def _set_overlap(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    values = frozenset(p["values"])
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        raw = table.value(i, p["field"])
        if is_missing(raw):
            members: set[Any] = set()
        elif isinstance(raw, list | tuple | set | frozenset):
            members = set(raw)
        else:
            raise InputError(f"Feld {p['field']!r} erwartet eine Liste.")
        hit = bool(members & values) if p["mode"] == "any" else bool(members - values)
        if hit:
            out.flags[i] = True
            out.evidence[i] = {"members": sorted(str(m) for m in members)}
            out.reasons[i] = f"{p['field']}: {sorted(str(m) for m in members)}."
    return out


def _check_truthy(params: Mapping[str, Any], where: str) -> None:
    need(
        isinstance(params["fields"], list) and bool(params["fields"]),
        where,
        "fields muss eine nicht leere Liste sein",
    )
    need(isinstance(params["truthy_values"], list), where, "truthy_values muss eine Liste sein")


def _check_set(params: Mapping[str, Any], where: str) -> None:
    need(isinstance(params["values"], list), where, "values muss eine Liste sein")


def _check_range(params: Mapping[str, Any], where: str) -> None:
    for key in ("lower", "upper"):
        need(
            params[key] is None or is_number(params[key]), where, f"{key} muss Zahl oder null sein"
        )
    need(
        params["lower"] is not None or params["upper"] is not None,
        where,
        "mindestens eine Grenze ist nötig",
    )
    need(is_number(params["missing_value"]), where, "missing_value muss eine Zahl sein")


def _check_overlap(params: Mapping[str, Any], where: str) -> None:
    _check_set(params, where)
    need(params["mode"] in ("any", "outside"), where, "mode muss any/outside sein")


SCORE_KINDS: dict[str, Kind] = {
    "truthy_all": Kind(
        "record", frozenset({"fields", "truthy_values"}), frozenset(), _truthy_all, _check_truthy
    ),
    "text_in_set": Kind(
        "record",
        frozenset({"field", "values", "missing_text"}),
        frozenset(),
        _text_in_set,
        _check_set,
    ),
    "number_range": Kind(
        "record",
        frozenset(
            {"field", "lower", "lower_inclusive", "upper", "upper_inclusive", "missing_value"}
        ),
        frozenset(),
        _number_range,
        _check_range,
    ),
    "set_overlap": Kind(
        "record", frozenset({"field", "values", "mode"}), frozenset(), _set_overlap, _check_overlap
    ),
}
