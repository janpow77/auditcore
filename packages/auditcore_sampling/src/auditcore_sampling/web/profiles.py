"""Named method profiles as offered to user interfaces (framework-free).

The catalogue is derived from :data:`auditcore_sampling.METHODS`; it adds
labels, formulas and parameter descriptions but never a method of its own.
"""

from __future__ import annotations

from .. import __version__
from ..sizes import METHODS, MUS_DECISION, RECOMMENDED_MUS_METHOD, Method

LIBRARY = f"auditcore_sampling {__version__}"

_LABELS = {
    "portal.mus_poisson": "MUS – Poisson-Zuverlässigkeitsfaktoren (audit-portal)",
    "flowstat.mus_z_attribute": "MUS – z-Attributformel (FlowStat, abgelöst)",
    "flowstat.srs_normal": "Einfache Zufallsstichprobe – Normalapproximation (FlowStat)",
    "portal.srs_normal": "Einfache Zufallsstichprobe – Normalapproximation (audit-portal)",
}
_FORMULAS = {
    "portal.mus_poisson": "n = ⌈RF · V / max(M − V · r, M / 2)⌉, J = V / n",
    "flowstat.mus_z_attribute": "n = ⌈V · z² · (1 − r) / (M² + z² · (1 − r))⌉, J = V / n",
    "flowstat.srs_normal": "n₀ = z² · p · (1 − p) / e², n = min(⌈n₀ / (1 + (n₀ − 1) / N)⌉, N)",
    "portal.srs_normal": "n₀ = z² · p · (1 − p) / e², n = min(⌈n₀ / (1 + (n₀ − 1) / N)⌉, N)",
}
_DEFAULT_VARIANT = {"portal.mus_poisson": "portal", "flowstat.mus_z_attribute": "flowstat"}

MUS_PARAMETERS: tuple[dict[str, object], ...] = (
    {"key": "population_value", "label": "Wert der Grundgesamtheit (V)", "unit": "EUR",
     "type": "number", "minimum": 0},
    {"key": "materiality", "label": "Wesentlichkeit (M)", "unit": "EUR",
     "type": "number", "exclusive_minimum": 0},
    {"key": "expected_error_rate", "label": "Erwartete Fehlerrate (r)", "unit": "Anteil",
     "type": "number", "minimum": 0, "exclusive_maximum": 1},
    {"key": "confidence_level", "label": "Konfidenzniveau", "unit": "Anteil", "type": "choice"},
)
SRS_PARAMETERS: tuple[dict[str, object], ...] = (
    {"key": "population_size", "label": "Umfang der Grundgesamtheit (N)", "unit": "Stück",
     "type": "integer", "minimum": 1},
    {"key": "margin_of_error", "label": "Fehlertoleranz (e)", "unit": "Anteil",
     "type": "number", "exclusive_minimum": 0, "exclusive_maximum": 1},
    {"key": "expected_proportion", "label": "Erwarteter Anteil (p)", "unit": "Anteil",
     "type": "number", "minimum": 0, "maximum": 1, "suggested": 0.5},
    {"key": "confidence_level", "label": "Konfidenzniveau", "unit": "Anteil", "type": "choice"},
)

SELECTION_VARIANTS: tuple[dict[str, str], ...] = (
    {
        "id": "portal",
        "label": "Nur positive Werte, Treffer einmalig (audit-portal)",
        "description": "Null-, fehlende und negative Werte werden getrennt ausgewiesen; "
        "mehrfach getroffene Positionen erscheinen einmal.",
    },
    {
        "id": "flowstat",
        "label": "Kumulierte Summe über alle Werte (FlowStat)",
        "description": "Negative Werte gehen in die kumulierte Summe ein; mehrfach "
        "getroffene Positionen werden je Treffer gezählt.",
    },
)
ALLOCATION_METHODS: tuple[dict[str, str], ...] = (
    {"id": "proportional", "label": "Proportional zum Schichtumfang",
     "formula": "n_h = min(⌈n · N_h / N⌉, N_h)"},
    {"id": "equal", "label": "Gleich verteilt", "formula": "n_h = min(⌈n / H⌉, N_h)"},
)


def _levels(chosen: Method) -> list[dict[str, float]]:
    return [{"level": level, "factor": factor} for level, factor in sorted(chosen.factors.items())]


def method_profile(chosen: Method) -> dict[str, object]:
    """UI description of one library method."""
    parameters = MUS_PARAMETERS if chosen.kind == "mus" else SRS_PARAMETERS
    return {
        "id": chosen.id,
        "kind": chosen.kind,
        "label": _LABELS[chosen.id],
        "status": chosen.status,
        "recommended": chosen.id == RECOMMENDED_MUS_METHOD,
        "source": chosen.source,
        "note": chosen.note,
        "formula": _FORMULAS[chosen.id],
        "confidence_levels": _levels(chosen),
        "parameters": [dict(p) for p in parameters],
        "selection": "mus" if chosen.kind == "mus" else "srs",
        "default_variant": _DEFAULT_VARIANT.get(chosen.id),
    }


def catalogue() -> dict[str, object]:
    """All method profiles, selection variants and allocation methods."""
    ordered = sorted(METHODS.values(), key=lambda m: (m.kind, m.id != RECOMMENDED_MUS_METHOD, m.id))
    return {
        "library": LIBRARY,
        "recommended": {"mus": RECOMMENDED_MUS_METHOD},
        "decision": dict(MUS_DECISION),
        "methods": [method_profile(m) for m in ordered],
        "selection_variants": [dict(v) for v in SELECTION_VARIANTS],
        "allocation_methods": [dict(a) for a in ALLOCATION_METHODS],
    }
