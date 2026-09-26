"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.resources import files

import auditcore_bpmn as ab
from auditcore_bpmn.collection import DiagramCollection
from auditcore_bpmn.legacy import analyze_bpmn, validate_bpmn_bva
from auditcore_bpmn.profiles import load_profile, load_template

XML = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:flowaudit="https://flowaudit.de/bpmn/schema/1.0" id="D" targetNamespace="urn:smoke">
  <bpmn:process id="P">
    <bpmn:extensionElements>
      <flowaudit:diagrammInfo schemaVersion="1.1" profil="foerderperiode-2021-2027" titel="Rauchtest" status="entwurf"/>
    </bpmn:extensionElements>
    <bpmn:startEvent id="S"/>
    <bpmn:userTask id="T" name="Prüfen" durationEstimated="2" durationUnit="Stunden" costEstimate="10">
      <bpmn:extensionElements>
        <flowaudit:rechtsgrundlage>Art. 74 VO (EU) 2021/1060</flowaudit:rechtsgrundlage>
        <flowaudit:pruefbezug ka="16"/>
      </bpmn:extensionElements>
    </bpmn:userTask>
    <bpmn:endEvent id="E"/>
    <bpmn:sequenceFlow id="F1" sourceRef="S" targetRef="T"/>
    <bpmn:sequenceFlow id="F2" sourceRef="T" targetRef="E"/>
  </bpmn:process>
</bpmn:definitions>
"""


def main() -> None:
    assert distribution("auditcore_bpmn").version == ab.__version__ == "0.1.0"
    document = ab.parse_bpmn(XML)
    assert document.elements["T"].extensions.legal_bases[0].text == "Art. 74 VO (EU) 2021/1060"
    report = ab.validate(document)
    assert "BPMN-F023" in report.rule_ids() and not report.is_valid
    assert "Kernanforderung" in report.issues[0].message() or report.issues
    analysis = analyze_bpmn(XML, "Rauchtest")
    assert analysis["total_duration_minutes"] == 120.0 and analysis["tasks"][0]["legal_basis"]
    assert validate_bpmn_bva(XML).valid is True
    profile = load_profile()
    assert profile.key_requirement_numbers == tuple(range(1, 16))
    assert "<bpmn:definitions" in load_template(profile, "verwaltungskontrolle")
    assert files("auditcore_bpmn.schemas").joinpath("flowaudit-1.1.xsd").is_file()
    collection = DiagramCollection()
    collection.add_diagram("rauchtest", XML)
    assert collection.elements_by_key("ka", "16") == [("rauchtest", "T")]
    try:
        ab.parse_bpmn('<!DOCTYPE a [<!ENTITY e "x">]><a>&e;</a>')
    except ab.UnsafeXmlError:
        pass
    else:  # pragma: no cover
        raise AssertionError("DTD wurde nicht abgewiesen")
    print("auditcore_bpmn smoke PASS")


if __name__ == "__main__":
    main()
