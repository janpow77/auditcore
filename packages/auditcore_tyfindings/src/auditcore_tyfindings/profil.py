"""Versionierte ToF-Profile laden, prüfen und mit Fingerabdruck versehen.

Ein Profil ist eine JSON-Ressource ``<id>-<version>.json`` in
:mod:`auditcore_tyfindings.profile_data`. Der Fingerabdruck ist der SHA-256
über das kanonische JSON des Profildokuments (wie in ``auditcore_risk``).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from auditcore_common.hashing import canonical_sha256
from auditcore_common.profiles import load_packaged_profile, packaged_profile_ids

from .errors import ProfilFehler
from .modell import KennzifferEintrag, Schluesselwortregel, ToFEintrag, ToFProfil

SCHEMA: Final = "auditcore_tyfindings.profile/1"
#: Profil, das :func:`auditcore_tyfindings.zuordnen` ohne ``profil`` verwendet.
#: Ein neues Profil ändert diesen Wert nur mit einer neuen Paketversion.
STANDARDPROFIL: Final = ("efre.tof_2021_2027", "2026.10.2")
_RESSOURCEN: Final = "auditcore_tyfindings.profile_data"
_SCHLUESSEL: Final = frozenset(
    {
        "schema",
        "id",
        "version",
        "status",
        "legal_status",
        "source",
        "open_decisions",
        "katalog",
        "kennziffern",
        "formalregeln",
        "derived_from",
    }
)

JsonObjekt = dict[str, object]


def fingerprint(daten: Mapping[str, object]) -> str:
    """SHA-256 des kanonischen JSON-Profildokuments."""
    return canonical_sha256(daten)


def _objekt(wert: object, wo: str) -> JsonObjekt:
    if not isinstance(wert, dict):
        raise ProfilFehler(f"{wo}: Objekt erwartet.")
    return wert


def _liste(daten: JsonObjekt, schluessel: str) -> list[object]:
    wert = daten.get(schluessel)
    if not isinstance(wert, list):
        raise ProfilFehler(f"'{schluessel}' muss eine Liste sein.")
    return wert


def _text(daten: JsonObjekt, schluessel: str, wo: str) -> str:
    wert = daten.get(schluessel)
    if not isinstance(wert, str) or not wert:
        raise ProfilFehler(f"{wo}: '{schluessel}' muss ein nicht leerer Text sein.")
    return wert


def _wahrheitswert(daten: JsonObjekt, schluessel: str, wo: str) -> bool:
    wert = daten.get(schluessel)
    if not isinstance(wert, bool):
        raise ProfilFehler(f"{wo}: '{schluessel}' muss true oder false sein.")
    return wert


def _katalog(daten: JsonObjekt) -> tuple[ToFEintrag, ...]:
    eintraege: list[ToFEintrag] = []
    for roh in _liste(daten, "katalog"):
        zeile = _objekt(roh, "Katalog")
        nummer = _text(zeile, "nummer", "Katalog")
        if "." not in nummer:
            raise ProfilFehler(f"Katalog: Nummer {nummer!r} ohne Kategorie.")
        eintraege.append(
            ToFEintrag(
                nummer=nummer,
                kategorie_bezeichnung=_text(zeile, "kategorie", nummer),
                original=_text(zeile, "original", nummer),
                kurzbezeichnung=_text(zeile, "kurzbezeichnung", nummer),
                kategorie_de=(
                    _text(zeile, "kategorie_de", nummer) if "kategorie_de" in zeile else None
                ),
            )
        )
    nummern = [e.nummer for e in eintraege]
    if len(set(nummern)) != len(nummern):
        raise ProfilFehler("Katalog: doppelte Nummer.")
    _kategorie_de_einheitlich(eintraege)
    return tuple(eintraege)


def _kategorie_de_einheitlich(eintraege: list[ToFEintrag]) -> None:
    """``kategorie_de`` steht in allen oder keinem Eintrag und ist je Kategorie gleich."""
    vorhanden = {e.kategorie_de is not None for e in eintraege}
    if len(vorhanden) > 1:
        raise ProfilFehler("Katalog: 'kategorie_de' fehlt in einzelnen Einträgen.")
    je_kategorie: dict[str, str | None] = {}
    for eintrag in eintraege:
        bisher = je_kategorie.setdefault(eintrag.kategorie, eintrag.kategorie_de)
        if bisher != eintrag.kategorie_de:
            raise ProfilFehler(
                f"Katalog: Kategorie {eintrag.kategorie} mit abweichender deutscher Bezeichnung."
            )


def _regel(roh: object, nummern: frozenset[str], wo: str) -> Schluesselwortregel:
    zeile = _objekt(roh, wo)
    suchwort = _text(zeile, "suchwort", wo)
    tof = _text(zeile, "tof", wo)
    if suchwort != suchwort.lower():
        raise ProfilFehler(f"{wo}: Suchwort {suchwort!r} ist nicht klein geschrieben.")
    if tof not in nummern:
        raise ProfilFehler(f"{wo}: Unterkategorie {tof!r} fehlt im Katalog.")
    gold_plating = zeile.get("gold_plating", False)
    if not isinstance(gold_plating, bool):
        raise ProfilFehler(f"{wo}: 'gold_plating' muss true oder false sein.")
    return Schluesselwortregel(_text(zeile, "id", wo), suchwort, tof, gold_plating)


def _kennziffer(roh: object, nummern: frozenset[str]) -> KennzifferEintrag:
    zeile = _objekt(roh, "Kennziffertabelle")
    code = _text(zeile, "kennziffer", "Kennziffertabelle")
    tof = zeile.get("tof")
    if tof is not None and (not isinstance(tof, str) or tof not in nummern):
        raise ProfilFehler(f"Kennziffer {code}: Unterkategorie {tof!r} fehlt im Katalog.")
    bemerkung = zeile.get("bemerkung", "")
    if not isinstance(bemerkung, str):
        raise ProfilFehler(f"Kennziffer {code}: 'bemerkung' muss Text sein.")
    return KennzifferEintrag(
        kennziffer=code,
        tof=tof,
        finanziell=_wahrheitswert(zeile, "finanziell", code),
        mehrdeutig=_wahrheitswert(zeile, "mehrdeutig", code),
        regeln=tuple(_regel(r, nummern, code) for r in _liste(zeile, "regeln")),
        gold_plating=_wahrheitswert(zeile, "gold_plating", code),
        bemerkung=bemerkung,
    )


def _kennziffern(daten: JsonObjekt, nummern: frozenset[str]) -> Mapping[str, KennzifferEintrag]:
    tabelle: dict[str, KennzifferEintrag] = {}
    for roh in _liste(daten, "kennziffern"):
        eintrag = _kennziffer(roh, nummern)
        if eintrag.kennziffer in tabelle:
            raise ProfilFehler(f"Kennziffer {eintrag.kennziffer} ist doppelt.")
        tabelle[eintrag.kennziffer] = eintrag
    return MappingProxyType(tabelle)


def _regel_ids_eindeutig(profil: ToFProfil) -> None:
    ids = [r.regel_id for r in profil.formalregeln]
    for eintrag in profil.kennziffern.values():
        ids += [eintrag.regel_id, *(r.regel_id for r in eintrag.regeln)]
    if len(set(ids)) != len(ids):
        raise ProfilFehler("Regelkennungen sind nicht eindeutig.")


def profil_aus_dict(daten: Mapping[str, object]) -> ToFProfil:
    """Profildokument prüfen und als :class:`ToFProfil` liefern."""
    roh = _objekt(dict(daten), "Profil")
    unbekannt = set(roh) - _SCHLUESSEL
    if unbekannt:
        raise ProfilFehler(f"Unbekannte Profilschlüssel: {sorted(unbekannt)}.")
    if roh.get("schema") != SCHEMA:
        raise ProfilFehler(f"Profilschema {SCHEMA} erwartet.")
    if "derived_from" in roh:
        herkunft = _objekt(roh["derived_from"], "derived_from")
        if herkunft.get("id") != roh.get("id"):
            raise ProfilFehler("'derived_from' muss auf dasselbe Profil verweisen.")
        _text(herkunft, "version", "derived_from")
    katalog = _katalog(roh)
    nummern = frozenset(e.nummer for e in katalog)
    entscheidungen = _liste(roh, "open_decisions")
    if not all(isinstance(e, str) for e in entscheidungen):
        raise ProfilFehler("'open_decisions' muss eine Liste von Texten sein.")
    profil = ToFProfil(
        id=_text(roh, "id", "Profil"),
        version=_text(roh, "version", "Profil"),
        status=_text(roh, "status", "Profil"),
        legal_status=_text(roh, "legal_status", "Profil"),
        quelle=MappingProxyType(dict(_objekt(roh.get("source"), "Quelle"))),
        katalog=katalog,
        kennziffern=_kennziffern(roh, nummern),
        formalregeln=tuple(_regel(r, nummern, "Formalregel") for r in _liste(roh, "formalregeln")),
        offene_entscheidungen=tuple(str(e) for e in entscheidungen),
        fingerprint=fingerprint(roh),
    )
    _regel_ids_eindeutig(profil)
    return profil


def verfuegbare_profile() -> tuple[tuple[str, str], ...]:
    """Verpackte ``(id, version)``-Paare."""
    return packaged_profile_ids(_RESSOURCEN)


def load_profile(profile_id: str, version: str) -> ToFProfil:
    """Ein ausdrücklich benanntes, verpacktes Profil in einer Version laden."""
    return load_packaged_profile(
        _RESSOURCEN,
        profile_id,
        version,
        parse=profil_aus_dict,
        identity=lambda p: (p.id, p.version),
        error=ProfilFehler,
        require_text=True,
        invalid_name="invalid_or_hidden",
    )
