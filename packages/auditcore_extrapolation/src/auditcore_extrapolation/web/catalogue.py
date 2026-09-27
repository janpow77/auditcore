"""Methods, factor profiles and error classes as offered to user interfaces."""

from __future__ import annotations

from .. import __version__, _rf_table
from ..confidence import SYSTEM_ASSESSMENT_LABELS, SYSTEM_ASSESSMENT_LEVELS
from ..evaluation import MATERIALITY_RATE
from ..factors import PROFILES, RECOMMENDED_PROFILE, RF_ZERO_TABLE, Z_TABLE
from ..methods import METHODS
from ..negative import APPROACHES as NEGATIVE_APPROACHES
from ..sources import GUIDANCE, RER_TEMPLATE, cpr, guidance
from ..subsampling import SUBSAMPLE_ESTIMATORS
from ._contract import CONTRACT, MAX_STRATA, MAX_UNITS
from ._design import MAX_PERIODS

LIBRARY = f"auditcore_extrapolation {__version__}"

ERROR_CLASSES: tuple[dict[str, str], ...] = (
    {
        "id": "random",
        "label": "Zufälliger Fehler",
        "description": "Wird auf die Grundgesamtheit hochgerechnet.",
    },
    {
        "id": "systemic",
        "label": "Systemischer Fehler (abgegrenzt)",
        "description": "Nur wenn der Gesamtumfang in der Grundgesamtheit abgegrenzt ist; geht mit "
        "dem abgegrenzten Betrag in die TER ein, nicht hochgerechnet. Sonst als zufälliger "
        "Fehler erfassen (Leitfaden, Anhang 1).",
    },
    {
        "id": "anomalous",
        "label": "Anomaler Fehler",
        "description": "Nachweislich nicht repräsentativ, nur mit Begründung; nicht hochgerechnet. "
        "Nicht korrigiert: Teil der TER; korrigiert: nicht Teil der TER (Leitfaden, Anhang 6).",
    },
)

CONCLUSIONS: tuple[dict[str, str], ...] = (
    {"id": "material", "label": "Wesentlicher Fehler"},
    {"id": "not_material", "label": "Kein wesentlicher Fehler"},
    {"id": "inconclusive", "label": "Nicht schlüssig – weitere Prüfungshandlungen"},
)


DESIGNS: tuple[dict[str, str], ...] = (
    {"id": "single", "label": "Ein Zeitraum", "source": guidance("6.1–6.4")},
    {
        "id": "periods",
        "label": "Mehrere Zeiträume des Geschäftsjahres",
        "source": guidance("6.1.3, 6.2.3, 6.3.3, 6.3.4, 6.4.9, 7.3; Anhang 2"),
    },
    {"id": "groups", "label": "Gruppe von Programmen", "source": guidance("7.8")},
)


ATTRIBUTE_APPROACHES: tuple[dict[str, str], ...] = (
    {
        "id": "normal",
        "label": "Merkmalsstichprobe (Normalapproximation)",
        "source": guidance("7.9.3–7.9.5"),
    },
    {
        "id": "discovery",
        "label": "Discovery-Stichprobe (exakte Binomialgrenze)",
        "source": guidance("7.9.6"),
    },
    {
        "id": "stop_or_go",
        "label": "Stop-or-go-Stichprobe (exakte Binomialgrenze)",
        "source": guidance("7.9.6"),
    },
)


def _system_assessment() -> list[dict[str, object]]:
    return [
        {
            "category": category,
            "label": SYSTEM_ASSESSMENT_LABELS[category],
            "confidence_level": level,
        }
        for category, level in SYSTEM_ASSESSMENT_LEVELS.items()
    ]


def _levels() -> dict[str, list[float]]:
    return {
        "z": sorted(Z_TABLE),
        "mus.conservative": sorted(set(RF_ZERO_TABLE) & set(_rf_table.LEVELS)),
    }


def catalogue() -> dict[str, object]:
    """``GET /profiles``: everything a form needs, no method preselected."""
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "sources": {
            "guidance": GUIDANCE,
            "rer_template": RER_TEMPLATE,
            "ter": cpr("2 Nr. 35"),
            "rer": cpr("2 Nr. 36"),
            "non_statistical": cpr("79 Abs. 2"),
            "periods": guidance("7.3"),
            "subsampling": guidance("7.6, 6.5.3"),
            "recalculation": guidance("7.7"),
            "system_assessment": guidance("3.2.1"),
            "groups": guidance("7.8"),
            "attributes": guidance("7.9"),
            "negative_units": guidance("4.6"),
            "exclusion": guidance("7.10"),
        },
        "methods": [m.to_dict() for m in METHODS.values()],
        "factor_profiles": [p.to_dict() for p in PROFILES.values()],
        "recommended_profile": RECOMMENDED_PROFILE,
        "confidence_levels": _levels(),
        "materiality": {"default": MATERIALITY_RATE, "maximum": MATERIALITY_RATE},
        "error_classes": [dict(c) for c in ERROR_CLASSES],
        "conclusions": [dict(c) for c in CONCLUSIONS],
        "designs": [dict(d) for d in DESIGNS],
        "subsample_estimators": [
            {"id": key, "label": label} for key, label in SUBSAMPLE_ESTIMATORS.items()
        ],
        "system_assessment": _system_assessment(),
        "attribute_approaches": [dict(a) for a in ATTRIBUTE_APPROACHES],
        "negative_approaches": [
            {"id": key, "label": label} for key, label in NEGATIVE_APPROACHES.items()
        ],
        "limits": {"max_units": MAX_UNITS, "max_strata": MAX_STRATA, "max_periods": MAX_PERIODS},
    }
