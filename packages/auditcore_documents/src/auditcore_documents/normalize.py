"""Abgleichsnormalisierung und Wortdifferenz (unverändert aus ``parsing.py`` des Originals).

Die ``normalise_*``-Funktionen erzeugen **Vergleichsschlüssel**, keinen Text
zur Weitergabe: Sie schreiben klein (``casefold``), vereinheitlichen
Leerraum und entfernen je nach Variante führende Nummerierungen und
Satzzeichen. Für Zuordnung, Ähnlichkeit und Änderungsart ist das gewollt;
für Extraktion, Anzeige oder Ablage (Beträge, Kennungen, Gliederungsnummern,
Zitate) sind sie ungeeignet, weil Information verloren geht. Extraktion
arbeitet auf dem Originaltext (``CompareItem.text``, ``read_text_paragraphs``).
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Callable
from typing import Literal

_NUMBERING = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]?|[a-z]\)|[-–—])\s*", re.IGNORECASE)

#: ``"once"``: eine führende Nummerierung je Aufruf (Original, charakterisiert,
#: Standard aller Vergleichsprofile); ``"all"``: bis zum Fixpunkt, idempotent.
Numbering = Literal["once", "all"]


def _fixpoint(step: Callable[[str], str], text: str) -> str:
    """``step`` wiederholen, bis sich nichts mehr ändert (jeder Schritt kürzt oder hält)."""
    current = step(text)
    for _ in range(len(current) + 1):
        following = step(current)
        if following == current:
            return current
        current = following
    return current


def _for_match_once(text: str) -> str:
    text = _NUMBERING.sub("", text or "")
    return re.sub(r"\s+", " ", text).strip().casefold()


def _semantic_once(text: str) -> str:
    value = _for_match_once(text)
    value = re.sub(r"[^\w§]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def normalise_for_match(text: str, *, numbering: Numbering = "once") -> str:
    """Vergleichsschlüssel für die Zuordnung; führende Nummerierung wird ignoriert.

    Nur für den Abgleich: Kleinschreibung und Entfernen der Nummerierung
    verändern den Text; nicht für Extraktion oder Anzeige verwenden.

    ``numbering="once"`` (Standard) entfernt wie das Original genau eine
    führende Nummerierung und ist deshalb nicht idempotent („1. 2. Text“ →
    „2. text“); ``numbering="all"`` entfernt alle und ist idempotent.
    """
    return _for_match_once(text) if numbering == "once" else _fixpoint(_for_match_once, text)


def normalise_semantic(text: str, *, numbering: Numbering = "once") -> str:
    """Vergleichsschlüssel ohne Zeichensetzung und Nummerierung (Änderungsart).

    Nur für den Abgleich: entfernt zusätzlich Satzzeichen (auch Dezimal- und
    Datumstrenner); nicht für Extraktion oder Anzeige verwenden.

    ``numbering`` wie bei :func:`normalise_for_match`; mit ``"all"`` werden
    auch Ziffern entfernt, die erst das Streichen der Satzzeichen freilegt
    („:0“ → „“), das Ergebnis ist idempotent.
    """
    return _semantic_once(text) if numbering == "once" else _fixpoint(_semantic_once, text)


def normalise_verbatim(text: str) -> str:
    """Vergleichsschlüssel: nur Leerraum und Groß-/Kleinschreibung vereinheitlichen.

    Nur für den Abgleich (wortgleiche Fassungen erkennen), nicht für Extraktion.
    """
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def word_diff(old: str, new: str) -> list[str]:
    """``difflib.ndiff`` über Wörter; leer, wenn beide Texte gleich sind."""
    if old == new:
        return []
    return list(difflib.ndiff((old or "").split(), (new or "").split()))
