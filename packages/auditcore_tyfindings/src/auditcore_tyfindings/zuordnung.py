"""Zuordnung von Fehlerkennziffern und nichtfinanziellen Mängeln zu ToF-Unterkategorien.

Portiert ``ToFZuordnen`` und ``ToFFormalZuordnen`` aus ``modAKB_ToF.bas``:

* Kennziffer: exakter Textvergleich in der Kennziffertabelle („1.1“ ≠ „1.10“).
  Bei mehrdeutigen Kennziffern gewinnt die erste Schlüsselwortregel, deren
  Suchwort in der klein geschriebenen Beschreibung vorkommt; sonst gilt die
  Unterkategorie der Tabelle; ohne sie bleibt der Beleg „nicht zugeordnet“.
* Gold-plating: Kennzeichen der Tabellenzeile, bei einem Regeltreffer mit
  „!GP“ zusätzlich gesetzt.
* Formal: erste Schlüsselwortregel mit Treffer in der Beschreibung.
"""

from __future__ import annotations

from functools import cache

from .errors import EingabeFehler
from .modell import (
    OHNE_KENNZIFFER,
    WEG_KENNZIFFER,
    WEG_NICHT_ZUGEORDNET,
    WEG_SCHLUESSELWORT,
    Schluesselwortregel,
    ToFEintrag,
    ToFProfil,
    Zuordnung,
    kategorie,
)
from .profil import STANDARDPROFIL, load_profile

_NICHT_ZUGEORDNET = Zuordnung(None, None, WEG_NICHT_ZUGEORDNET, False, None)


@cache
def standardprofil() -> ToFProfil:
    """Das Profil :data:`~auditcore_tyfindings.profil.STANDARDPROFIL` (einmal geladen)."""
    return load_profile(*STANDARDPROFIL)


def _profil(profil: ToFProfil | None) -> ToFProfil:
    return standardprofil() if profil is None else profil


def _text(wert: object, name: str) -> str:
    if not isinstance(wert, str):
        raise EingabeFehler(f"{name} ist als Text anzugeben, nicht als {type(wert).__name__}.")
    return wert


def kennziffer_normalisieren(kennziffer: str) -> str:
    """Schlüssel der Kennziffertabelle wie im VBA-Import (``ToKey``).

    Geschützte Leerzeichen werden zu Leerzeichen, Ränder abgeschnitten; leer,
    „-“ und „/“ werden zu „ohne Kennziffer“. Der Text selbst bleibt unverändert
    („1.10“ wird nicht zu „1.1“).
    """
    schluessel = _text(kennziffer, "Die Fehlerkennziffer").replace("\xa0", " ").strip()
    return OHNE_KENNZIFFER if schluessel in {"", "-", "/"} else schluessel


def _erster_treffer(
    regeln: tuple[Schluesselwortregel, ...], beschreibung: str
) -> Schluesselwortregel | None:
    text = beschreibung.lower()
    for regel in regeln:
        if regel.suchwort in text:
            return regel
    return None


def zuordnen(kennziffer: str, beschreibung: str = "", profil: ToFProfil | None = None) -> Zuordnung:
    """ToF-Unterkategorie einer Belegkürzung aus Fehlerkennziffer und Beschreibung."""
    gewaehlt = _profil(profil)
    eintrag = gewaehlt.kennziffern.get(kennziffer_normalisieren(kennziffer))
    text = _text(beschreibung, "Die Beschreibung")
    if eintrag is None:
        return _NICHT_ZUGEORDNET
    regel = _erster_treffer(eintrag.regeln, text) if eintrag.mehrdeutig else None
    if regel is not None:
        return Zuordnung(
            regel.tof,
            kategorie(regel.tof),
            WEG_SCHLUESSELWORT,
            eintrag.gold_plating or regel.gold_plating,
            regel.regel_id,
        )
    if eintrag.tof is not None:
        tof = eintrag.tof
        gold_plating = eintrag.gold_plating
        return Zuordnung(tof, kategorie(tof), WEG_KENNZIFFER, gold_plating, eintrag.regel_id)
    return Zuordnung(None, None, WEG_NICHT_ZUGEORDNET, eintrag.gold_plating, eintrag.regel_id)


def formal_zuordnen(beschreibung: str, profil: ToFProfil | None = None) -> Zuordnung:
    """ToF-Unterkategorie eines nichtfinanziellen Mangels über die Formalregeln."""
    regel = _erster_treffer(_profil(profil).formalregeln, _text(beschreibung, "Die Beschreibung"))
    if regel is None:
        return _NICHT_ZUGEORDNET
    return Zuordnung(regel.tof, kategorie(regel.tof), WEG_SCHLUESSELWORT, False, regel.regel_id)


def katalog(profil: ToFProfil | None = None) -> tuple[ToFEintrag, ...]:
    """Alle Unterkategorien der Kommissionstabelle in Katalogreihenfolge."""
    return _profil(profil).katalog
