"""New-contract report data and renderers (JSON, HTML, XLSX, optional PDF)."""

from __future__ import annotations

import io
import json
from datetime import UTC, date, datetime
from typing import Any

import pytest

from auditcore_dataprotection.calculation import Answer, AnswerValue, parse_scenarios, propose
from auditcore_dataprotection.export import (
    assessment_report,
    overview_rows,
    register_report,
    render_assessment_html,
    to_json_bytes,
)
from auditcore_dataprotection.model import (
    Assessment,
    AssessmentStatus,
    Consultation,
    RegisterStatus,
    RegisterVersion,
)
from auditcore_dataprotection.register import content_hash
from auditcore_dataprotection.rules import load_profile

PROFILE = load_profile("regulierung.dsgvo", "2026.09.1")
NOW = datetime(2026, 9, 3, 10, 0, tzinfo=UTC)
ACTIVITY = {
    "id": "t-1",
    "name": "Bürgerportal <script>alert(1)</script>",
    "referat": "Referat A",
    "zweck": "=1+1",
    "ermaechtigungsgrundlage": "§ 3 EGovG",
    "kategorien_betroffene": "Bürgerinnen und Bürger",
    "kategorien_daten": "Kontaktdaten",
    "kategorien_empfaenger": "keine",
    "drittlandtransfer": False,
    "anzahl_betroffene": 12000,
}


def make_assessment(**changes: Any) -> Assessment:
    answers = {q: Answer(AnswerValue.NO) for q in PROFILE.question_keys}
    answers["art35_3_a"] = Answer(AnswerValue.YES, "Profiling <b>fett</b>")
    answers["edsa_05_umfang"] = Answer(AnswerValue.UNKNOWN)
    scenarios = parse_scenarios(
        [
            {
                "dimension": "vertraulichkeit",
                "description": "Unbefugter Zugriff",
                "severity": 4,
                "likelihood": 4,
                "measures": ["verschluesselung"],
                "residual_severity": 3,
                "residual_justification": "Pseudonyme Kennungen",
            }
        ],
        PROFILE,
    )
    proposal = propose(PROFILE, answers, scenarios).to_dict()
    values: dict[str, Any] = dict(
        tenant_id="mandant-1",
        assessment_id="a-1",
        register_id="verarbeitungsverzeichnis",
        activity_id="t-1",
        activity_name=ACTIVITY["name"],
        version=2,
        status=AssessmentStatus.DPO_INVOLVED,
        profile_id=PROFILE.id,
        profile_version=PROFILE.version,
        profile_fingerprint=PROFILE.fingerprint,
        register_version=3,
        activity_snapshot=ACTIVITY,
        answers=answers,
        scenarios=scenarios,
        proposal=proposal,
        created_by="anna",
        created_at=NOW,
        updated_at=NOW,
        editors=("anna", "carl"),
        necessity="Erforderlich",
        proportionality="Angemessen",
        decision="freigabe",
        deviation=True,
        deviation_justification="x" * 50,
        decided_by="anna",
        decided_at=NOW,
        dpo_vote="zugestimmt_mit_auflagen",
        dpo_statement="Auflage",
        dpo_by="dora",
        dpo_at=NOW,
        consultation=Consultation("HBDI", "keine Bedenken", "2026-09-02", "anna", NOW),
        predecessor_id="a-0",
        changes_to_predecessor=(
            {"feld": "zweck", "bezeichnung": "Zweck", "vorher": "A", "nachher": "B"},
        ),
    )
    values.update(changes)
    return Assessment(**values)


def make_register() -> RegisterVersion:
    content = {
        "deckblatt": {"verantwortlicher": {"name": "Behörde"}, "dsb": {}},
        "referate": ["Referat A"],
        "taetigkeiten": [ACTIVITY, {"id": "t-2", "name": "Ohne Referat"}],
    }
    return RegisterVersion(
        tenant_id="mandant-1",
        register_id="verarbeitungsverzeichnis",
        version=3,
        status=RegisterStatus.RELEASED,
        content=content,
        content_hash=content_hash(content),
        created_by="anna",
        created_at=NOW,
        editors=("anna",),
        released_by="bert",
        released_at=NOW,
        predecessor_version=2,
    )


