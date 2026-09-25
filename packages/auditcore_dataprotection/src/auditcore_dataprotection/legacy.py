"""Behavior-compatible adapter for the source application ``regulierung``.

These functions reproduce the characterized outputs of
``regulierung@a5d48ea`` exactly, including behavior this library corrects in
its own contract (see ``docs/behavior-changes.md``): unknown questions are
skipped, truthy strings count as "yes", empty surveys yield
``nur_schwellwert`` and explicit residual values are not range-checked.

They exist so an existing consumer can switch to the installed package
without changing results, and so the differences to the corrected contract
stay testable. New consumers should use :mod:`auditcore_dataprotection.calculation`
and :mod:`auditcore_dataprotection.assessment` instead.

The implementation is split into :mod:`.legacy_scoring` (screening, risk,
proposal, prefill), :mod:`.legacy_admin` (administration, identifiers,
catalogue) and :mod:`.legacy_report` (HTML report); every name stays
importable from this module.
"""

from __future__ import annotations

import warnings

from .legacy_admin import (
    PLACEHOLDER_EMPTY,
    REGIME_KEYWORDS,
    legacy_activities_with_identifiers,
    legacy_activity_identifier,
    legacy_answers_from_json,
    legacy_catalog_json,
    legacy_check_regime,
    legacy_compare_activity,
    legacy_fill_placeholders,
    legacy_preview,
    legacy_regime_suggestion,
    legacy_scenarios_from_json,
)
from .legacy_report import legacy_report_html
from .legacy_scoring import (
    LEGACY_PROFILE_VERSION,
    LEGACY_SCREENING_NOT_REQUIRED,
    LEGACY_SCREENING_REQUIRED,
    REGIME_DSGVO,
    REGIME_JI,
    LegacyAnswer,
    LegacyScenario,
    LegacyThreshold,
    legacy_norm,
    legacy_prefill,
    legacy_profile,
    legacy_proposal,
    legacy_recommendation_text,
    legacy_reference,
    legacy_risk,
    legacy_risk_level,
    legacy_threshold,
)

__all__ = [
    "LEGACY_PROFILE_VERSION",
    "LEGACY_SCREENING_NOT_REQUIRED",
    "LEGACY_SCREENING_REQUIRED",
    "PLACEHOLDER_EMPTY",
    "REGIME_DSGVO",
    "REGIME_JI",
    "REGIME_KEYWORDS",
    "LegacyAnswer",
    "LegacyScenario",
    "LegacyThreshold",
    "legacy_activities_with_identifiers",
    "legacy_activity_identifier",
    "legacy_answers_from_json",
    "legacy_catalog_json",
    "legacy_check_regime",
    "legacy_compare_activity",
    "legacy_fill_placeholders",
    "legacy_norm",
    "legacy_prefill",
    "legacy_preview",
    "legacy_profile",
    "legacy_proposal",
    "legacy_recommendation_text",
    "legacy_reference",
    "legacy_regime_suggestion",
    "legacy_report_html",
    "legacy_risk",
    "legacy_risk_level",
    "legacy_scenarios_from_json",
    "legacy_threshold",
]

#: German constant names of earlier versions and their English successors.
_DEPRECATED = {
    "PFLICHT": ("LEGACY_SCREENING_REQUIRED", LEGACY_SCREENING_REQUIRED),
    "KEINE_PFLICHT": ("LEGACY_SCREENING_NOT_REQUIRED", LEGACY_SCREENING_NOT_REQUIRED),
}


def __getattr__(name: str) -> str:
    """Deprecated aliases; they keep their value and warn once per access."""
    if name in _DEPRECATED:
        replacement, value = _DEPRECATED[name]
        warnings.warn(
            f"auditcore_dataprotection.legacy.{name} ist veraltet; "
            f"stattdessen {replacement} verwenden.",
            DeprecationWarning,
            stacklevel=2,
        )
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
