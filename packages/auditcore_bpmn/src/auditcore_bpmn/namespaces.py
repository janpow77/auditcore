"""XML-Namensräume von BPMN 2.0 und der FlowAudit-Erweiterung."""

from __future__ import annotations

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

#: Unveränderter Namensraum seit Schema 1.0; die Version 1.1 steht im
#: Attribut ``schemaVersion`` von ``flowaudit:diagrammInfo``.
FLOWAUDIT_NAMESPACE = "https://flowaudit.de/bpmn/schema/1.0"
FLOWAUDIT_PREFIX = "flowaudit"
FLOWAUDIT_SCHEMA_VERSION = "1.1"

#: Bevorzugte Präfixe beim Schreiben, falls das Dokument keine eigenen hat.
PREFERRED_PREFIXES = {
    BPMN_NS: "bpmn",
    BPMNDI_NS: "bpmndi",
    DC_NS: "dc",
    DI_NS: "di",
    XSI_NS: "xsi",
    FLOWAUDIT_NAMESPACE: FLOWAUDIT_PREFIX,
}


def q(namespace: str, local: str) -> str:
    """Qualifizierter Name in ElementTree-Schreibweise ``{uri}local``."""
    return f"{{{namespace}}}{local}"


def local_name(tag: object) -> str:
    """Lokaler Name eines Tags; Kommentare und Verarbeitungsanweisungen ergeben ``""``."""
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def namespace_of(tag: object) -> str | None:
    """Namensraum eines Tags oder ``None`` ohne Namensraum."""
    if isinstance(tag, str) and tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return None


def is_bpmn(tag: object, *locals_: str) -> bool:
    """``True``, wenn ``tag`` im BPMN-Namensraum liegt (und optional einen der Namen trägt)."""
    if namespace_of(tag) != BPMN_NS:
        return False
    return not locals_ or local_name(tag) in locals_


def is_flowaudit(tag: object, *locals_: str) -> bool:
    """``True``, wenn ``tag`` im FlowAudit-Namensraum liegt (und optional einen der Namen trägt)."""
    if namespace_of(tag) != FLOWAUDIT_NAMESPACE:
        return False
    return not locals_ or local_name(tag) in locals_


#: Farbangaben gängiger Modellierungswerkzeuge an DI-Formen.
BIOC_NS = "http://bpmn.io/schema/bpmn/biocolor/1.0"
COLOR_NS = "http://www.omg.org/spec/BPMN/non-normative/color/1.0"
