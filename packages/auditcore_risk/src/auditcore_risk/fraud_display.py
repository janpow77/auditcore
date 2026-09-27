"""Display facts of ``signal_score`` profiles: codes per sub-check, labels and severities.

The codes a profile can produce come from its derivation rules; the optional
``parameters.display`` block adds German labels per code and per sub-check
(``{"checks": {check: label}, "codes": {code: {"label": …, "note": …}}}``).
Severity is never invented: blockers carry the profile's ``blocker_level``,
TED warnings the severity of their red flag, all other warnings none.
Nothing here changes blockers, warnings, score or level of
:func:`~auditcore_risk.score_signals`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .base import JsonObject
from .errors import ProfileError
from .fraud_profile import FraudProfile, require_parameters

#: Derivation keys whose value is a fixed code, per sub-check (profile order of the source).
CODE_KEYS: Mapping[str, tuple[str, ...]] = {
    "duplicate": ("exact_blocker", "fuzzy_warning", "failed_warning"),
    "sanctions": ("hit_blocker", "error_warning", "failed_warning"),
    "pep": ("hit_warning", "error_warning", "failed_warning"),
    "company": ("failed_warning",),
    "ted": ("failed_warning",),
}
_DISPLAY_KEYS = frozenset({"checks", "codes"})
_CODE_KEYS = frozenset({"label", "note"})


@dataclass(frozen=True)
class SignalCode:
    """One code a sub-check can raise."""

    code: str
    check: str
    blocker: bool
    failure: bool


def _text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f"display: {where} muss ein nicht leerer Text sein.")
    return value


def validate_display(display: object, order: Sequence[str]) -> None:
    """Contract of the optional ``display`` block of a ``signal_score`` profile."""
    if not isinstance(display, Mapping) or set(display) - _DISPLAY_KEYS:
        raise ProfileError("display: erlaubt sind nur 'checks' und 'codes'.")
    checks = display.get("checks", {})
    if not isinstance(checks, Mapping) or not set(checks) <= set(order):
        raise ProfileError("display.checks: nur Teilprüfungen aus 'order'.")
    for check, label in checks.items():
        _text(label, f"checks.{check}")
    codes = display.get("codes", {})
    if not isinstance(codes, Mapping):
        raise ProfileError("display.codes muss Code → Angaben zuordnen.")
    for code, entry in codes.items():
        if not isinstance(entry, Mapping) or "label" not in entry or set(entry) - _CODE_KEYS:
            raise ProfileError(f"display.codes.{code}: 'label' ist Pflicht, sonst nur 'note'.")
        _text(entry["label"], f"codes.{code}.label")
        if "note" in entry:
            _text(entry["note"], f"codes.{code}.note")


def signal_codes(profile: FraudProfile) -> tuple[SignalCode, ...]:
    """Fixed codes of the profile in sub-check order (company blocker indicators included)."""
    p = require_parameters(profile, "signal_score")
    out: list[SignalCode] = []
    for check in p["order"]:
        rules = p["derivation"][check]
        for key in CODE_KEYS[check]:
            blocker, failure = key.endswith("_blocker"), key == "failed_warning"
            out.append(SignalCode(rules[key], check, blocker, failure))
        if check == "company":
            out.extend(SignalCode(code, check, True, False) for code in rules["blocker_indicators"])
    return tuple(out)


def _display(profile: FraudProfile) -> JsonObject:
    display: JsonObject = require_parameters(profile, "signal_score").get("display", {})
    return display


def check_label(profile: FraudProfile, check: str) -> str | None:
    """Label of a sub-check from ``display.checks`` (``None`` without one)."""
    label: str | None = _display(profile).get("checks", {}).get(check)
    return label


def code_label(profile: FraudProfile, code: str, check: str | None) -> str:
    """Label from ``display.codes``; else ``<sub-check label>: <code>``; else the code."""
    entry = _display(profile).get("codes", {}).get(code)
    if entry is not None:
        label: str = entry["label"]
        return label
    base = check_label(profile, check) if check else None
    return f"{base}: {code}" if base else code


def code_note(profile: FraudProfile, code: str) -> str | None:
    """Note from ``display.codes`` (``None`` without one)."""
    entry = _display(profile).get("codes", {}).get(code)
    note: str | None = None if entry is None else entry.get("note")
    return note


def blocker_severity(profile: FraudProfile) -> str:
    """Severity of every blocker: the profile's ``blocker_level`` in upper case."""
    level: str = require_parameters(profile, "signal_score")["levels"]["blocker_level"]
    return level.upper()
