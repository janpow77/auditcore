"""Schwärzung mit Pflichtvorschau: Plan, Auswahl, Anwendung und Nachprüfung.

Ablauf
------
1. :func:`build_plan` durchsucht die Datei und liefert jede Fundstelle mit
   fester Kennung, Rechteck, Fundtext und Quelle. Gesucht wird auf dem
   Seitentext (zeichengenau, über Zeilenumbrüche und Silbentrennung hinweg)
   und in versteckten Ablagen: Metadaten, XMP, Lesezeichen, Kommentare,
   Links, Formularfelder und Dateianhänge.
2. Die Nutzerin oder der Nutzer wählt Fundstellen ab oder wieder aus und
   ergänzt bei Bedarf eigene Bereiche.
3. :func:`apply_plan` sucht mit denselben Kriterien erneut, prüft, dass
   Datei (SHA-256) und Kennungen zum Plan passen, und schwärzt genau die
   bestätigte Auswahl.
4. Anschließend wird die Ausgabe erneut durchsucht. Ist eine ausgewählte
   Fundstelle noch lesbar, wird keine Datei ausgeliefert (fail-closed).

Das Paket hängt nur von PyMuPDF ab und hält keinen Zustand; der Plan wird
nirgends gespeichert. Er enthält Klartext der Fundstellen und darf weder
protokolliert noch abgelegt werden; dasselbe gilt für die Suchbegriffe in
``Selection`` und ``ApplyReport.by_source`` und für die Meldung von
``RedactionVerificationError``. Dateigröße und Seitenzahl begrenzt der
Aufrufer.
"""

from __future__ import annotations

from auditcore_pdf.redaction.apply import apply_plan, redact_all
from auditcore_pdf.redaction.common import (
    MANUAL_SOURCE,
    MAX_AREAS,
    MAX_AREAS_PER_PAGE,
    MAX_TERM_LENGTH,
    MAX_TERMS,
    NER_PATTERN_ID,
    NER_PROPAGATED_ID,
    PLAN_VERSION,
    REDACTED_MARK,
    RedactionError,
    RedactionNerError,
    RedactionStaleError,
    RedactionVerificationError,
)
from auditcore_pdf.redaction.criteria import Criteria
from auditcore_pdf.redaction.ner_calls import SpacyPipeline, spacy_ner
from auditcore_pdf.redaction.ner_rules import NerFn
from auditcore_pdf.redaction.patterns import PATTERNS, PatternSpec, Validator, source_label
from auditcore_pdf.redaction.plan import Candidate, PageInfo, Plan
from auditcore_pdf.redaction.scan import build_plan
from auditcore_pdf.redaction.selection import ApplyReport, Area, Selection

__all__ = [
    "MANUAL_SOURCE",
    "MAX_AREAS",
    "MAX_AREAS_PER_PAGE",
    "MAX_TERMS",
    "MAX_TERM_LENGTH",
    "NER_PATTERN_ID",
    "NER_PROPAGATED_ID",
    "PATTERNS",
    "PLAN_VERSION",
    "REDACTED_MARK",
    "ApplyReport",
    "Area",
    "Candidate",
    "Criteria",
    "NerFn",
    "PageInfo",
    "PatternSpec",
    "Plan",
    "RedactionError",
    "RedactionNerError",
    "RedactionStaleError",
    "RedactionVerificationError",
    "Selection",
    "SpacyPipeline",
    "Validator",
    "apply_plan",
    "build_plan",
    "redact_all",
    "source_label",
    "spacy_ner",
]
