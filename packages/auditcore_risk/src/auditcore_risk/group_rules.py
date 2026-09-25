"""Group rule kinds: repeated awards, leave-one-out deduction rates, top shares.

These kinds aggregate over several records (per case, payee or group) and
then flag each record by the aggregate it belongs to.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Mapping, Sequence
from typing import Any

from .base import (
    MISSING_KEY,
    Context,
    JsonObject,
    Outcome,
    Table,
    correct_sum,
    present_amounts,
    relevance,
)
from .values import coerce_number, fmt, hashable, is_missing

#: Grouping key per record; a missing value keeps the raw missing marker.
Keys = list[object]
PairKey = tuple[object, object]


# --------------------------------------------------------------------------- concentration


def _grouping_keys(table: Table, name: str) -> Keys:
    """Hashable key per record, the missing value itself where the cell is missing."""
    keys: Keys = []
    for i in range(len(table)):
        raw = table.value(i, name)
        keys.append(raw if is_missing(raw) else hashable(raw, name))
    return keys


def _payee_keys(table: Table, name: str) -> list[Hashable]:
    """Payee per record; a missing payee reads as the empty text (excluded later)."""
    payees: list[Hashable] = []
    for i in range(len(table)):
        raw = table.value(i, name)
        payees.append(hashable("" if is_missing(raw) else raw, name))
    return payees


def _pair_hits(
    cases: Keys,
    payees: list[Hashable],
    valid: list[bool],
    amounts: list[float],
    rule: JsonObject,
) -> dict[PairKey, tuple[int, float]]:
    """Case/payee pairs with more than ``count_gt`` receipts summing above ``sum_gt``."""
    pairs: dict[PairKey, list[float]] = {}
    for i, case in enumerate(cases):
        if valid[i] and not is_missing(case):
            pairs.setdefault((case, payees[i]), []).append(amounts[i])
    return {
        k: (len(v), correct_sum(v))
        for k, v in pairs.items()
        if len(v) > rule["count_gt"] and correct_sum(v) > rule["sum_gt"]
    }


def _group_hits(
    groups: Keys,
    cases: Keys,
    payees: list[Hashable],
    valid: list[bool],
    amounts: list[float],
    rule: JsonObject,
) -> dict[PairKey, tuple[int, float]]:
    """Group/payee pairs over more than ``cases_gt`` cases summing above ``sum_gt``."""
    acc: dict[PairKey, tuple[set[object], list[float]]] = {}
    for i, group in enumerate(groups):
        if valid[i] and not is_missing(group):
            entry = acc.setdefault((group, payees[i]), (set(), []))
            if not is_missing(cases[i]):
                entry[0].add(cases[i])
            entry[1].append(amounts[i])
    return {
        k: (len(c), correct_sum(a))
        for k, (c, a) in acc.items()
        if len(c) > rule["cases_gt"] and correct_sum(a) > rule["sum_gt"]
    }


def _concentration_reason(evidence: JsonObject, p: JsonObject) -> str:
    pair_rule, group_rule = p["pair"], p["group"]
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
    return "Wiederholte Beauftragung: " + "; ".join(parts) + "."


def _concentration_evidence(
    case: object,
    group: object | None,
    payee: Hashable,
    pair_hits: Mapping[PairKey, tuple[int, float]],
    group_hits: Mapping[PairKey, tuple[int, float]],
    has_groups: bool,
) -> dict[str, object]:
    evidence: dict[str, object] = {}
    if not is_missing(case) and (case, payee) in pair_hits:
        count, total = pair_hits[(case, payee)]
        evidence["pair"] = {"case": case, "payee": payee, "count": count, "sum": total}
    if has_groups and not is_missing(group) and (group, payee) in group_hits:
        count, total = group_hits[(group, payee)]
        evidence["group"] = {"group": group, "payee": payee, "cases": count, "sum": total}
    return evidence


def counterparty_concentration(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Repeated awards to one payee per case or across cases of one group."""
    n = len(table)
    payee_f, case_f, group_f = p["payee_field"], p["case_field"], p["group_field"]
    out = Outcome.constant(n, False)
    if not table.has(payee_f, case_f):
        return out
    amounts = present_amounts(table, p, "amount_field")
    relevant = relevance(table, p["relevance"])
    payees = _payee_keys(table, payee_f)
    valid = [str(payees[i]).strip() != "" and relevant[i] for i in range(n)]
    cases = _grouping_keys(table, case_f)
    pair_hits = _pair_hits(cases, payees, valid, amounts, p["pair"])
    has_groups = table.has(group_f)
    groups: Keys = _grouping_keys(table, group_f) if has_groups else [None] * n
    group_hits = (
        _group_hits(groups, cases, payees, valid, amounts, p["group"]) if has_groups else {}
    )
    for i in range(n):
        evidence = _concentration_evidence(
            cases[i], groups[i], payees[i], pair_hits, group_hits, has_groups
        )
        if evidence and relevant[i]:
            out.flags[i] = True
            out.reasons[i] = _concentration_reason(evidence, p)
            out.evidence[i] = evidence
    return out


# --------------------------------------------------------------------------- leave one out


