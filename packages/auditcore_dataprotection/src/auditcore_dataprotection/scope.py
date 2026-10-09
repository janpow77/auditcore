"""Scope of an activity: personal data in test operation and duplicate hints.

Synthetic subject-matter data do not exclude user accounts, access logs or
support cases (T-20); pseudonymised copies of real cases stay personal data
(T-19). An application may support several activities and one activity may
use several applications (``anwendungs_ids``); the same activity is recorded
once, not once per installation (T-03).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

PERSONAL_TEST_DATA = ("pseudonymisiert", "echt")
_ACCOUNT_FIELDS = ("protokollierung", "rechte_matrix", "zugriffsschutz", "betrieb")


def _filled(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def personal_data_findings(activity: Mapping[str, object]) -> tuple[str, ...]:
    """Contradictions between "no personal data" and what the activity describes."""
    findings: list[str] = []
    test_data = activity.get("testdaten")
    if test_data in PERSONAL_TEST_DATA:
        findings.append(
            f"Testdaten „{test_data}“ sind personenbezogen; sie gelten weder als anonym "
            "noch als personenbezugsfrei."
        )
    if activity.get("personenbezug") is False:
        described = [f for f in _ACCOUNT_FIELDS if _filled(activity.get(f))]
        if described or test_data in PERSONAL_TEST_DATA:
            findings.append(
                "„Kein Personenbezug“ widerspricht den Angaben zu Konten, Protokollen oder "
                f"Testdaten ({', '.join(described) or 'testdaten'}); Beschäftigtenkennungen "
                "in Zugriffsprotokollen sind personenbezogen."
            )
    return tuple(findings)


def application_ids(activity: Mapping[str, object]) -> tuple[str, ...]:
    """Applications that support the activity."""
    raw = activity.get("anwendungs_ids")
    return tuple(str(a) for a in raw) if isinstance(raw, list) else ()


def activities_of_application(
    activities: Sequence[Mapping[str, object]], application_id: str
) -> tuple[str, ...]:
    """Activity ids an application supports (many-to-many)."""
    return tuple(str(a.get("id")) for a in activities if application_id in application_ids(a))


def duplicate_hints(activities: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    """Activities with the same name and purpose, or the same central reference."""
    seen: dict[tuple[str, str], str] = {}
    refs: dict[str, str] = {}
    hints: list[str] = []
    for activity in activities:
        ident = str(activity.get("id") or "")
        key = (
            str(activity.get("name") or "").strip().casefold(),
            str(activity.get("zweck") or "").strip().casefold(),
        )
        if key[0] and key in seen:
            hints.append(f"{ident} wiederholt Bezeichnung und Zweck von {seen[key]}.")
        seen.setdefault(key, ident)
        ref = str(activity.get("hausverzeichnis_referenz") or "").strip()
        if ref and ref in refs:
            hints.append(f"{ident} verweist auf denselben Hausverzeichniseintrag wie {refs[ref]}.")
        refs.setdefault(ref, ident)
    return tuple(hints)
