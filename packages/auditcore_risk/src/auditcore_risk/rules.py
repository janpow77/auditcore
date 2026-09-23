"""Rule kinds: the reusable mechanics behind every profile rule.

A rule kind is pure mechanics. Every fachliche setting — amounts, thresholds,
proximity, patterns, minimum counts, the name-matching profile and scorer —
comes from the profile parameters; there are no hidden defaults. Each kind
returns, per record, a flag (``True``/``False``, or ``None`` if the record
cannot be decided), the evidence that led to it and a German reason.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from importlib.util import find_spec
from typing import Any

from .errors import DependencyError, InputError, ProfileError
from .values import as_date, coerce_number, fmt, hashable, is_missing, strict_amount, text

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


def _sum(values: Sequence[float]) -> float:
    """Correctly rounded sum; non-finite values follow IEEE arithmetic."""
    if all(math.isfinite(v) for v in values):
        return math.fsum(values)
    return float(sum(values))


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


# --------------------------------------------------------------------------- kinds


def _round_multiple(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    amounts = _amounts(table, p)
    multiple = float(p["multiple"])
    out = Outcome.constant(len(table), False)
    for i, a in enumerate(amounts):
        flag = (a > 0 or not p["positive_only"]) and a % multiple == 0
        out.flags[i] = bool(flag)
        if flag:
            out.reasons[i] = f"Betrag {fmt(a)} ist ein glattes Vielfaches von {fmt(multiple)}."
            out.evidence[i] = {"amount": a, "multiple": multiple}
    return out


def _procurement_threshold(
    spec: Mapping[str, Any], table: Table, index: int, ctx: Context
) -> tuple[float | None, dict[str, Any]]:
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


def _near_threshold(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    amounts = _amounts(table, p)
    thresholds = p["thresholds"]
    static = [float(t) for t in thresholds["static"]]
    lower = p["lower"]
    eu_spec = thresholds.get("procurement_eu")

    def bound(t: float) -> float:
        """Lower edge exactly as the source computes it (``(1 - p) · t`` or ``t · f``)."""
        if "proximity" in lower:
            return (1 - float(lower["proximity"])) * t
        return t * float(lower["factor"])

    out = Outcome.constant(len(table), False)
    out.matches = [0] * len(table)
    for i, a in enumerate(amounts):
        candidates: list[tuple[float, dict[str, Any]]] = [(t, {"source": "static"}) for t in static]
        undetermined: dict[str, Any] | None = None
        if eu_spec is not None:
            value, info = _procurement_threshold(eu_spec, table, i, ctx)
            if value is None:
                undetermined = info
            else:
                candidates.append((value, {"source": "procurement_eu", **info}))
        hits = []
        if math.isfinite(a) and a > 0:
            for t, info in candidates:
                if bound(t) <= a < t:
                    hits.append({"threshold": t, "lower_bound": bound(t), **info})
                    if p["count"] == "first":
                        break
        out.matches[i] = len(hits)
        if hits:
            out.flags[i] = True
            first = hits[0]
            kind = "Profilschwelle" if first["source"] == "static" else "jahresbezogene EU-Schwelle"
            out.reasons[i] = (
                f"Betrag {fmt(a)} liegt im Bereich [{fmt(first['lower_bound'])}; "
                f"{fmt(first['threshold'])}) knapp unter der Schwelle {fmt(first['threshold'])} "
                f"({kind})."
            )
            out.evidence[i] = {"amount": a, "matches": hits}
        elif undetermined is not None:
            out.flags[i] = None
            out.reasons[i] = (
                "Nicht entscheidbar: keine belegte jahresbezogene EU-Schwelle "
                f"({undetermined['unavailable']})."
            )
            out.evidence[i] = {"amount": a, "unavailable": undetermined}
    return out


def identifier_state(p: Mapping[str, Any], raw: Any) -> str:
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


def _missing_procurement(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    amounts = _amounts(table, p, "amount_field")
    relevant = _relevance(table, p["relevance"])
    id_field = p["id_field"]
    has_ids = table.has(id_field)
    if not has_ids and p["id_column_missing"] != "counts_as_missing":
        raise InputError(f"Spalte {id_field!r} fehlt.")
    out = Outcome.constant(len(table), False)
    for i, a in enumerate(amounts):
        raw = text(table.value(i, id_field)) if has_ids else None
        why = identifier_state(p, raw) if has_ids else "Spalte fehlt"
        flag = a > float(p["amount_gt"]) and bool(why) and relevant[i]
        out.flags[i] = flag
        if flag:
            out.reasons[i] = (
                f"Betrag {fmt(a)} über {fmt(float(p['amount_gt']))}; Vergabekennung {why}"
                f"{f' ({raw!r})' if raw is not None else ''}; Kostenart vergaberelevant."
            )
            out.evidence[i] = {"amount": a, "id": raw, "id_state": why}
    return out


def _entity_profile(p: Mapping[str, Any], ctx: Context) -> Any:
    if find_spec("rapidfuzz") is None:
        raise DependencyError("Der Namensabgleich verlangt 'auditcore_risk[fuzzy]' (rapidfuzz).")
    from auditcore_entity_matching import load_profile

    spec = p["normalization"]
    key = ("entity", spec["profile"], spec["version"])
    if key not in ctx.cache:
        ctx.cache[key] = load_profile(spec["profile"], spec["version"])
    return ctx.cache[key]


def pair_similarity(
    p: Mapping[str, Any], raw_a: Any, raw_b: Any, ctx: Context
) -> tuple[float, str, str, str]:
    """Score, method and both comparison forms of one name pair (``str()`` like the source)."""
    from auditcore_entity_matching import normalize, pair_score

    profile = _entity_profile(p, ctx)
    minimum = int(p["min_length"])
    a = normalize(None if raw_a is None else str(raw_a), profile)
    b = normalize(None if raw_b is None else str(raw_b), profile)
    if not a or not b or len(a) < minimum or len(b) < minimum:
        return 0.0, "zu kurz", a, b
    if a in b or b in a:
        return float(p["containment_score"]), "enthalten", a, b
    return pair_score(a, b, p["scorer"]) / float(p["scale"]), str(p["scorer"]), a, b


def _name_similarity(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    profile = _entity_profile(p, ctx)
    override = (
        p["override_field"] if p["override_field"] and table.has(p["override_field"]) else None
    )
    out = Outcome.constant(len(table), False)
    scores: list[float] = []
    for i in range(len(table)):
        score, how, a, b = pair_similarity(
            p, table.value(i, p["left_field"]), table.value(i, p["right_field"]), ctx
        )
        scores.append(score)
        if override is not None:
            value = table.value(i, override)
            flag = False if is_missing(value) else bool(value)
            basis = "übernommene Vorberechnung"
        else:
            flag = score >= float(p["threshold"])
            basis = f"Ähnlichkeit {score:.4f} ≥ {p['threshold']}"
        out.flags[i] = flag
        if flag:
            out.reasons[i] = (
                f"Begünstigter und Auftragnehmer stimmen überein ({basis}; "
                f"Vergleichsform {a!r} / {b!r})."
            )
            out.evidence[i] = {
                "left": a,
                "right": b,
                "score": score,
                "method": how,
                "override_field": override,
                "normalization": dict(profile.reference),
            }
    out.values[p["value_name"]] = scores
    return out


def _concentration(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    n = len(table)
    payee_f, case_f, group_f = p["payee_field"], p["case_field"], p["group_field"]
    out = Outcome.constant(n, False)
    if not table.has(payee_f, case_f):
        return out
    amounts = _amounts(table, p, "amount_field")
    relevant = _relevance(table, p["relevance"])
    payees = []
    for i in range(n):
        raw = table.value(i, payee_f)
        payees.append(hashable("" if is_missing(raw) else raw, payee_f))
    valid = [str(payees[i]).strip() != "" and relevant[i] for i in range(n)]
    cases = []
    for i in range(n):
        raw = table.value(i, case_f)
        cases.append(raw if is_missing(raw) else hashable(raw, case_f))
    pair_rule, group_rule = p["pair"], p["group"]
    pairs: dict[tuple[Any, Any], list[float]] = {}
    for i in range(n):
        if valid[i] and not is_missing(cases[i]):
            pairs.setdefault((cases[i], payees[i]), []).append(amounts[i])
    pair_hits = {
        k: (len(v), _sum(v))
        for k, v in pairs.items()
        if len(v) > pair_rule["count_gt"] and _sum(v) > pair_rule["sum_gt"]
    }
    group_hits: dict[tuple[Any, Any], tuple[int, float]] = {}
    groups = None
    if table.has(group_f):
        groups = []
        for i in range(n):
            raw = table.value(i, group_f)
            groups.append(raw if is_missing(raw) else hashable(raw, group_f))
    if groups is not None:
        acc: dict[tuple[Any, Any], tuple[set[Any], list[float]]] = {}
        for i in range(n):
            if valid[i] and not is_missing(groups[i]):
                entry = acc.setdefault((groups[i], payees[i]), (set(), []))
                if not is_missing(cases[i]):
                    entry[0].add(cases[i])
                entry[1].append(amounts[i])
        group_hits = {
            k: (len(c), _sum(a))
            for k, (c, a) in acc.items()
            if len(c) > group_rule["cases_gt"] and _sum(a) > group_rule["sum_gt"]
        }
    for i in range(n):
        evidence: dict[str, Any] = {}
        if not is_missing(cases[i]) and (cases[i], payees[i]) in pair_hits:
            count, total = pair_hits[(cases[i], payees[i])]
            evidence["pair"] = {"case": cases[i], "payee": payees[i], "count": count, "sum": total}
        if (
            groups is not None
            and not is_missing(groups[i])
            and (groups[i], payees[i]) in group_hits
        ):
            count, total = group_hits[(groups[i], payees[i])]
            evidence["group"] = {
                "group": groups[i],
                "payee": payees[i],
                "cases": count,
                "sum": total,
            }
        if evidence and relevant[i]:
            out.flags[i] = True
            parts = []
            if "pair" in evidence:
                e = evidence["pair"]
                parts.append(
                    f"{e['count']} vergaberelevante Belege mit zusammen {fmt(e['sum'])} "
                    f"(> {pair_rule['count_gt']} Belege, > {fmt(pair_rule['sum_gt'])})"
                )
            if "group" in evidence:
                e = evidence["group"]
                parts.append(
                    f"Auftragnehmer bei {e['cases']} Vorhaben desselben Begünstigten mit "
                    f"zusammen {fmt(e['sum'])} (> {group_rule['cases_gt']} Vorhaben, "
                    f"> {fmt(group_rule['sum_gt'])})"
                )
            out.reasons[i] = "Wiederholte Beauftragung: " + "; ".join(parts) + "."
            out.evidence[i] = evidence
    return out


def _ratio_history(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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


def _leave_one_out(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    n = len(table)
    group_f, case_f, deduction_f = p["group_field"], p["case_field"], p["deduction_field"]
    amounts = _amounts(table, p, "amount_field")
    deductions = []
    for i in range(n):
        if table.has(deduction_f):
            value = coerce_number(table.value(i, deduction_f), deduction_f)
            deductions.append(float(p["deduction_missing_value"]) if value is None else value)
        else:
            deductions.append(float(p["deduction_missing_value"]))
    per_case: dict[tuple[Any, Any], tuple[list[float], list[float]]] = {}
    per_group: dict[Any, tuple[list[float], list[float], set[Any]]] = {}
    for i in range(n):
        group, case = table.value(i, group_f), table.value(i, case_f)
        if is_missing(group):
            continue
        g = per_group.setdefault(hashable(group, group_f), ([], [], set()))
        g[0].append(amounts[i])
        g[1].append(deductions[i])
        if not is_missing(case):
            g[2].add(hashable(case, case_f))
            c = per_case.setdefault((group, case), ([], []))
            c[0].append(amounts[i])
            c[1].append(deductions[i])
    triggered: dict[Any, list[dict[str, Any]]] = {}
    for (group, case), (gross, cut) in per_case.items():
        g_gross, g_cut, g_cases = per_group[group]
        gross_loo = _sum(g_gross) - _sum(gross)
        cut_loo = _sum(g_cut) - _sum(cut)
        rate = cut_loo / gross_loo * float(p["percent_factor"]) if gross_loo > 0 else 0.0
        if rate > float(p["rate_gt"]) and len(g_cases) > int(p["min_cases_gt"]):
            triggered.setdefault(case, []).append(
                {"group": group, "rate_percent": rate, "cases_in_group": len(g_cases)}
            )
    out = Outcome.constant(n, False)
    for i in range(n):
        case = table.value(i, case_f)
        if not is_missing(case) and case in triggered:
            hits = triggered[case]
            own = table.value(i, group_f)
            out.flags[i] = True
            detail = "; ".join(
                f"Gruppe {h['group']!r}: {h['rate_percent']:.2f} % ohne dieses Vorhaben"
                for h in hits
            )
            foreign = all(is_missing(own) or h["group"] != own for h in hits)
            out.reasons[i] = (
                f"Hohe historische Kürzungsquote (> {p['rate_gt']} %) der übrigen Vorhaben: "
                f"{detail}."
                + (
                    " Merkmal über gleiche Vorhabenkennung aus anderer Gruppe übernommen"
                    " (Legacyverhalten)."
                    if foreign
                    else ""
                )
            )
            out.evidence[i] = {
                "case": case,
                "own_group": own,
                "triggering": hits,
                "matched_by_case_only": foreign,
            }
    return out


def _numeric_compare(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    name = p["field"]
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        if table.has(name):
            value = coerce_number(table.value(i, name), name)
            number = float(p["missing_value"]) if value is None else value
        else:
            number = float(p["column_missing_value"])
        flag = _compare(number, p["op"], float(p["value"]))
        out.flags[i] = flag
        if flag:
            out.reasons[i] = f"{name} = {number:g} {_OPS[p['op']]} {p['value']}."
            out.evidence[i] = {"value": number, "op": p["op"], "limit": p["value"]}
    return out


def _text_equals(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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


def _missing_value(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        if is_missing(table.value(i, p["field"])):
            out.flags[i] = True
            out.reasons[i] = f"{p['field']} fehlt."
            out.evidence[i] = {"field": p["field"]}
    return out


def _instant(value: Any, name: str) -> datetime | None:
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


def _date_before(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
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


def _duplicate_key(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    names = list(p["fields"])
    keys = []
    for i in range(len(table)):
        values = [table.value(i, name) for name in names]
        keys.append(
            tuple(
                _MISSING_KEY if is_missing(v) else hashable(v, names[j])
                for j, v in enumerate(values)
            )
        )
    counts: dict[tuple[Any, ...], int] = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    out = Outcome.constant(len(table), False)
    for i, key in enumerate(keys):
        if counts[key] > 1:
            out.flags[i] = True
            out.reasons[i] = f"Schlüssel {', '.join(names)} kommt {counts[key]}-mal vor."
            out.evidence[i] = {"occurrences": counts[key]}
    return out


def _nonzero_without_text(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    amounts = _amounts(table, p, "amount_field")
    out = Outcome.constant(len(table), False)
    for i, a in enumerate(amounts):
        note = text(table.value(i, p["text_field"]))
        if a != 0 and (note is None or note.strip() == ""):
            out.flags[i] = True
            out.reasons[i] = f"{p['amount_field']} {fmt(a)} ohne {p['text_field']}."
            out.evidence[i] = {"amount": a}
    return out


def _balance_mismatch(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    minuend = _amounts(table, {**p, "field": p["minuend"]})
    subtrahends = [_amounts(table, {**p, "field": s}) for s in p["subtrahends"]]
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


def _amount_with_marker(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    amounts = _amounts(table, p, "amount_field")
    pattern = re.compile(p["marker_pattern"])
    out = Outcome.constant(len(table), False)
    for i, a in enumerate(amounts):
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


def _nanmax(values: Sequence[float]) -> float:
    present = [v for v in values if not math.isnan(v)]
    return max(present) if present else math.nan


def _top_share(p: Mapping[str, Any], table: Table, ctx: Context) -> Outcome:
    name, group_f = p["amount_field"], p["group_field"]
    numbers = [coerce_number(table.value(i, name), name) for i in range(len(table))]
    present = [v for v in numbers if v is not None]
    total = _sum(present)
    out = Outcome.constant(len(table), None)
    if not total > 0:
        out.dataset = {"triggered": False, "value": None, "reason": "Gesamtsumme nicht positiv."}
        return out
    sums: dict[Any, list[float]] = {}
    for i, v in enumerate(numbers):
        raw = table.value(i, group_f)
        key = _MISSING_KEY if is_missing(raw) else hashable(raw, group_f)
        sums.setdefault(key, [])
        if v is not None:
            sums[key].append(v)
    by_group = {k: _sum(v) for k, v in sums.items()}
    top = _nanmax(list(by_group.values()))
    share = top / total
    triggered = share >= float(p["share_ge"])
    leader = next((k for k, v in by_group.items() if v == top), None)
    out.dataset = {
        "triggered": bool(triggered),
        "value": share,
        "reason": (
            f"Anteil des größten {group_f} an der Summe {name}: {share:.4f} "
            f"(Schwelle ≥ {p['share_ge']})."
        ),
        "evidence": {
            "group": None if leader is _MISSING_KEY else leader,
            "group_sum": top,
            "total": total,
        },
    }
    return out


# --------------------------------------------------------------------------- registry

_AMOUNT = frozenset({"parse", "missing_value"})
_RELEVANCE_KEYS = {"field", "exclude_pattern", "ignore_case", "column_missing"}

KINDS: dict[str, Kind] = {
    "round_multiple": Kind(
        "record",
        frozenset({"field", "multiple", "positive_only"}) | _AMOUNT,
        frozenset(),
        _round_multiple,
    ),
    "near_threshold": Kind(
        "record",
        frozenset({"field", "thresholds", "lower", "count"}) | _AMOUNT,
        frozenset(),
        _near_threshold,
    ),
    "missing_procurement": Kind(
        "record",
        frozenset(
            {
                "amount_field",
                "amount_gt",
                "id_field",
                "id_column_missing",
                "blank_values",
                "blank_casefold",
                "placeholder_pattern",
                "relevance",
            }
        )
        | _AMOUNT,
        frozenset(),
        _missing_procurement,
    ),
    "name_similarity": Kind(
        "record",
        frozenset(
            {
                "left_field",
                "right_field",
                "normalization",
                "min_length",
                "containment_score",
                "scorer",
                "scale",
                "threshold",
                "override_field",
                "value_name",
            }
        ),
        frozenset(),
        _name_similarity,
    ),
    "counterparty_concentration": Kind(
        "record",
        frozenset(
            {
                "amount_field",
                "payee_field",
                "case_field",
                "group_field",
                "relevance",
                "pair",
                "group",
            }
        )
        | _AMOUNT,
        frozenset(),
        _concentration,
    ),
    "ratio_history": Kind(
        "record",
        frozenset({"total_field", "part_field", "ratio_gt", "total_min"}),
        frozenset(),
        _ratio_history,
    ),
    "leave_one_out_rate": Kind(
        "record",
        frozenset(
            {
                "group_field",
                "case_field",
                "amount_field",
                "deduction_field",
                "deduction_missing_value",
                "rate_gt",
                "percent_factor",
                "min_cases_gt",
            }
        )
        | _AMOUNT,
        frozenset(),
        _leave_one_out,
    ),
    "numeric_compare": Kind(
        "record",
        frozenset({"field", "column_missing_value", "missing_value", "op", "value"}),
        frozenset(),
        _numeric_compare,
    ),
    "text_equals": Kind(
        "record", frozenset({"field", "column_missing_value", "value"}), frozenset(), _text_equals
    ),
    "missing_value": Kind("record", frozenset({"field"}), frozenset(), _missing_value),
    "date_before": Kind("record", frozenset({"field", "before_field"}), frozenset(), _date_before),
    "duplicate_key": Kind("record", frozenset({"fields"}), frozenset(), _duplicate_key),
    "nonzero_without_text": Kind(
        "record",
        frozenset({"amount_field", "text_field"}) | _AMOUNT,
        frozenset(),
        _nonzero_without_text,
    ),
    "balance_mismatch": Kind(
        "record",
        frozenset({"minuend", "subtrahends", "tolerance"}) | _AMOUNT,
        frozenset(),
        _balance_mismatch,
    ),
    "amount_with_marker": Kind(
        "record",
        frozenset({"amount_field", "amount_gt", "marker_field", "marker_pattern", "lowercase"})
        | _AMOUNT,
        frozenset(),
        _amount_with_marker,
    ),
    "top_share": Kind(
        "dataset", frozenset({"group_field", "amount_field", "share_ge"}), frozenset(), _top_share
    ),
}


def _need(condition: bool, where: str, message: str) -> None:
    if not condition:
        raise ProfileError(f"{where}: {message}")


def _number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def validate_params(kind: str, params: Mapping[str, Any], where: str) -> None:
    """Exact parameter set of the kind plus the value checks that matter for safety."""
    spec = KINDS[kind]
    keys = set(params)
    _need(spec.required <= keys, where, f"fehlende Parameter {sorted(spec.required - keys)}")
    unknown = keys - spec.required - spec.optional
    _need(not unknown, where, f"unbekannte Parameter {sorted(unknown)}")
    if "parse" in params:
        _need(params["parse"] in ("strict", "coerce"), where, "parse muss strict/coerce sein")
        _need(_number(params["missing_value"]), where, "missing_value muss eine Zahl sein")
    for key in (
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
    ):
        if key in params:
            _need(_number(params[key]), where, f"{key} muss eine endliche Zahl sein")
    for key in ("placeholder_pattern", "marker_pattern"):
        if params.get(key):
            try:
                re.compile(params[key])
            except re.error as exc:
                raise ProfileError(f"{where}: ungültiges Muster {key}: {exc}") from exc
    relevance = params.get("relevance")
    if relevance is not None:
        _need(
            isinstance(relevance, dict) and set(relevance) == _RELEVANCE_KEYS,
            where,
            f"relevance braucht genau {sorted(_RELEVANCE_KEYS)}",
        )
        _need(
            relevance["column_missing"] in ("relevant", "error"),
            where,
            "relevance.column_missing muss relevant/error sein",
        )
        try:
            re.compile(relevance["exclude_pattern"])
        except (re.error, TypeError) as exc:
            raise ProfileError(f"{where}: ungültiges Ausschlussmuster: {exc}") from exc
    if kind == "near_threshold":
        thresholds = params["thresholds"]
        _need(
            isinstance(thresholds, dict) and "static" in thresholds,
            where,
            "thresholds braucht 'static'",
        )
        _need(
            set(thresholds) <= {"static", "procurement_eu", "annotations"},
            where,
            "unbekannter Schwellenschlüssel",
        )
        _need(
            all(_number(t) and t > 0 for t in thresholds["static"]),
            where,
            "statische Schwellen müssen positive Zahlen sein",
        )
        eu = thresholds.get("procurement_eu")
        if eu is not None:
            needed = {"profile", "version", "category", "authority_type", "date_source"}
            _need(
                isinstance(eu, dict) and needed <= set(eu),
                where,
                f"procurement_eu braucht {sorted(needed)}",
            )
            _need(
                eu["date_source"] in ("record", "reference_date"),
                where,
                "date_source muss record/reference_date sein",
            )
            _need(
                eu["date_source"] != "record" or isinstance(eu.get("date_field"), str),
                where,
                "date_source record verlangt date_field",
            )
        lower = params["lower"]
        _need(
            isinstance(lower, dict) and len(lower) == 1 and set(lower) <= {"proximity", "factor"},
            where,
            "lower braucht genau proximity oder factor",
        )
        value = next(iter(lower.values()))
        _need(_number(value) and 0 < value < 1, where, "lower muss zwischen 0 und 1 liegen")
        _need(params["count"] in ("first", "all"), where, "count muss first/all sein")
    if kind == "numeric_compare":
        _need(params["op"] in _OPS, where, f"op muss eine von {sorted(_OPS)} sein")
    if kind == "missing_procurement":
        _need(
            params["id_column_missing"] in ("counts_as_missing", "error"),
            where,
            "id_column_missing muss counts_as_missing/error sein",
        )
    if kind == "name_similarity":
        norm = params["normalization"]
        _need(
            isinstance(norm, dict) and set(norm) == {"profile", "version"},
            where,
            "normalization braucht profile und version",
        )
        _need(
            params["scorer"] in ("ratio", "token_set_ratio", "token_sort_ratio", "WRatio"),
            where,
            "unbekannter Scorer",
        )
    if kind == "counterparty_concentration":
        _need(set(params["pair"]) == {"count_gt", "sum_gt"}, where, "pair braucht count_gt, sum_gt")
        _need(
            set(params["group"]) == {"cases_gt", "sum_gt"}, where, "group braucht cases_gt, sum_gt"
        )
