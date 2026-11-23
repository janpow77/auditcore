"""Aufruf der KI-Namenserkennung: Ergebnisprüfung und spaCy-Adapter."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol

from auditcore_pdf.redaction.common import RedactionNerError
from auditcore_pdf.redaction.ner_rules import NerFn


class _Entity(Protocol):
    @property
    def start_char(self) -> int: ...
    @property
    def end_char(self) -> int: ...
    @property
    def label_(self) -> str: ...


class _Doc(Protocol):
    @property
    def ents(self) -> Sequence[_Entity]: ...


class SpacyPipeline(Protocol):
    """Was der Adapter von einer spaCy-Pipeline braucht."""

    def pipe(self, texts: Iterable[str]) -> Iterable[_Doc]: ...


_FAILED = "KI-Namenserkennung ist fehlgeschlagen"
_INVALID = "KI-Namenserkennung lieferte ein ungültiges Ergebnis"


def _ner_results(ner: NerFn, jobs: list[str]) -> list[list[tuple[int, int]]]:
    """Ergebnis der KI prüfen: je Text eine Liste von (start, ende)."""
    if not jobs:
        return []
    try:
        raw = ner(jobs)
    except Exception as exc:  # Fehler der KI-Funktion selbst: Serverseite
        raise RedactionNerError(_FAILED) from exc
    try:
        items = iter(raw)
    except TypeError as exc:  # kein Ergebnis in Listenform
        raise RedactionNerError(_INVALID) from exc
    try:
        # Generatoren (auch innere) laufen erst hier: ihre Fehler sind
        # Fehler der KI-Funktion, falsche Werte ein ungültiges Ergebnis.
        results = [[(int(s), int(e)) for s, e in spans] for spans in items]
    except (TypeError, ValueError) as exc:
        raise RedactionNerError(_INVALID) from exc
    except Exception as exc:
        raise RedactionNerError(_FAILED) from exc
    if len(results) != len(jobs):
        raise RedactionNerError(_INVALID)
    return results


def spacy_ner(nlp: SpacyPipeline) -> NerFn:
    """Adapter: spaCy-Pipeline → Zeichenspannen der Personennamen je Text."""

    def run(texts: list[str]) -> list[list[tuple[int, int]]]:
        result: list[list[tuple[int, int]]] = []
        for doc in nlp.pipe(texts):
            result.append([(e.start_char, e.end_char) for e in doc.ents if e.label_ == "PER"])
        return result

    return run
