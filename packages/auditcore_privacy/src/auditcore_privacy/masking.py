"""Maskierung von Textauszügen zur sicheren Anzeige in Prüfberichten."""

from __future__ import annotations


def mask_text(text: str, *, prefix_len: int = 4, suffix_len: int = 2) -> str:
    """Maskiert sensible Zeichenfolgen mit Schutzpunkten (•).

    Kurze Zeichenfolgen werden vollständig überdeckt, damit keine identifizierenden
    Reste verbleiben. Bei längeren Werten bleiben wenige Randzeichen zur
    Wiedererkennung erhalten.
    """
    cleaned = " ".join(str(text).split())
    length = len(cleaned)
    if length == 0:
        return ""
    if length <= prefix_len + suffix_len + 2:
        return "•" * length
    middle_count = max(3, length - prefix_len - suffix_len)
    return f"{cleaned[:prefix_len]}{'•' * middle_count}{cleaned[-suffix_len:]}"
