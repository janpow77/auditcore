"""Evaluate one explicitly selected profile over records.

``evaluate`` needs no pandas: records are mappings (``dict`` rows). Every hit
carries its code, label, reason, evidence, the rule origin in the source and
the profile identity. Different profiles are never combined into a score.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any

from .errors import InputError, ProfileError
from .profiles import RiskProfile, Rule
from .rules import KINDS, Context, Outcome, Table, _sum, identifier_state, pair_similarity
from .values import strict_amount

#: Library identity recorded in every evaluation (T-31).
LIBRARY = "auditcore_risk 0.1.0"


@dataclass(frozen=True)
class FlagHit:
    """One raised flag with its justification."""

    code: str
    label: str
    reason: str
    evidence: Mapping[str, Any]
    interpretation: str
    note: str | None
    origin: Mapping[str, Any]


@dataclass(frozen=True)
class RecordResult:
    """Flags of one record in profile order (``None`` = not decidable)."""

    index: int
    flags: Mapping[str, bool | None]
    hits: tuple[FlagHit, ...]
    undetermined: Mapping[str, str]
    values: Mapping[str, Any]

    @property
    def codes(self) -> tuple[str, ...]:
        """Codes of the raised flags in profile order."""
        return tuple(hit.code for hit in self.hits)


@dataclass(frozen=True)
class DatasetFinding:
    """Result of a dataset-wide rule (for example a concentration share)."""

    code: str
    label: str
    triggered: bool
    value: float | None
    reason: str
    evidence: Mapping[str, Any]
    origin: Mapping[str, Any]


@dataclass(frozen=True)
class Evaluation:
    """Complete, profile-bound result; ``summary`` follows the profile's format."""

    profile: Mapping[str, str]
    records: tuple[RecordResult, ...]
    dataset: tuple[DatasetFinding, ...]
    skipped: Mapping[str, str]
    summary: tuple[Mapping[str, Any], ...]
    library: str = LIBRARY

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible view (evidence values are plain data)."""
        return {
            "library": self.library,
            "profile": dict(self.profile),
            "records": [
                {
                    "index": r.index,
                    "flags": dict(r.flags),
                    "codes": list(r.codes),
                    "undetermined": dict(r.undetermined),
                    "values": dict(r.values),
                    "hits": [
                        {
                            "code": h.code,
                            "label": h.label,
                            "reason": h.reason,
                            "interpretation": h.interpretation,
                            "note": h.note,
                            "evidence": _plain(h.evidence),
                            "origin": _plain(h.origin),
                        }
                        for h in r.hits
                    ],
                }
                for r in self.records
            ],
            "dataset": [
                {
                    "code": d.code,
                    "label": d.label,
                    "triggered": d.triggered,
                    "value": d.value,
                    "reason": d.reason,
                    "evidence": _plain(d.evidence),
                }
                for d in self.dataset
            ],
            "skipped": dict(self.skipped),
            "summary": [dict(s) for s in self.summary],
        }


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    return value


def _columns(rows: Sequence[Mapping[str, Any]], columns: Iterable[str] | None) -> tuple[str, ...]:
    if columns is not None:
        found = tuple(columns)
    else:
        seen: dict[str, None] = {}
        for row in rows:
            for key in row:
                seen.setdefault(key, None)
        found = tuple(seen)
    if not all(isinstance(c, str) for c in found):
        raise InputError("Spaltennamen müssen Text sein.")
    return found


def _run(rule: Rule, table: Table, ctx: Context) -> tuple[Outcome | None, str | None]:
    missing = [c for c in rule.requires if not table.has(c)]
    if missing:
        if rule.when_missing_columns == "error":
            raise InputError(f"Regel {rule.code}: Spalten fehlen {missing}.")
        if rule.when_missing_columns == "skip":
            return None, f"Spalten fehlen: {', '.join(missing)}"
        return Outcome.constant(len(table), False), None
    return KINDS[rule.kind].run(rule.params, table, ctx), None


def evaluate(
    records: Iterable[Mapping[str, Any]],
    profile: RiskProfile,
    *,
    columns: Iterable[str] | None = None,
    reference_date: date | None = None,
) -> Evaluation:
    """Evaluate ``profile`` over ``records``.

    Args:
        records: one mapping per record; a key missing in one record is a
            missing value (like a ``NaN`` cell).
        profile: an explicitly loaded :class:`RiskProfile`.
        columns: the column set; defaults to the union of the record keys.
            Column presence matters for rules with defensive behavior.
        reference_date: key date for profiles whose year-bound thresholds use
            ``date_source = reference_date``.
    """
    if not isinstance(profile, RiskProfile):
        raise ProfileError("Ein ausdrücklich geladenes Regelprofil ist erforderlich.")
    rows = list(records)
    if not all(isinstance(r, Mapping) for r in rows):
        raise InputError("Jeder Datensatz muss eine Zuordnung Spalte → Wert sein.")
    table = Table(rows, _columns(rows, columns))
    ctx = Context(reference_date=reference_date)
    n = len(table)
    outcomes: dict[str, Outcome] = {}
    skipped: dict[str, str] = {}
    dataset: list[DatasetFinding] = []
    for rule in profile.rules:
        outcome, reason = _run(rule, table, ctx)
        if outcome is None:
            skipped[rule.code] = str(reason)
            continue
        outcomes[rule.code] = outcome
        if rule.scope == "dataset" and outcome.dataset is not None:
            d = outcome.dataset
            dataset.append(
                DatasetFinding(
                    code=rule.code,
                    label=rule.label,
                    triggered=bool(d["triggered"]),
                    value=d.get("value"),
                    reason=str(d["reason"]),
                    evidence=MappingProxyType(dict(d.get("evidence", {}))),
                    origin=rule.origin,
                )
            )
    record_rules = [r for r in profile.rules if r.scope == "record" and r.code in outcomes]
    results = []
    for i in range(n):
        flags: dict[str, bool | None] = {}
        hits = []
        undetermined: dict[str, str] = {}
        values: dict[str, Any] = {}
        for rule in record_rules:
            outcome = outcomes[rule.code]
            flag = outcome.flags[i]
            flags[rule.code] = flag
            for name, series in outcome.values.items():
                values[name] = series[i]
            if flag is None:
                undetermined[rule.code] = outcome.reasons[i] or "nicht entscheidbar"
            elif flag:
                hits.append(
                    FlagHit(
                        code=rule.code,
                        label=rule.label,
                        reason=outcome.reasons[i] or rule.label,
                        evidence=MappingProxyType(dict(outcome.evidence[i] or {})),
                        interpretation=rule.interpretation,
                        note=rule.note,
                        origin=rule.origin,
                    )
                )
        results.append(
            RecordResult(
                i,
                MappingProxyType(flags),
                tuple(hits),
                MappingProxyType(undetermined),
                MappingProxyType(values),
            )
        )
    summary = _summary(profile, table, record_rules, outcomes, dataset)
    return Evaluation(
        profile=MappingProxyType(profile.reference),
        records=tuple(results),
        dataset=tuple(dataset),
        skipped=MappingProxyType(skipped),
        summary=tuple(MappingProxyType(s) for s in summary),
    )


def _summary(
    profile: RiskProfile,
    table: Table,
    record_rules: list[Rule],
    outcomes: Mapping[str, Outcome],
    dataset: list[DatasetFinding],
) -> list[dict[str, Any]]:
    spec = profile.summary
    n = len(table)
    out: list[dict[str, Any]] = []
    if spec["format"] == "riskanalysis.red_flag_summary":
        name = spec["amount_field"]
        amounts = [
            strict_amount(table.value(i, name), name, None) if table.has(name) else None
            for i in range(n)
        ]
        for rule in record_rules:
            flags = outcomes[rule.code].flags
            hits = sum(1 for f in flags if f)
            volume = _sum([a for a, f in zip(amounts, flags, strict=True) if f and a is not None])
            entry: dict[str, Any] = {
                "code": rule.code,
                "bezeichnung": rule.label,
                "treffer": hits,
                "basis": n,
                "anteil_prozent": round(hits / n * 100, 2) if n else 0.0,
                "volumen": round(volume, 2),
            }
            undecided = sum(1 for f in flags if f is None)
            if undecided:
                entry["unbestimmt"] = undecided
            out.append(entry)
        return out
    by_code = {d.code: d for d in dataset}
    for rule in profile.rules:
        if rule.scope == "dataset":
            finding = by_code.get(rule.code)
            if finding is not None and finding.triggered:
                value = finding.value
                share = None if value is None or math.isnan(value) or math.isinf(value) else value
                out.append({"code": rule.code, "share": share})
            continue
        if rule.code not in outcomes:
            continue
        outcome = outcomes[rule.code]
        if outcome.matches is not None:
            count = sum(outcome.matches)
        else:
            count = sum(1 for f in outcome.flags if f)
        if count:
            out.append({"code": rule.code, "count": count})
    return out


def name_similarity(rule: Rule, left: Any, right: Any) -> float:
    """Similarity of one name pair under a ``name_similarity`` rule (for example RF09).

    Returns the same value the rule records per record (``name_match``); the
    decision threshold stays in the rule.
    """
    if rule.kind != "name_similarity":
        raise ProfileError(f"Regel {rule.code} ist kein Namensabgleich.")
    return pair_similarity(rule.params, left, right, Context())[0]


def identifier_missing(rule: Rule, value: Any) -> bool:
    """Whether ``value`` counts as a missing procurement identifier under ``rule``."""
    if rule.kind != "missing_procurement":
        raise ProfileError(f"Regel {rule.code} prüft keine Vergabekennung.")
    return bool(identifier_state(rule.params, value))


def missing_columns(profile: RiskProfile, columns: Iterable[str]) -> dict[str, list[str]]:
    """Per rule, required columns absent from ``columns`` (planning aid for consumers)."""
    present = set(columns)
    return {
        r.code: [c for c in r.requires if c not in present]
        for r in profile.rules
        if any(c not in present for c in r.requires)
    }


__all__ = [
    "DatasetFinding",
    "Evaluation",
    "FlagHit",
    "RecordResult",
    "evaluate",
    "identifier_missing",
    "missing_columns",
    "name_similarity",
]
