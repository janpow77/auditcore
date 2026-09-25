"""safe_xml and html_text against the package copies (differential)."""

from __future__ import annotations

import sys

import legacy_reference as legacy
import pytest
from samples import SAMPLES, assert_same_outcome, rng

from auditcore_common import html_text
from auditcore_common.html_text import DOCUMENT_MARKERS, anchor_links, has_html_marker
from auditcore_common.safe_xml import defused_fromstring, parse_xml

XML_MESSAGE = "Für XML-Sanktionslisten ist 'auditcore_registry_sources[xml]' zu installieren."
DOCUMENTS = [
    b"<a/>",
    b"<?xml version='1.0'?><ns:list xmlns:ns='urn:x'><ns:e id='1'>T\xc3\xa4xt</ns:e></ns:list>",
    b"<a><b>1</b><b>2</b></a>",
    b"<a>",
    b"",
    b"<!DOCTYPE a [<!ENTITY e 'x'>]><a>&e;</a>",
    b"<!DOCTYPE a SYSTEM 'http://example.invalid/a.dtd'><a/>",
    b'<!DOCTYPE a [<!ENTITY % p SYSTEM "file:///etc/passwd"> %p;]><a/>',
]


def _parse_new(data: bytes) -> object:
    from xml.etree.ElementTree import tostring  # nosec B405 - serialising a parsed tree

    return tostring(
        parse_xml(data, error=legacy.DependencyError, message=XML_MESSAGE), encoding="unicode"
    )


def _parse_old(data: bytes) -> object:
    from xml.etree.ElementTree import tostring  # nosec B405 - serialising a parsed tree

    return tostring(legacy.registry_fromstring(data), encoding="unicode")


@pytest.mark.parametrize("data", DOCUMENTS)
def test_parse_xml_matches_registry(data: bytes) -> None:
    assert_same_outcome(lambda: _parse_old(data), lambda: _parse_new(data))


def test_forbid_dtd_is_passed_through() -> None:
    from defusedxml import DTDForbidden

    with pytest.raises(DTDForbidden):
        parse_xml(DOCUMENTS[5], error=legacy.DependencyError, message="m", forbid_dtd=True)


def test_missing_defusedxml_raises_the_callers_error(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [m for m in sys.modules if m.startswith("defusedxml")]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, "defusedxml", None)
    assert_same_outcome(lambda: _parse_old(b"<a/>"), lambda: _parse_new(b"<a/>"))
    with pytest.raises(legacy.DependencyError) as info:
        defused_fromstring(legacy.DependencyError, "fehlt")
    assert str(info.value) == "fehlt" and isinstance(info.value.__cause__, ImportError)


TOKENS = [
    "<a href='x'>",
    '<a href="/y?q=1&amp;z=2">',
    "<a>",
    "<a href=''>",
    "<a name=n href=z>",
    "</a>",
    "<A HREF='u'>",
    "</A>",
    "<b>",
    "</b>",
    " text ",
    "Übersicht",
    "&amp;",
    "&#x41;",
    "\n\t",
    "<script>",
    "</script>",
    "<!-- c -->",
    "<br/>",
    "<a href=v/>",
    "<p",
    "<",
    "a",
]


def _old_links(html: str) -> list[tuple[str, str]]:
    parser = legacy.LegalLinks()
    parser.feed(html)
    return parser.links


def test_anchor_links_match_legal_parser() -> None:
    r = rng(41)
    for _ in range(SAMPLES):
        html = "".join(r.choice(TOKENS) for _ in range(r.randint(0, 25)))
        assert_same_outcome(lambda: _old_links(html), lambda: anchor_links(html))
    assert html_text.LinkCollector().links == []


def _property_old(body: str) -> bool:
    return not ("<html" not in body[:4096].lower() and "<!doctype" not in body[:4096].lower())


def _legal_old(text: str) -> bool:
    return not ("<a" not in text.lower() and "<html" not in text.lower())


def test_has_html_marker_matches_property_and_legal() -> None:
    r = rng(42)
    parts = ["<HTML>", "<!DOCTYPE html>", "<a ", "x" * 4000, "İ" * 2100, "<ht", "ml>", "y"]
    texts = ["", "<html", "x" * 4092 + "<html", "x" * 4093 + "<html"] + [
        "".join(r.choice(parts) for _ in range(r.randint(0, 6))) for _ in range(SAMPLES)
    ]
    for text in texts:
        assert _property_old(text) == has_html_marker(text)
        assert _property_old(text) == has_html_marker(text, DOCUMENT_MARKERS, window=4096)
        assert _legal_old(text) == has_html_marker(text, ("<a", "<html"), window=None)
