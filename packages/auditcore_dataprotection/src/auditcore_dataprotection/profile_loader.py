"""Loading and validating rule profile documents (packaged JSON, schema 1 and 2).

Profile documents are external JSON data; they are read here with ``Any`` at
the boundary and turned into the immutable records of :mod:`.profile_model`.
Nothing is defaulted silently: a missing or inconsistent section raises
:class:`~auditcore_dataprotection.errors.ProfileError`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import resources
from types import MappingProxyType
from typing import Any

from .errors import ProfileError
from .hashing import canonical_sha256
from .profile_model import (
    CONSULTATION_TIMING_FINAL,
    DECISIONS,
    EFFECTS,
    PROFILE_SCHEMA_EDPB,
    PROFILE_SCHEMAS,
    ConsultationNotice,
    Measure,
    Question,
    RiskBand,
    RuleProfile,
)
from .profile_sections import edpb_fields, frozen, ordered, require

_NOTICE_TEXTS = (
    "legal_basis",
    "decision_reference",
    "preliminary_text",
    "final_text",
    "not_required_text",
    "rejected_text",
)


def fingerprint(data: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON representation of a profile document."""
    return canonical_sha256(data)


def _questions(items: Any) -> tuple[Question, ...]:
    """Screening questions of a profile document."""
    return tuple(
        Question(
            key=q["key"],
            block=q["block"],
            text=q["text"],
            legal_basis=q["legal_basis"],
            legal_basis_ji=q["legal_basis_ji"],
            reference=q["reference"],
            effect=q["effect"],
            explanation=q["explanation"],
            prefill=q["prefill"],
        )
        for q in items
    )


def _measures(items: Any) -> tuple[Measure, ...]:
    """Catalogue measures of a profile document."""
    return tuple(
        Measure(
            key=m["key"],
            title=m["title"],
            legal_basis=m["legal_basis"],
            reduces_likelihood=int(m["reduces_likelihood"]),
            reduces_severity=int(m["reduces_severity"]),
            explanation=m["explanation"],
            category=str(m.get("category", "")),
        )
        for m in items
    )


def _consultation_notice(recommendation: Mapping[str, Any]) -> ConsultationNotice | None:
    """Optional notice timing (DP-C21); absent in source-characterised profiles."""
    raw = recommendation.get("consultation_notice")
    if raw is None:
        return None
    notice = ConsultationNotice(
        timing=str(raw["timing"]),
        legal_basis=str(raw["legal_basis"]),
        decision_reference=str(raw["decision_reference"]),
        preliminary_text=str(raw["preliminary_text"]),
        final_text=str(raw["final_text"]),
        not_required_text=str(raw["not_required_text"]),
        rejected_text=str(raw["rejected_text"]),
    )
    require(
        notice.timing == CONSULTATION_TIMING_FINAL,
        f"Unbekannter Zeitpunkt des Konsultationshinweises '{notice.timing}'.",
    )
    require(
        all(getattr(notice, name).strip() for name in _NOTICE_TEXTS),
        "Der Konsultationshinweis des Profils ist unvollständig.",
    )
    return notice


# ---------------------------------------------------------------------------
# Whole document
# ---------------------------------------------------------------------------


def _validate(
    questions: tuple[Question, ...],
    block_keys: list[str],
    measures: tuple[Measure, ...],
    bands: tuple[RiskBand, ...],
    scale: Mapping[str, Any],
    recommendation: Mapping[str, Any],
) -> None:
    """Consistency checks of a profile document; raises ``ProfileError``."""
    keys = [q.key for q in questions]
    require(len(keys) == len(set(keys)), "Doppelte Frageschlüssel im Profil.")
    require(all(q.effect in EFFECTS for q in questions), "Unbekannte Wirkung einer Frage.")
    require(all(q.block in block_keys for q in questions), "Frage ohne bekannten Block.")
    measure_keys = [m.key for m in measures]
    require(len(measure_keys) == len(set(measure_keys)), "Doppelte Maßnahmenschlüssel.")
    bounded = [b.up_to for b in bands if b.up_to is not None]
    require(bounded == sorted(bounded) and bands[-1].up_to is None, "Ungültige Risikostufen.")
    require(1 <= scale["min"] < scale["max"], "Ungültige Bewertungsskala.")
    require(
        0 < recommendation["conditions_from"] <= recommendation["consult_from"],
        "Ungültige Empfehlungsschwellen.",
    )
    require(set(recommendation["texts"]) == set(DECISIONS), "Empfehlungstexte unvollständig.")


