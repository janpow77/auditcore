"""Vorlagenbibliothek des Profils 2021–2027: synthetisch, neutral, fehlerfrei geprüft."""

from __future__ import annotations

import pytest
from helpers import STICHTAG, institution_names

from auditcore_bpmn import validate
from auditcore_bpmn.model import parse_bpmn
from auditcore_bpmn.profiles import load_profile, load_template

PROFILE = load_profile()
FORBIDDEN = ("hessen", "gmbh", "@", " eur ", "€", *institution_names())


@pytest.mark.parametrize("template", PROFILE.templates, ids=lambda t: t.id)
def test_template_is_valid_neutral_and_profiled(template) -> None:  # type: ignore[no-untyped-def]
    xml = load_template(PROFILE, template.id)
    document = parse_bpmn(xml)
    info = document.diagram_info
    assert (
        info is not None
        and info.profile == PROFILE.id
        and info.status == "entwurf"
        and info.title == template.title["de"]
    )
    assert "synthetisch" in template.origin
    report = validate(document, reference_date=STICHTAG)
    assert report.errors == () and report.warnings == (), [i.message() for i in report.issues]
    assert all(lane.extensions.actor and lane.extensions.actor.role in PROFILE.roles for lane in document.lanes)
    assert any(e.extensions.legal_bases for e in document.activities)
    assert not any(word in xml.lower() for word in FORBIDDEN)
    shapes = xml.count("<bpmndi:BPMNShape")
    assert shapes == len(document.flow_nodes) + len(document.lanes) + len(document.participants) + len(
        document.by_type("dataObjectReference")
    )
