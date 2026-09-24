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

from .base import Context, Outcome, Table, _sum, seq_sum
from .errors import InputError, ProfileError
from .profiles import RiskProfile, Rule
from .rules import KINDS, identifier_state, pair_similarity
from .values import strict_amount

#: Library identity recorded in every evaluation (T-31).
LIBRARY = "auditcore_risk 0.3.0"


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
    severity: str | None = None
    messages: Mapping[str, str] | None = None


@dataclass(frozen=True)
class RecordResult:
    """Flags of one record in profile order (``None`` = not decidable)."""

    index: int
    flags: Mapping[str, bool | None]
    hits: tuple[FlagHit, ...]
    undetermined: Mapping[str, str]
    values: Mapping[str, Any]
    assessment: Mapping[str, Any] | None = None

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
                    "assessment": None if r.assessment is None else _plain(r.assessment),
                    "hits": [
                        {
                            "code": h.code,
                            "label": h.label,
                            "reason": h.reason,
                            "interpretation": h.interpretation,
                            "note": h.note,
                            "severity": h.severity,
                            "messages": None if h.messages is None else dict(h.messages),
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
    if isinstance(value, date):
        return value.isoformat()
    return value


def flatten_record(record: Mapping[str, Any], separator: str = ".") -> dict[str, Any]:
    """One level of nested mappings as ``parent.child`` fields (lists stay values).

    Example: ``{"context": {"median_amount": 5.0}}`` → ``{"context.median_amount": 5.0}``;
    a nested ``None`` keeps the parent key with ``None``.
    """
    flat: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, Mapping):
            for child, inner in value.items():
                flat[f"{key}{separator}{child}"] = inner
        else:
            flat[str(key)] = value
    return flat


def _messages(rule: Rule, variant: str | None, values: Mapping[str, Any]) -> dict[str, str] | None:
    if rule.messages is None:
        return None
    templates = rule.messages.get(variant or "default")
    if templates is None:
        raise ProfileError(f"Regel {rule.code}: keine Texte für Variante {variant!r}.")
    try:
        return {part: str(template).format(**values) for part, template in templates.items()}
    except (KeyError, ValueError, TypeError) as exc:
        raise ProfileError(f"Regel {rule.code}: Textvorlage passt nicht ({exc!r}).") from exc


def _points_assessment(
    profile: RiskProfile, flags: Mapping[str, bool | None], points: Mapping[str, float]
) -> dict[str, Any]:
    """Legacy point score of *this* profile: sum of the points of true criteria."""
    spec = profile.assessment
    if spec is None:
        raise ProfileError(f"Profil {profile.id} enthält keine Bewertung.")
    score: Any = 0
    detail = []
    for rule in profile.rules:
        if flags.get(rule.code):
            score = score + points[rule.code]
            if spec["detail_template"] is not None and points[rule.code] > 0:
                detail.append(
                    str(spec["detail_template"]).format(
                        label=rule.label, points=points[rule.code], code=rule.code
                    )
                )
    if spec["cap"] is not None:
        score = min(score, spec["cap"])
    stage = next((s["stage"] for s in spec["stages"] if score >= s["min"]), spec["default_stage"])
    return {
        "score": score,
        "stage": stage,
        "criteria": {code: bool(value) for code, value in flags.items()},
        "detail": detail,
        "points": dict(points),
        "source_version": spec["source_version"],
        "kind": spec["kind"],
    }


def _assessment(profile: RiskProfile, hits: list[FlagHit]) -> dict[str, Any]:
    """Legacy score of *this* profile: sum of severity weights in rule order."""
    spec = profile.assessment
    if spec is None:
        raise ProfileError(f"Profil {profile.id} enthält keine Bewertung.")
    weights = spec["weights"]
    total = seq_sum(float(weights.get(h.severity, spec["fallback_weight"])) for h in hits)
    score = min(total / float(spec["divisor"]), float(spec["cap"])) if hits else 0.0
    highest = next(
        (level for level in spec["severity_order"] if any(h.severity == level for h in hits)),
        None,
    )
    text = spec["summary"]
    if not hits:
        summary = str(text["none"])
    else:
        word = (
            text["level_words"].get(highest, text["unknown_level"])
            if highest
            else text["unknown_level"]
        )
        key = "one" if len(hits) == 1 else "many"
        summary = str(text[key]).format(count=len(hits), level=word)
    return {
        "score": score,
        "highest_severity": highest,
        "summary": summary,
        "findings": [
            {"code": h.code, "severity": h.severity, **(dict(h.messages) if h.messages else {})}
            for h in hits
        ],
        "source_version": spec["source_version"],
        "kind": spec["kind"],
    }


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
        if rule.when_missing_columns == "undetermined":
            # Nur die Betragsspalte darf fehlen (beim Laden geprüft); die Regelart
            # weist jeden Datensatz, den der Betrag entscheiden würde, als unbestimmt aus.
            return KINDS[rule.kind].run(rule.params, table, ctx), None
        return Outcome.constant(len(table), False), None
    return KINDS[rule.kind].run(rule.params, table, ctx), None


def evaluate(
    records: Iterable[Mapping[str, Any]],
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
    used_points = _points_for(profile, points)
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
                evidence = dict(outcome.evidence[i] or {})
                variant = outcome.variants[i] if outcome.variants is not None else None
                severity = (
                    outcome.severities[i]
                    if outcome.severities is not None and outcome.severities[i] is not None
                    else rule.severity
                )
                echo = {
                    alias: table.value(i, field)
                    for alias, field in (rule.echo_fields or {}).items()
                }
                hits.append(
                    FlagHit(
                        code=rule.code,
                        label=rule.label,
                        reason=outcome.reasons[i] or rule.label,
                        evidence=MappingProxyType(evidence),
                        interpretation=rule.interpretation,
                        note=rule.note,
                        origin=rule.origin,
                        severity=severity,
                        messages=_messages(rule, variant, {**evidence, **echo}),
                    )
                )
        if profile.assessment is None:
            assessment = None
        elif profile.assessment["kind"] == "points_stages":
            assessment = MappingProxyType(_points_assessment(profile, flags, used_points))
        else:
            assessment = MappingProxyType(_assessment(profile, hits))
        results.append(
            RecordResult(
                i,
                MappingProxyType(flags),
                tuple(hits),
                MappingProxyType(undetermined),
                MappingProxyType(values),
                assessment,
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


def _points_for(profile: RiskProfile, override: Mapping[str, float] | None) -> dict[str, float]:
    spec = profile.assessment
    if spec is None or spec["kind"] != "points_stages":
        if override is not None:
            raise ProfileError(f"Profil {profile.id} vergibt keine Punkte.")
        return {}
    if override is None:
        return {r.code: r.points if r.points is not None else 0 for r in profile.rules}
    if spec["points_override"] != "allowed":
        raise ProfileError(f"Profil {profile.id} erlaubt keine übergebenen Punkte.")
    codes = {r.code for r in profile.rules}
    if set(override) != codes:
        raise ProfileError(f"Punkte für genau {sorted(codes)} sind anzugeben.")
    for value in override.values():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ProfileError("Punkte müssen Zahlen sein.")
    return dict(override)


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
    if spec["format"] == "none":
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
    "flatten_record",
    "identifier_missing",
    "missing_columns",
    "name_similarity",
]
