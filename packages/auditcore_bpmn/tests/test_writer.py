"""Schreiben von Diagramm-Infos und Erweiterungen; Rundlauf bleibt erhalten."""

from __future__ import annotations

import pytest
from helpers import INFO_OK, doc, ext, fixture_text, linear

from auditcore_bpmn.errors import BpmnError
from auditcore_bpmn.extensions import DiagramInfo, Extensions, LegalBasis, Marker
from auditcore_bpmn.legacy import analyze_bpmn
from auditcore_bpmn.model import parse_bpmn
from auditcore_bpmn.writer import main_element_id, new_definitions, remove_extensions, set_diagram_info, set_extensions


def test_set_diagram_info_moves_to_collaboration_and_sets_version() -> None:
    xml = doc(ext(INFO_OK) + linear("T1"), collaboration='<bpmn:participant id="Pool" processRef="P1"/>')
    written = set_diagram_info(xml, DiagramInfo(title="Neu", schema_version="1.0", status="entwurf"))
    document = parse_bpmn(written)
    assert document.diagram_info_owner == "C1"
    assert document.diagram_info is not None and document.diagram_info.title == "Neu"
    assert document.diagram_info.schema_version == "1.1"
    assert document.elements["P1"].extensions.diagram_info is None


def test_set_extensions_normalizes_legal_basis_and_stays_readable_for_legacy() -> None:
    written = set_extensions(
        doc(linear("T1")),
        "T1",
        Extensions(
            legal_bases=(LegalBasis(act="VO (EU) 2021/1060", article="74", paragraph="2"),), markers=(Marker("frist"),)
        ),
    )
    basis = parse_bpmn(written).elements["T1"].extensions.legal_bases[0]
    assert basis.act == "Verordnung (EU) 2021/1060"
    assert basis.text == "Artikel 74 Absatz 2 der Verordnung (EU) 2021/1060"
    task = analyze_bpmn(written)["tasks"][0]
    assert task["legal_basis"] == "Artikel 74 Absatz 2 der Verordnung (EU) 2021/1060"


def test_remove_and_errors() -> None:
    written = set_extensions(doc(linear("T1")), "T1", Extensions(markers=(Marker("frist"),)))
    assert parse_bpmn(remove_extensions(written, "T1", "kennzeichen")).elements["T1"].extensions.is_empty
    with pytest.raises(BpmnError):
        set_extensions(doc(linear("T1")), "fehlt", Extensions())
    with pytest.raises(BpmnError):
        main_element_id(parse_bpmn('<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"/>'))


def test_model_passed_in_is_not_modified() -> None:
    document = parse_bpmn(fixture_text("synthetic/typen_kollaboration.bpmn"))
    set_extensions(document, "Erfassen", Extensions(markers=(Marker("system"),)))
    assert document.elements["Erfassen"].extensions.markers == ()


def test_new_definitions() -> None:
    document = parse_bpmn(new_definitions("Prozess_A", "Neu"))
    assert document.processes[0].name == "Neu" and "StartEvent_1" in document.elements
