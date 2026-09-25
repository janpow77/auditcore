"""Meldungskatalog der Prüfregeln: stabile IDs, Schweregrad, Gruppe und Texte (de/en).

Die IDs sind Teil der öffentlichen Schnittstelle und ändern sich nicht;
entfallende Regeln werden nicht neu vergeben. Platzhalter in geschweiften
Klammern füllt :meth:`ValidationIssue.message`; ein Parameter ``name_en``
geht für Englisch dem Parameter ``name`` vor.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .severity import ERROR, NOTE, SEVERITIES, SEVERITY_LABELS, WARNING
from .texts_audit import TEXTS as _AUDIT
from .texts_content import TEXTS as _CONTENT
from .texts_structure import TEXTS as _STRUCTURE

__all__ = ["ERROR", "MESSAGES", "NOTE", "SEVERITIES", "SEVERITY_LABELS", "WARNING", "RuleMessage"]


class _Defaults(dict[str, object]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(frozen=True)
class RuleMessage:
    """Meldungsvorlage einer Regel."""

    id: str
    severity: str
    group: str
    de: str
    en: str

    def render(self, language: str, params: Mapping[str, object]) -> str:
        """Text in ``language`` mit eingesetzten Parametern."""
        template = self.en if language == "en" else self.de
        suffix = "_en" if language == "en" else "_de"
        values = _Defaults(params)
        for key, value in params.items():
            if key.endswith(suffix):
                values[key[: -len(suffix)]] = value
        return template.format_map(values)


MESSAGES: Mapping[str, RuleMessage] = MappingProxyType(
    {
        rid: RuleMessage(rid, severity, group, de, en)
        for rid, severity, group, de, en in (*_STRUCTURE, *_CONTENT, *_AUDIT)
    }
)
