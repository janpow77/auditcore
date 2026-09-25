"""Amount rule kinds: round amounts, threshold proximity, procurement identifiers.

Every setting comes from the profile parameters; a missing amount is either
the profile's substitute value or, with ``missing_amount_reason``, undecidable.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping

from .base import (
    Context,
    JsonObject,
    Outcome,
    Table,
    amount_values,
    present_amounts,
    procurement_threshold,
    relevance,
)
from .errors import InputError
from .values import fmt, text

#: One threshold candidate: its value and where it comes from (static or year-bound EU).
Candidate = tuple[float, dict[str, object]]


def round_multiple(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Amount is an exact multiple of ``multiple`` (optionally positive amounts only)."""
    multiple = float(p["multiple"])
    out = Outcome.constant(len(table), False)
    for i, a in enumerate(present_amounts(table, p)):
        flag = (a > 0 or not p["positive_only"]) and a % multiple == 0
        out.flags[i] = bool(flag)
        if flag:
            out.reasons[i] = f"Betrag {fmt(a)} ist ein glattes Vielfaches von {fmt(multiple)}."
            out.evidence[i] = {"amount": a, "multiple": multiple}
    return out


def _lower_bound(lower: JsonObject, threshold: float) -> float:
    """Lower edge exactly as the source computes it (``(1 - p) · t`` or ``t · f``)."""
    if "proximity" in lower:
        return (1 - float(lower["proximity"])) * threshold
    return threshold * float(lower["factor"])


def _threshold_candidates(
    p: JsonObject, table: Table, index: int, ctx: Context
) -> tuple[list[Candidate], dict[str, object] | None]:
    """Static thresholds plus the year-bound EU threshold (or why it is unavailable)."""
    thresholds = p["thresholds"]
    candidates: list[Candidate] = [(float(t), {"source": "static"}) for t in thresholds["static"]]
    eu_spec = thresholds.get("procurement_eu")
    if eu_spec is None:
        return candidates, None
    value, info = procurement_threshold(eu_spec, table, index, ctx)
    if value is None:
        return candidates, info
    candidates.append((value, {"source": "procurement_eu", **info}))
    return candidates, None


def _threshold_hits(
    amount: float, candidates: list[Candidate], p: JsonObject
) -> list[dict[str, object]]:
    """Thresholds whose band ``[lower bound; threshold)`` contains ``amount``."""
    hits: list[dict[str, object]] = []
    if not (math.isfinite(amount) and amount > 0):
        return hits
    for threshold, info in candidates:
        bound = _lower_bound(p["lower"], threshold)
        if bound <= amount < threshold:
            hits.append({"threshold": threshold, "lower_bound": bound, **info})
            if p["count"] == "first":
                break
    return hits


def _near_hit_reason(amount: float, first: JsonObject) -> str:
    kind = "Profilschwelle" if first["source"] == "static" else "jahresbezogene EU-Schwelle"
    return (
        f"Betrag {fmt(amount)} liegt im Bereich [{fmt(first['lower_bound'])}; "
        f"{fmt(first['threshold'])}) knapp unter der Schwelle {fmt(first['threshold'])} "
        f"({kind})."
    )


def unavailable_threshold_reason(unavailable: Mapping[str, object]) -> str:
    """Reason for a record whose decision needs a year-bound EU threshold that is not proven."""
    return (
        "Nicht entscheidbar: keine belegte jahresbezogene EU-Schwelle "
        f"({unavailable['unavailable']})."
    )


