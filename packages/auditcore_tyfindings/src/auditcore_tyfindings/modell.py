"""Unveränderliche Datenmodelle: Katalog, Regeln, Profil und Ergebnis einer Zuordnung."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal

#: Zuordnungsweg „Kennziffer“: Unterkategorie aus der Kennziffertabelle.
WEG_KENNZIFFER: Final = "Kennziffer"
#: Zuordnungsweg „Schlüsselwort“: Treffer einer Schlüsselwort- oder Formalregel.
WEG_SCHLUESSELWORT: Final = "Schlüsselwort"
#: Zuordnungsweg und VBA-Anzeigetext, wenn keine Unterkategorie gefunden wurde.
WEG_NICHT_ZUGEORDNET: Final = "nicht zugeordnet"
#: Schlüssel der Kennziffertabelle für Belege ohne Fehlerkennziffer.
OHNE_KENNZIFFER: Final = "ohne Kennziffer"

Zuordnungsweg = Literal["Kennziffer", "Schlüsselwort", "nicht zugeordnet"]


def kategorie(unterkategorie: str | None) -> str | None:
    """ToF-Kategorie einer Unterkategorie: der Text vor dem ersten Punkt („4.16“ → „4“).

    Ohne Punkt (auch ``None`` oder „nicht zugeordnet“) gibt es keine Kategorie
    (``None``); die VBA-Ausgabe schreibt dann eine leere Zelle.
    """
    if unterkategorie is None or "." not in unterkategorie:
        return None
    return unterkategorie.split(".", 1)[0]


@dataclass(frozen=True)
class ToFEintrag:
    """Eine Unterkategorie der Kommissionstabelle „Types of findings 2021–2027“."""

    nummer: str
    kategorie_bezeichnung: str
    original: str
    kurzbezeichnung: str

    @property
    def kategorie(self) -> str:
        """Nummer der Kategorie („4.16“ → „4“)."""
        return self.nummer.split(".", 1)[0]


@dataclass(frozen=True)
class Schluesselwortregel:
    """Suchwort (klein geschrieben, Teilzeichenkette) → Unterkategorie; erster Treffer gewinnt."""

    regel_id: str
    suchwort: str
    tof: str
    gold_plating: bool = False


@dataclass(frozen=True)
class KennzifferEintrag:
    """Zeile der Kennziffertabelle (VBA ``ToFStandard``)."""

    kennziffer: str
    tof: str | None
    finanziell: bool
    mehrdeutig: bool
    regeln: tuple[Schluesselwortregel, ...]
    gold_plating: bool
    bemerkung: str

    @property
    def regel_id(self) -> str:
        """Kennung der Tabellenzeile im Ergebnis."""
        return f"kennziffer:{self.kennziffer}"


@dataclass(frozen=True)
class Zuordnung:
    """Ergebnis einer Zuordnung; ``tof_unterkategorie`` ist ``None``, wenn nicht zugeordnet."""

    tof_unterkategorie: str | None
    tof_kategorie: str | None
    zuordnungsweg: Zuordnungsweg
    gold_plating: bool
    regel_id: str | None

    @property
    def zugeordnet(self) -> bool:
        """True, wenn eine Unterkategorie gefunden wurde."""
        return self.tof_unterkategorie is not None

    @property
    def anzeige(self) -> str:
        """Unterkategorie wie in der VBA-Ausgabe („nicht zugeordnet“ statt ``None``)."""
        return self.tof_unterkategorie or WEG_NICHT_ZUGEORDNET


@dataclass(frozen=True)
class ToFProfil:
    """Versioniertes Profil: Katalog, Kennziffertabelle und Formalregeln mit Fingerabdruck."""

    id: str
    version: str
    status: str
    legal_status: str
    quelle: Mapping[str, object]
    katalog: tuple[ToFEintrag, ...]
    kennziffern: Mapping[str, KennzifferEintrag]
    formalregeln: tuple[Schluesselwortregel, ...]
    offene_entscheidungen: tuple[str, ...]
    fingerprint: str

    @property
    def referenz(self) -> dict[str, str]:
        """Identität für Ergebnisprotokolle."""
        return {"id": self.id, "version": self.version, "fingerprint": self.fingerprint}

    def eintrag(self, nummer: str) -> ToFEintrag | None:
        """Katalogeintrag zur Nummer (exakter Textvergleich) oder ``None``."""
        for eintrag in self.katalog:
            if eintrag.nummer == nummer:
                return eintrag
        return None
