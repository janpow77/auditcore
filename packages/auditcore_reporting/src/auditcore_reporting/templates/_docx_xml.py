"""Safe parsing (``auditcore_common.safe_xml``, DTDs forbidden) and faithful serialisation.

ElementTree renames namespace prefixes and drops unused declarations; Word
needs the original prefixes (``mc:Ignorable="w14 wp14"`` names them). The
serialiser therefore writes every element with the prefixes declared in the
source part and repeats all source declarations on the root element.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from xml.etree.ElementTree import Element  # nosec B405 - type and tree only; parsing is defused
from xml.sax.saxutils import escape, quoteattr

from auditcore_common.safe_xml import parse_xml

from .errors import RenderDependencyError, UnsafeDocumentError

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
DECLARATION = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
_DECLARATIONS = re.compile(rb'xmlns(?::([A-Za-z_][\w.-]*))?\s*=\s*"([^"]*)"')
_MESSAGE = "DOCX-Vorlagen benötigen defusedxml: Extra auditcore_reporting[docx]."


def q(local: str) -> str:
    """Clark name in the WordprocessingML namespace (``{W}p``)."""
    return f"{{{W}}}{local}"


P, R, T, BR, TAB = q("p"), q("r"), q("t"), q("br"), q("tab")
TBL, TR, TC, BODY = q("tbl"), q("tr"), q("tc"), q("body")
TXBX, SDT_CONTENT = q("txbxContent"), q("sdtContent")


class Part:
    """A parsed XML part with the namespace declarations of its source."""

    def __init__(self, name: str, raw: bytes) -> None:
        self.name = name
        self.declarations = self._declarations(raw)
        try:
            self.root = parse_xml(
                raw, error=RenderDependencyError, message=_MESSAGE, forbid_dtd=True
            )
        except RenderDependencyError:
            raise
        except Exception as exc:  # defusedxml and expat errors
            raise UnsafeDocumentError(
                f"{name}: kein gültiges oder ein unsicheres XML ({exc})."
            ) from exc

    def _declarations(self, raw: bytes) -> dict[str, str]:
        mapping: dict[str, str] = {}
        prefixes: dict[str, str] = {}
        for prefix_raw, uri_raw in _DECLARATIONS.findall(raw):
            prefix, uri = prefix_raw.decode("utf-8"), uri_raw.decode("utf-8")
            if prefixes.setdefault(prefix, uri) != uri:
                raise UnsafeDocumentError(f"{self.name}: Präfix {prefix!r} mehrdeutig deklariert.")
            mapping.setdefault(uri, prefix)
        return mapping

    def to_bytes(self) -> bytes:
        """Serialised part (UTF-8, standalone declaration as Word writes it)."""
        out: list[str] = []
        try:
            self._write(self.root, out, root=True)
        except RecursionError as exc:
            raise UnsafeDocumentError(f"{self.name}: zu tief verschachtelt.") from exc
        return DECLARATION + "".join(out).encode("utf-8")

    def _name(self, clark: str) -> str:
        if not clark.startswith("{"):
            return clark
        uri, local = clark[1:].split("}", 1)
        if uri == XML_NS:
            return f"xml:{local}"
        if uri not in self.declarations:
            raise UnsafeDocumentError(f"{self.name}: Namensraum {uri!r} ohne Präfix.")
        prefix = self.declarations[uri]
        return f"{prefix}:{local}" if prefix else local

    def _write(self, element: Element, out: list[str], root: bool = False) -> None:
        name = self._name(element.tag)
        attributes = [f" {self._name(k)}={quoteattr(v)}" for k, v in element.attrib.items()]
        if root:
            attributes[:0] = [
                f" xmlns{':' + prefix if prefix else ''}={quoteattr(uri)}"
                for uri, prefix in self.declarations.items()
            ]
        out.append(f"<{name}{''.join(attributes)}")
        if element.text is None and len(element) == 0:
            out.append("/>")
        else:
            out.append(">" + escape(element.text or ""))
            for child in element:
                self._write(child, out)
                out.append(escape(child.tail or ""))
            out.append(f"</{name}>")


def own_texts(paragraph: Element) -> tuple[list[Element], list[Element]]:
    """``w:t`` of a paragraph and its text box containers (nested paragraphs excluded)."""
    texts: list[Element] = []
    boxes: list[Element] = []
    stack = list(reversed(list(paragraph)))
    while stack:
        element = stack.pop()
        if element.tag == T:
            texts.append(element)
        elif element.tag == TXBX:
            boxes.append(element)
        else:
            stack.extend(reversed(list(element)))
    return texts, boxes


def paragraph_text(paragraph: Element) -> str:
    """Visible own text of a paragraph (``w:t`` only)."""
    return "".join(t.text or "" for t in own_texts(paragraph)[0])


def all_text(element: Element) -> str:
    """Every ``w:t`` below ``element`` (used for whole table rows)."""
    return "".join(t.text or "" for t in element.iter(T))


def iter_paragraphs(root: Element) -> Iterator[Element]:
    """All paragraphs in document order."""
    return root.iter(P)