def test_assessment_report_is_complete_and_serialisable() -> None:
    report = assessment_report(make_assessment(), PROFILE, tenant_label="Behörde")
    assert report["meta"]["profile"]["fingerprint"] == PROFILE.fingerprint
    assert report["meta"]["recorded_profile"]["version"] == "2026.09.1"
    assert report["meta"]["locked"] is False
    assert len(report["screening"]["questions"]) == len(PROFILE.questions)
    by_key = {q["key"]: q for q in report["screening"]["questions"]}
    assert by_key["art35_3_a"]["answer"] == "ja"
    assert by_key["edsa_05_umfang"]["answer"] == "unbekannt"
    assert report["screening"]["unknown"] == ["edsa_05_umfang"]
    assert report["screening"]["complete"] is False
    assert report["risk"]["scenarios"][0]["explicit_residual"] == ["severity"]
    assert report["consultation"]["authority"] == "HBDI"
    assert report["dpo"]["by"] == "dora"
    assert report["changes_to_predecessor"][0]["feld"] == "zweck"
    decoded = json.loads(to_json_bytes(report))
    assert decoded["lifecycle"]["created_at"] == NOW.isoformat()
    assert to_json_bytes(report) == to_json_bytes(report)


def test_html_escapes_input_and_shows_profile_and_gaps() -> None:
    html = render_assessment_html(assessment_report(make_assessment(), PROFILE))
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "<b>fett</b>" not in html
    assert "regulierung.dsgvo" in html and "2026.09.1" in html
    assert "Unvollständig" in html and "gelten nicht als Nein" in html
    assert "Änderungen gegenüber der Vorfassung" in html
    assert "HBDI" in html


def test_html_shows_missing_consultation_and_empty_risk() -> None:
    assessment = make_assessment(
        consultation=None,
        scenarios=(),
        proposal={**make_assessment().proposal, "consultation_required": True, "risk": None},
    )
    html = render_assessment_html(assessment_report(assessment, PROFILE))
    assert "noch nicht dokumentiert" in html
    assert "noch kein Risikoszenario" in html


def test_register_report_groups_and_checks() -> None:
    report = register_report(make_register(), PROFILE)
    assert [d["name"] for d in report["departments"]] == ["Referat A", "Ohne Referat"]
    assert report["meta"]["content_hash"] == make_register().content_hash
    codes = {(i["code"], i["subject"]) for i in report["issues"]}
    assert ("missing_field", "deckblatt:dsb") in codes
    assert any(i["blocking"] for i in report["issues"])
    assert report["columns"][0]["title"]
    json.loads(to_json_bytes(report))


def test_overview_rows_are_plain() -> None:
    rows = overview_rows([{"id": "t-1", "dsfa": {"freigegeben_am": NOW, "status": "entwurf"}}])
    assert rows[0]["dsfa"]["freigegeben_am"] == NOW.isoformat()


openpyxl = pytest.importorskip("openpyxl")


def test_register_xlsx_is_literal_text() -> None:
    from auditcore_dataprotection.excel import render_register_xlsx

    data = render_register_xlsx(register_report(make_register(), PROFILE))
    book = openpyxl.load_workbook(io.BytesIO(data))
    sheet = book["Verarbeitungstätigkeiten"]
    values = [c for row in sheet.iter_rows() for c in row if c.value == "=1+1"]
    assert values and all(c.data_type == "s" for c in values)
    assert book.sheetnames == ["Vorblatt", "Verarbeitungstätigkeiten", "Prüfhinweise"]


def test_overview_xlsx() -> None:
    from auditcore_dataprotection.excel import render_overview_xlsx

    rows = [
        {
            "id": "t-1",
            "position": 1,
            "name": '=HYPERLINK("x")',
            "zweck": "z",
            "dsfa": {
                "status": "freigegeben",
                "version": 1,
                "freigegeben_am": date(2026, 9, 1),
                "pruefung_erforderlich": True,
            },
        }
    ]
    book = openpyxl.load_workbook(io.BytesIO(render_overview_xlsx(rows, "Behörde", NOW)))
    cell = book["Folgenabschätzungen"]["C2"]
    assert cell.value == '=HYPERLINK("x")' and cell.data_type == "s"
    assert book["Folgenabschätzungen"]["K2"].value == "Ja"


def test_pdf_renderer() -> None:
    pytest.importorskip("weasyprint")
    from auditcore_dataprotection.pdf import render_pdf

    assert (
        render_pdf(render_assessment_html(assessment_report(make_assessment(), PROFILE)))[:5]
        == b"%PDF-"
    )