def near_threshold(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Amount just below a static or year-bound threshold (split-contract indicator)."""
    out = Outcome.constant(len(table), False)
    out.matches = [0] * len(table)
    for i, a in enumerate(amount_values(table, p)):
        if a is None:
            # Nur mit missing_amount_reason (missing_value null): ohne Betrag nicht entscheidbar.
            out.flags[i] = None
            out.reasons[i] = str(p["missing_amount_reason"])
            out.evidence[i] = {"amount": None, "field": p["field"]}
            continue
        candidates, undetermined = _threshold_candidates(p, table, i, ctx)
        hits = _threshold_hits(a, candidates, p)
        out.matches[i] = len(hits)
        if hits:
            out.flags[i] = True
            out.reasons[i] = _near_hit_reason(a, hits[0])
            out.evidence[i] = {"amount": a, "matches": hits}
        elif undetermined is not None:
            out.flags[i] = None
            out.reasons[i] = unavailable_threshold_reason(undetermined)
            out.evidence[i] = {"amount": a, "unavailable": undetermined}
    return out


def identifier_state(p: JsonObject, raw: object) -> str:
    """Why an identifier counts as missing (``""`` = genuine identifier present)."""
    value = text(raw)
    stripped = "" if value is None else value.strip()
    compare = stripped.lower() if p["blank_casefold"] else stripped
    blanks = {b.lower() if p["blank_casefold"] else b for b in p["blank_values"]}
    if value is None or compare in blanks:
        return "fehlt"
    if p["placeholder_pattern"] and re.match(p["placeholder_pattern"], stripped):
        return "ist ein Platzhalter"
    return ""


def _procurement_reason(p: JsonObject, amount: float, why: str, raw: str | None) -> str:
    return (
        f"Betrag {fmt(amount)} über {fmt(float(p['amount_gt']))}; Vergabekennung {why}"
        f"{f' ({raw!r})' if raw is not None else ''}; Kostenart vergaberelevant."
    )


def missing_procurement(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Amount above the limit without a genuine procurement identifier (relevant cost types)."""
    amounts = amount_values(table, p, "amount_field")
    relevant = relevance(table, p["relevance"])
    id_field = p["id_field"]
    has_ids = table.has(id_field)
    if not has_ids and p["id_column_missing"] != "counts_as_missing":
        raise InputError(f"Spalte {id_field!r} fehlt.")
    out = Outcome.constant(len(table), False)
    for i, a in enumerate(amounts):
        raw = text(table.value(i, id_field)) if has_ids else None
        why = identifier_state(p, raw) if has_ids else "Spalte fehlt"
        if a is None:
            # Nur mit missing_amount_reason: unbestimmt nur, wo der Betrag entscheiden würde
            # (Vergabekennung fehlt und Kostenart vergaberelevant); sonst kein Merkmal.
            if why and relevant[i]:
                out.flags[i] = None
                out.reasons[i] = str(p["missing_amount_reason"])
                out.evidence[i] = {
                    "amount": None,
                    "field": p["amount_field"],
                    "id": raw,
                    "id_state": why,
                }
            continue
        flag = a > float(p["amount_gt"]) and bool(why) and relevant[i]
        out.flags[i] = flag
        if flag:
            out.reasons[i] = _procurement_reason(p, a, why, raw)
            out.evidence[i] = {"amount": a, "id": raw, "id_state": why}
    return out


def nonzero_without_text(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Non-zero amount without the explaining text."""
    out = Outcome.constant(len(table), False)
    for i, a in enumerate(present_amounts(table, p, "amount_field")):
        note = text(table.value(i, p["text_field"]))
        if a != 0 and (note is None or note.strip() == ""):
            out.flags[i] = True
            out.reasons[i] = f"{p['amount_field']} {fmt(a)} ohne {p['text_field']}."
            out.evidence[i] = {"amount": a}
    return out


def balance_mismatch(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Minuend minus all subtrahends differs from zero by more than the tolerance."""
    minuend = present_amounts(table, {**p, "field": p["minuend"]})
    subtrahends = [present_amounts(table, {**p, "field": s}) for s in p["subtrahends"]]
    out = Outcome.constant(len(table), False)
    for i, m in enumerate(minuend):
        rest = m
        for column in subtrahends:
            rest = rest - column[i]
        if abs(rest) > float(p["tolerance"]):
            out.flags[i] = True
            out.reasons[i] = (
                f"{p['minuend']} − {' − '.join(p['subtrahends'])} = {fmt(rest)} "
                f"(Toleranz {p['tolerance']})."
            )
            out.evidence[i] = {"difference": rest}
    return out


def amount_with_marker(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Amount above the limit together with a marker text matching the pattern."""
    pattern = re.compile(p["marker_pattern"])
    out = Outcome.constant(len(table), False)
    for i, a in enumerate(present_amounts(table, p, "amount_field")):
        marker = text(table.value(i, p["marker_field"])) or ""
        if p["lowercase"]:
            marker = marker.lower()
        if a > float(p["amount_gt"]) and pattern.search(marker):
            out.flags[i] = True
            out.reasons[i] = (
                f"Betrag {fmt(a)} über {fmt(float(p['amount_gt']))} mit {p['marker_field']} "
                f"{marker!r}."
            )
            out.evidence[i] = {"amount": a, "marker": marker}
    return out
