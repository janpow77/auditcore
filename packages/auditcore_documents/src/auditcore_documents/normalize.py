"""Normalisierung und Wortdifferenz (unverändert aus ``parsing.py`` des Originals)."""

from __future__ import annotations

import difflib
import re

_NUMBERING = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]?|[a-z]\)|[-–—])\s*", re.IGNORECASE)


def normalise_for_match(text: str) -> str:
    """Für die Zuordnung normalisieren; führende Nummerierung wird ignoriert."""
    text = _NUMBERING.sub("", text or "")
    return re.sub(r"\s+", " ", text).strip().casefold()


def normalise_semantic(text: str) -> str:
    """Reine Zeichensetzungs- und Nummerierungsänderungen herausrechnen."""
    value = normalise_for_match(text)
    value = re.sub(r"[^\w§]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def normalise_verbatim(text: str) -> str:
    """Nur Leerraum und Groß-/Kleinschreibung vereinheitlichen."""
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def word_diff(old: str, new: str) -> list[str]:
    """``difflib.ndiff`` über Wörter; leer, wenn beide Texte gleich sind."""
    if old == new:
        return []
    return list(difflib.ndiff((old or "").split(), (new or "").split()))
