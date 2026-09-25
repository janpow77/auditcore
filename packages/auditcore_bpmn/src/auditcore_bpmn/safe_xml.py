"""Gehärtetes Parsen von BPMN-XML.

Weist jede Dokumenttyp-Deklaration (DTD), Entitätsdeklaration und jeden
externen Verweis ab (kein XXE, keine Entitätsexpansion). Mit installiertem
Extra ``xml`` läuft das Parsen über ``defusedxml`` (``forbid_dtd``,
``forbid_entities``, ``forbid_external``); ohne Extra über einen
gleichwertig gehärteten Expat-Parser der Standardbibliothek. Beide Wege
liefern denselben Baum und dieselben Fehlerklassen. BPMN-Dateien enthalten
nie eine DTD.

Kommentare, Verarbeitungsanweisungen und die Präfixe der
Namensraumdeklarationen bleiben erhalten, damit :mod:`auditcore_bpmn.serialize`
das Dokument ohne Bedeutungsverlust zurückschreiben kann.
"""

from __future__ import annotations

import xml.parsers.expat as expat
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, NoReturn
from xml.etree import ElementTree as ET

from .errors import BpmnXmlError, UnsafeXmlError, XmlTooLargeError

#: Höchstgröße in Zeichen bzw. Bytes (wie das Altschema ``max_length=5_000_000``).
MAX_XML_SIZE = 5_000_000

Backend = Literal["auto", "defusedxml", "expat"]


@dataclass
class ParsedXml:
    """Wurzel des geparsten Dokuments und seine Namensraumdeklarationen."""

    root: ET.Element
    #: ``(präfix, uri)`` in Dokumentreihenfolge; ``""`` ist der Standardnamensraum.
    namespaces: list[tuple[str, str]] = field(default_factory=list)
    #: Tatsächlich verwendeter Parser: ``"defusedxml"`` oder ``"expat"``.
    backend: str = "expat"
    #: Kommentare und Verarbeitungsanweisungen vor dem Wurzelelement.
    prolog: list[ET.Element[Any]] = field(default_factory=list)


class _Target:
    """Parser-Ziel: ElementTree-Baum plus Namensraumdeklarationen."""

    def __init__(self) -> None:
        self._builder = ET.TreeBuilder(insert_comments=True, insert_pis=True)
        self.namespaces: list[tuple[str, str]] = []
        self.prolog: list[ET.Element[Any]] = []
        self._depth = 0

    def start_ns(self, prefix: str | None, uri: str | None) -> None:
        """Hält eine Namensraumdeklaration fest."""
        self.namespaces.append((prefix or "", uri or ""))

    def start(self, tag: str, attrs: dict[str, str]) -> ET.Element:
        """Beginn eines Elements."""
        self._depth += 1
        return self._builder.start(tag, attrs)

    def end(self, tag: str) -> ET.Element:
        """Ende eines Elements."""
        self._depth -= 1
        return self._builder.end(tag)

    def data(self, text: str) -> None:
        """Textinhalt."""
        self._builder.data(text)

    def comment(self, text: str) -> ET.Element | None:
        """Kommentar (vor der Wurzel im Prolog)."""
        if self._depth == 0:
            self.prolog.append(ET.Comment(text))
            return None
        return self._builder.comment(text)

    def pi(self, target: str, text: str | None = None) -> ET.Element | None:
        """Verarbeitungsanweisung (vor der Wurzel im Prolog)."""
        if self._depth == 0:
            self.prolog.append(ET.ProcessingInstruction(target, text))
            return None
        return self._builder.pi(target, text)

    def close(self) -> ET.Element:
        """Wurzelelement."""
        return self._builder.close()


def _check_size(data: str | bytes, max_size: int) -> None:
    if len(data) > max_size:
        raise XmlTooLargeError(f"BPMN-XML ist zu groß ({len(data)} > {max_size} Zeichen bzw. Bytes).")


