"""Versionierte Tabelle: Kürzungsgrund der Beleglisten → Fehlerkennziffer.

Die Schlüssel stammen aus den Beleglisten der Zwischengeschalteten Stelle.

Die Tabelle ist bewusst fast leer. Sicher bekannt ist nur der Schlüssel „0“
(kein Kürzungsgrund, also keine Fehlerkennziffer). Die übrigen Schlüssel sind
als bekannt, aber noch nicht zugeordnet geführt (Status ``offen``); ihre
Fehlerkennziffer ist **vom Fachbereich zu befüllen** und wird hier nicht
erfunden. Eine Befüllung erscheint als neue Tabellenversion.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import Final, Literal

from auditcore_common.profiles import load_packaged_profile

from .errors import EingabeFehler, ProfilFehler
from .profil import fingerprint

SCHEMA: Final = "auditcore_tyfindings.kuerzungsgrund/1"
STANDARDTABELLE: Final = ("efre.kuerzungsgrund_zs", "2026.10.1")
_RESSOURCEN: Final = "auditcore_tyfindings.kuerzungsgrund_data"
_STATUS: Final = frozenset({"kein_kuerzungsgrund", "offen", "zugeordnet"})

KuerzungsgrundStatus = Literal["kein_kuerzungsgrund", "offen", "zugeordnet"]


@dataclass(frozen=True)
class KuerzungsgrundEintrag:
    """Ein Schlüssel der Belegliste; ``kennziffer`` nur bei Status ``zugeordnet``."""

    schluessel: str
    status: KuerzungsgrundStatus
    kennziffer: str | None
    bemerkung: str


@dataclass(frozen=True)
class KuerzungsgrundTabelle:
    """Versionierte Schlüsseltabelle mit Fingerabdruck."""

    id: str
    version: str
    status: str
    eintraege: Mapping[str, KuerzungsgrundEintrag]
    fingerprint: str


def _eintrag(roh: object) -> KuerzungsgrundEintrag:
    if not isinstance(roh, dict):
        raise ProfilFehler("Kürzungsgrund: Objekt erwartet.")
    schluessel, status = roh.get("schluessel"), roh.get("status")
    kennziffer, bemerkung = roh.get("kennziffer"), roh.get("bemerkung", "")
    if not isinstance(schluessel, str) or status not in _STATUS or not isinstance(bemerkung, str):
        raise ProfilFehler(f"Kürzungsgrund {schluessel!r}: Schlüssel oder Status ungültig.")
    if (status == "zugeordnet") != isinstance(kennziffer, str):
        raise ProfilFehler(f"Kürzungsgrund {schluessel}: Kennziffer nur bei Status zugeordnet.")
    return KuerzungsgrundEintrag(schluessel, status, kennziffer, bemerkung)


def tabelle_aus_dict(daten: Mapping[str, object]) -> KuerzungsgrundTabelle:
    """Tabellendokument prüfen und als :class:`KuerzungsgrundTabelle` liefern."""
    roh = dict(daten)
    eintraege = roh.get("eintraege")
    if roh.get("schema") != SCHEMA or not isinstance(eintraege, list):
        raise ProfilFehler(f"Tabellenschema {SCHEMA} mit Liste 'eintraege' erwartet.")
    tabelle: dict[str, KuerzungsgrundEintrag] = {}
    for eintrag in map(_eintrag, eintraege):
        if eintrag.schluessel in tabelle:
            raise ProfilFehler(f"Kürzungsgrund {eintrag.schluessel} ist doppelt.")
        tabelle[eintrag.schluessel] = eintrag
    return KuerzungsgrundTabelle(
        id=str(roh.get("id")),
        version=str(roh.get("version")),
        status=str(roh.get("status")),
        eintraege=MappingProxyType(tabelle),
        fingerprint=fingerprint(roh),
    )


def load_kuerzungsgruende(tabelle_id: str, version: str) -> KuerzungsgrundTabelle:
    """Eine ausdrücklich benannte, verpackte Tabellenversion laden."""
    return load_packaged_profile(
        _RESSOURCEN,
        tabelle_id,
        version,
        parse=tabelle_aus_dict,
        identity=lambda t: (t.id, t.version),
        error=ProfilFehler,
        require_text=True,
        invalid_name="invalid_or_hidden",
    )


@cache
def standardtabelle() -> KuerzungsgrundTabelle:
    """Die Tabelle :data:`STANDARDTABELLE` (einmal geladen)."""
    return load_kuerzungsgruende(*STANDARDTABELLE)


def kuerzungsgrund(
    schluessel: str, tabelle: KuerzungsgrundTabelle | None = None
) -> KuerzungsgrundEintrag | None:
    """Eintrag zum Schlüssel (exakter Text nach Abschneiden der Ränder) oder ``None``."""
    if not isinstance(schluessel, str):
        raise EingabeFehler("Der Kürzungsgrund ist als Text anzugeben.")
    gewaehlt = standardtabelle() if tabelle is None else tabelle
    return gewaehlt.eintraege.get(schluessel.strip())


def kennziffer_aus_kuerzungsgrund(
    schluessel: str, tabelle: KuerzungsgrundTabelle | None = None
) -> str | None:
    """Fehlerkennziffer zum Kürzungsgrund oder ``None``.

    ``None`` heißt: kein Kürzungsgrund („0“), Zuordnung noch offen (vom
    Fachbereich zu befüllen) oder Schlüssel unbekannt. Die Fälle trennt
    :func:`kuerzungsgrund` über ``status``.
    """
    eintrag = kuerzungsgrund(schluessel, tabelle)
    return None if eintrag is None else eintrag.kennziffer
