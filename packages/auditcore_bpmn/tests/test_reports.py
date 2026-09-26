"""Berichte: Prozesstabelle, RCM, Feststellungsliste, Durchlauftest, KA-Vorschlag, Formate."""

from __future__ import annotations

import csv
import io

import pytest
from helpers import doc, ext, fixture_text, linear_with

from auditcore_bpmn.model import parse_bpmn
from auditcore_bpmn.reports import (
    PROCESS_TABLE_COLUMNS,
    category_proposals,
    finding_list,
    flow_order,
    process_table,
    risk_control_matrix,
    to_csv,
    to_myst,
    to_xlsx,
    walkthrough_status,
)

VOLL = fixture_text("synthetic/flowaudit_1_1_vollstaendig.bpmn")
TYPEN = fixture_text("synthetic/typen_kollaboration.bpmn")


def test_flow_order() -> None:
    assert [n.id for n in flow_order(parse_bpmn(VOLL))] == ["Start", "Pruefen", "Zahlen", "Ende"]


def test_process_table() -> None:
    rows = process_table(VOLL)
    assert [r["schritt"] for r in rows] == ["Verwaltungsprüfung durchführen", "Auszahlung anweisen"]
    first = rows[0]
    assert first["akteur"] == "Verwaltungsbehörde (Prüfreferat)"
    assert (
        first["rechtsgrundlage"].startswith("Artikel 74 Absatz 1 Buchstabe a")
        and "§ 44 LHO" in first["rechtsgrundlage"]
    )
    assert (
        first["kontrolle"] == "Belegprüfung nach Checkliste (Schlüsselkontrolle)" and first["nachweis"] == "Prüfvermerk"
    )
    assert first["frist"] == "10 arbeitstage (ab Eingang)" and first["ka_bk"] == "KA 4 · BK 4.2"
    typen = {r["element_id"]: r for r in process_table(TYPEN)}
    assert (
        typen["Erfassen"]["nachweis"] == "Vorgangsakte (elektronische Akte)"
        and typen["Erfassen"]["it_system"] == "Fachanwendung"
    )
    assert len(process_table(VOLL, activities_only=False)) == 4


def test_risk_control_matrix() -> None:
    rows = risk_control_matrix(VOLL)
    assert [(r["risiko_id"], r["kontrolle_id"]) for r in rows] == [("R1", "K1"), ("R-D1", "K1")]
    assert (
        rows[0]["schluesselkontrolle"] == "ja"
        and rows[0]["test"] == "erfuellt"
        and rows[1]["ort"] == "Verwaltungsprüfung durchführen"
    )
    orphan = doc(linear_with('<flowaudit:risiko id="R" kontrollen="KX"/>', '<flowaudit:risiko id="R2"/>'))
    rows = risk_control_matrix(orphan)
    assert rows[0]["kontrolle"] == "(unbekannt)" and rows[1]["kontrolle_id"] == ""


def test_finding_list_and_walkthrough() -> None:
    findings = finding_list(VOLL)
    assert findings == [
        {
            "id": "FS1",
            "kennung": "T01 F1",
            "element": "Verwaltungsprüfung durchführen",
            "element_id": "Pruefen",
            "art": "formell",
            "einstufung": "gering",
            "ka": "4",
            "bk": "4.2",
            "beschreibung": "Prüfvermerk unvollständig.",
            "empfehlung": "Vermerkvorlage ergänzen.",
            "frist": "2026-12-31",
            "status": "offen",
        }
    ]
    status = walkthrough_status(VOLL)
    assert (
        status["results"] == {"erfuellt": 1}
        and status["untested"] == ["Zahlen"]
        and status["steps"][0]["fall"] == "V-001"
    )


def _finding(ka: str, art: str, einstufung: str, status: str = "offen") -> str:
    return (
        f'<flowaudit:feststellung kennung="F-{ka}-{einstufung}" ka="{ka}" art="{art}" einstufung="{einstufung}" status="{status}">'
        "<flowaudit:beschreibung>x</flowaudit:beschreibung></flowaudit:feststellung>"
    )


def test_category_proposals_are_only_proposals() -> None:
    def task(task_id: str, *children: str) -> str:
        return f'<bpmn:task id="{task_id}" name="{task_id}">{ext(*children)}</bpmn:task>'

    body = (
        task("T1", '<flowaudit:pruefbezug ka="1"/>')
        + task(
            "T2",
            _finding("2", "formell", "gering"),
            _finding("3", "finanziell", "gering"),
            _finding("5", "formell", "schwerwiegend"),
            _finding("6", "formell", "schwerwiegend", "entfallen"),
        )
        + task("T3", '<flowaudit:pruefbezug ka="7"/>', '<flowaudit:pruefschritt ergebnis="nicht_erfuellt"/>')
    )
    proposals = {p.key_requirement: p for p in category_proposals([doc(body)])}
    assert [proposals[n].proposal for n in (1, 2, 3, 5, 6, 7, 8)] == [1, 2, 3, 4, None, 2, None]
    assert proposals[2].findings == ("F-2-gering",)
    data = proposals[5].to_dict()
    assert (
        data["category_text"].startswith("Funktionsfähigkeit im Wesentlichen nicht vorhanden")
        and "Prüfer" in data["note"]
    )
    assert len(proposals) == 15


def test_formats() -> None:
    rows = process_table(VOLL)
    text = to_csv(rows, PROCESS_TABLE_COLUMNS)
    parsed = list(csv.reader(io.StringIO(text), delimiter=";"))
    assert parsed[0] == list(PROCESS_TABLE_COLUMNS.values()) and len(parsed) == 3
    assert to_csv([]) == "\n"
    myst = to_myst(rows, PROCESS_TABLE_COLUMNS, title="Prozessbeschreibung", target="prozess")
    assert myst.startswith("(prozess)=\n## Prozessbeschreibung") and "| Nr. | Schritt |" in myst
    assert to_myst([{"a": "x|y\nz"}]).splitlines()[-1] == "| x\\|y z |"
    openpyxl = pytest.importorskip("openpyxl")
    book = openpyxl.load_workbook(io.BytesIO(to_xlsx({"Prozess": rows, "RCM": risk_control_matrix(VOLL), "Leer": []})))
    assert book.sheetnames == ["Prozess", "RCM", "Leer"] and book["Prozess"]["B1"].value == "schritt"
