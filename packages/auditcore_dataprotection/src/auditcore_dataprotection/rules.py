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
from dataclasses import dataclass, field
from importlib import resources
from types import MappingProxyType
from typing import Any

from .errors import ProfileError

PROFILE_SCHEMA = "auditcore_dataprotection.profile/1"
#: Schema 2 adds sources, decisions, consultation grounds, severity floors,
#: measure categories, implementation states and DPIA master data, aligned with
#: the EDPB template for data protection impact assessments (2026, v1.0).
PROFILE_SCHEMA_EDPB = "auditcore_dataprotection.profile/2"
PROFILE_SCHEMAS = frozenset({PROFILE_SCHEMA, PROFILE_SCHEMA_EDPB})

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
#: Schema 2 only: the controller abandons the processing ("REJECTED" in the
#: EDPB template, section 6). Never proposed by the system, only decided.
DECISION_REJECTED = "verworfen"

#: Wording of the WP 248 criteria in schema 1 profiles (source behaviour).
LEGACY_CRITERIA_LABEL = "Kriterien des Europäischen Datenschutzausschusses"

DOSSIER_KINDS = frozenset({"text", "date", "choice"})

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
    category: str = ""


@dataclass(frozen=True)
class Source:
    """A guideline, standard or template the profile relies on, cited by name."""

    key: str
    title: str
    issuer: str
    date: str
    status: str
    reference: str
    used_for: str


@dataclass(frozen=True)
class SeverityFloor:
    """From this severity on, a scenario is at least in ``min_band``."""

    severity: int
    min_band: str
    reference: str


@dataclass(frozen=True)
class DossierField:
    """A master-data field of the DPIA (EDPB template, sections 0 to 2)."""

    key: str
    title: str
    reference: str
    kind: str
    required: bool
    choices: tuple[tuple[str, str], ...] = ()


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
    schema: str = PROFILE_SCHEMA
    criteria_label: str = LEGACY_CRITERIA_LABEL
    sources: tuple[Source, ...] = ()
    decisions: tuple[str, ...] = DECISIONS
    decision_titles: Mapping[str, str] = field(default_factory=dict)
    consultation_grounds: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    conditions_required_for: frozenset[str] = frozenset()
    severity_floors: tuple[SeverityFloor, ...] = ()
    measure_categories: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    implementation_states: Mapping[str, str] = field(default_factory=dict)
    acceptance_levels: Mapping[str, str] = field(default_factory=dict)
    dossier_fields: tuple[DossierField, ...] = ()
    risk_matrix: Mapping[tuple[int, int], str] = field(default_factory=dict)
    risk_method: str = ""
    band_recommendations: Mapping[str, str] = field(default_factory=dict)

    @property
    def edpb(self) -> bool:
        """True for schema 2 profiles aligned with the EDPB DPIA template."""
        return self.schema == PROFILE_SCHEMA_EDPB

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

    def band_rank(self, label: str) -> int:
        """Order of a band label, lowest first."""
        for index, band in enumerate(self.bands):
            if band.label == label:
                return index
        raise ProfileError(f"Unbekannte Risikostufe '{label}' im Profil {self.id}.")

    def matrix_band(self, severity: int, likelihood: int) -> str:
        """Band of a severity/likelihood pair from the profile's risk matrix (schema 2)."""
        try:
            return self.risk_matrix[(severity, likelihood)]
        except KeyError as exc:
            raise ProfileError(
                f"Die Risikomatrix des Profils {self.id} deckt Schwere {severity} und "
                f"Wahrscheinlichkeit {likelihood} nicht ab."
            ) from exc

    def severity_floor(self, severity: int) -> SeverityFloor | None:
        """Strictest floor that applies to a severity level, if any."""
        applicable = [f for f in self.severity_floors if severity >= f.severity]
        if not applicable:
            return None
        return max(applicable, key=lambda f: self.band_rank(f.min_band))

    def dossier_field(self, key: str) -> DossierField:
        """Return one master-data field or raise ``ProfileError``."""
        for item in self.dossier_fields:
            if item.key == key:
                return item
        raise ProfileError(f"Unbekanntes Feld '{key}' der Folgenabschätzung im Profil {self.id}.")

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
            category=str(m.get("category", "")),
        )
        for m in items
    )