def _build_profile(data: Mapping[str, Any]) -> RuleProfile:
    """Validate and build; ``KeyError``/``TypeError`` of missing sections pass through."""
    require(data["schema"] in PROFILE_SCHEMAS, "Unbekanntes Profilschema.")
    screening = data["screening"]
    risk = data["risk"]
    recommendation = data["recommendation"]
    workflow = data["workflow"]
    questions = _questions(screening["questions"])
    measures = _measures(risk["measures"])
    bands = tuple(RiskBand(b["up_to"], b["label"]) for b in risk["bands"])
    scale = risk["scale"]
    texts = recommendation["texts"]
    _validate(
        questions, [b["key"] for b in screening["blocks"]], measures, bands, scale, recommendation
    )
    return RuleProfile(
        id=data["id"],
        version=data["version"],
        status=data["status"],
        legal_status=data["legal_status"],
        regime=data["regime"]["key"],
        regime_title=data["regime"]["title"],
        regime_explanation=data["regime"]["explanation"],
        regime_notice=data["regime"]["notice"],
        norms=frozen(data["regime"]["norms"]),
        blocks=tuple((b["key"], b["title"]) for b in screening["blocks"]),
        questions=questions,
        points_threshold=int(screening["points_threshold"]),
        scale_min=int(scale["min"]),
        scale_max=int(scale["max"]),
        severity_levels=MappingProxyType({int(k): v for k, v in risk["severity"].items()}),
        likelihood_levels=MappingProxyType({int(k): v for k, v in risk["likelihood"].items()}),
        dimensions=ordered(risk["dimensions"]),
        sdm_dimensions=frozenset(risk["sdm_dimensions"]),
        bands=bands,
        mitigation_cap=int(risk["mitigation"]["cap_per_axis"]),
        mitigation_floor=int(risk["mitigation"]["floor"]),
        measures=measures,
        consult_from=int(recommendation["consult_from"]),
        conditions_from=int(recommendation["conditions_from"]),
        maximum_product=int(recommendation["maximum_product"]),
        recommendation_texts=frozen(texts),
        large_scale_threshold=int(data["prefill"]["large_scale_threshold"]),
        min_justification_length=int(workflow["min_justification_length"]),
        dpo_votes=tuple(workflow["dpo_votes"]),
        significant_fields=ordered(workflow["significant_fields"]),
        status_texts=frozen(workflow["status_texts"]),
        vote_texts=frozen(workflow["vote_texts"]),
        data_subject_view_templates=tuple(
            frozen(t) for t in workflow["data_subject_view_templates"]
        ),
        register_columns=tuple((c["key"], c["title"]) for c in data["register"]["columns"]),
        register_references=frozen(data["register"]["legal_references"]),
        source=frozen(data["source"]),
        fingerprint=fingerprint(data),
        consultation_notice=_consultation_notice(recommendation),
        **(edpb_fields(data, measures) if data["schema"] == PROFILE_SCHEMA_EDPB else {}),
    )


def profile_from_dict(data: Mapping[str, Any]) -> RuleProfile:
    """Validate a profile document and build an immutable ``RuleProfile``.

    Raises:
        ProfileError: schema violations, duplicate keys, unknown effects or
            inconsistent thresholds. Nothing is defaulted silently.
    """
    try:
        return _build_profile(data)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        if isinstance(exc, ProfileError):
            raise
        raise ProfileError(f"Profil ist unvollständig oder fehlerhaft: {exc!r}") from exc


def available_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs, sorted; no profile is a hidden default."""
    found = []
    for entry in resources.files("auditcore_dataprotection.profiles").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found.append((str(data["id"]), str(data["version"])))
    return tuple(sorted(found))


def load_profile(profile_id: str, version: str) -> RuleProfile:
    """Load an explicitly named packaged profile version.

    Raises:
        ProfileError: the id/version pair is not packaged.
    """
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise ProfileError("Profilkennung und Version sind als Text anzugeben.")
    name = f"{profile_id}-{version}.json"
    entry = resources.files("auditcore_dataprotection.profiles").joinpath(name)
    if "/" in name or "\\" in name or not entry.is_file():
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    data = json.loads(entry.read_text(encoding="utf-8"))
    profile = profile_from_dict(data)
    if (profile.id, profile.version) != (profile_id, version):
        raise ProfileError("Profildatei und Profilkennung stimmen nicht überein.")
    return profile
