"""Fragenkatalog 2026.10.3: Zuständigkeiten, Tabellen mit Auswahl, Datum, Abschlussfragen."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

import pytest
from pruefkatalog_support import FACH, TENANT, full_activity, hdsig, kat, new_register

from auditcore_dataprotection.errors import ValidationError
from auditcore_dataprotection.register_content import check_activity
from auditcore_dataprotection.wizard_catalog import ROLES, catalog_for, load_catalog
from auditcore_dataprotection.wizard_values import check_typed


def _issues(activity: dict[str, Any]) -> list[tuple[str, str, bool]]:
    found = check_activity(activity, hdsig())
    return [(i.code, i.subject.rsplit(":", 1)[-1], i.blocking) for i in found]


def test_jede_frage_nennt_eine_zustaendige_stelle() -> None:
    catalog = catalog_for(hdsig())
    assert all(q.role in ROLES for q in catalog.questions)
    assert catalog.question("3.7.1").role == "it_betrieb"
    assert catalog.question("3.7.2").role == "recht"
    assert catalog.question("2.1").role == "fachbereich"
    assert catalog.question("W09:gesamt_01_sonstiges_hohes_risiko").number.startswith("9.1.")


def test_katalog_nennt_amtliche_quellen() -> None:
    source = files("auditcore_dataprotection.catalogs").joinpath("wizard-2026.10.3.json")
    raw = json.loads(source.read_text(encoding="utf-8"))
    titles = " ".join(s["title"] for s in raw["sources"])
    assert "EDSA" in titles and "DSK" in titles and "HBDI" in titles
    hints = " ".join(load_catalog().question("3.7.2").hints)
    assert "Leitlinien 07/2020" in hints


def test_fristen_je_datenkategorie() -> None:
    rows = [{"kategorie": "Verfahrensakte", "frist": "5 Jahre nach Abschluss"}]
    assert not [i for i in _issues(full_activity(speicherdauer=rows)) if "speicherdauer" in i[1]]
    open_ = [{"kategorie": "Protokolle", "begruendung": "Vorgabe offen", "pruefstelle": "IT"}]
    found = [i for i in _issues(full_activity(speicherdauer=open_)) if "speicherdauer" in i[1]]
    assert found == [("open_justified", "speicherdauer[1]", False)]
    missing = [{"kategorie": "Protokolle"}]
    found = [i for i in _issues(full_activity(speicherdauer=missing)) if "speicherdauer" in i[1]]
    assert found == [("missing_field", "speicherdauer[1]", True)]
    assert [i for i in _issues(full_activity(speicherdauer=[])) if i[1] == "speicherdauer"]


def test_auftragsverarbeiter_ohne_vertrag_bleibt_offen() -> None:
    rows = [
        {"dienstleister": "Rechenzentrum", "einordnung": "Auftragsverarbeiter", "vertrag": "fehlt"},
        {
            "dienstleister": "Gericht",
            "einordnung": "eigenständig Verantwortlicher",
            "vertrag": "fehlt",
        },
        {"dienstleister": "Wartung", "einordnung": "Auftragsverarbeiter", "vertrag": "liegt vor"},
    ]
    found = [i for i in _issues(full_activity(dienstleister_einordnung=rows)) if "dienst" in i[1]]
    assert found == [("missing_contract", "dienstleister_einordnung[1]", False)]


def test_tabellenfelder_werden_typgeprueft() -> None:
    world = kat()
    with pytest.raises(ValidationError, match="Tabelle"):
        new_register(world, full_activity(dienstleister="Rechenzentrum"))
    with pytest.raises(ValidationError, match="Text oder eine Tabelle"):
        new_register(world, full_activity(speicherdauer=5))


def test_auswahlspalte_und_datum_werden_geprueft() -> None:
    catalog = load_catalog()
    table = catalog.question("3.7.2")
    row = {"dienstleister": "A", "einordnung": "Auftragsverarbeiter", "vertrag": "liegt vor"}
    check_typed(table, json.dumps([row]))
    with pytest.raises(ValidationError, match="Einordnung"):
        check_typed(table, json.dumps([{**row, "einordnung": "Partner"}]))
    date_q = catalog.question("11.1.1")
    check_typed(date_q, "2026-10-01")
    with pytest.raises(ValidationError):
        check_typed(date_q, "1. Oktober")


def test_offene_punkte_werden_zur_aufgabe() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    world.workspace.answer(TENANT, FACH, activity_id, "1.8", "ja", expected_revision=1)
    tasks = world.workspace.overview(TENANT, FACH, activity_id)["assistent"]["tasks"]
    assert {"question": "1.8", "kind": "offene_punkte"}.items() <= next(
        t for t in tasks if t["question"] == "1.8"
    ).items()
    world.workspace.answer(TENANT, FACH, activity_id, "1.8", "nein", expected_revision=2)
    tasks = world.workspace.overview(TENANT, FACH, activity_id)["assistent"]["tasks"]
    assert not [t for t in tasks if t["question"] == "1.8"]
