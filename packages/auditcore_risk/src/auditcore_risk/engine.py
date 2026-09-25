"""Evaluate one explicitly selected profile over records.

``evaluate`` needs no pandas: records are mappings (``dict`` rows). Every hit
carries its code, label, reason, evidence, the rule origin in the source and
the profile identity. Different profiles are never combined into a score.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from types import MappingProxyType

from .assessment import points_for, record_assessment, render_messages
from .base import Context, Outcome, Table
from .errors import InputError, ProfileError
from .profiles import RiskProfile, Rule
from .results import LIBRARY, DatasetFinding, Evaluation, FlagHit, RecordResult
from .rules import KINDS, identifier_state, pair_similarity
from .summary import summarize


def flatten_record(record: Mapping[str, object], separator: str = ".") -> dict[str, object]:
    """One level of nested mappings as ``parent.child`` fields (lists stay values).

    Example: ``{"context": {"median_amount": 5.0}}`` → ``{"context.median_amount": 5.0}``;
    a nested ``None`` keeps the parent key with ``None``.
    """
    flat: dict[str, object] = {}
    for key, value in record.items():
        if isinstance(value, Mapping):
            for child, inner in value.items():
                flat[f"{key}{separator}{child}"] = inner
        else:
            flat[str(key)] = value
    return flat


def _columns(
    rows: Sequence[Mapping[str, object]], columns: Iterable[str] | None
) -> tuple[str, ...]:
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
        if rule.when_missing_columns == "undetermined":
            # Nur die Betragsspalte darf fehlen (beim Laden geprüft); die Regelart
            # weist jeden Datensatz, den der Betrag entscheiden würde, als unbestimmt aus.
            return KINDS[rule.kind].run(rule.params, table, ctx), None
        return Outcome.constant(len(table), False), None
    return KINDS[rule.kind].run(rule.params, table, ctx), None


def _dataset_finding(rule: Rule, outcome: Outcome) -> DatasetFinding | None:
    """Finding of a dataset-wide rule (``None`` for record rules)."""
    if rule.scope != "dataset" or outcome.dataset is None:
        return None
    d = outcome.dataset
    return DatasetFinding(
        code=rule.code,
        label=rule.label,
        triggered=bool(d["triggered"]),
        value=d.get("value"),
        reason=str(d["reason"]),
        evidence=MappingProxyType(dict(d.get("evidence", {}))),
        origin=rule.origin,
    )


def _run_rules(
    profile: RiskProfile, table: Table, ctx: Context
) -> tuple[dict[str, Outcome], dict[str, str], list[DatasetFinding]]:
    """Outcome per applied rule, skipped rules with reason, dataset findings."""
    outcomes: dict[str, Outcome] = {}
    skipped: dict[str, str] = {}
    dataset: list[DatasetFinding] = []
    for rule in profile.rules:
        outcome, reason = _run(rule, table, ctx)
        if outcome is None:
            skipped[rule.code] = str(reason)
            continue
        outcomes[rule.code] = outcome
        finding = _dataset_finding(rule, outcome)
        if finding is not None:
            dataset.append(finding)
    return outcomes, skipped, dataset


def _flag_hit(rule: Rule, outcome: Outcome, table: Table, index: int) -> FlagHit:
    evidence = dict(outcome.evidence[index] or {})
    variant = outcome.variants[index] if outcome.variants is not None else None
    severity = (
        outcome.severities[index]
        if outcome.severities is not None and outcome.severities[index] is not None
        else rule.severity
    )
    echo = {alias: table.value(index, field) for alias, field in (rule.echo_fields or {}).items()}
    return FlagHit(
        code=rule.code,
        label=rule.label,
        reason=outcome.reasons[index] or rule.label,
        evidence=MappingProxyType(evidence),
        interpretation=rule.interpretation,
        note=rule.note,
        origin=rule.origin,
        severity=severity,
        messages=render_messages(rule, variant, {**evidence, **echo}),
    )


def _record_result(
    profile: RiskProfile,
    table: Table,
    index: int,
    record_rules: Sequence[Rule],
    outcomes: Mapping[str, Outcome],
    points: Mapping[str, float],
) -> RecordResult:
    flags: dict[str, bool | None] = {}
    hits: list[FlagHit] = []
    undetermined: dict[str, str] = {}
    values: dict[str, object] = {}
    for rule in record_rules:
        outcome = outcomes[rule.code]
        flag = outcome.flags[index]
        flags[rule.code] = flag
        for name, series in outcome.values.items():
            values[name] = series[index]
        if flag is None:
            undetermined[rule.code] = outcome.reasons[index] or "nicht entscheidbar"
        elif flag:
            hits.append(_flag_hit(rule, outcome, table, index))
    assessment = record_assessment(profile, flags, hits, points)
    return RecordResult(
        index,
        MappingProxyType(flags),
        tuple(hits),
        MappingProxyType(undetermined),
        MappingProxyType(values),
        None if assessment is None else MappingProxyType(assessment),
    )


def evaluate(
    records: Iterable[Mapping[str, object]],
    profile: RiskProfile,
    *,
    columns: Iterable[str] | None = None,
    reference_date: date | None = None,
    points: Mapping[str, float] | None = None,
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
        points: criterion points supplied by the consumer (e.g. calibrated
            weights); only for profiles whose assessment allows it, all codes
            required. The profile's own points are used otherwise.
    """
    if not isinstance(profile, RiskProfile):
        raise ProfileError("Ein ausdrücklich geladenes Regelprofil ist erforderlich.")
    rows = list(records)
    if not all(isinstance(r, Mapping) for r in rows):
        raise InputError("Jeder Datensatz muss eine Zuordnung Spalte → Wert sein.")
    table = Table(rows, _columns(rows, columns))
    ctx = Context(reference_date=reference_date)
    used_points = points_for(profile, points)
    outcomes, skipped, dataset = _run_rules(profile, table, ctx)
    record_rules = [r for r in profile.rules if r.scope == "record" and r.code in outcomes]
    results = [
        _record_result(profile, table, i, record_rules, outcomes, used_points)
        for i in range(len(table))
    ]
    summary = summarize(profile, table, record_rules, outcomes, dataset)
    return Evaluation(
        profile=MappingProxyType(profile.reference),
        records=tuple(results),
        dataset=tuple(dataset),
        skipped=MappingProxyType(skipped),
        summary=tuple(MappingProxyType(s) for s in summary),
    )


def name_similarity(rule: Rule, left: object, right: object) -> float:
    """Similarity of one name pair under a ``name_similarity`` rule (for example RF09).

    Returns the same value the rule records per record (``name_match``); the
    decision threshold stays in the rule.
    """
    if rule.kind != "name_similarity":
        raise ProfileError(f"Regel {rule.code} ist kein Namensabgleich.")
    return pair_similarity(rule.params, left, right, Context())[0]


def identifier_missing(rule: Rule, value: object) -> bool:
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
    "LIBRARY",
    "DatasetFinding",
    "Evaluation",
    "FlagHit",
    "RecordResult",
    "evaluate",
    "flatten_record",
    "identifier_missing",
    "missing_columns",
    "name_similarity",
]
