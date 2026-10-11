"""Origin of an entry: confirmed by a person, imported, template or AI suggestion.

Only confirmed entries count. Imported values, template texts and AI
suggestions stay visible as unconfirmed proposals until a named person adopts
them (LIB-05, GUI-16, T-33); a seemingly complete legal reasoning from a
template or a language model never becomes a decision on its own.
"""

from __future__ import annotations

CONFIRMED = "bestaetigt"
IMPORTED = "importiert"
TEMPLATE = "vorlage"
AI_SUGGESTION = "ki_vorschlag"
ORIGINS = (CONFIRMED, IMPORTED, TEMPLATE, AI_SUGGESTION)

ORIGIN_TITLES = {
    CONFIRMED: "bestätigt",
    IMPORTED: "importiert – unbestätigt",
    TEMPLATE: "Vorlage – unbestätigt",
    AI_SUGGESTION: "KI-Vorschlag – unbestätigt",
}


def is_confirmed(origin: str) -> bool:
    """True only for entries a person entered or confirmed."""
    return origin == CONFIRMED
