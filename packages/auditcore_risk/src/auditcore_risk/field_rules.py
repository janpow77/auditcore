"""Field rule kinds: comparisons, missing values, dates and duplicate keys per record."""

from __future__ import annotations

from collections.abc import Hashable
from datetime import date, datetime

from .base import MISSING_KEY, OPERATOR_SYMBOLS, Context, JsonObject, Outcome, Table, compare
from .errors import InputError
from .values import coerce_number, hashable, is_missing, text


def ratio_history(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Share of invalid versions above ``ratio_gt`` with at least ``total_min`` versions."""
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        total = coerce_number(table.value(i, p["total_field"]), p["total_field"]) or 0.0
        part = coerce_number(table.value(i, p["part_field"]), p["part_field"]) or 0.0
        ratio = part / total if total > 0 else 0.0
        flag = ratio > float(p["ratio_gt"]) and total >= float(p["total_min"])
        out.flags[i] = flag
        if flag:
            out.reasons[i] = (
                f"{part:g} von {total:g} Versionen ungültig (Anteil {ratio:.2f} > "
                f"{p['ratio_gt']}, mindestens {p['total_min']} Versionen)."
            )
            out.evidence[i] = {"total": total, "part": part, "ratio": ratio}
    return out


def numeric_compare(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Number (or its substitute) compared with a fixed limit."""
    name = p["field"]
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        if table.has(name):
            value = coerce_number(table.value(i, name), name)
            number = float(p["missing_value"]) if value is None else value
        else:
            number = float(p["column_missing_value"])
        flag = compare(number, p["op"], float(p["value"]))
        out.flags[i] = flag
        if flag:
            out.reasons[i] = f"{name} = {number:g} {OPERATOR_SYMBOLS[p['op']]} {p['value']}."
            out.evidence[i] = {"value": number, "op": p["op"], "limit": p["value"]}
    return out


def text_equals(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Text value equal to the profile value."""
    name = p["field"]
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        value = text(table.value(i, name)) if table.has(name) else p["column_missing_value"]
        flag = value == p["value"]
        out.flags[i] = flag
        if flag:
            out.reasons[i] = f"{name} = {value!r}."
            out.evidence[i] = {"value": value}
    return out


def missing_value(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """The field is missing."""
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        if is_missing(table.value(i, p["field"])):
            out.flags[i] = True
            out.reasons[i] = f"{p['field']} fehlt."
            out.evidence[i] = {"field": p["field"]}
    return out


def _instant(value: object, name: str) -> datetime | None:
    if is_missing(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.strip())
        except ValueError as exc:
            raise InputError(f"Feld {name!r}: kein ISO-Datum {value!r}.") from exc
    raise InputError(f"Feld {name!r}: kein Datum {value!r}.")


def date_before(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """One date lies before another one."""
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        early = _instant(table.value(i, p["field"]), p["field"])
        late = _instant(table.value(i, p["before_field"]), p["before_field"])
        if early is not None and late is not None and early < late:
            out.flags[i] = True
            out.reasons[i] = (
                f"{p['field']} {early.date()} liegt vor {p['before_field']} {late.date()}."
            )
            out.evidence[i] = {p["field"]: early.isoformat(), p["before_field"]: late.isoformat()}
    return out


def duplicate_key(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """The combination of ``fields`` occurs more than once (missing values compare equal)."""
    names = list(p["fields"])
    keys: list[tuple[Hashable, ...]] = []
    for i in range(len(table)):
        values = [table.value(i, name) for name in names]
        keys.append(
            tuple(
                MISSING_KEY if is_missing(v) else hashable(v, names[j])
                for j, v in enumerate(values)
            )
        )
    counts: dict[tuple[Hashable, ...], int] = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    out = Outcome.constant(len(table), False)
    for i, key in enumerate(keys):
        if counts[key] > 1:
            out.flags[i] = True
            out.reasons[i] = f"Schlüssel {', '.join(names)} kommt {counts[key]}-mal vor."
            out.evidence[i] = {"occurrences": counts[key]}
    return out
