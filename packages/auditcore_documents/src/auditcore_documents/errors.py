"""Fehlervertrag der Bibliothek.

``CompareError`` entspricht dem gleichnamigen Fehler des Originals
(``ValueError``, vom Nutzer behebbar). ``ParseError`` war im Original eine
eigene ``ValueError``-Unterklasse, die die Fassade in ``CompareError``
übersetzte; hier ist sie direkt eine Unterklasse von ``CompareError``, damit
Aufrufer mit einem ``except CompareError`` alle fachlichen Fehler erfassen.
"""

from __future__ import annotations


class CompareError(ValueError):
    """Ein vom Nutzer behebbarer Vergleichsfehler."""


class ParseError(CompareError):
    """Beschädigte, geschützte, nicht unterstützte oder unlesbare Eingabe."""


class DependencyError(CompareError):
    """Ein optionales Extra (lxml, pypdf, rapidfuzz, python-docx) fehlt."""


class LimitExceededError(ParseError):
    """Eine konfigurierte Ressourcengrenze wurde überschritten."""
