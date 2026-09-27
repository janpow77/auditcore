"""Catalogue of the guidance-based planning for user interfaces (contract ``/1``)."""

from __future__ import annotations

from .. import guidance as g
from ..guidance.sources import guidance as section
from ..intermediate_body import PROFILES as PROCEDURES
from ..intermediate_body import escalation_ladder
from .profiles import LIBRARY

CONTRACT = "auditcore_sampling.guidance/1"

_COMMON = (
    "factor_profile",
    "confidence_level",
    "book_value",
    "anticipated_error_rate",
    "materiality_rate",
)
METHODS: tuple[dict[str, object], ...] = (
    {
        "id": g.SRS,
        "label": "Einfache Zufallsstichprobe",
        "section": "6.1.1.2",
        "formula": "n = (N × z × σ_e / (TE − AE))²",
        "fields": (*_COMMON, "population_size", "error_sd", "finite_population_correction"),
    },
    {
        "id": f"{g.SRS}_stratified",
        "label": "Einfache Zufallsstichprobe, geschichtet",
        "section": "6.1.2.2",
        "formula": "n = (N × z × σ_w / (TE − AE))², n_h = N_h / N × n",
        "fields": (*_COMMON, "strata", "finite_population_correction"),
    },
    {
        "id": g.DIFFERENCE,
        "label": "Differenzenschätzung",
        "section": "6.2.1.2",
        "formula": "n = (N × z × σ_e / (TE − AE))²",
        "fields": (*_COMMON, "population_size", "error_sd", "finite_population_correction"),
    },
    {
        "id": f"{g.DIFFERENCE}_stratified",
        "label": "Differenzenschätzung, geschichtet",
        "section": "6.2.2.2",
        "formula": "n = (N × z × σ_w / (TE − AE))², n_h = N_h / N × n",
        "fields": (*_COMMON, "strata", "finite_population_correction"),
    },
    {
        "id": g.MUS_STANDARD,
        "label": "MUS – Standardansatz",
        "section": "6.3.1.2",
        "formula": "n = (z × BV × σ_r / (TE − AE))², Hochwertschicht BV_i > BV / n",
        "fields": (*_COMMON, "error_rate_sd", "book_values"),
    },
    {
        "id": g.MUS_STRATIFIED,
        "label": "MUS – geschichtet",
        "section": "6.3.2.2",
        "formula": "n = (z × BV × σ_rw / (TE − AE))², n_h = BV_h / BV × n",
        "fields": (
            "factor_profile",
            "confidence_level",
            "anticipated_error_rate",
            "materiality_rate",
            "strata",
        ),
    },
    {
        "id": g.MUS_CONSERVATIVE,
        "label": "MUS – konservativer Ansatz",
        "section": "6.3.5.2",
        "formula": "n = BV × RF / (TE − AE × EF), SI = BV / n",
        "fields": _COMMON,
    },
    {
        "id": g.NONSTATISTICAL,
        "label": "Nicht-statistische Stichprobe (Mindestumfang)",
        "section": "6.4.3",
        "formula": "n ≥ Mindestanteil × N",
        "fields": ("rule", "population_size", "book_value", "assurance_level"),
    },
)
#: Table of the confidence levels offered per method (``None``: no confidence level).
_TABLE_OF: dict[str, str | None] = {g.MUS_CONSERVATIVE: "reliability", g.NONSTATISTICAL: None}
ASSURANCE_LABELS = {
    "works_well": "Funktioniert gut (Kategorie 1)",
    "works": "Funktioniert, Verbesserungen nötig (Kategorie 2)",
    "works_partially": "Funktioniert teilweise (Kategorie 3)",
    "does_not_work": "Funktioniert im Wesentlichen nicht (Kategorie 4)",
}


def _levels() -> dict[str, list[dict[str, float]]]:
    def rows(table: object) -> list[dict[str, float]]:
        items = sorted(table.items())  # type: ignore[attr-defined]
        return [{"level": level, "value": value} for level, value in items]

    return {"z": rows(g.Z_TABLE), "reliability": rows(g.RF_TABLE), "expansion": rows(g.EF_TABLE)}


def guidance_catalogue() -> dict[str, object]:
    """``GET /guidance/profiles``: methods, factor profiles, tables, rules and procedures."""
    methods = [
        {
            **m,
            "fields": list(m["fields"]),  # type: ignore[call-overload]
            "source": section(str(m["section"])),
            "confidence_table": _TABLE_OF.get(str(m["id"]), "z"),
        }
        for m in METHODS
    ]
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "status": g.GUIDANCE_STATUS,
        "status_label": g.GUIDANCE_STATUS_LABEL,
        "guidance": g.GUIDANCE,
        "materiality_rate": g.MATERIALITY_RATE,
        "methods": methods,
        "factor_profiles": [p.to_dict() for p in g.FACTOR_PROFILES.values()],
        "tables": _levels(),
        "nonstatistical_rules": [r.to_dict() for r in g.RULES.values()],
        "assurance_levels": [{"id": k, "label": v} for k, v in ASSURANCE_LABELS.items()],
        "procedures": [
            {**p.to_dict(), "ladder": list(escalation_ladder(p))} for p in PROCEDURES.values()
        ],
    }
