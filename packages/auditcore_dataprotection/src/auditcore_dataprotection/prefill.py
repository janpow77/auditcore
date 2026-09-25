"""Suggested screening answers from register data; never stored automatically."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from auditcore_common.text import group_thousands_de as _number

from .rules import RuleProfile


@dataclass(frozen=True)
class PrefillSuggestion:
    """A suggestion only; it never becomes an answer without confirmation."""

    question: str
    value: bool
    reason: str


def _count(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _sensitive_data_suggestions(
    source: str, count: int | None, large: bool
) -> list[PrefillSuggestion]:
    """Art. 9/10 data and, with many persons, processing on a large scale."""
    found = [
        PrefillSuggestion(
            "edsa_04_sensible_daten",
            True,
            f"Das Verarbeitungsverzeichnis weist Daten nach {source} DSGVO aus.",
        )
    ]
    if large and count is not None:
        found.append(
            PrefillSuggestion(
                "art35_3_b",
                True,
                f"Das Verzeichnis weist Daten nach {source} DSGVO und {_number(count)} "
                "betroffene Personen aus; das spricht für eine umfangreiche Verarbeitung.",
            )
        )
    return found


def prefill_from_activity(
    profile: RuleProfile, activity: Mapping[str, object]
) -> dict[str, PrefillSuggestion]:
    """Suggest answers from register data (Art. 9/10 data, number of persons, transfers).

    Only explicit ``True`` flags and integer counts are used; anything else is
    ignored rather than reinterpreted.
    """
    special = activity.get("besondere_kategorien") is True
    criminal = activity.get("daten_art10") is True
    count = _count(activity.get("anzahl_betroffene"))
    large = count is not None and count >= profile.large_scale_threshold
    candidates: list[PrefillSuggestion] = []
    if special or criminal:
        source = "Artikel 9" if special else "Artikel 10"
        candidates.extend(_sensitive_data_suggestions(source, count, large))
    if large and count is not None:
        candidates.append(
            PrefillSuggestion(
                "edsa_05_umfang",
                True,
                f"Das Verzeichnis nennt {_number(count)} betroffene Personen und erreicht damit "
                f"den Anhaltswert von {_number(profile.large_scale_threshold)} oder liegt "
                "darüber.",
            )
        )
    if activity.get("drittlandtransfer") is True:
        candidates.append(
            PrefillSuggestion(
                "edsa_06_abgleich",
                False,
                "Das Verzeichnis weist eine Übermittlung in ein Drittland aus. Das ist für sich "
                "kein Kriterium der Liste, erhöht aber das Risiko und ist bei den Szenarien zu "
                "berücksichtigen (Kapitel V DSGVO).",
            )
        )
    known = set(profile.question_keys)
    return {s.question: s for s in candidates if s.question in known}
