"""Zurückschreiben eines geparsten Dokuments ohne Bedeutungsverlust.

``xml.etree.ElementTree.tostring`` vergibt eigene Präfixe (``ns0``) und
bricht damit QName-Werte wie ``xsi:type="bpmn:tFormalExpression"``. Dieser
Schreiber verwendet die Präfixe des Originaldokuments, deklariert alle
Namensräume am Wurzelelement, erhält Kommentare und
Verarbeitungsanweisungen und arbeitet ohne globalen Zustand (threadsicher).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from xml.etree import ElementTree as ET

from .namespaces import PREFERRED_PREFIXES, namespace_of
from .safe_xml import ParsedXml


def _escape_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _escape_attr(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("\n", "&#10;")
        .replace("\r", "&#13;")
        .replace("\t", "&#09;")
    )


class _PrefixMap:
    """Zuordnung URI → Präfix, bevorzugt aus dem Originaldokument."""

    def __init__(self, declared: Iterable[tuple[str, str]]) -> None:
        self.by_uri: dict[str, str] = {}
        self.used_prefixes: set[str] = set()
        self.default_uri: str | None = None
        for prefix, uri in declared:
            if not uri:
                continue
            if prefix == "":
                if self.default_uri is None and uri not in self.by_uri:
                    self.default_uri = uri
                    self.by_uri[uri] = ""
                continue
            if uri not in self.by_uri and prefix not in self.used_prefixes:
                self.by_uri[uri] = prefix
                self.used_prefixes.add(prefix)
        self._attribute_alias: dict[str, str] = {}

    def _new_prefix(self, uri: str) -> str:
        preferred = PREFERRED_PREFIXES.get(uri)
        if preferred and preferred not in self.used_prefixes:
            prefix = preferred
        else:
            number = 0
            while f"ns{number}" in self.used_prefixes:
                number += 1
            prefix = f"ns{number}"
        self.used_prefixes.add(prefix)
        return prefix

    def element_prefix(self, uri: str) -> str:
        """Präfix eines Namensraums für Elemente."""
        if uri not in self.by_uri:
            self.by_uri[uri] = self._new_prefix(uri)
        return self.by_uri[uri]

    def attribute_prefix(self, uri: str) -> str:
        """Attribute brauchen stets ein Präfix; Standardnamensraum gilt nicht für sie."""
        prefix = self.element_prefix(uri)
        if prefix:
            return prefix
        if uri not in self._attribute_alias:
            self._attribute_alias[uri] = self._new_prefix(uri)
        return self._attribute_alias[uri]

    def declarations(self) -> list[tuple[str, str]]:
        """Alle zu deklarierenden Namensräume."""
        result = [(prefix, uri) for uri, prefix in self.by_uri.items()]
        result += [(prefix, uri) for uri, prefix in self._attribute_alias.items()]
        return sorted(result, key=lambda item: (item[0] != "", item[0]))


def _qualified(name: str, prefixes: _PrefixMap, *, attribute: bool) -> str:
    uri = namespace_of(name)
    if uri is None:
        return name
    local = name.split("}", 1)[1]
    if uri == "http://www.w3.org/XML/1998/namespace":
        return f"xml:{local}"
    prefix = prefixes.attribute_prefix(uri) if attribute else prefixes.element_prefix(uri)
    return f"{prefix}:{local}" if prefix else local


def _collect(element: ET.Element, prefixes: _PrefixMap) -> None:
    for node in element.iter():
        if isinstance(node.tag, str):
            _qualified(node.tag, prefixes, attribute=False)
            for key in node.attrib:
                _qualified(key, prefixes, attribute=True)


def _write(element: ET.Element[Any], prefixes: _PrefixMap, out: list[str], root: bool) -> None:
    tag: object = element.tag
    if tag is ET.Comment:
        out.append(f"<!--{element.text or ''}-->")
    elif tag is ET.ProcessingInstruction:
        out.append(f"<?{element.text or ''}?>")
    else:
        name = _qualified(str(tag), prefixes, attribute=False)
        out.append(f"<{name}")
        if root:
            for prefix, uri in prefixes.declarations():
                attribute = f"xmlns:{prefix}" if prefix else "xmlns"
                out.append(f' {attribute}="{_escape_attr(uri)}"')
        for key, value in element.attrib.items():
            out.append(f' {_qualified(key, prefixes, attribute=True)}="{_escape_attr(value)}"')
        if element.text or len(element):
            out.append(">")
            if element.text:
                out.append(_escape_text(element.text))
            for child in element:
                _write(child, prefixes, out, root=False)
            out.append(f"</{name}>")
        else:
            out.append("/>")
    if not root and element.tail:
        out.append(_escape_text(element.tail))


def serialize_element(
    element: ET.Element,
    namespaces: Iterable[tuple[str, str]] = (),
    *,
    xml_declaration: bool = True,
    prolog: Iterable[ET.Element] = (),
) -> str:
    """Schreibt ``element`` als vollständiges Dokument (UTF-8-Deklaration)."""
    prefixes = _PrefixMap(namespaces)
    _collect(element, prefixes)
    out: list[str] = []
    if xml_declaration:
        out.append('<?xml version="1.0" encoding="UTF-8"?>\n')
    for node in prolog:
        _write(node, prefixes, out, root=False)
        out.append("\n")
    _write(element, prefixes, out, root=True)
    out.append("\n")
    return "".join(out)


def serialize(parsed: ParsedXml, *, xml_declaration: bool = True) -> str:
    """Schreibt ein mit :func:`auditcore_bpmn.safe_xml.parse_xml` gelesenes Dokument zurück."""
    return serialize_element(
        parsed.root,
        parsed.namespaces,
        xml_declaration=xml_declaration,
        prolog=parsed.prolog,
    )
