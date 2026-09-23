"""Versioned, source-bound rule profiles for screening, risk and workflow.

A profile is data, not code: questions with their legal references, measures,
scales, thresholds, recommendation texts and workflow parameters. Every
calculation names the exact profile identifier, version and content
fingerprint it used. Profiles of different legal regimes are separate
profiles; nothing here merges or harmonises them.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from types import MappingProxyType
from typing import Any

from .errors import ProfileError

PROFILE_SCHEMA = "auditcore_dataprotection.profile/1"

EFFECT_HARD = "hart"
EFFECT_POINT = "punkt"
EFFECT_FRIA = "fria"
EFFECTS = frozenset({EFFECT_HARD, EFFECT_POINT, EFFECT_FRIA})

#: Recommendation keys shared with the source application.
RECOMMENDATION_SCREENING_ONLY = "nur_schwellwert"
RECOMMENDATION_RELEASE = "freigabe"
RECOMMENDATION_RELEASE_WITH_CONDITIONS = "freigabe_mit_auflagen"
RECOMMENDATION_CONSULTATION = "konsultation_aufsichtsbehoerde"
#: New in this library: the survey does not allow a recommendation yet.
RECOMMENDATION_INCOMPLETE = "unvollstaendig"

DECISIONS = (
    RECOMMENDATION_SCREENING_ONLY,
    RECOMMENDATION_RELEASE,
    RECOMMENDATION_RELEASE_WITH_CONDITIONS,
    RECOMMENDATION_CONSULTATION,
)


@dataclass(frozen=True)
class Question:
    """A screening question with its effect and cited legal basis."""

    key: str
    block: str
    text: str
    legal_basis: str
    legal_basis_ji: str | None
    reference: str
    effect: str
    explanation: str
    prefill: str | None


@dataclass(frozen=True)
class Measure:
    """A catalogue measure; reductions are upper bounds for the proposal."""

    key: str
    title: str
    legal_basis: str
    reduces_likelihood: int
    reduces_severity: int
    explanation: str


@dataclass(frozen=True)
class RiskBand:
    """Inclusive upper bound of a product value; ``None`` means open-ended."""

    up_to: int | None
    label: str


@dataclass(frozen=True)
class RuleProfile:
    """Immutable, explicitly selected rule profile."""

    id: str
    version: str
    status: str
    legal_status: str
    regime: str
    regime_title: str
    regime_explanation: str
    regime_notice: str
    norms: Mapping[str, str]
    blocks: tuple[tuple[str, str], ...]
    questions: tuple[Question, ...]
    points_threshold: int
    scale_min: int
    scale_max: int
    severity_levels: Mapping[int, str]
    likelihood_levels: Mapping[int, str]
    dimensions: Mapping[str, str]
    sdm_dimensions: frozenset[str]
    bands: tuple[RiskBand, ...]
    mitigation_cap: int
    mitigation_floor: int
    measures: tuple[Measure, ...]
    consult_from: int
    conditions_from: int
    maximum_product: int
    recommendation_texts: Mapping[str, str]
    large_scale_threshold: int
    min_justification_length: int
    dpo_votes: tuple[str, ...]
    significant_fields: Mapping[str, str]
    status_texts: Mapping[str, str]
    vote_texts: Mapping[str, str]
    data_subject_view_templates: tuple[Mapping[str, str], ...]
    register_columns: tuple[tuple[str, str], ...]
    register_references: Mapping[str, str]
    source: Mapping[str, Any]
    fingerprint: str

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded with every result that used this profile."""
        return {"id": self.id, "version": self.version, "fingerprint": self.fingerprint}

    def question(self, key: str) -> Question:
        """Return one question or raise ``ProfileError`` for an unknown key."""
        for question in self.questions:
            if question.key == key:
                return question
        raise ProfileError(f"Unbekannte Frage '{key}' im Profil {self.id} {self.version}.")

    def measure(self, key: str) -> Measure:
        """Return one measure or raise ``ProfileError`` for an unknown key."""
        for measure in self.measures:
            if measure.key == key:
                return measure
        raise ProfileError(f"Unbekannte Maßnahme '{key}' im Profil {self.id} {self.version}.")

    def norm(self, key: str) -> str:
        """Citable norm of this regime, for example ``"dsfa"`` or ``"konsultation"``."""
        try:
            return self.norms[key]
        except KeyError as exc:
            raise ProfileError(f"Norm '{key}' fehlt im Profil {self.id}.") from exc

    def band(self, value: int) -> str:
        """Risk band label of a severity × likelihood product."""
        for band in self.bands:
            if band.up_to is None or value <= band.up_to:
                return band.label
        raise ProfileError("Risikostufen des Profils decken den Wert nicht ab.")

    @property
    def question_keys(self) -> tuple[str, ...]:
        """Question keys in profile order."""
        return tuple(q.key for q in self.questions)


