"""Gezielte Änderungen an BPMN-Dokumenten (FlowAudit-Erweiterungen).

Alle Funktionen nehmen XML (``str``/``bytes``) oder ein :class:`BpmnDocument`
und liefern das geänderte Dokument als XML-Text. Alles außerhalb der
betroffenen FlowAudit-Elemente bleibt erhalten (DI, fremde Erweiterungen,
Kommentare, Präfixe). Ein übergebenes Modell wird nicht verändert.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from .errors import BpmnError
from .extensions import DiagramInfo, Extensions, write_extensions
from .model import BpmnDocument, document_from_xml, parse_bpmn
from .namespaces import BPMN_NS, FLOWAUDIT_SCHEMA_VERSION
from .safe_xml import parse_xml
from .serialize import serialize


def copy_document(source: str | bytes | BpmnDocument) -> BpmnDocument:
    """Unabhängige, veränderbare Kopie (über einen Rundlauf)."""
    if isinstance(source, BpmnDocument):
        return document_from_xml(parse_xml(serialize(source.parsed)))
    return parse_bpmn(source)


def main_element_id(document: BpmnDocument) -> str:
    """Träger der Diagramm-Infos: Kollaboration, sonst erster Prozess."""
    for element_type in ("collaboration", "process"):
        for element in document.by_type(element_type):
            return element.id
    raise BpmnError("Das Dokument enthält weder bpmn:collaboration noch bpmn:process.")


def set_diagram_info(source: str | bytes | BpmnDocument, info: DiagramInfo) -> str:
    """Schreibt ``flowaudit:diagrammInfo`` (Schema 1.1) an das Hauptelement; genau ein Vorkommen."""
    document = copy_document(source)
    target = main_element_id(document)
    owner = document.diagram_info_owner
    if owner and owner != target:
        write_extensions(document.xml_element(owner), Extensions(), replace=["diagrammInfo"])
    info = replace(info, schema_version=FLOWAUDIT_SCHEMA_VERSION)
    write_extensions(document.xml_element(target), Extensions(diagram_info=info), replace=["diagrammInfo"])
    return serialize(document.parsed)


def set_extensions(
    source: str | bytes | BpmnDocument,
    element_id: str,
    extensions: Extensions,
    *,
    replace_kinds: Iterable[str] | None = None,
) -> str:
    """Schreibt FlowAudit-Angaben an ein Element.

    ``replace_kinds`` nennt die lokalen XML-Namen, die ersetzt werden (z. B.
    ``["rechtsgrundlage"]`` zum Leeren); ohne Angabe genau die in
    ``extensions`` gesetzten Arten. Strukturierte Rechtsgrundlagen erhalten
    ihre ausgeschriebene Normalform als Textinhalt.
    """
    document = copy_document(source)
    if element_id not in document.elements:
        raise BpmnError(f"Element „{element_id}“ ist im Dokument nicht vorhanden.")
    extensions = replace(extensions, legal_bases=tuple(item.normalized() for item in extensions.legal_bases))
    write_extensions(document.xml_element(element_id), extensions, replace=replace_kinds)
    return serialize(document.parsed)


def remove_extensions(source: str | bytes | BpmnDocument, element_id: str, *kinds: str) -> str:
    """Entfernt die genannten FlowAudit-Elemente (lokale XML-Namen) an einem Element."""
    return set_extensions(source, element_id, Extensions(), replace_kinds=kinds)


def new_definitions(process_id: str = "Process_1", name: str | None = None) -> str:
    """Minimales BPMN-Dokument mit Startereignis."""
    name_attribute = f' name="{name}"' if name else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<bpmn:definitions xmlns:bpmn="{BPMN_NS}" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">'
        f'<bpmn:process id="{process_id}" isExecutable="false"{name_attribute}>'
        '<bpmn:startEvent id="StartEvent_1"/></bpmn:process></bpmn:definitions>\n'
    )
