"""``signal_score``: blockers, warnings, score and level from the sub-check results.

Sanctions, PEP and company results are *consumed* as plain mappings (port
contract); the screening itself belongs to the registry/screening libraries.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .base import JsonObject
from .errors import InputError, ProfileError
from .fraud_profile import FraudProfile, as_number, require_parameters

KNOWN_CHECKS = frozenset({"duplicate", "sanctions", "pep", "company", "ted"})


@dataclass(frozen=True)
class SignalAssessment:
    """Blockers, warnings, score components, score and level of one invoice."""

    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    checks_performed: tuple[str, ...]
    components: tuple[JsonObject, ...]
    raw_score: float
    score: float
    level: str
    profile: Mapping[str, str]


@dataclass
class _Derivation:
    """Blockers and warnings in derivation order, performed checks and their results."""

    blockers: list[str]
    warnings: list[str]
    performed: list[str]
    results: dict[str, JsonObject]


# --------------------------------------------------------------------------- derivation


def _derive_duplicate(value: JsonObject, rules: JsonObject, d: _Derivation) -> None:
    if value["is_duplicate"]:
        if any(m["match_type"] == "exact" for m in value["matches"]):
            d.blockers.append(rules["exact_blocker"])
        else:
            d.warnings.append(rules["fuzzy_warning"])


def _derive_sanctions(value: JsonObject, rules: JsonObject, d: _Derivation) -> None:
    if value["is_sanctioned"]:
        d.blockers.append(rules["hit_blocker"])
    elif value.get("error_message"):
        d.warnings.append(rules["error_warning"])


def _derive_pep(value: JsonObject, rules: JsonObject, d: _Derivation) -> None:
    if not value["is_clean"]:
        d.warnings.append(rules["hit_warning"])
    elif value.get("error_message"):
        d.warnings.append(rules["error_warning"])


def _derive_company(value: JsonObject, rules: JsonObject, d: _Derivation) -> None:
    for indicator in value["risk_indicators"]:
        if indicator in rules["blocker_indicators"]:
            d.blockers.append(indicator)
        elif indicator not in rules["ignored_indicators"]:
            d.warnings.append(indicator)


def _derive_ted(value: JsonObject, rules: JsonObject, d: _Derivation) -> None:
    for flag in value.get("red_flags", []):
        if flag.get("severity", rules["default_severity"]) in rules["warning_severities"]:
            d.warnings.append(
                rules["warning_prefix"] + str(flag.get("flag_type", rules["unknown_type"]))
            )


_DERIVATIONS: dict[str, Callable[[JsonObject, JsonObject, _Derivation], None]] = {
    "duplicate": _derive_duplicate,
    "sanctions": _derive_sanctions,
    "pep": _derive_pep,
    "company": _derive_company,
    "ted": _derive_ted,
}


def _derive(signals: JsonObject, p: JsonObject) -> _Derivation:
    """Blockers and warnings of the checks in profile order (switched-off checks skipped)."""
    d = _Derivation([], [], [], {})
    for check in p["order"]:
        value = signals.get(check)
        if value is None:
            continue
        rules = p["derivation"][check]
        if not isinstance(value, Mapping):
            raise InputError(f"Signal {check!r} muss eine Zuordnung oder None sein.")
        if value.get("failed"):
            d.warnings.append(rules["failed_warning"])
            continue
        d.performed.append(rules["performed"])
        d.results[check] = value
        derive = _DERIVATIONS.get(check)
        if derive is not None:
            derive(value, rules, d)
    return d


# --------------------------------------------------------------------------- score components

Component = dict[str, Any]
Results = Mapping[str, JsonObject]


def _component(name: str, value: float, detail: Mapping[str, object]) -> Component:
    return {"component": name, "contribution": value, **detail}


def _top(matches: list[JsonObject], key: str, where: str) -> float:
    return max((as_number(m[key], where) for m in matches), default=0)


def _company(results: Results, w: JsonObject, policy: JsonObject) -> Component | None:
    if "company" not in results:
        return None
    verification = as_number(results["company"]["verification_score"], "company")
    return _component(
        "company", (1.0 - verification) * w["company_weight"], {"verification_score": verification}
    )


def _duplicate(results: Results, w: JsonObject, policy: JsonObject) -> Component | None:
    dup = results.get("duplicate")
    if not (dup and dup["is_duplicate"]):
        return None
    top = _top(dup["matches"], "confidence", "duplicate")
    return _component("duplicate", top * w["duplicate_weight"], {"max_confidence": top})


def _sanctions(results: Results, w: JsonObject, policy: JsonObject) -> Component | None:
    sanctions = results.get("sanctions")
    if not (sanctions and sanctions["is_sanctioned"]):
        return None
    top = _top(sanctions["matches"], "match_score", "sanctions")
    return _component("sanctions", top * w["sanctions_weight"], {"max_match_score": top})


def _pep(results: Results, w: JsonObject, policy: JsonObject) -> Component | None:
    pep = results.get("pep")
    if not (pep and not pep["is_clean"]):
        return None
    top = _top(pep["matches"], "match_score", "pep")
    return _component("pep", top * w["pep_weight"], {"max_match_score": top})


def _ted(results: Results, w: JsonObject, policy: JsonObject) -> Component | None:
    ted = results.get("ted")
    if not (ted and len(ted.get("red_flags", [])) > 0):
        return None
    legitimacy = ted.get("legitimacy_score", 1.0)
    if not isinstance(legitimacy, int | float) or isinstance(legitimacy, bool):
        raise InputError(
            "TED-Legitimität muss eine Zahl zwischen 0 und 1 sein; die Quelle liefert ein "
            "Wörterbuch (0–100) und bricht an dieser Stelle ab (siehe RK-C09)."
        )
    if policy.get("ted_legitimacy_scale") == "unit_interval" and not 0 <= legitimacy <= 1:
        raise InputError("TED-Legitimität muss im Intervall 0–1 liegen (Entscheidung K8).")
    return _component("ted", (1.0 - legitimacy) * w["ted_weight"], {"legitimacy_score": legitimacy})


#: Score components of the sub-check results in the source's order.
_CHECK_COMPONENTS = (_company, _duplicate, _sanctions, _pep, _ted)


def _components(d: _Derivation, w: JsonObject, policy: JsonObject) -> list[Component]:
    after = policy.get("warning_count", "before_dedup") == "after_dedup"
    n_blockers = len(dict.fromkeys(d.blockers)) if after else len(d.blockers)
    n_warnings = len(dict.fromkeys(d.warnings)) if after else len(d.warnings)
    components = [
        _component("blockers", n_blockers * w["per_blocker"], {"count": n_blockers}),
        _component("warnings", n_warnings * w["per_warning"], {"count": n_warnings}),
    ]
    for make in _CHECK_COMPONENTS:
        component = make(d.results, w, policy)
        if component is not None:
            components.append(component)
    return components


def _level(levels: JsonObject, blocked: bool, raw: float) -> str:
    if blocked:
        blocker: str = levels["blocker_level"]
        return blocker
    level: str = next(
        (t["level"] for t in levels["thresholds"] if raw >= t["min"]), levels["default"]
    )
    return level


def score_signals(signals: JsonObject, profile: FraudProfile) -> SignalAssessment:
    """Legacy blocker/warning derivation and score of the fraud-check manager.

    ``signals`` maps each check name to ``None`` (check switched off),
    ``{"failed": True}`` (check raised) or its result mapping, for example
    ``{"is_sanctioned": True, "error_message": None, "matches": [{"match_score": 0.9}]}``.
    Warnings keep their derivation order and are de-duplicated deterministically.
    """
    p = require_parameters(profile, "signal_score")
    d = _derive(signals, p)
    w = p["score"]
    components = _components(d, w, p.get("policy", {}))
    score = 0.0
    for component in components:
        score += component["contribution"]
    raw = min(float(w["cap"]), score)
    return SignalAssessment(
        blockers=tuple(dict.fromkeys(d.blockers)),
        warnings=tuple(dict.fromkeys(d.warnings)),
        checks_performed=tuple(d.performed),
        components=tuple(MappingProxyType(c) for c in components),
        raw_score=raw,
        score=round(raw, int(w["output_digits"])),
        level=_level(p["levels"], bool(d.blockers), raw),
        profile=MappingProxyType(profile.reference),
    )


def validate_signal(p: JsonObject) -> None:
    """Parameter contract of a ``signal_score`` profile."""
    need = {"order", "derivation", "score", "levels"}
    if not need <= set(p) or set(p) - need - {"policy"}:
        raise ProfileError(f"signal_score braucht {sorted(need)} (optional policy).")
    policy = p.get("policy", {})
    if (
        set(policy) - {"warning_count", "ted_legitimacy_scale"}
        or policy.get("warning_count", "before_dedup") not in ("before_dedup", "after_dedup")
        or policy.get("ted_legitimacy_scale", "legacy") not in ("legacy", "unit_interval")
    ):
        raise ProfileError(
            "policy: warning_count before_dedup/after_dedup, "
            "ted_legitimacy_scale legacy/unit_interval."
        )
    if sorted(p["order"]) != sorted(p["derivation"]) or len(set(p["order"])) != len(p["order"]):
        raise ProfileError("Reihenfolge und Ableitungsregeln müssen übereinstimmen.")
    if not set(p["order"]) <= KNOWN_CHECKS:
        raise ProfileError(f"Unbekannte Teilprüfung in {p['order']}.")
    for key, value in p["score"].items():
        if key != "output_digits" and not isinstance(value, int | float):
            raise ProfileError(f"Gewicht {key} muss eine Zahl sein.")
    thresholds = [t["min"] for t in p["levels"]["thresholds"]]
    if thresholds != sorted(thresholds, reverse=True):
        raise ProfileError("Stufen müssen absteigend geordnet sein.")
