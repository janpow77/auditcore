"""Ähnlichkeitsmaße für die Zuordnung.

Das Original wählte das Maß still nach der Umgebung: ``rapidfuzz`` (Produktion,
``token_set_ratio``) oder – falls der Import scheiterte – ``difflib``. Beide
liefern andere Zuordnungen. Hier wird das Maß ausdrücklich benannt; fehlt
``rapidfuzz`` für ein Profil, das es verlangt, folgt ``DependencyError``
statt eines stillen Wechsels (Verhaltensänderung DC-C01).
"""

from __future__ import annotations

import difflib
from collections.abc import Callable
from typing import Literal

from auditcore_documents.errors import DependencyError

ScorerName = Literal["rapidfuzz-token-set", "difflib-ratio"]
#: Ähnlichkeit zweier bereits normalisierter Texte als ganze Zahl 0–100.
Scorer = Callable[[str, str], int]


def difflib_ratio(left: str, right: str) -> int:
    """Rückfall des Originals: ``round(100 * SequenceMatcher.ratio())``."""
    return round(100 * difflib.SequenceMatcher(None, left, right).ratio())


def _token_set_ratio() -> Callable[[str, str], float]:
    try:
        from rapidfuzz import fuzz
    except ImportError as exc:
        raise DependencyError(
            "Das Ähnlichkeitsmaß rapidfuzz-token-set benötigt das Extra "
            "'fuzzy' (rapidfuzz); ein stiller Wechsel auf difflib erfolgt nicht."
        ) from exc
    return fuzz.token_set_ratio


def rapidfuzz_token_set() -> Scorer:
    """Produktionsmaß des Originals: ``round(float(fuzz.token_set_ratio(a, b)))``."""
    ratio = _token_set_ratio()

    def score(left: str, right: str) -> int:
        return round(float(ratio(left, right)))

    return score


def get_scorer(name: ScorerName) -> Scorer:
    if name == "rapidfuzz-token-set":
        return rapidfuzz_token_set()
    if name == "difflib-ratio":
        return difflib_ratio
    raise ValueError(f"Unbekanntes Ähnlichkeitsmaß: {name}")
