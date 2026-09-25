"""Legacy-exact administration helpers of ``regulierung@a5d48ea``.

Pure parts of ``services/dsfa/verwaltung.py``, the register identifiers and
prefill templates of ``services/mandant_dsgvo_service.py`` and
``katalog.katalog_als_json``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

from .errors import ValidationError
from .legacy_scoring import (
    REGIME_DSGVO,
    REGIME_JI,
    LegacyAnswer,
    LegacyScenario,
    _questions,
    legacy_profile,
    legacy_proposal,
)
from .rules import RuleProfile

#: Legacy keyword heuristic of the source application (KPAnG enforcement).
REGIME_KEYWORDS = ("ordnungswidrigkeit", "bußgeld", "bussgeld", "owi", "vollzug", "kpang")
PLACEHOLDER_EMPTY = "(noch einzutragen)"
_PLACEHOLDER_EXEMPT = frozenset({"dsb_anrede", "dsb_titel", "plz", "dsb_plz"})
_PLACEHOLDER_PREFIX = "{{mandant:"

# ---------------------------------------------------------------------------
# Administration adapter (verwaltung.py, pure parts)
# ---------------------------------------------------------------------------


def legacy_answers_from_json(answers: Mapping[str, object] | None) -> list[LegacyAnswer]:
    """``verwaltung._antworten_aus_json``: unknown keys dropped, ``bool()`` conversion."""
    questions = _questions()
    read: list[LegacyAnswer] = []
    for key, value in (answers or {}).items():
        if key not in questions:
            continue
        if isinstance(value, dict):
            read.append(
                LegacyAnswer(key, bool(value.get("ja")), str(value.get("begruendung") or ""))
            )
        else:
            read.append(LegacyAnswer(key, bool(value)))
    return read


def _optional_int(entry: Mapping[str, Any], key: str) -> int | None:
    return int(entry[key]) if entry.get(key) not in (None, "") else None


def _legacy_scenario(entry: Mapping[str, Any]) -> LegacyScenario:
    """One scenario with the conversions of the source; raises on unusable values."""
    try:
        return LegacyScenario(
            dimension=str(entry.get("dimension") or ""),
            beschreibung=str(entry.get("beschreibung") or ""),
            schwere=int(entry.get("schwere") or 0),
            wahrscheinlichkeit=int(entry.get("wahrscheinlichkeit") or 0),
            massnahmen=tuple(entry.get("massnahmen") or ()),
            netto_schwere=_optional_int(entry, "netto_schwere"),
            netto_wahrscheinlichkeit=_optional_int(entry, "netto_wahrscheinlichkeit"),
        )
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            "Ein Risikoszenario enthält unbrauchbare Werte; Schwere und "
            "Wahrscheinlichkeit müssen ganze Zahlen von 1 bis 4 sein."
        ) from exc


def legacy_scenarios_from_json(scenarios: Sequence[object] | None) -> list[LegacyScenario]:
    """``verwaltung._szenarien_aus_json``: gross values 1..4, residual values unchecked."""
    read = [_legacy_scenario(entry) for entry in scenarios or [] if isinstance(entry, dict)]
    for scenario in read:
        if not (1 <= scenario.schwere <= 4 and 1 <= scenario.wahrscheinlichkeit <= 4):
            raise ValidationError(
                "Schwere und Wahrscheinlichkeit sind auf einer Skala von 1 bis 4 einzustufen."
            )
    return read


def legacy_check_regime(value: str | None) -> str:
    """``verwaltung.pruefe_regime``."""
    chosen = (value or REGIME_DSGVO).strip()
    if chosen not in (REGIME_DSGVO, REGIME_JI):
        raise ValidationError(
            f"Unbekannter Rechtsrahmen. Zulässig sind {REGIME_DSGVO} und {REGIME_JI}."
        )
    return chosen


def legacy_preview(
    answers: Mapping[str, object], scenarios: Sequence[object], regime: str = REGIME_DSGVO
) -> dict[str, Any]:
    """``verwaltung.berechne_vorschlag``."""
    return legacy_proposal(
        legacy_answers_from_json(answers),
        legacy_scenarios_from_json(scenarios),
        legacy_check_regime(regime),
    )


def legacy_regime_suggestion(activity: Mapping[str, object]) -> str:
    """``verwaltung.regime_vorschlag`` keyword heuristic (source-specific, not general)."""
    text = " ".join(
        str(activity.get(name) or "") for name in ("name", "zweck", "referat", "rechtsgrundlage")
    ).casefold()
    return REGIME_JI if any(word in text for word in REGIME_KEYWORDS) else REGIME_DSGVO


def legacy_compare_activity(
    before: Mapping[str, object], after: Mapping[str, object]
) -> list[dict[str, Any]]:
    """``verwaltung.vergleiche_taetigkeit``; ``(old or "") != (new or "")`` semantics."""
    differences: list[dict[str, Any]] = []
    for name, title in legacy_profile(REGIME_DSGVO).significant_fields.items():
        old = before.get(name)
        new = after.get(name)
        if (old or "") != (new or ""):
            differences.append({"feld": name, "bezeichnung": title, "vorher": old, "nachher": new})
    return differences


# ---------------------------------------------------------------------------
# Register identifiers and prefill templates (mandant_dsgvo_service.py)
# ---------------------------------------------------------------------------


def legacy_activity_identifier(name: str, position: int) -> str:
    """``taetigkeit_kennung``: SHA-1 of the case-folded name, position for duplicates."""
    raw = (name or "").strip().casefold()
    identifier = "t-" + hashlib.sha1(raw.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
    return identifier if position <= 1 else f"{identifier}-{position}"


def legacy_activities_with_identifiers(
    activities: Sequence[object] | None,
) -> list[dict[str, Any]]:
    """``taetigkeiten_mit_kennung``; existing identifiers stay unchanged."""
    result: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for entry in activities or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("id"):
            result.append(entry)
            continue
        name = str(entry.get("name") or "")
        seen[name] = seen.get(name, 0) + 1
        result.append({**entry, "id": legacy_activity_identifier(name, seen[name])})
    return result


def legacy_fill_placeholders(value: Any, values: Mapping[str, str]) -> Any:
    """``fuelle_platzhalter``: ``{{mandant:feld}}`` recursively, empty fields marked.

    Works on arbitrary JSON templates, so input and output are untyped JSON.
    """
    if isinstance(value, dict):
        return {k: legacy_fill_placeholders(v, values) for k, v in value.items()}
    if isinstance(value, list):
        return [legacy_fill_placeholders(v, values) for v in value]
    if isinstance(value, str) and value.startswith(_PLACEHOLDER_PREFIX) and value.endswith("}}"):
        name = value[len(_PLACEHOLDER_PREFIX) : -2]
        replacement = values.get(name, "")
        if not replacement and name not in _PLACEHOLDER_EXEMPT:
            return PLACEHOLDER_EMPTY
        return replacement
    return value


# ---------------------------------------------------------------------------
# Catalogue (katalog.py)
# ---------------------------------------------------------------------------


def _catalog_blocks(dsgvo: RuleProfile) -> list[dict[str, Any]]:
    return [
        {
            "block": block,
            "titel": title,
            "fragen": [
                {
                    "schluessel": q.key,
                    "text": q.text,
                    "rechtsgrundlage": q.legal_basis,
                    "wirkung": q.effect,
                    "erlaeuterung": q.explanation,
                    "vorbelegung": q.prefill,
                }
                for q in dsgvo.questions
                if q.block == block
            ],
        }
        for block, title in dsgvo.blocks
    ]


def legacy_catalog_json() -> dict[str, Any]:
    """``katalog.katalog_als_json``."""
    dsgvo = legacy_profile(REGIME_DSGVO)
    return {
        "bloecke": _catalog_blocks(dsgvo),
        "regime": [
            {
                "schluessel": profile.regime,
                "titel": profile.regime_title,
                "erlaeuterung": profile.regime_explanation,
                "hinweis": profile.regime_notice,
                "normen": dict(profile.norms),
            }
            for profile in (dsgvo, legacy_profile(REGIME_JI))
        ],
        "schwelle_punkte": dsgvo.points_threshold,
        "dimensionen": dict(dsgvo.dimensions),
        "sdm_dimensionen": sorted(dsgvo.sdm_dimensions),
        "standpunkt_begruendungen": [dict(t) for t in dsgvo.data_subject_view_templates],
        "schwere": {str(k): v for k, v in dsgvo.severity_levels.items()},
        "wahrscheinlichkeit": {str(k): v for k, v in dsgvo.likelihood_levels.items()},
        "massnahmen": [
            {
                "schluessel": m.key,
                "bezeichnung": m.title,
                "rechtsgrundlage": m.legal_basis,
                "senkt_wahrscheinlichkeit": m.reduces_likelihood,
                "senkt_schwere": m.reduces_severity,
                "erlaeuterung": m.explanation,
            }
            for m in dsgvo.measures
        ],
    }
