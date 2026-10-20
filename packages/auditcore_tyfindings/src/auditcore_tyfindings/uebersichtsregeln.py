"""Versioniertes Regelwerk für den Abgleich der Übersicht über die Verwaltungsüberprüfungen.

Fallgruppen der Kürzungsbeschreibungen, Merkmale (Unregelmäßigkeit, Betrug,
Vergabe, noch ausstehende Abhilfe, offene Angaben der Zwischengeschalteten
Stelle), Themen nichtfinanzieller Feststellungen und Schwellen – portiert aus
``modAKB_Regeln.bas`` (AKB-Auswertung 1.8.1, Funktion ``RegelnStandard``) und
von der Prüfbehörde am 20.10.2026 fachlich bestätigt.

Eine Regel trifft, wenn die Kennziffer passt (falls angegeben), eines der
Stichwörter vorkommt (falls angegeben), eines der Zusatzwörter vorkommt (falls
angegeben) und keines der Ausschlusswörter. Stichwörter sind Teilzeichenfolgen
des kleingeschriebenen Textes; ``[wort]`` verlangt das ganze Wort. Kennziffern
werden exakt verglichen, ``1.*`` steht für alle Kennziffern der Kategorie 1.
Die erste zutreffende Regel eines Bereichs gewinnt.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from typing import Final

from auditcore_common.profiles import load_packaged_profile

from .errors import EingabeFehler, ProfilFehler
from .profil import fingerprint

SCHEMA: Final = "auditcore_tyfindings.uebersichtsregeln/1"
DEFAULT_RULE_SET: Final = ("efre.uebersicht_vue", "2026.10.1")
_RESSOURCEN: Final = "auditcore_tyfindings.uebersichtsregeln_data"
BEREICHE: Final = frozenset(
    {
        "FALLGRUPPE",
        "UR",
        "BETRUG",
        "VERGABE",
        "NF_FINANZIELL",
        "ABHILFE_KUENFTIG",
        "NF_THEMA",
        "ZGS_OFFEN",
        "SCHWELLE",
    }
)
_BEWERTUNGEN: Final = frozenset({"", "Fehler", "kein Fehler"})
_SATZZEICHEN: Final = (",", ".", ";", ":", "/", "(", ")", "-", "!", "?", '"')


@dataclass(frozen=True)
class OverviewRule:
    """Eine Regel eines Bereichs; ``wert`` nur im Bereich ``SCHWELLE``."""

    id: str
    bereich: str
    name: str
    stichwoerter: tuple[str, ...]
    zusatz: tuple[str, ...]
    ausschluss: tuple[str, ...]
    kennziffern: tuple[str, ...]
    ausgenommene_kennziffern: tuple[str, ...]
    wert: float | str | None
    bewertung: str
    tof: str
    quelle: str
    status: str


@dataclass(frozen=True)
class OverviewRuleSet:
    """Versioniertes Regelwerk mit Fingerabdruck; Regeln in fachlicher Reihenfolge."""

    id: str
    version: str
    status: str
    regeln: tuple[OverviewRule, ...]
    fingerprint: str


def _text_list(roh: Mapping[str, object], feld: str, regel_id: str) -> tuple[str, ...]:
    werte = roh.get(feld, [])
    if not isinstance(werte, list) or not all(isinstance(w, str) and w.strip() for w in werte):
        raise ProfilFehler(f"Regel {regel_id}: '{feld}' muss eine Liste nichtleerer Texte sein.")
    return tuple(w.strip().lower() for w in werte)


def _text_field(roh: Mapping[str, object], feld: str, regel_id: str) -> str:
    wert = roh.get(feld, "")
    if not isinstance(wert, str):
        raise ProfilFehler(f"Regel {regel_id}: '{feld}' muss ein Text sein.")
    return wert


def _value(roh: Mapping[str, object], bereich: str, regel_id: str) -> float | str | None:
    wert = roh.get("wert")
    if bereich == "SCHWELLE":
        if isinstance(wert, bool) or not isinstance(wert, (int, float, str)):
            raise ProfilFehler(f"Regel {regel_id}: Schwelle ohne Zahl oder Text.")
        return float(wert) if isinstance(wert, (int, float)) else wert
    if wert is not None:
        raise ProfilFehler(f"Regel {regel_id}: 'wert' nur im Bereich SCHWELLE.")
    return None


def _rule(roh: object) -> OverviewRule:
    if not isinstance(roh, dict):
        raise ProfilFehler("Regel: Objekt erwartet.")
    regel_id, bereich = roh.get("id"), roh.get("bereich")
    if not isinstance(regel_id, str) or not isinstance(bereich, str) or bereich not in BEREICHE:
        raise ProfilFehler(f"Regel {regel_id!r}: Kennung oder Bereich ungültig.")
    regel = OverviewRule(
        id=regel_id,
        bereich=bereich,
        name=_text_field(roh, "name", regel_id),
        stichwoerter=_text_list(roh, "stichwoerter", regel_id),
        zusatz=_text_list(roh, "zusatz", regel_id),
        ausschluss=_text_list(roh, "ausschluss", regel_id),
        kennziffern=_text_list(roh, "kennziffern", regel_id),
        ausgenommene_kennziffern=_text_list(roh, "ausgenommene_kennziffern", regel_id),
        wert=_value(roh, bereich, regel_id),
        bewertung=_text_field(roh, "bewertung", regel_id),
        tof=_text_field(roh, "tof", regel_id),
        quelle=_text_field(roh, "quelle", regel_id),
        status=_text_field(roh, "status", regel_id),
    )
    _check_content(regel)
    return regel


def _check_content(regel: OverviewRule) -> None:
    if not regel.name.strip():
        raise ProfilFehler(f"Regel {regel.id}: Name fehlt.")
    if regel.bewertung not in _BEWERTUNGEN:
        raise ProfilFehler(f"Regel {regel.id}: Bewertung {regel.bewertung!r} unbekannt.")
    if regel.bereich != "SCHWELLE" and not (regel.stichwoerter or regel.kennziffern):
        raise ProfilFehler(f"Regel {regel.id}: weder Stichwörter noch Kennziffern.")


def rule_set_from_dict(daten: Mapping[str, object]) -> OverviewRuleSet:
    """Regelwerksdokument prüfen und als :class:`OverviewRuleSet` liefern."""
    roh = dict(daten)
    regeln = roh.get("regeln")
    if roh.get("schema") != SCHEMA or not isinstance(regeln, list):
        raise ProfilFehler(f"Regelwerksschema {SCHEMA} mit Liste 'regeln' erwartet.")
    geladen = tuple(map(_rule, regeln))
    kennungen = [r.id for r in geladen]
    if len(set(kennungen)) != len(kennungen):
        raise ProfilFehler("Regelkennungen sind doppelt.")
    return OverviewRuleSet(
        id=str(roh.get("id")),
        version=str(roh.get("version")),
        status=str(roh.get("status")),
        regeln=geladen,
        fingerprint=fingerprint(roh),
    )


def load_overview_rules(regelwerk_id: str, version: str) -> OverviewRuleSet:
    """Eine ausdrücklich benannte, verpackte Regelwerksversion laden."""
    return load_packaged_profile(
        _RESSOURCEN,
        regelwerk_id,
        version,
        parse=rule_set_from_dict,
        identity=lambda w: (w.id, w.version),
        error=ProfilFehler,
        require_text=True,
        invalid_name="invalid_or_hidden",
    )


@cache
def default_rule_set() -> OverviewRuleSet:
    """Das Regelwerk :data:`DEFAULT_RULE_SET` (einmal geladen)."""
    return load_overview_rules(*DEFAULT_RULE_SET)


def _normalize(text: str) -> str:
    return text.replace("\r", " ").replace("\n", " ").replace("\xa0", " ").lower()


def _word_text(text: str) -> str:
    for zeichen in _SATZZEICHEN:
        text = text.replace(zeichen, " ")
    return f" {text} "


def _word_matches(text: str, woerter: str, stichwort: str) -> bool:
    if stichwort.startswith("[") and stichwort.endswith("]"):
        return f" {stichwort[1:-1]} " in woerter
    return stichwort in text


def _any_matches(text: str, woerter: str, liste: Sequence[str]) -> bool:
    return any(_word_matches(text, woerter, w) for w in liste)


def _code_matches(kennziffer: str, liste: Sequence[str]) -> bool:
    for muster in liste:
        if muster.endswith("*"):
            if kennziffer and kennziffer.startswith(muster[:-1]):
                return True
        elif kennziffer == muster:
            return True
    return False


def _matches(regel: OverviewRule, text: str, woerter: str, kennziffer: str) -> bool:
    if regel.kennziffern and not _code_matches(kennziffer, regel.kennziffern):
        return False
    if _code_matches(kennziffer, regel.ausgenommene_kennziffern):
        return False
    if regel.stichwoerter and not _any_matches(text, woerter, regel.stichwoerter):
        return False
    if regel.zusatz and not _any_matches(text, woerter, regel.zusatz):
        return False
    return not _any_matches(text, woerter, regel.ausschluss)


def rules_of_area(
    bereich: str, regelwerk: OverviewRuleSet | None = None
) -> tuple[OverviewRule, ...]:
    """Alle Regeln eines Bereichs in fachlicher Reihenfolge."""
    if bereich not in BEREICHE:
        raise EingabeFehler(f"Bereich {bereich!r} unbekannt.")
    gewaehlt = default_rule_set() if regelwerk is None else regelwerk
    return tuple(r for r in gewaehlt.regeln if r.bereich == bereich)


def match_rule(
    bereich: str,
    text: str,
    kennziffer: str = "",
    regelwerk: OverviewRuleSet | None = None,
) -> OverviewRule | None:
    """Erste zutreffende Regel des Bereichs für Text und Kennziffer, sonst ``None``."""
    if not isinstance(text, str) or not isinstance(kennziffer, str):
        raise EingabeFehler("Text und Kennziffer sind als Text anzugeben.")
    normal = _normalize(text)
    woerter = _word_text(normal)
    for regel in rules_of_area(bereich, regelwerk):
        if regel.bereich != "SCHWELLE" and _matches(regel, normal, woerter, kennziffer.strip()):
            return regel
    return None


def threshold(name: str, regelwerk: OverviewRuleSet | None = None) -> float | str:
    """Wert der Schwelle ``name`` (Groß- und Kleinschreibung egal)."""
    for regel in rules_of_area("SCHWELLE", regelwerk):
        if regel.name.upper() == name.upper() and regel.wert is not None:
            return regel.wert
    raise ProfilFehler(f"Schwelle {name!r} ist im Regelwerk nicht enthalten.")
