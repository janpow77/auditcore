"""Fehlerklassen von auditcore_bpmn."""

from __future__ import annotations

from xml.etree.ElementTree import ParseError


class BpmnError(Exception):
    """Basisklasse aller Fehler dieses Pakets."""


class BpmnXmlError(BpmnError, ParseError):
    """BPMN-XML ist nicht wohlgeformt.

    Unterklasse von :class:`xml.etree.ElementTree.ParseError`, damit
    vorhandene ``except ParseError``-Zweige der Anwendungen weiter greifen.
    """


class UnsafeXmlError(BpmnXmlError):
    """Abgewiesenes Dokument: DTD, Entitäten oder externe Verweise."""


class XmlTooLargeError(BpmnXmlError):
    """Das Dokument überschreitet die zulässige Größe."""


class CollectionError(BpmnError, ValueError):
    """Unzulässige Änderung oder unzulässiger Inhalt einer Diagrammsammlung."""


class CatalogError(BpmnError, ValueError):
    """Unbekannter oder fehlerhafter Katalog."""


class OptionalDependencyError(BpmnError, ImportError):
    """Ein optionales Extra ist nicht installiert."""
