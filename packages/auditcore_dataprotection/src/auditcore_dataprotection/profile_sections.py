"""Sections of rule profile documents: primitives and the schema 2 (EDPB) parts.

Profile documents are external JSON data read with ``Any`` at the boundary.
Every schema 2 section is required; nothing is defaulted.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, TypedDict, TypeVar

from .errors import ProfileError
from .profile_model import (
    DECISION_REJECTED,
    DECISIONS,
    DOSSIER_KINDS,
    PROFILE_SCHEMA_EDPB,
    RELEASE_BLOCKING,
    RELEASE_MODES,
    DossierField,
    Measure,
    SeverityFloor,
    Source,
)

_V = TypeVar("_V")


def frozen(mapping: Mapping[str, _V]) -> Mapping[str, _V]:
    return MappingProxyType(dict(mapping))


def ordered(items: Any) -> Mapping[str, str]:
    """Ordered key/title list of the profile document as a read-only mapping."""
    result = {str(item["key"]): str(item["title"]) for item in items}
    if len(result) != len(items):
        raise ProfileError("Doppelte Schlüssel in einer geordneten Profilliste.")
    return MappingProxyType(result)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileError(message)


# ---------------------------------------------------------------------------
# Schema 2 sections (EDPB template 2026)
# ---------------------------------------------------------------------------


class EdpbFields(TypedDict, total=False):
    """Keyword arguments of :class:`RuleProfile` that only schema 2 profiles set.

    Schema 1 profiles pass none of them (the defaults of ``RuleProfile`` apply);
    :func:`edpb_fields` always returns every key.
    """

    schema: str
    criteria_label: str
    sources: tuple[Source, ...]
    decisions: tuple[str, ...]
    decision_titles: Mapping[str, str]
    consultation_grounds: Mapping[str, tuple[str, str]]
    conditions_required_for: frozenset[str]
    severity_floors: tuple[SeverityFloor, ...]
    measure_categories: Mapping[str, tuple[str, str]]
    implementation_states: Mapping[str, str]
    acceptance_levels: Mapping[str, str]
    dossier_fields: tuple[DossierField, ...]
    risk_matrix: Mapping[tuple[int, int], str]
    risk_method: str
    band_recommendations: Mapping[str, str]
    release_mode: str


def _decisions(recommendation: Mapping[str, Any]) -> tuple[str, ...]:
    """Decisions of a schema 2 profile: every proposal plus ``verworfen``."""
    decisions = tuple(str(d["key"]) for d in recommendation["decisions"])
    require(len(decisions) == len(set(decisions)), "Doppelte Entscheidungen im Profil.")
    require(
        set(DECISIONS) <= set(decisions), "Das Profil muss alle Vorschläge als Entscheidung kennen."
    )
    require(DECISION_REJECTED in decisions, "Die Entscheidung 'verworfen' fehlt im Profil.")
    return decisions


def _consultation_grounds(recommendation: Mapping[str, Any]) -> dict[str, tuple[str, str]]:
    grounds = {
        str(g["key"]): (str(g["title"]), str(g["reference"]))
        for g in recommendation["consultation_grounds"]
    }
    require(bool(grounds), "Das Profil nennt keinen Grund für eine Konsultation.")
    return grounds


def _severity_floors(risk: Mapping[str, Any], bands: list[object]) -> tuple[SeverityFloor, ...]:
    scale = risk["scale"]
    floors = tuple(
        SeverityFloor(int(f["severity"]), str(f["min_band"]), str(f["reference"]))
        for f in risk["severity_floors"]
    )
    require(
        all(f.min_band in bands and scale["min"] <= f.severity <= scale["max"] for f in floors),
        "Ungültige Mindeststufe im Profil.",
    )
    return floors


def _measure_categories(
    risk: Mapping[str, Any], measures: tuple[Measure, ...]
) -> dict[str, tuple[str, str]]:
    categories = {
        str(c["key"]): (str(c["title"]), str(c["reference"])) for c in risk["measure_categories"]
    }
    require(all(m.category in categories for m in measures), "Maßnahme ohne bekannte Kategorie.")
    return categories


def _risk_matrix(risk: Mapping[str, Any], bands: list[object]) -> dict[tuple[int, int], str]:
    scale = risk["scale"]
    levels = range(int(scale["min"]), int(scale["max"]) + 1)
    matrix = {
        (int(s), int(lik)): str(label)
        for s, row in risk["matrix"].items()
        for lik, label in row.items()
    }
    require(
        set(matrix) == {(s, lik) for s in levels for lik in levels}
        and all(label in bands for label in matrix.values()),
        "Die Risikomatrix muss jede Kombination der Skala mit einer bekannten Stufe belegen.",
    )
    return matrix


def _band_recommendations(
    recommendation: Mapping[str, Any], matrix: Mapping[tuple[int, int], str]
) -> dict[str, str]:
    by_band = {str(k): str(v) for k, v in recommendation["by_band"].items()}
    require(
        set(matrix.values()) <= set(by_band) and set(by_band.values()) <= set(DECISIONS),
        "Jede Stufe der Risikomatrix braucht einen Vorschlag.",
    )
    return by_band


def _dossier_fields(data: Mapping[str, Any]) -> tuple[DossierField, ...]:
    dossier = tuple(
        DossierField(
            key=str(f["key"]),
            title=str(f["title"]),
            reference=str(f["reference"]),
            kind=str(f["kind"]),
            required=bool(f["required"]),
            choices=tuple((str(c["key"]), str(c["title"])) for c in f.get("choices", ())),
        )
        for f in data["dossier"]["fields"]
    )
    require(all(f.kind in DOSSIER_KINDS for f in dossier), "Unbekannte Feldart im Profil.")
    require(
        all(bool(f.choices) == (f.kind == "choice") for f in dossier),
        "Auswahlfelder brauchen Auswahlwerte, andere Felder keine.",
    )
    require(len({f.key for f in dossier}) == len(dossier), "Doppelte Felder der Folgenabschätzung.")
    return dossier


def _sources(data: Mapping[str, Any]) -> tuple[Source, ...]:
    sources = tuple(
        Source(
            key=str(q["key"]),
            title=str(q["title"]),
            issuer=str(q["issuer"]),
            date=str(q["date"]),
            status=str(q["status"]),
            reference=str(q["reference"]),
            used_for=str(q["used_for"]),
        )
        for q in data["sources"]
    )
    require(bool(sources), "Ein Profil nach Schema 2 muss seine Quellen nennen.")
    return sources


def edpb_fields(data: Mapping[str, Any], measures: tuple[Measure, ...]) -> EdpbFields:
    """Schema 2 sections; every one is required, nothing is defaulted.

    The sections are validated in document order so the first inconsistency
    reported stays the same.
    """
    risk = data["risk"]
    recommendation = data["recommendation"]
    workflow = data["workflow"]
    decisions = _decisions(recommendation)
    grounds = _consultation_grounds(recommendation)
    conditional = frozenset(str(k) for k in workflow["conditions_required_for"])
    require(conditional <= set(decisions), "Bedingungen für eine unbekannte Entscheidung.")
    bands = [b["label"] for b in risk["bands"]]
    floors = _severity_floors(risk, bands)
    categories = _measure_categories(risk, measures)
    matrix = _risk_matrix(risk, bands)
    by_band = _band_recommendations(recommendation, matrix)
    method = str(risk["method"])
    require(bool(method.strip()), "Das Profil muss seine Risikomethode beschreiben.")
    dossier = _dossier_fields(data)
    sources = _sources(data)
    return {
        "schema": PROFILE_SCHEMA_EDPB,
        "criteria_label": str(data["screening"]["criteria_label"]),
        "sources": sources,
        "decisions": decisions,
        "decision_titles": frozen(
            {str(d["key"]): str(d["title"]) for d in recommendation["decisions"]}
        ),
        "consultation_grounds": frozen(grounds),
        "conditions_required_for": conditional,
        "severity_floors": floors,
        "measure_categories": frozen(categories),
        "implementation_states": ordered(risk["implementation_states"]),
        "acceptance_levels": ordered(risk["acceptance_levels"]),
        "dossier_fields": dossier,
        "risk_matrix": MappingProxyType(matrix),
        "risk_method": method,
        "band_recommendations": frozen(by_band),
        "release_mode": _release_mode(workflow),
    }


def _release_mode(workflow: Mapping[str, Any]) -> str:
    """Release mode of a schema 2 profile; profiles before 2026.10.3 block."""
    mode = str(workflow.get("release_mode", RELEASE_BLOCKING))
    require(mode in RELEASE_MODES, f"Unbekannter Freigabemodus '{mode}'.")
    return mode