def _syntax_error(error: expat.ExpatError) -> BpmnXmlError:
    """Fehlermeldung wie ``xml.etree.ElementTree`` (Code, Zeile, Spalte)."""
    message = f"{expat.ErrorString(error.code)}: line {error.lineno}, column {error.offset}"
    result = BpmnXmlError(message)
    result.code = error.code
    result.position = (error.lineno, error.offset)
    return result


def _reject(kind: str) -> Callable[..., NoReturn]:
    def handler(*_args: object) -> NoReturn:
        raise UnsafeXmlError(f"XML mit {kind} wird nicht verarbeitet.")

    return handler


def _parse_expat(data: str | bytes) -> _Target:
    target = _Target()
    parser = expat.ParserCreate(namespace_separator="}")
    parser.buffer_text = True
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)

    def fix(name: str) -> str:
        return "{" + name if "}" in name else name

    def start(name: str, attrs: dict[str, str]) -> None:
        target.start(fix(name), {fix(key): value for key, value in attrs.items()})

    parser.StartElementHandler = start
    parser.EndElementHandler = lambda name: target.end(fix(name))
    parser.CharacterDataHandler = target.data
    parser.CommentHandler = target.comment
    parser.ProcessingInstructionHandler = target.pi
    parser.StartNamespaceDeclHandler = target.start_ns
    parser.StartDoctypeDeclHandler = _reject("DOCTYPE-Deklaration")
    parser.EntityDeclHandler = _reject("Entitätsdeklaration")
    parser.UnparsedEntityDeclHandler = _reject("Entitätsdeklaration")
    parser.ExternalEntityRefHandler = _reject("externem Verweis")
    try:
        parser.Parse(data, True)
    except expat.ExpatError as error:
        raise _syntax_error(error) from error
    return target


def _parse_defused(data: str | bytes) -> _Target:
    from defusedxml.common import DefusedXmlException
    from defusedxml.ElementTree import DefusedXMLParser

    target = _Target()
    parser = DefusedXMLParser(target=target, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    try:
        parser.feed(data)
        parser.close()
    except DefusedXmlException as error:
        raise UnsafeXmlError(f"XML mit DTD, Entität oder externem Verweis wird nicht verarbeitet: {error}") from error
    except ET.ParseError as error:
        result = BpmnXmlError(str(error))
        result.code = getattr(error, "code", 0)
        result.position = getattr(error, "position", (0, 0))
        raise result from error
    return target


def defusedxml_available() -> bool:
    """``True``, wenn das Extra ``xml`` (defusedxml) installiert ist."""
    try:
        import defusedxml.ElementTree  # noqa: F401
    except ImportError:
        return False
    return True


def parse_xml(data: str | bytes, *, max_size: int = MAX_XML_SIZE, backend: Backend = "auto") -> ParsedXml:
    """Parst BPMN-XML gehärtet.

    :raises XmlTooLargeError: Dokument größer als ``max_size``.
    :raises UnsafeXmlError: DTD, Entitäten oder externe Verweise.
    :raises BpmnXmlError: nicht wohlgeformt.
    """
    if not isinstance(data, str | bytes):
        raise TypeError("BPMN-XML muss als str oder bytes übergeben werden.")
    _check_size(data, max_size)
    use_defused = backend == "defusedxml" or (backend == "auto" and defusedxml_available())
    target = _parse_defused(data) if use_defused else _parse_expat(data)
    try:
        root = target.close()
    except Exception as error:  # pragma: no cover - nur bei leerem Dokument erreichbar
        raise BpmnXmlError(f"BPMN-XML ist leer: {error}") from error
    return ParsedXml(
        root=root,
        namespaces=target.namespaces,
        backend="defusedxml" if use_defused else "expat",
        prolog=target.prolog,
    )


def safe_fromstring(data: str | bytes, *, max_size: int = MAX_XML_SIZE) -> ET.Element:
    """Kurzform: nur das Wurzelelement."""
    return parse_xml(data, max_size=max_size).root
