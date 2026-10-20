"""Types of Findings (ToF) 2021–2027 für Feststellungen der EFRE-Verwaltungsprüfungen.

Katalog der Kommissionstabelle, Zuordnung der Fehlerkennziffern der
Verwaltungsbehörde (Kennziffertabelle mit Schlüsselwortregeln und
Gold-plating-Kennzeichen) und Schlüsselwortregeln für nichtfinanzielle
Mängel – als versioniertes Profil mit Fingerabdruck, portiert aus
``modAKB_ToF.bas``. Dazu das Regelwerk für den Abgleich der Übersicht über
die Verwaltungsüberprüfungen (Fallgruppen, Merkmale, Schwellen), portiert aus
``modAKB_Regeln.bas``.
"""

from __future__ import annotations

from .errors import EingabeFehler, ProfilFehler, TyFindingsFehler
from .kuerzungsgrund import (
    KuerzungsgrundEintrag,
    KuerzungsgrundTabelle,
    kennziffer_aus_kuerzungsgrund,
    kuerzungsgrund,
    load_kuerzungsgruende,
)
from .modell import (
    OHNE_KENNZIFFER,
    WEG_KENNZIFFER,
    WEG_NICHT_ZUGEORDNET,
    WEG_SCHLUESSELWORT,
    KennzifferEintrag,
    Schluesselwortregel,
    ToFEintrag,
    ToFProfil,
    Zuordnung,
    kategorie,
)
from .profil import STANDARDPROFIL, load_profile, profil_aus_dict, verfuegbare_profile
from .uebersichtsregeln import (
    DEFAULT_RULE_SET,
    OverviewRule,
    OverviewRuleSet,
    default_rule_set,
    load_overview_rules,
    match_rule,
    rule_set_from_dict,
    rules_of_area,
    threshold,
)
from .zuordnung import (
    formal_zuordnen,
    katalog,
    kennziffer_normalisieren,
    standardprofil,
    zuordnen,
)

__version__ = "0.3.0"

__all__ = [
    "OHNE_KENNZIFFER",
    "STANDARDPROFIL",
    "DEFAULT_RULE_SET",
    "WEG_KENNZIFFER",
    "WEG_NICHT_ZUGEORDNET",
    "WEG_SCHLUESSELWORT",
    "EingabeFehler",
    "KennzifferEintrag",
    "KuerzungsgrundEintrag",
    "KuerzungsgrundTabelle",
    "ProfilFehler",
    "Schluesselwortregel",
    "ToFEintrag",
    "ToFProfil",
    "TyFindingsFehler",
    "OverviewRule",
    "OverviewRuleSet",
    "Zuordnung",
    "formal_zuordnen",
    "katalog",
    "kategorie",
    "kennziffer_aus_kuerzungsgrund",
    "kennziffer_normalisieren",
    "kuerzungsgrund",
    "load_kuerzungsgruende",
    "load_profile",
    "load_overview_rules",
    "profil_aus_dict",
    "match_rule",
    "rules_of_area",
    "rule_set_from_dict",
    "threshold",
    "standardprofil",
    "default_rule_set",
    "verfuegbare_profile",
    "zuordnen",
]
