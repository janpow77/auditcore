"""Overview of an evaluation in the summary format the profile names.

* ``riskanalysis.red_flag_summary`` — hits, base, share and volume per rule
  (keys of the source: ``bezeichnung``, ``treffer``, ``anteil_prozent`` …);
* ``flowstat.counts`` — triggered dataset shares and hit counts per rule;
* ``none`` — no overview.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from .base import Outcome, Table, correct_sum
from .profiles import RiskProfile, Rule
from .results import DatasetFinding
from .values import strict_amount


def red_flag_entry(rule: Rule, hits: int, base: int, volume: float) -> dict[str, object]:
    """One riskanalysis overview row (also used by the frame adapter)."""
    return {
        "code": rule.code,
        "bezeichnung": rule.label,
        "treffer": hits,
        "basis": base,
        "anteil_prozent": round(hits / base * 100, 2) if base else 0.0,
        "volumen": round(volume, 2),
    }


def _red_flag_summary(
    profile: RiskProfile,
    table: Table,
    record_rules: Sequence[Rule],
    outcomes: Mapping[str, Outcome],
) -> list[dict[str, object]]:
    n = len(table)
    name = profile.summary["amount_field"]
    amounts = [
        strict_amount(table.value(i, name), name, None) if table.has(name) else None
        for i in range(n)
    ]
    out = []
    for rule in record_rules:
        flags = outcomes[rule.code].flags
        hits = sum(1 for f in flags if f)
        volume = correct_sum(
            [a for a, f in zip(amounts, flags, strict=True) if f and a is not None]
        )
        entry = red_flag_entry(rule, hits, n, volume)
        undecided = sum(1 for f in flags if f is None)
        if undecided:
            entry["unbestimmt"] = undecided
        out.append(entry)
    return out


def _finite_or_none(value: float | None) -> float | None:
    return None if value is None or math.isnan(value) or math.isinf(value) else value


def _hit_count(outcome: Outcome) -> int:
    if outcome.matches is not None:
        return sum(outcome.matches)
    return sum(1 for f in outcome.flags if f)


def _counts_summary(
    profile: RiskProfile, outcomes: Mapping[str, Outcome], dataset: Sequence[DatasetFinding]
) -> list[dict[str, object]]:
    by_code = {d.code: d for d in dataset}
    out: list[dict[str, object]] = []
    for rule in profile.rules:
        if rule.scope == "dataset":
            finding = by_code.get(rule.code)
            if finding is not None and finding.triggered:
                out.append({"code": rule.code, "share": _finite_or_none(finding.value)})
            continue
        if rule.code not in outcomes:
            continue
        count = _hit_count(outcomes[rule.code])
        if count:
            out.append({"code": rule.code, "count": count})
    return out


def summarize(
    profile: RiskProfile,
    table: Table,
    record_rules: Sequence[Rule],
    outcomes: Mapping[str, Outcome],
    dataset: Sequence[DatasetFinding],
) -> list[dict[str, object]]:
    """Overview rows in the profile's summary format."""
    summary_format = profile.summary["format"]
    if summary_format == "riskanalysis.red_flag_summary":
        return _red_flag_summary(profile, table, record_rules, outcomes)
    if summary_format == "none":
        return []
    return _counts_summary(profile, outcomes, dataset)