def _edpb_fields(data: Mapping[str, Any], measures: tuple[Measure, ...]) -> dict[str, Any]:
    """Schema 2 sections; every one is required, nothing is defaulted."""
    risk = data["risk"]
    recommendation = data["recommendation"]
    workflow = data["workflow"]
    decisions = tuple(str(d["key"]) for d in recommendation["decisions"])
    _require(len(decisions) == len(set(decisions)), "Doppelte Entscheidungen im Profil.")
    _require(
        set(DECISIONS) <= set(decisions), "Das Profil muss alle Vorschläge als Entscheidung kennen."
    )
    _require(DECISION_REJECTED in decisions, "Die Entscheidung 'verworfen' fehlt im Profil.")
    grounds = {
        str(g["key"]): (str(g["title"]), str(g["reference"]))
        for g in recommendation["consultation_grounds"]
    }
    _require(bool(grounds), "Das Profil nennt keinen Grund für eine Konsultation.")
    conditional = frozenset(str(k) for k in workflow["conditions_required_for"])
    _require(conditional <= set(decisions), "Bedingungen für eine unbekannte Entscheidung.")
    bands = [b["label"] for b in risk["bands"]]
    scale = risk["scale"]
    floors = tuple(
        SeverityFloor(int(f["severity"]), str(f["min_band"]), str(f["reference"]))
        for f in risk["severity_floors"]
    )
    _require(
        all(f.min_band in bands and scale["min"] <= f.severity <= scale["max"] for f in floors),
        "Ungültige Mindeststufe im Profil.",
    )
    categories = {
        str(c["key"]): (str(c["title"]), str(c["reference"])) for c in risk["measure_categories"]
    }
    _require(all(m.category in categories for m in measures), "Maßnahme ohne bekannte Kategorie.")
    levels = range(int(scale["min"]), int(scale["max"]) + 1)
    matrix = {
        (int(s), int(lik)): str(label)
        for s, row in risk["matrix"].items()
        for lik, label in row.items()
    }
    _require(
        set(matrix) == {(s, lik) for s in levels for lik in levels}
        and all(label in bands for label in matrix.values()),
        "Die Risikomatrix muss jede Kombination der Skala mit einer bekannten Stufe belegen.",
    )
    by_band = {str(k): str(v) for k, v in recommendation["by_band"].items()}
    _require(
        set(matrix.values()) <= set(by_band) and set(by_band.values()) <= set(DECISIONS),
        "Jede Stufe der Risikomatrix braucht einen Vorschlag.",
    )
    method = str(risk["method"])
    _require(bool(method.strip()), "Das Profil muss seine Risikomethode beschreiben.")
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
    _require(all(f.kind in DOSSIER_KINDS for f in dossier), "Unbekannte Feldart im Profil.")
    _require(
        all(bool(f.choices) == (f.kind == "choice") for f in dossier),
        "Auswahlfelder brauchen Auswahlwerte, andere Felder keine.",
    )
    _require(
        len({f.key for f in dossier}) == len(dossier), "Doppelte Felder der Folgenabschätzung."
    )
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
    _require(bool(sources), "Ein Profil nach Schema 2 muss seine Quellen nennen.")
    return {
        "schema": PROFILE_SCHEMA_EDPB,
        "criteria_label": str(data["screening"]["criteria_label"]),
        "sources": sources,
        "decisions": decisions,
        "decision_titles": _frozen(
            {str(d["key"]): str(d["title"]) for d in recommendation["decisions"]}
        ),
        "consultation_grounds": _frozen(grounds),
        "conditions_required_for": conditional,
        "severity_floors": floors,
        "measure_categories": _frozen(categories),
        "implementation_states": _ordered(risk["implementation_states"]),
        "acceptance_levels": _ordered(risk["acceptance_levels"]),
        "dossier_fields": dossier,
        "risk_matrix": MappingProxyType(matrix),
        "risk_method": method,
        "band_recommendations": _frozen(by_band),
    }


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
        _require(data["schema"] in PROFILE_SCHEMAS, "Unbekanntes Profilschema.")
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
            **(_edpb_fields(data, measures) if data["schema"] == PROFILE_SCHEMA_EDPB else {}),
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
