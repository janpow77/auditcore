"""Types of Findings (ToF) 2021–2027 für Feststellungen der EFRE-Verwaltungsprüfungen.

Katalog der Kommissionstabelle, Zuordnung der Fehlerkennziffern der
Verwaltungsbehörde (Kennziffertabelle mit Schlüsselwortregeln und
Gold-plating-Kennzeichen) und Schlüsselwortregeln für nichtfinanzielle
Mängel – als versioniertes Profil mit Fingerabdruck, portiert aus
``modAKB_ToF.bas``.
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
from .zuordnung import (
    formal_zuordnen,
    katalog,
    kennziffer_normalisieren,
    standardprofil,
    zuordnen,
)

__version__ = "0.1.0"

__all__ = [
    "OHNE_KENNZIFFER",
    "STANDARDPROFIL",
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
    "Zuordnung",
    "formal_zuordnen",
    "katalog",
    "kategorie",
    "kennziffer_aus_kuerzungsgrund",
    "kennziffer_normalisieren",
    "kuerzungsgrund",
    "load_kuerzungsgruende",
    "load_profile",
    "profil_aus_dict",
    "standardprofil",
    "verfuegbare_profile",
    "zuordnen",
]
