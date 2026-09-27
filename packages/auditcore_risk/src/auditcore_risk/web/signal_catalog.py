"""Descriptions of ``signal_score`` profiles in the shape of the risk-flags contract.

Rule views per signal code and the ``ProfileDetail`` of a fraud-check signal
profile, so that ``<flowaudit-risk-flags>`` can show labels, severities,
weights and sub-checks. Framework-free; see :mod:`.signals` for records.
"""

from __future__ import annotations

from collections.abc import Sequence

from ..errors import ProfileError
from ..fraud import available_fraud_profiles, load_fraud_profile
from ..fraud_display import (
    SignalCode,
    blocker_severity,
    check_label,
    code_label,
    code_note,
    signal_codes,
)
from ..fraud_profile import FraudProfile
from .jsontypes import JsonObject, JsonValue, json_object, json_safe
from .service import ApiError, handle_profile

_SOURCE_KEYS = ("repository", "path", "commit", "symbols", "decision", "derived_from", "change")


def signal_profile(profile_id: object, version: object) -> FraudProfile:
    """Explicitly named ``signal_score`` profile; anything else is a 404."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ApiError(400, "invalid_request", "Profil braucht 'id' und 'version' als Text.")
    try:
        return load_fraud_profile(profile_id, version, "signal_score")
    except ProfileError as exc:
        raise ApiError(404, "profile_not_found", str(exc)) from exc


def _parameters(profile: FraudProfile, entry: SignalCode) -> JsonObject:
    score = profile.parameters["score"]
    per = "per_blocker" if entry.blocker else "per_warning"
    out: JsonObject = {per: json_safe(score[per])}
    weight = f"{entry.check}_weight"
    if weight in score:
        out[weight] = json_safe(score[weight])
    return out


def origin(profile: FraudProfile) -> JsonObject:
    """Source repository, path and symbols of the profile (``origin`` of rules and hits)."""
    source = profile.source
    return {k: json_safe(source[k]) for k in ("repository", "path", "symbols") if k in source}


def rule_view(profile: FraudProfile, entry: SignalCode) -> JsonObject:
    """Display description of one signal code (shape of the risk ``RuleView``)."""
    return {
        "code": entry.code,
        "label": code_label(profile, entry.code, entry.check),
        "kind": "signal_score",
        "scope": "record",
        "severity": blocker_severity(profile) if entry.blocker else None,
        "interpretation": "indicator",
        "note": code_note(profile, entry.code),
        "requires": [entry.check],
        "when_missing_columns": "skip",
        "column": None,
        "points": None,
        "inputs": [entry.check],
        "parameters": _parameters(profile, entry),
        "params": {},
        "origin": origin(profile),
    }


def _field(profile: FraudProfile, check: str, codes: Sequence[SignalCode]) -> JsonObject:
    label = check_label(profile, check)
    uses: list[JsonValue] = [
        {
            "code": c.code,
            "label": code_label(profile, c.code, c.check),
            "role": "Teilprüfung",
            "absent": "nicht bewertet (Teilprüfung abgeschaltet)",
            "empty": "nicht bewertet (Teilprüfung abgeschaltet)",
        }
        for c in codes
        if c.check == check
    ]
    return {
        "name": check,
        "meaning": label,
        "meaning_source": None if label is None else "parameters.display.checks",
        "requirement": "optional",
        "required_by": [],
        "value_required_by": [],
        "uses": uses,
    }


def _summary(profile: FraudProfile) -> JsonObject:
    return {
        **json_object(profile.reference),
        "kind": profile.kind,
        "legal_status": profile.legal_status,
        "rule_count": len(signal_codes(profile)),
        "field_count": len(profile.parameters["order"]),
        "open_decision_count": len(profile.open_decisions),
    }


def signal_profile_detail(profile: FraudProfile) -> JsonObject:
    """``GET /profiles/{id}/{version}`` of a ``signal_score`` profile (``ProfileDetail``)."""
    codes = signal_codes(profile)
    source = {k: profile.source[k] for k in _SOURCE_KEYS if k in profile.source}
    return {
        **_summary(profile),
        "source": json_object(source),
        "input_contract": None,
        "open_decisions": list[JsonValue](profile.open_decisions),
        "output": {},
        "summary_format": None,
        "assessment": "signal_score",
        "rules": [rule_view(profile, c) for c in codes],
        "fields": [_field(profile, check, codes) for check in profile.parameters["order"]],
    }


def handle_profile_or_signals(profile_id: str, version: str) -> JsonObject:
    """``GET /profiles/{id}/{version}``: rule profile, else ``signal_score`` profile."""
    try:
        return handle_profile(profile_id, version)
    except ApiError as exc:
        if exc.status != 404:
            raise
        try:
            profile = load_fraud_profile(profile_id, version, "signal_score")
        except ProfileError:
            raise exc from None
        return signal_profile_detail(profile)


def handle_signal_profiles() -> JsonObject:
    """``GET /fraud-profiles``: every packaged ``signal_score`` profile."""
    profiles: list[JsonValue] = []
    for profile_id, version in available_fraud_profiles():
        profile = load_fraud_profile(profile_id, version)
        if profile.kind == "signal_score":
            profiles.append(_summary(profile))
    return {"profiles": profiles}