def fingerprint(data: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON representation of a profile document."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _frozen(mapping: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(mapping))


def _ordered(items: Any) -> Mapping[str, str]:
    """Ordered key/title list of the profile document as a read-only mapping."""
    result = {str(item["key"]): str(item["title"]) for item in items}
    if len(result) != len(items):
        raise ProfileError("Doppelte Schlüssel in einer geordneten Profilliste.")
    return MappingProxyType(result)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileError(message)


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
        )
        for m in items
    )


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
    _require(len(keys) == len(set(keys)), "Doppelte Frageschlüssel im Profil.")
    _require(all(q.effect in EFFECTS for q in questions), "Unbekannte Wirkung einer Frage.")
    _require(all(q.block in block_keys for q in questions), "Frage ohne bekannten Block.")
    measure_keys = [m.key for m in measures]
    _require(len(measure_keys) == len(set(measure_keys)), "Doppelte Maßnahmenschlüssel.")
    bounded = [b.up_to for b in bands if b.up_to is not None]
    _require(bounded == sorted(bounded) and bands[-1].up_to is None, "Ungültige Risikostufen.")
    _require(1 <= scale["min"] < scale["max"], "Ungültige Bewertungsskala.")
    _require(
        0 < recommendation["conditions_from"] <= recommendation["consult_from"],
        "Ungültige Empfehlungsschwellen.",
    )
    _require(set(recommendation["texts"]) == set(DECISIONS), "Empfehlungstexte unvollständig.")


def profile_from_dict(data: Mapping[str, Any]) -> RuleProfile:
    """Validate a profile document and build an immutable ``RuleProfile``.

    Raises:
        ProfileError: schema violations, duplicate keys, unknown effects or
            inconsistent thresholds. Nothing is defaulted silently.
    """
    try:
        _require(data["schema"] == PROFILE_SCHEMA, "Unbekanntes Profilschema.")
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
            questions,
            [b["key"] for b in screening["blocks"]],
            measures,
            bands,
            scale,
            recommendation,
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
            norms=_frozen(data["regime"]["norms"]),
            blocks=tuple((b["key"], b["title"]) for b in screening["blocks"]),
            questions=questions,
            points_threshold=int(screening["points_threshold"]),
            scale_min=int(scale["min"]),
            scale_max=int(scale["max"]),
            severity_levels=MappingProxyType({int(k): v for k, v in risk["severity"].items()}),
            likelihood_levels=MappingProxyType({int(k): v for k, v in risk["likelihood"].items()}),
            dimensions=_ordered(risk["dimensions"]),
            sdm_dimensions=frozenset(risk["sdm_dimensions"]),
            bands=bands,
            mitigation_cap=int(risk["mitigation"]["cap_per_axis"]),
            mitigation_floor=int(risk["mitigation"]["floor"]),
            measures=measures,
            consult_from=int(recommendation["consult_from"]),
            conditions_from=int(recommendation["conditions_from"]),
            maximum_product=int(recommendation["maximum_product"]),
            recommendation_texts=_frozen(texts),
            large_scale_threshold=int(data["prefill"]["large_scale_threshold"]),
            min_justification_length=int(workflow["min_justification_length"]),
            dpo_votes=tuple(workflow["dpo_votes"]),
            significant_fields=_ordered(workflow["significant_fields"]),
            status_texts=_frozen(workflow["status_texts"]),
            vote_texts=_frozen(workflow["vote_texts"]),
            data_subject_view_templates=tuple(
                _frozen(t) for t in workflow["data_subject_view_templates"]
            ),
            register_columns=tuple((c["key"], c["title"]) for c in data["register"]["columns"]),
            register_references=_frozen(data["register"]["legal_references"]),
            source=_frozen(data["source"]),
            fingerprint=fingerprint(data),
        )
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