def _deductions(table: Table, p: JsonObject) -> list[float]:
    name = p["deduction_field"]
    substitute = float(p["deduction_missing_value"])
    if not table.has(name):
        return [substitute] * len(table)
    out = []
    for i in range(len(table)):
        value = coerce_number(table.value(i, name), name)
        out.append(substitute if value is None else value)
    return out


#: Per case: gross amounts and deductions; per group: the same plus its cases.
CaseSums = dict[tuple[Hashable, Hashable], tuple[list[float], list[float]]]
GroupSums = dict[Hashable, tuple[list[float], list[float], set[Hashable]]]


def _case_and_group_sums(
    table: Table, p: JsonObject, amounts: list[float], deductions: list[float]
) -> tuple[CaseSums, GroupSums]:
    group_f, case_f = p["group_field"], p["case_field"]
    per_case: CaseSums = {}
    per_group: GroupSums = {}
    for i in range(len(table)):
        group, case = table.value(i, group_f), table.value(i, case_f)
        if is_missing(group):
            continue
        group_key = hashable(group, group_f)
        g = per_group.setdefault(group_key, ([], [], set()))
        g[0].append(amounts[i])
        g[1].append(deductions[i])
        if not is_missing(case):
            case_key = hashable(case, case_f)
            g[2].add(case_key)
            c = per_case.setdefault((group_key, case_key), ([], []))
            c[0].append(amounts[i])
            c[1].append(deductions[i])
    return per_case, per_group


def _triggered_cases(
    per_case: CaseSums, per_group: GroupSums, p: JsonObject
) -> dict[object, list[dict[str, Any]]]:
    """Cases whose group, without the case itself, has a deduction rate above ``rate_gt``."""
    triggered: dict[object, list[dict[str, Any]]] = {}
    for (group, case), (gross, cut) in per_case.items():
        g_gross, g_cut, g_cases = per_group[group]
        gross_loo = correct_sum(g_gross) - correct_sum(gross)
        cut_loo = correct_sum(g_cut) - correct_sum(cut)
        rate = cut_loo / gross_loo * float(p["percent_factor"]) if gross_loo > 0 else 0.0
        if rate > float(p["rate_gt"]) and len(g_cases) > int(p["min_cases_gt"]):
            triggered.setdefault(case, []).append(
                {"group": group, "rate_percent": rate, "cases_in_group": len(g_cases)}
            )
    return triggered


def _leave_one_out_reason(hits: Sequence[JsonObject], rate_gt: object, foreign: bool) -> str:
    detail = "; ".join(
        f"Gruppe {h['group']!r}: {h['rate_percent']:.2f} % ohne dieses Vorhaben" for h in hits
    )
    return f"Hohe historische Kürzungsquote (> {rate_gt} %) der übrigen Vorhaben: {detail}." + (
        " Merkmal über gleiche Vorhabenkennung aus anderer Gruppe übernommen (Legacyverhalten)."
        if foreign
        else ""
    )


def leave_one_out_rate(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Historical deduction rate of the other cases of the group (leave-one-out)."""
    amounts = present_amounts(table, p, "amount_field")
    per_case, per_group = _case_and_group_sums(table, p, amounts, _deductions(table, p))
    triggered = _triggered_cases(per_case, per_group, p)
    same_group = p.get("propagation", "case_any_group") == "same_group"
    out = Outcome.constant(len(table), False)
    for i in range(len(table)):
        case = table.value(i, p["case_field"])
        if is_missing(case) or case not in triggered:
            continue
        hits = triggered[case]
        own = table.value(i, p["group_field"])
        if same_group:
            hits = [h for h in hits if not is_missing(own) and h["group"] == own]
            if not hits:
                continue
        foreign = all(is_missing(own) or h["group"] != own for h in hits)
        out.flags[i] = True
        out.reasons[i] = _leave_one_out_reason(hits, p["rate_gt"], foreign)
        out.evidence[i] = {
            "case": case,
            "own_group": own,
            "triggering": hits,
            "matched_by_case_only": foreign,
        }
    return out


# --------------------------------------------------------------------------- top share


def _nanmax(values: Sequence[float]) -> float:
    present = [v for v in values if not math.isnan(v)]
    return max(present) if present else math.nan


def top_share(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Dataset finding: share of the largest group in the total amount."""
    name, group_f = p["amount_field"], p["group_field"]
    numbers = [coerce_number(table.value(i, name), name) for i in range(len(table))]
    present = [v for v in numbers if v is not None]
    total = correct_sum(present)
    out = Outcome.constant(len(table), None)
    if not total > 0:
        out.dataset = {"triggered": False, "value": None, "reason": "Gesamtsumme nicht positiv."}
        return out
    sums: dict[Hashable, list[float]] = {}
    for i, v in enumerate(numbers):
        raw = table.value(i, group_f)
        key = MISSING_KEY if is_missing(raw) else hashable(raw, group_f)
        sums.setdefault(key, [])
        if v is not None:
            sums[key].append(v)
    by_group = {k: correct_sum(v) for k, v in sums.items()}
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
            "group": None if leader is MISSING_KEY else leader,
            "group_sum": top,
            "total": total,
        },
    }
    return out
