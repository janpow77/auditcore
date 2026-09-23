"""
Red-Flag-Engine (Beleg-Ebene) — Umstellung auf auditcore_risk.

Ersetzt ``backend/app/pipeline/red_flags.py`` in riskanalysis (und inhaltsgleich
``backend/app/verwk/pipeline/red_flags.py`` in flowinvoice). Die Mechanik und
alle Gewichte, Schwellen und Muster kommen aus dem quellengebundenen Profil
``riskanalysis.legacy`` in Version ``b5c523bf7eaa`` (exakte Reproduktion von
riskanalysis@b5c523b). RF10–RF12 bleiben [deskriptiv]: keine Fehlerquoten,
nie neben der 2-%-Wesentlichkeit interpretieren.

Voraussetzung (requirements.txt):
    auditcore_risk[fuzzy,pandas]==0.2.0
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from auditcore_risk import identifier_missing, load_profile, name_similarity
from auditcore_risk.frame import compute_red_flags as _compute
from auditcore_risk.frame import red_flag_summary as _summary

PROFILE = load_profile("riskanalysis.legacy", "b5c523bf7eaa")

RED_FLAG_LABELS = {rule.code: rule.label for rule in PROFILE.rules}
RED_FLAG_CODES = [rule.code for rule in PROFILE.rules]
VERGABE_SCHWELLEN = list(PROFILE.rule("RF02").params["thresholds"]["static"])
RF08_BAGATELLGRENZE = float(PROFILE.rule("RF08").params["amount_gt"])


def _hat_echte_vergabe(vergabenummer: pd.Series) -> pd.Series:
    """True, wenn eine echte Vergabe-Kennung vorliegt (Regel RF08 des Profils)."""
    rule = PROFILE.rule("RF08")
    return vergabenummer.map(lambda v: not identifier_missing(rule, v)).astype(bool)


def _name_match(name_ben: str, name_emp: str) -> float:
    """Ähnlichkeit Begünstigter ↔ Auftragnehmer (Regel RF09 des Profils)."""
    return name_similarity(PROFILE.rule("RF09"), name_ben, name_emp)


def compute_red_flags(valid: pd.DataFrame) -> pd.DataFrame:
    """Ergänzt die gültigen Belege um Red-Flag-bool-Spalten und ``red_flag_codes``."""
    return _compute(valid, PROFILE)


def red_flag_summary(valid_rf: pd.DataFrame) -> list[dict[str, Any]]:
    """Aggregiert die Red-Flag-Treffer für die Übersicht."""
    return _summary(valid_rf, PROFILE)
