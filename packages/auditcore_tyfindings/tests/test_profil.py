"""Katalog, Profilversion, Fingerabdruck und Profilprüfung."""

from __future__ import annotations

import copy
import json
from collections import Counter
from importlib import resources

import pytest

from auditcore_tyfindings import (
    STANDARDPROFIL,
    ProfilFehler,
    katalog,
    kategorie,
    load_profile,
    profil_aus_dict,
    standardprofil,
    verfuegbare_profile,
)

FINGERPRINT = "149acf962219ec306a83615e56e42500691dd56aa08557f147688862a0adcdc5"
#: Anzahl der Unterkategorien je Kategorie der Kommissionstabelle 2021–2027.
JE_KATEGORIE = {
    "1": 25,
    "2": 11,
    "3": 5,
    "4": 18,
    "5": 3,
    "6": 1,
    "7": 9,
    "8": 1,
    "9": 3,
    "10": 2,
    "11": 2,
    "12": 1,
    "13": 2,
    "14": 2,
    "15": 1,
}


def _dokument() -> dict[str, object]:
    datei = resources.files("auditcore_tyfindings.profile_data").joinpath(
        "efre.tof_2021_2027-2026.10.1.json"
    )
    return json.loads(datei.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def test_katalog_vollstaendig() -> None:
    eintraege = katalog()
    assert len(eintraege) == 86
    assert len({e.nummer for e in eintraege}) == 86
    assert Counter(e.kategorie for e in eintraege) == JE_KATEGORIE
    assert all(e.kategorie_bezeichnung.startswith(f"{e.kategorie} ") for e in eintraege)
    assert eintraege[0].nummer == "1.1" and eintraege[-1].nummer == "15.1"


def test_katalog_mit_echten_umlauten() -> None:
    eintrag = standardprofil().eintrag("4.16")
    assert eintrag is not None
    assert eintrag.kurzbezeichnung == "Verstoß gegen besondere Förderbestimmungen"
    assert eintrag.original.startswith("Expenditure noncompliant")
    assert standardprofil().eintrag("1.10") != standardprofil().eintrag("1.1")
    assert standardprofil().eintrag("16") is None


@pytest.mark.parametrize(
    ("unterkategorie", "erwartet"),
    [("4.16", "4"), ("10.1", "10"), ("1.10", "1"), ("nicht zugeordnet", None), (None, None)],
)
def test_kategorie(unterkategorie: str | None, erwartet: str | None) -> None:
    assert kategorie(unterkategorie) == erwartet


def test_fingerprint_stabil() -> None:
    profil = load_profile(*STANDARDPROFIL)
    assert profil.fingerprint == FINGERPRINT
    assert profil_aus_dict(_dokument()).fingerprint == FINGERPRINT
    assert profil.referenz == {
        "id": "efre.tof_2021_2027",
        "version": "2026.10.1",
        "fingerprint": FINGERPRINT,
    }


def test_fingerprint_aendert_sich_mit_dem_inhalt() -> None:
    dokument = _dokument()
    dokument["formalregeln"][0]["tof"] = "9.1"  # type: ignore[index]
    assert profil_aus_dict(dokument).fingerprint != FINGERPRINT


def test_verfuegbare_profile() -> None:
    assert verfuegbare_profile() == (STANDARDPROFIL, ("efre.tof_2021_2027", "2026.10.2"))


@pytest.mark.parametrize(
    ("profil_id", "version"),
    [("efre.tof_2021_2027", "2099.1.1"), ("unbekannt", "2026.10.1"), ("../x", "1")],
)
def test_unbekanntes_profil(profil_id: str, version: str) -> None:
    with pytest.raises(ProfilFehler):
        load_profile(profil_id, version)


def test_version_als_text() -> None:
    with pytest.raises(ProfilFehler):
        load_profile("efre.tof_2021_2027", 2026.1)  # type: ignore[arg-type]


def _veraendert(pfad: tuple[object, ...], wert: object) -> dict[str, object]:
    dokument = copy.deepcopy(_dokument())
    ziel: object = dokument
    for schritt in pfad[:-1]:
        ziel = ziel[schritt]  # type: ignore[index]
    ziel[pfad[-1]] = wert  # type: ignore[index]
    return dokument


@pytest.mark.parametrize(
    ("pfad", "wert"),
    [
        (("schema",), "anders/1"),
        (("unbekannt",), 1),
        (("katalog", 1, "nummer"), "1.1"),
        (("katalog", 0, "nummer"), "1"),
        (("katalog", 0, "original"), ""),
        (("kennziffern", 0, "tof"), "99.1"),
        (("kennziffern", 1, "kennziffer"), "8.1"),
        (("kennziffern", 0, "finanziell"), 1),
        (("kennziffern", 0, "bemerkung"), 1),
        (("kennziffern", 8, "regeln", 0, "suchwort"), "Skonto"),
        (("kennziffern", 8, "regeln", 0, "gold_plating"), "ja"),
        (("kennziffern", 8, "regeln", 1, "id"), "kennziffer:8.9:regel:1"),
        (("formalregeln", 0, "tof"), "9.9"),
        (("formalregeln",), {}),
        (("formalregeln", 0), "eigentümer"),
        (("open_decisions",), [1]),
    ],
)
def test_fehlerhaftes_profil(pfad: tuple[object, ...], wert: object) -> None:
    with pytest.raises(ProfilFehler):
        profil_aus_dict(_veraendert(pfad, wert))


#: Deutsche Kategoriebezeichnungen, fachlich freigegeben am 05.10.2026
#: (identisch mit der FlowInvoice-Übergangstabelle).
KATEGORIE_DE = {
    "1": "Öffentliche Auftragsvergabe",
    "2": "Staatliche Beihilfen",
    "3": "Nicht förderfähiges Vorhaben",
    "4": "Nicht förderfähige Ausgaben",
    "5": "Vereinfachte Kostenoptionen",
    "6": "Nicht kostenbezogene Finanzierung",
    "7": "Finanzinstrumente",
    "8": "Information und Kommunikation",
    "9": "Fehlende Nachweise oder Unterlagen",
    "10": "Rechen- und Buchungsfehler im Vorhaben",
    "11": "Leistungsindikatoren",
    "12": "Umweltvorschriften",
    "13": "Chancengleichheit und Nichtdiskriminierung",
    "14": "Wirtschaftlichkeit der Haushaltsführung",
    "15": "Datenschutz",
}


def _dokument_2026_10_2() -> dict[str, object]:
    datei = resources.files("auditcore_tyfindings.profile_data").joinpath(
        "efre.tof_2021_2027-2026.10.2.json"
    )
    return json.loads(datei.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def test_profil_2026_10_2_fuehrt_deutsche_kategorien() -> None:
    profil = load_profile("efre.tof_2021_2027", "2026.10.2")
    assert {k: profil.kategorie_de(k) for k in KATEGORIE_DE} == KATEGORIE_DE
    assert all(e.kategorie_de == KATEGORIE_DE[e.kategorie] for e in profil.katalog)
    assert profil.kategorie_de("16") is None
    assert profil.fingerprint != FINGERPRINT


def test_standardprofil_ohne_deutsche_kategorien_unveraendert() -> None:
    assert STANDARDPROFIL == ("efre.tof_2021_2027", "2026.10.1")
    assert standardprofil().kategorie_de("4") is None
    assert all(e.kategorie_de is None for e in katalog())


def test_2026_10_2_unterscheidet_sich_nur_durch_kategorie_de_und_kennung() -> None:
    alt, neu = _dokument(), _dokument_2026_10_2()
    assert neu.pop("derived_from") == {"id": "efre.tof_2021_2027", "version": "2026.10.1"}
    assert neu.pop("version") == "2026.10.2" and alt.pop("version") == "2026.10.1"
    eintraege = neu["katalog"]
    assert isinstance(eintraege, list)
    for eintrag in eintraege:
        eintrag.pop("kategorie_de")
    assert neu == alt


def test_kategorie_de_muss_vollstaendig_und_einheitlich_sein() -> None:
    teilweise = copy.deepcopy(_dokument_2026_10_2())
    teilweise["katalog"][0].pop("kategorie_de")  # type: ignore[index]
    with pytest.raises(ProfilFehler, match="fehlt in einzelnen"):
        profil_aus_dict(teilweise)
    abweichend = copy.deepcopy(_dokument_2026_10_2())
    abweichend["katalog"][1]["kategorie_de"] = "Anders"  # type: ignore[index]
    with pytest.raises(ProfilFehler, match="abweichender deutscher"):
        profil_aus_dict(abweichend)
    fremd = copy.deepcopy(_dokument_2026_10_2())
    fremd["derived_from"] = {"id": "anderes", "version": "1"}
    with pytest.raises(ProfilFehler, match="derived_from"):
        profil_aus_dict(fremd)
