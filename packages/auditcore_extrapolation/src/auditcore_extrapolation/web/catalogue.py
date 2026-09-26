"""Methods, factor profiles and error classes as offered to user interfaces."""

from __future__ import annotations

from .. import __version__, _rf_table
from ..evaluation import MATERIALITY_RATE
from ..factors import PROFILES, RECOMMENDED_PROFILE, RF_ZERO_TABLE, Z_TABLE
from ..methods import METHODS
from ..sources import GUIDANCE, RER_TEMPLATE, cpr
from ._contract import CONTRACT, MAX_STRATA, MAX_UNITS

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
        },
        "methods": [m.to_dict() for m in METHODS.values()],
        "factor_profiles": [p.to_dict() for p in PROFILES.values()],
        "recommended_profile": RECOMMENDED_PROFILE,
        "confidence_levels": _levels(),
        "materiality": {"default": MATERIALITY_RATE, "maximum": MATERIALITY_RATE},
        "error_classes": [dict(c) for c in ERROR_CLASSES],
        "conclusions": [dict(c) for c in CONCLUSIONS],
        "limits": {"max_units": MAX_UNITS, "max_strata": MAX_STRATA},
    }
