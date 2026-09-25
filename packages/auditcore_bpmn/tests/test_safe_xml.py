"""Gehärtetes Parsen: beide Wege (defusedxml, Expat) liefern dasselbe und weisen Angriffe ab."""

from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest

from auditcore_bpmn.errors import BpmnXmlError, UnsafeXmlError, XmlTooLargeError
from auditcore_bpmn.safe_xml import defusedxml_available, parse_xml, safe_fromstring

BACKENDS = ["expat", "defusedxml"] if defusedxml_available() else ["expat"]
SAMPLE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n<!-- vorne --><?pi vorne?>'
    '<b:definitions xmlns:b="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:x="urn:x">'
    '<!--c--><b:process id="P" x:a="1"><?pi da?>Tä &amp; &lt;</b:process></b:definitions>'
)
ATTACKS = [
    '<!DOCTYPE a [<!ENTITY e "x">]><a>&e;</a>',
    '<!DOCTYPE a [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;">]><a>&lol2;</a>',
    '<!DOCTYPE a SYSTEM "file:///etc/passwd"><a/>',
    '<!DOCTYPE a [<!ENTITY % p SYSTEM "http://example.invalid/x.dtd"> %p;]><a/>',
    "<!DOCTYPE a><a/>",
]


@pytest.mark.parametrize("backend", BACKENDS)
def test_parses_tree_namespaces_and_prolog(backend: str) -> None:
    parsed = parse_xml(SAMPLE, backend=backend)  # type: ignore[arg-type]
    assert parsed.backend == backend
    assert ("b", "http://www.omg.org/spec/BPMN/20100524/MODEL") in parsed.namespaces
    assert ("x", "urn:x") in parsed.namespaces
    process = parsed.root[1]
    assert process.get("{urn:x}a") == "1"
    assert "Tä & <" in "".join(process.itertext())
    assert [node.tag for node in parsed.prolog] == [ET.Comment, ET.ProcessingInstruction]


def test_both_backends_build_identical_trees() -> None:
    if len(BACKENDS) < 2:
        pytest.skip("defusedxml nicht installiert")
    trees = [ET.tostring(parse_xml(SAMPLE, backend=b).root) for b in BACKENDS]  # type: ignore[arg-type]
    assert trees[0] == trees[1]


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("attack", ATTACKS)
def test_rejects_dtd_entities_and_external_references(backend: str, attack: str) -> None:
    with pytest.raises(UnsafeXmlError):
        parse_xml(attack, backend=backend)  # type: ignore[arg-type]


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("broken", ["<broken>", "<a><b></a>", "", "<a>&undefined;</a>"])
def test_malformed_xml_raises_parse_error_subclass(backend: str, broken: str) -> None:
    with pytest.raises(BpmnXmlError) as info:
        parse_xml(broken, backend=backend)  # type: ignore[arg-type]
    assert isinstance(info.value, ET.ParseError)
    assert "line" in str(info.value)


def test_size_limit_and_type() -> None:
    with pytest.raises(XmlTooLargeError):
        parse_xml("<a/>" + " " * 20, max_size=10)
    with pytest.raises(TypeError):
        parse_xml(42)  # type: ignore[arg-type]


def test_bytes_with_declared_encoding() -> None:
    data = '<?xml version="1.0" encoding="ISO-8859-1"?><a>Grüße</a>'.encode("iso-8859-1")
    assert safe_fromstring(data).text == "Grüße"
