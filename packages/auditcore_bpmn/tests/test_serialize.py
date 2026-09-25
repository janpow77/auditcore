"""Zurückschreiben ohne Bedeutungsverlust (Präfixe, QName-Werte, Kommentare)."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from helpers import FIXTURES

from auditcore_bpmn.safe_xml import parse_xml
from auditcore_bpmn.serialize import serialize, serialize_element


def _canonical(xml: str) -> str:
    return ET.canonicalize(xml, strip_text=True)


def test_roundtrip_keeps_prefixes_and_semantics() -> None:
    original = (
        '<model:definitions xmlns:model="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="D"><!-- Hinweis -->'
        '<model:process id="P"><model:sequenceFlow id="F"><model:conditionExpression '
        'xsi:type="model:tFormalExpression">a &lt; b</model:conditionExpression></model:sequenceFlow>'
        "</model:process></model:definitions>"
    )
    written = serialize(parse_xml(original))
    assert "<model:definitions" in written and 'xsi:type="model:tFormalExpression"' in written
    assert "<!-- Hinweis -->" in written
    assert _canonical(written) == _canonical(original)


def test_default_namespace_and_attribute_alias() -> None:
    uri = "http://www.omg.org/spec/BPMN/20100524/MODEL"
    root = ET.Element(f"{{{uri}}}definitions", {f"{{{uri}}}qualified": "1", "plain": 'a"b\n'})
    written = serialize_element(root, [("", uri)], xml_declaration=False)
    assert written.startswith("<definitions")
    assert 'bpmn:qualified="1"' in written and 'plain="a&quot;b&#10;"' in written
    assert ET.fromstring(written).get(f"{{{uri}}}qualified") == "1"


def test_unknown_namespace_gets_generated_prefix() -> None:
    root = ET.Element("{urn:unbekannt}a")
    ET.SubElement(root, "{urn:anders}b")
    written = serialize_element(root, [], xml_declaration=False)
    assert 'xmlns:ns0="urn:unbekannt"' in written and "ns1:b" in written


def test_all_synthetic_fixtures_roundtrip() -> None:
    for path in sorted((FIXTURES / "synthetic").glob("*.bpmn")):
        text = path.read_text(encoding="utf-8")
        again = serialize(parse_xml(serialize(parse_xml(text))))
        assert _canonical(again) == _canonical(text), path.name
