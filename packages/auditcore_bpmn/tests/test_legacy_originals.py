"""Die Originaltests aus audit_designer (test_bpmn_services, test_bpmn_flowaudit_extensions,
test_bpmn_api) gegen die Übernahmen – gleiche Eingaben, gleiche Erwartungen."""

from __future__ import annotations

from io import BytesIO

import pytest

from auditcore_bpmn.errors import BpmnXmlError
from auditcore_bpmn.legacy import (
    analyze_bpmn,
    assert_well_formed_xml,
    diagram_info_from_legacy,
    export_bpmn_to_excel,
    export_bpmn_to_pdf,
    validate_bpmn_bva,
)

FLOWSTAT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<model:definitions
    xmlns:model="http://www.omg.org/spec/BPMN/20100524/MODEL"
    targetNamespace="urn:test">
  <model:process id="Process_1">
    <model:startEvent id="Start_1" />
    <model:userTask id="Task_User" name="Prüfen"
                    duration="45" cost="12.50" resource="Sachbearbeitung"
                    frequencyPerYear="24" personnel_count="3" />
    <model:endEvent id="End_1" />
  </model:process>
</model:definitions>
"""

XML_MIT_METADATEN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:flowaudit="https://flowaudit.de/bpmn/schema/1.0"
    targetNamespace="urn:test">
  <bpmn:process id="Process_1">
    <bpmn:userTask id="Task_1" name="Vergabe prüfen">
      <bpmn:documentation>Fachliche Beschreibung des Schritts.</bpmn:documentation>
      <bpmn:extensionElements>
        <flowaudit:rechtsgrundlage>§ 55 BHO; Art. 74 VO (EU) 2021/1060</flowaudit:rechtsgrundlage>
        <flowaudit:interneNotiz>Nur bei Auftragswerten über dem Schwellenwert.</flowaudit:interneNotiz>
      </bpmn:extensionElements>
    </bpmn:userTask>
    <bpmn:task id="Task_2" name="Ablegen" />
  </bpmn:process>
</bpmn:definitions>
"""

MINIMAL_BPMN_XML = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  id="defs_1" targetNamespace="http://example.com/bpmn">
  <bpmn:process id="proc_1" isExecutable="false">
    <bpmn:startEvent id="start_1" name="Start" />
    <bpmn:task id="task_1" name="Beispiel-Task" />
    <bpmn:endEvent id="end_1" name="Ende" />
    <bpmn:sequenceFlow id="flow_1" sourceRef="start_1" targetRef="task_1" />
    <bpmn:sequenceFlow id="flow_2" sourceRef="task_1" targetRef="end_1" />
  </bpmn:process>
</bpmn:definitions>
"""


def test_validation_parses_xml_and_accepts_any_bpmn_namespace_prefix() -> None:
    result = validate_bpmn_bva(FLOWSTAT_XML)
    assert result.valid is True and result.errors == []


def test_validation_rejects_malformed_xml_even_with_bpmn_like_text() -> None:
    result = validate_bpmn_bva(
        '<bpmn:startEvent xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"><bpmn:endEvent>'
    )
    assert result.valid is False and "nicht wohlgeformt" in result.errors[0]


def test_malformed_xml_cannot_be_persisted() -> None:
    with pytest.raises(BpmnXmlError, match="nicht wohlgeformt"):
        assert_well_formed_xml("<broken>")
    assert_well_formed_xml(MINIMAL_BPMN_XML)


def test_validation_rejects_unknown_sequence_flow_reference() -> None:
    xml = FLOWSTAT_XML.replace(
        '<model:endEvent id="End_1" />',
        '<model:endEvent id="End_1" />\n<model:sequenceFlow id="Flow_Broken" sourceRef="Task_User" targetRef="Missing" />',
    )
    result = validate_bpmn_bva(xml)
    assert result.valid is False and any("unbekannte targetRef 'Missing'" in e for e in result.errors)


def test_analysis_reads_compact_attributes_written_by_flowstat_editor() -> None:
    result = analyze_bpmn(FLOWSTAT_XML, "Testprozess")
    assert result["total_tasks"] == 1 and result["total_duration_minutes"] == 45.0
    assert result["total_cost"] == 12.5 and result["tasks_with_duration"] == 1 and result["tasks_with_cost"] == 1
    task = result["tasks"][0]
    assert task["resources_personnel"] == "Sachbearbeitung" and task["frequency"] == 24 and task["personnel_count"] == 3


def test_rechtsgrundlage_und_notiz_werden_gelesen() -> None:
    tasks = {t["task_id"]: t for t in analyze_bpmn(XML_MIT_METADATEN, "Testprozess")["tasks"]}
    assert tasks["Task_1"]["legal_basis"] == "§ 55 BHO; Art. 74 VO (EU) 2021/1060"
    assert tasks["Task_1"]["internal_note"] == "Nur bei Auftragswerten über dem Schwellenwert."
    assert tasks["Task_1"]["documentation"] == "Fachliche Beschreibung des Schritts."
    assert tasks["Task_2"]["legal_basis"] is None and tasks["Task_2"]["internal_note"] is None


def test_alias_notiz_wird_ebenfalls_gelesen() -> None:
    tasks = {t["task_id"]: t for t in analyze_bpmn(XML_MIT_METADATEN.replace("interneNotiz", "notiz"))["tasks"]}
    assert tasks["Task_1"]["internal_note"] == "Nur bei Auftragswerten über dem Schwellenwert."


def test_excel_export_fuehrt_beide_spalten() -> None:
    openpyxl = pytest.importorskip("openpyxl")
    blatt = openpyxl.load_workbook(BytesIO(export_bpmn_to_excel(XML_MIT_METADATEN, "Testprozess").getvalue()))["Tasks"]
    kopf = [zelle.value for zelle in blatt[1]]
    assert "Rechtsgrundlagen" in kopf and "Interne Notizen" in kopf
    spalte = kopf.index("Rechtsgrundlagen") + 1
    werte = [blatt.cell(row=zeile, column=spalte).value for zeile in (2, 3)]
    assert "§ 55 BHO; Art. 74 VO (EU) 2021/1060" in werte and None in werte


def test_validate_minimal_and_pdf_export() -> None:
    assert validate_bpmn_bva(MINIMAL_BPMN_XML).valid is True
    pytest.importorskip("reportlab")
    assert export_bpmn_to_pdf(MINIMAL_BPMN_XML, "PDF Export").getvalue().startswith(b"%PDF-")


def test_diagram_info_from_legacy_row() -> None:
    info = diagram_info_from_legacy(
        {
            "name": "Name",
            "header_title": None,
            "header_subtitle": "Unter",
            "description": "B",
            "version": 3,
            "is_archived": True,
            "header_color": None,
            "process_owner": "Referat",
        }
    )
    assert (info.title, info.subtitle, info.version, info.status) == ("Name", "Unter", "3", "archiviert")
    assert info.header_color == "#1976d2" and info.header_text_color == "#ffffff" and info.process_owner == "Referat"
    assert diagram_info_from_legacy({"header_title": "Kopf", "name": "Name"}).status is None
