"""Versioned, source-bound rule profiles for screening, risk and workflow.

A profile is data, not code: questions with their legal references, measures,
scales, thresholds, recommendation texts and workflow parameters. Every
calculation names the exact profile identifier, version and content
fingerprint it used. Profiles of different legal regimes are separate
profiles; nothing here merges or harmonises them.

The records live in :mod:`.profile_model`, loading and validation in
:mod:`.profile_loader`; every name stays importable from here.
"""

from __future__ import annotations

from .profile_loader import available_profiles, fingerprint, load_profile, profile_from_dict
from .profile_model import (
    CONSULTATION_TIMING_FINAL,
    DECISION_REJECTED,
    DECISIONS,
    DOSSIER_KINDS,
    EFFECT_FRIA,
    EFFECT_HARD,
    EFFECT_POINT,
    EFFECTS,
    LEGACY_CRITERIA_LABEL,
    NOTICE_NONE,
    NOTICE_NOT_REQUIRED,
    NOTICE_PRELIMINARY,
    NOTICE_REQUIRED,
    PROFILE_SCHEMA,
    PROFILE_SCHEMA_EDPB,
    PROFILE_SCHEMAS,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_INCOMPLETE,
    RECOMMENDATION_RELEASE,
    RECOMMENDATION_RELEASE_WITH_CONDITIONS,
    RECOMMENDATION_SCREENING_ONLY,
    RELEASE_BLOCKING,
    RELEASE_DOCUMENTATION,
    RELEASE_MODES,
    ConsultationNotice,
    DossierField,
    Measure,
    Question,
    RiskBand,
    RuleProfile,
    SeverityFloor,
    Source,
)

__all__ = [
    "CONSULTATION_TIMING_FINAL",
    "DECISIONS",
    "DECISION_REJECTED",
    "DOSSIER_KINDS",
    "EFFECTS",
    "EFFECT_FRIA",
    "EFFECT_HARD",
    "EFFECT_POINT",
    "LEGACY_CRITERIA_LABEL",
    "NOTICE_NONE",
    "NOTICE_NOT_REQUIRED",
    "NOTICE_PRELIMINARY",
    "NOTICE_REQUIRED",
    "PROFILE_SCHEMA",
    "PROFILE_SCHEMAS",
    "PROFILE_SCHEMA_EDPB",
    "RECOMMENDATION_CONSULTATION",
    "RECOMMENDATION_INCOMPLETE",
    "RECOMMENDATION_RELEASE",
    "RECOMMENDATION_RELEASE_WITH_CONDITIONS",
    "RECOMMENDATION_SCREENING_ONLY",
    "RELEASE_BLOCKING",
    "RELEASE_DOCUMENTATION",
    "RELEASE_MODES",
    "ConsultationNotice",
    "DossierField",
    "Measure",
    "Question",
    "RiskBand",
    "RuleProfile",
    "SeverityFloor",
    "Source",
    "available_profiles",
    "fingerprint",
    "load_profile",
    "profile_from_dict",
]
