"""Gemeinsame Konstanten, Fehlerklassen und Textnormalisierung der Schwärzung."""

from __future__ import annotations

import hashlib
import unicodedata
from typing import TypeAlias

PLAN_VERSION = 1
MAX_TERMS = 200
MAX_TERM_LENGTH = 200
MAX_AREAS = 500
MAX_AREAS_PER_PAGE = 100
REDACTED_MARK = "[geschwärzt]"
NER_PATTERN_ID = "ki_namen"
MANUAL_SOURCE = "bereich"

# Quelle der Fundstellen, die nicht die KI selbst gemeldet hat, sondern die
# als bereits erkannter Name im Dokument nachgesucht wurden. Eigene Gruppe,
# damit die Vorschau sie gesammelt abwählen kann.
NER_PROPAGATED_ID = "ki_namen_nachgesucht"

# Prüfgruppe der Nachprüfung für alle versteckten Ablagen.
HIDDEN_GROUP = "versteckte Inhalte"

# Trennzeichen im Suchtext. HARD trennt Spalten oder Absätze, über die kein
# Treffer laufen darf (kein Leerraum für ``\s``), SOFT steht für einen
# gewöhnlichen Zeilenumbruch im Fließtext.
_HARD = "\x00"
_SOFT = " "
_HYPHENS = "-\u00ad\u2010\u2011"

#: Fundort einer versteckten Ablage (Art, Seite, Objektnummer, Schlüssel …).
HiddenRef: TypeAlias = dict[str, str | int]
#: Rechteck als ``[x0, y0, x1, y1]``.
Box: TypeAlias = list[float]


class RedactionError(ValueError):
    """Eingabe ungeeignet (HTTP 400)."""


class RedactionStaleError(RedactionError):
    """Plan passt nicht zur Datei oder zu den Fundstellen (HTTP 409)."""


class RedactionNerError(RuntimeError):
    """Die KI-Namenserkennung lieferte ein ungültiges Ergebnis (HTTP 502)."""


class RedactionVerificationError(RuntimeError):
    """Nach dem Schwärzen ist noch etwas lesbar — keine Ausgabe (HTTP 422)."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__(
            "Schwärzung nicht ausgeliefert: Nachprüfung fand noch lesbare Fundstellen ("
            + "; ".join(problems[:5])
            + (" …" if len(problems) > 5 else "")
            + ")"
        )


def _norm(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split()).casefold()


_INVISIBLE = frozenset("\u200b\u200c\u200d\u2060\ufeff")
_CHAR_MAP = {"\u2010": "-", "\u2011": "-"}


def _clean(text: str) -> str:
    """Freier Text (Metadaten, Felder) in dieselbe Form wie der Seitentext."""
    # MuPDF liefert ein weiches Trennzeichen in Lesezeichen als NUL-Zeichen.
    text = "".join(ch for ch in text if ch not in _INVISIBLE and ch != "\x00")
    return unicodedata.normalize("NFC", text.replace("\u00ad", ""))


def _flat(text: str) -> str:
    """Vergleichsform: NFKC, ohne Groß-/Kleinschreibung, ohne Leerraum."""
    return "".join(unicodedata.normalize("NFKC", text).casefold().split())


def _candidate_id(*parts: object) -> str:
    return hashlib.sha256("\x1f".join(str(p) for p in parts).encode()).hexdigest()[:16]
