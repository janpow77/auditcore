"""Rule profile model: schema constants, catalogue records and :class:`RuleProfile`.

A profile is data, not code: questions with their legal references, measures,
scales, thresholds, recommendation texts and workflow parameters. Loading and
validating profile documents lives in :mod:`.profile_loader`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
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

#: Release modes of schema 2 profiles. ``sperrend``: open checks prevent the
#: release. ``dokumentation``: the library documents; open checks never prevent
#: the release and are recorded with it (user decision of 24.09.2026).
RELEASE_BLOCKING = "sperrend"
RELEASE_DOCUMENTATION = "dokumentation"
RELEASE_MODES = frozenset({RELEASE_BLOCKING, RELEASE_DOCUMENTATION})

#: DP-C21 (user decision A5 of 2026-09-23): the consultation notice under
#: Art. 36 Abs. 1 DSGVO is only given once the assessment is final and only if
#: the net risk after measures is still high. Profiles without a
#: ``consultation_notice`` section keep the immediate notice of the source.
CONSULTATION_TIMING_FINAL = "nach_abschliessender_bewertung"
#: No consultation notice (risk not high, or the assessment is incomplete).
NOTICE_NONE = "kein_hinweis"
#: Preliminary, clearly marked notice before the final assessment.
NOTICE_PRELIMINARY = "voraussichtlich_erforderlich"
#: Final notice: the net risk is still high after the final assessment.
NOTICE_REQUIRED = "erforderlich"
#: Final result: no prior consultation under Art. 36 Abs. 1 DSGVO.
NOTICE_NOT_REQUIRED = "nicht_erforderlich"

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
class ConsultationNotice:
    """When and how the prior consultation of the authority is notified (DP-C21)."""

    timing: str
    legal_basis: str
    decision_reference: str
    preliminary_text: str
    final_text: str
    not_required_text: str
    rejected_text: str


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
    release_mode: str = RELEASE_BLOCKING
    consultation_notice: ConsultationNotice | None = None

    @property
    def documentation_mode(self) -> bool:
        """True if open checks are documented instead of preventing a release."""
        return self.release_mode == RELEASE_DOCUMENTATION

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
