"""Fraud-check signals (``signal_score`` profiles) in the shape of the risk-flags contract.

:func:`signal_evaluation` turns the sub-check results of one or more invoices
into the ``POST /evaluate`` answer that ``<flowaudit-risk-flags>`` renders:
every blocker and warning of :func:`~auditcore_risk.score_signals` becomes a
hit, score and level the record's assessment. The values are exactly those of
``score_signals`` — this module only arranges them. A sub-check that failed
leaves its other codes undetermined; a switched-off one is not evaluated.
Contract: ``docs/ui/risk-rest.md`` (section „Betrugsprüfsignale“).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ..errors import RiskError
from ..fraud import SignalAssessment, score_signals
from ..fraud_display import (
    SignalCode,
    blocker_severity,
    check_label,
    code_label,
    code_note,
    signal_codes,
)
from ..fraud_profile import FraudProfile
from ..results import LIBRARY
from .jsontypes import JsonObject, JsonValue, json_object, json_safe
from .service import ApiError, Limits, library_error
from .signal_catalog import origin, rule_view, signal_profile

_EVALUATE_KEYS = frozenset({"profile", "records", "record_key"})
Record = Mapping[str, object]


# --------------------------------------------------------------------------- records


@dataclass
class _Record:
    """Flags, undetermined codes and hits of one invoice under construction."""

    flags: dict[str, bool | None] = field(default_factory=dict)
    undetermined: dict[str, str] = field(default_factory=dict)
    origin_check: dict[str, str] = field(default_factory=dict)


def _state(value: object) -> str:
    if value is None:
        return "off"
    if isinstance(value, Mapping) and value.get("failed"):
        return "failed"
    return "performed"


def _items(value: Mapping[str, object], key: str) -> list[object]:
    items = value.get(key)
    return list(items) if isinstance(items, list | tuple) else []


def _ted_code(flag: Mapping[str, object], rules: Mapping[str, object]) -> str:
    return f"{rules['warning_prefix']}{flag.get('flag_type', rules['unknown_type'])}"


def _dynamic(check: str, value: Mapping[str, object], rules: Mapping[str, object]) -> list[str]:
    """Codes a sub-check raises beyond its fixed codes (company indicators, TED flags)."""
    if check == "company":
        known = {*_items(rules, "blocker_indicators"), *_items(rules, "ignored_indicators")}
        return [str(i) for i in _items(value, "risk_indicators") if i not in known]
    if check == "ted":
        return [_ted_code(f, rules) for f in _items(value, "red_flags") if isinstance(f, Mapping)]
    return []


def _mark(
    profile: FraudProfile, record: Record, raised: set[str], extra: dict[str, SignalCode]
) -> _Record:
    """Flag state of every code of the performed/failed sub-checks of one record."""
    out = _Record()
    for entry in signal_codes(profile):
        state = _state(record.get(entry.check))
        if state == "off":
            continue
        out.origin_check[entry.code] = entry.check
        if state == "failed" and not entry.failure:
            out.flags[entry.code] = None
            name = _check_name(profile, entry.check)
            out.undetermined[entry.code] = f"Teilprüfung „{name}“ abgebrochen"
        else:
            out.flags[entry.code] = entry.code in raised
    derivation = profile.parameters["derivation"]
    for check in profile.parameters["order"]:
        value = record.get(check)
        if _state(value) != "performed" or not isinstance(value, Mapping):
            continue
        for code in _dynamic(check, value, derivation[check]):
            if code in raised:
                out.flags[code] = True
                out.origin_check[code] = check
                extra.setdefault(code, SignalCode(code, check, False, False))
    return out


def _ted_flag(record: Record, profile: FraudProfile, code: str) -> Mapping[str, object] | None:
    ted = record.get("ted")
    rules = profile.parameters["derivation"]["ted"]
    for flag in _items(ted, "red_flags") if isinstance(ted, Mapping) else []:
        if isinstance(flag, Mapping) and _ted_code(flag, rules) == code:
            return flag
    return None


def _severity(profile: FraudProfile, code: str, blocker: bool, record: Record) -> str | None:
    if blocker:
        return blocker_severity(profile)
    flag = _ted_flag(record, profile, code)
    severity = flag.get("severity") if flag is not None else None
    return severity.upper() if isinstance(severity, str) else None


def _evidence(
    assessment: SignalAssessment,
    check: str | None,
    record: Record,
    profile: FraudProfile,
    code: str,
) -> JsonObject:
    evidence: JsonObject = {"check": check}
    component = next((c for c in assessment.components if c["component"] == check), None)
    if component is not None:
        evidence["component"] = json_object(component)
    value = record.get(check) if check else None
    if isinstance(value, Mapping) and value.get("error_message"):
        evidence["error_message"] = json_safe(value["error_message"])
    flag = _ted_flag(record, profile, code) if check == "ted" else None
    if flag is not None:
        evidence["red_flag"] = json_object(flag)
    return evidence


def _check_name(profile: FraudProfile, check: str | None) -> str:
    if not check:
        return "unbekannt"
    return check_label(profile, check) or check


def _hits(
    profile: FraudProfile, assessment: SignalAssessment, marks: _Record, record: Record
) -> list[JsonValue]:
    hits: list[JsonValue] = []
    blockers = set(assessment.blockers)
    for code in (*assessment.blockers, *assessment.warnings):
        check = marks.origin_check.get(code)
        blocker = code in blockers
        kind = "Blocker" if blocker else "Warnung"
        hits.append(
            {
                "code": code,
                "label": code_label(profile, code, check),
                "reason": f"{kind} der Teilprüfung „{_check_name(profile, check)}“.",
                "interpretation": "indicator",
                "note": code_note(profile, code),
                "severity": _severity(profile, code, blocker, record),
                "messages": None,
                "evidence": _evidence(assessment, check, record, profile, code),
                "origin": origin(profile),
            }
        )
    return hits


def _assessment(assessment: SignalAssessment) -> JsonObject:
    return {
        "score": assessment.score,
        "raw_score": assessment.raw_score,
        "level": assessment.level,
        "blocked": bool(assessment.blockers),
        "blockers": list[JsonValue](assessment.blockers),
        "warnings": list[JsonValue](assessment.warnings),
        "checks_performed": ", ".join(assessment.checks_performed),
        "components": [json_object(c) for c in assessment.components],
    }


def _record_view(
    profile: FraudProfile,
    index: int,
    record: Record,
    record_key: str | None,
    extra: dict[str, SignalCode],
) -> JsonObject:
    assessment = score_signals(record, profile)
    raised = {*assessment.blockers, *assessment.warnings}
    marks = _mark(profile, record, raised, extra)
    for code in raised - set(marks.flags):  # not attributable to a sub-check
        marks.flags[code] = True
        extra.setdefault(code, SignalCode(code, "", False, False))
    hits = _hits(profile, assessment, marks, record)
    inputs = {c: json_safe({ch: record.get(ch)}) for c, ch in marks.origin_check.items()}
    return {
        "index": index,
        "key": json_safe(record.get(record_key)) if record_key else None,
        "flags": dict[str, JsonValue](marks.flags),
        "codes": list[JsonValue]([*assessment.blockers, *assessment.warnings]),
        "undetermined": dict[str, JsonValue](marks.undetermined),
        "values": {},
        "assessment": _assessment(assessment),
        "hits": hits,
        "inputs": dict[str, JsonValue](inputs),
    }


def _skipped(profile: FraudProfile, records: Sequence[Record]) -> dict[str, JsonValue]:
    """Codes of sub-checks switched off in every record."""
    if not records:
        return {}
    out: dict[str, JsonValue] = {}
    for entry in signal_codes(profile):
        if all(_state(r.get(entry.check)) == "off" for r in records):
            name = _check_name(profile, entry.check)
            out[entry.code] = f"Teilprüfung „{name}“ nicht durchgeführt"
    return out


def signal_evaluation(
    records: Sequence[Record], profile: FraudProfile, record_key: str | None = None
) -> JsonObject:
    """Risk-flags evaluation of sub-check results (one record per invoice).

    Each record maps sub-check names (``duplicate``, ``sanctions``, ``pep``,
    ``company``, ``ted``) to ``None``, ``{"failed": True}`` or the result
    mapping, exactly as :func:`~auditcore_risk.score_signals` expects; other
    keys (e.g. ``record_key``) are ignored by the scoring.

    Raises:
        InputError: a sub-check result violates the ``score_signals`` contract.
    """
    extra: dict[str, SignalCode] = {}
    views = [_record_view(profile, i, r, record_key, extra) for i, r in enumerate(records)]
    rules = [rule_view(profile, c) for c in signal_codes(profile)]
    rules += [rule_view(profile, c) for c in extra.values()]
    checks = [c for c in profile.parameters["order"] if any(c in r for r in records)]
    return {
        "library": LIBRARY,
        "profile": json_object(profile.reference),
        "records": list[JsonValue](views),
        "dataset": [],
        "skipped": _skipped(profile, records),
        "summary": [],
        "rules": list[JsonValue](rules),
        "columns": list[JsonValue](checks),
        "missing_columns": {},
    }


def _signal_records(body: Mapping[str, object], limits: Limits) -> list[Record]:
    records = body.get("records")
    if not isinstance(records, list) or not all(isinstance(r, Mapping) for r in records):
        raise ApiError(400, "invalid_request", "'records' muss eine Liste von Objekten sein.")
    if len(records) > limits.max_records:
        raise ApiError(
            413,
            "too_many_records",
            f"Höchstens {limits.max_records} Datensätze je Anfrage ({len(records)} erhalten).",
        )
    return list(records)


def handle_signal_evaluate(body: object, limits: Limits | None = None) -> JsonObject:
    """``POST /fraud-signals/evaluate``: sub-check results of invoices as risk flags."""
    if not isinstance(body, Mapping):
        raise ApiError(400, "invalid_request", "Erwartet wird ein JSON-Objekt.")
    unknown = sorted(str(k) for k in set(body) - _EVALUATE_KEYS)
    if unknown:
        raise ApiError(400, "invalid_request", f"Unbekannte Felder: {', '.join(unknown)}.")
    spec = body.get("profile")
    if not isinstance(spec, Mapping):
        raise ApiError(400, "invalid_request", "'profile' mit 'id' und 'version' fehlt.")
    profile = signal_profile(spec.get("id"), spec.get("version"))
    key = body.get("record_key")
    if key is not None and not isinstance(key, str):
        raise ApiError(400, "invalid_request", "'record_key' muss Text sein.")
    records = _signal_records(body, limits or Limits())
    try:
        return signal_evaluation(records, profile, key)
    except RiskError as exc:
        raise library_error(exc) from exc
