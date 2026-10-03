"""Column-wise evaluation of one profile without building records.

``evaluate_columns`` takes the columns of a table (lists, one-dimensional
ndarrays or pandas/polars series) instead of one mapping per record. The rule
kinds in :mod:`.column_kinds` decide all records at once; every other kind,
and every parameter combination those functions do not cover, runs the
record-wise kind over the same columns. Flags, hit counts, dataset findings
and the overview are the same as :func:`auditcore_risk.evaluate` returns for
the same table; per-hit reasons and evidence are not produced (evaluate the
hit rows with :func:`auditcore_risk.evaluate` when they are needed).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType

import numpy as np
from auditcore_compute import engine_report

from .base import Context, Outcome
from .column_kinds import VECTOR_KINDS, VectorOutcome
from .column_values import Bools, ColumnData, ColumnTable, Floats, Ints
from .engine import dataset_finding, run_rule
from .errors import ProfileError
from .profiles import RiskProfile, Rule
from .results import LIBRARY, DatasetFinding
from .summary import summarize

#: Evaluation path of a rule: vectorised over columns or record kind over the columns.
VECTORISED = "vectorised"
RECORDS = "records"


@dataclass(frozen=True)
class ColumnEvaluation:
    """Flags per rule as arrays, dataset findings and the overview of one profile."""

    profile: Mapping[str, str]
    size: int
    flags: Mapping[str, Bools]
    undetermined: Mapping[str, Bools]
    matches: Mapping[str, Ints]
    values: Mapping[str, Floats]
    dataset: tuple[DatasetFinding, ...]
    skipped: Mapping[str, str]
    summary: tuple[Mapping[str, object], ...]
    paths: Mapping[str, str]
    engine: tuple[Mapping[str, object], ...] = ()
    library: str = LIBRARY

    def hits(self, code: str) -> Ints:
        """Positions of the records the rule ``code`` flags."""
        found: Ints = np.flatnonzero(self.flags[code]).astype(np.int64)
        return found

    def record_flags(self, code: str) -> list[bool | None]:
        """Flags of ``code`` as in ``RecordResult.flags`` (``None`` = undetermined)."""
        flags, undetermined = self.flags[code], self.undetermined[code]
        return [None if u else bool(f) for f, u in zip(flags, undetermined, strict=True)]


def _from_outcome(outcome: Outcome) -> VectorOutcome:
    flags = np.array([f is True for f in outcome.flags], dtype=np.bool_)
    undetermined = np.array([f is None for f in outcome.flags], dtype=np.bool_)
    matches = None if outcome.matches is None else np.array(outcome.matches, dtype=np.int64)
    values = {k: np.array(v, dtype=np.float64) for k, v in outcome.values.items()}
    return VectorOutcome(flags, undetermined, matches, values, outcome.dataset)


def _apply(
    rule: Rule, data: ColumnData, table: ColumnTable, ctx: Context
) -> tuple[VectorOutcome | None, str]:
    """Vectorised outcome where possible, else the record kind; path or skip reason."""
    vector = VECTOR_KINDS.get(rule.kind)
    if vector is not None and data.has(*rule.requires):
        result = vector(rule.params, data, ctx)
        if result is not None:
            return result, VECTORISED
    outcome, reason = run_rule(rule, table, ctx)
    if outcome is None:
        return None, str(reason)
    return _from_outcome(outcome), RECORDS


def _count_outcome(result: VectorOutcome) -> Outcome:
    """Outcome carrying only the hit count (all ``flowstat.counts`` reads)."""
    hits = result.matches if result.matches is not None else result.flags
    return Outcome([], [], [], [int(hits.sum())])


def _summary_outcome(result: VectorOutcome) -> Outcome:
    """Record outcome with the flags and counts ``summarize`` reads."""
    pairs = zip(result.flags.tolist(), result.undetermined.tolist(), strict=True)
    flags: list[bool | None] = [None if undetermined else flag for flag, undetermined in pairs]
    size = len(flags)
    matches = None if result.matches is None else result.matches.tolist()
    return Outcome(flags, [None] * size, [None] * size, matches)


@dataclass
class _Collected:
    results: dict[str, VectorOutcome] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)
    dataset: list[DatasetFinding] = field(default_factory=list)


def _collect(profile: RiskProfile, data: ColumnData, ctx: Context) -> _Collected:
    collected = _Collected()
    table = ColumnTable(data)
    for rule in profile.rules:
        result, path = _apply(rule, data, table, ctx)
        if result is None:
            collected.skipped[rule.code] = path
            continue
        collected.results[rule.code] = result
        collected.paths[rule.code] = path
        finding = dataset_finding(rule, result.dataset)
        if finding is not None:
            collected.dataset.append(finding)
    return collected


def evaluate_columns(
    columns: Mapping[str, object], profile: RiskProfile, *, reference_date: date | None = None
) -> ColumnEvaluation:
    """Evaluate ``profile`` over named columns of equal length.

    Args:
        columns: column name → list, one-dimensional ndarray or pandas/polars
            series; the keys are the column set (presence matters as in
            :func:`auditcore_risk.evaluate`).
        profile: an explicitly loaded :class:`RiskProfile` without a
            per-record assessment.
        reference_date: key date for year-bound thresholds.

    Raises:
        ProfileError: no profile, or a profile with a per-record assessment
            (use :func:`auditcore_risk.evaluate`).
        InputError: columns of different length or invalid values.
    """
    if not isinstance(profile, RiskProfile):
        raise ProfileError("Ein ausdrücklich geladenes Regelprofil ist erforderlich.")
    if profile.assessment is not None:
        raise ProfileError(
            "Profile mit Bewertung je Datensatz werden nur über evaluate() ausgewertet."
        )
    data = ColumnData(columns)
    collected = _collect(profile, data, Context(reference_date=reference_date))
    record = [r for r in profile.rules if r.scope == "record" and r.code in collected.results]
    lean = profile.summary["format"] == "flowstat.counts"
    build = _count_outcome if lean else _summary_outcome
    outcomes = {r.code: build(collected.results[r.code]) for r in record}
    summary = summarize(profile, ColumnTable(data), record, outcomes, collected.dataset)
    results = {r.code: collected.results[r.code] for r in record}
    return ColumnEvaluation(
        profile=MappingProxyType(profile.reference),
        size=data.size,
        flags=MappingProxyType({c: v.flags for c, v in results.items()}),
        undetermined=MappingProxyType({c: v.undetermined for c, v in results.items()}),
        matches=MappingProxyType(
            {c: v.matches for c, v in results.items() if v.matches is not None}
        ),
        values=MappingProxyType({k: a for v in results.values() for k, a in v.values.items()}),
        dataset=tuple(collected.dataset),
        skipped=MappingProxyType(collected.skipped),
        summary=tuple(MappingProxyType(s) for s in summary),
        paths=MappingProxyType(collected.paths),
        engine=tuple(MappingProxyType(info.as_dict()) for info in engine_report()),
    )


__all__ = ["RECORDS", "VECTORISED", "ColumnEvaluation", "evaluate_columns"]
