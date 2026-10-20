"""Regelwerk für den Abgleich der Übersicht über die Verwaltungsüberprüfungen.

Alle Texte sind synthetisch. Der Paritätstest gegen ``modAKB_Regeln.bas``
läuft nur, wenn ``AUDITCORE_TYFINDINGS_REGELN_BAS`` auf das VBA-Modul zeigt.
"""

from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path

import pytest

from auditcore_tyfindings import (
    DEFAULT_RULE_SET,
    EingabeFehler,
    ProfilFehler,
    default_rule_set,
    load_overview_rules,
    match_rule,
    rule_set_from_dict,
    rules_of_area,
    threshold,
)

UMGEBUNG = "AUDITCORE_TYFINDINGS_REGELN_BAS"


def _name(bereich: str, text: str, kennziffer: str = "") -> str | None:
    treffer = match_rule(bereich, text, kennziffer)
    return None if treffer is None else treffer.name


def test_standardregelwerk_ist_geladen_und_eindeutig() -> None:
    werk = default_rule_set()
    assert (werk.id, werk.version) == DEFAULT_RULE_SET
    assert werk.status == "APPROVED"
    assert len(werk.fingerprint) == 64
    assert len({r.id for r in werk.regeln}) == len(werk.regeln)
    assert all(r.status and r.quelle for r in werk.regeln)
    assert load_overview_rules(*DEFAULT_RULE_SET).fingerprint == werk.fingerprint


def test_fallgruppen_in_fachlicher_reihenfolge() -> None:
    assert (
        _name("FALLGRUPPE", "Abschlagsrechnung zweimal abgerechnet")
        == "Doppelte Abrechnung oder doppelter Beleg"
    )
    assert _name("FALLGRUPPE", "Kürzung auf den Bewilligungsrahmen") is not None
    assert "Kappung" in str(_name("FALLGRUPPE", "Kürzung auf den Bewilligungsrahmen"))
    # Stunden gehen der Kappung vor; die Kappung schließt Stunden ausdrücklich aus
    assert "Arbeitsstunden" in str(_name("FALLGRUPPE", "Stunden über dem Bewilligungsrahmen"))
    assert "Skonto" in str(_name("FALLGRUPPE", "2 % Skonto nicht abgezogen"))
    assert _name("FALLGRUPPE", "Beleg ohne erkennbaren Bezug") is None


def test_ganzes_wort_und_ausschluss() -> None:
    assert _name("UR", "Kürzung der Kosten, UR") is not None
    assert _name("UR", "Kürzung wegen Natur der Kosten") is None
    assert _name("UR", "Kürzung, stellt keine UR dar") is None


def test_kennziffern_exakt_und_mit_stern() -> None:
    assert _name("BETRUG", "", "8.8") is not None
    assert _name("BETRUG", "", "8.80") is None
    assert _name("VERGABE", "Vergabe nicht dokumentiert", "5.1") is not None
    assert _name("VERGABE", "Vergabe nicht dokumentiert", "1.3") is None


def test_zusatzwort_ist_erforderlich() -> None:
    assert _name("BETRUG", "Abschlagsrechnung vorgelegt") is None
    assert _name("BETRUG", "Abschlagsrechnung nicht in Abzug gebracht") is not None


def test_angekuendigte_abhilfe() -> None:
    assert _name("ABHILFE_KUENFTIG", "Mangel wird mit dem FB geheilt") is not None
    assert _name("ABHILFE_KUENFTIG", "Unterlagen werden nachgereicht") is not None
    assert (
        _name("ABHILFE_KUENFTIG", "Unterlagen mussten erst angefragt werden, wurden dann vorgelegt")
        is None
    )


def test_schwellen() -> None:
    assert threshold("SYS_VORHABEN_MEHR_ALS") == 5.0
    assert threshold("sys_foepg_ab") == 3.0
    assert threshold("KZ_SAMMEL") == "16"
    with pytest.raises(ProfilFehler):
        threshold("UNBEKANNT")


def test_eingaben() -> None:
    assert len(rules_of_area("SCHWELLE")) > 0
    with pytest.raises(EingabeFehler):
        rules_of_area("UNBEKANNT")
    with pytest.raises(EingabeFehler):
        match_rule("UR", 5)  # type: ignore[arg-type]


def _dokument() -> dict[str, object]:
    return {
        "schema": "auditcore_tyfindings.uebersichtsregeln/1",
        "id": "test.regeln",
        "version": "1",
        "status": "TEST",
        "regeln": [
            {
                "id": "UR:1",
                "bereich": "UR",
                "name": "Test",
                "stichwoerter": ["test"],
                "wert": None,
                "bewertung": "",
            },
            {"id": "SCHWELLE:1", "bereich": "SCHWELLE", "name": "X", "wert": 2},
        ],
    }


@pytest.mark.parametrize(
    ("aenderung", "meldung"),
    [
        (lambda d: d.update(schema="falsch"), "Regelwerksschema"),
        (lambda d: d["regeln"].append(copy.deepcopy(d["regeln"][0])), "doppelt"),
        (lambda d: d["regeln"][0].update(wert=1), "nur im Bereich SCHWELLE"),
        (lambda d: d["regeln"][0].update(bewertung="vielleicht"), "Bewertung"),
        (lambda d: d["regeln"][0].update(stichwoerter=[]), "weder Stichwörter"),
        (lambda d: d["regeln"][1].update(wert=None), "Schwelle ohne"),
        (lambda d: d["regeln"][0].update(bereich="NEU"), "Bereich ungültig"),
        (lambda d: d["regeln"][0].update(stichwoerter="test"), "Liste nichtleerer Texte"),
        (lambda d: d["regeln"][0].update(stichwoerter=[" "]), "Liste nichtleerer Texte"),
        (lambda d: d["regeln"][0].update(quelle=5), "muss ein Text sein"),
        (lambda d: d["regeln"].append("keine Regel"), "Objekt erwartet"),
        (lambda d: d["regeln"][0].update(name=" "), "Name fehlt"),
    ],
)
def test_fehlerhafte_regelwerke(aenderung: object, meldung: str) -> None:
    dokument = _dokument()
    assert callable(aenderung)
    aenderung(dokument)
    with pytest.raises(ProfilFehler, match=meldung):
        rule_set_from_dict(dokument)


def test_paritaet_mit_vba_modul(monkeypatch: pytest.MonkeyPatch) -> None:
    pfad = os.environ.get(UMGEBUNG)
    if not pfad:
        pytest.skip(f"{UMGEBUNG} nicht gesetzt (modAKB_Regeln.bas, nur lokal)")
    werkzeuge = Path(__file__).resolve().parents[1] / "tools"
    monkeypatch.syspath_prepend(str(werkzeuge))
    spec = importlib.util.spec_from_file_location("vba_regeln", werkzeuge / "vba_regeln.py")
    assert spec is not None and spec.loader is not None
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    regeln_vba = modul.regeln_aus_vba(Path(pfad))
    assert [r["id"] for r in regeln_vba] == [r.id for r in default_rule_set().regeln]
    assert (
        rule_set_from_dict(
            {
                "schema": "auditcore_tyfindings.uebersichtsregeln/1",
                "id": "x",
                "version": "x",
                "regeln": regeln_vba,
            }
        ).regeln
        == default_rule_set().regeln
    )
