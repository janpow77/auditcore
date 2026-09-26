"""Schweregrade der Prüfregeln (Datenwerte) mit Bezeichnungen."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

#: Schweregrade (Datenwerte): Fehler, Warnung, Hinweis.
ERROR = "fehler"
WARNING = "warnung"
NOTE = "hinweis"
SEVERITIES = (ERROR, WARNING, NOTE)
SEVERITY_LABELS: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        ERROR: MappingProxyType({"de": "Fehler", "en": "Error"}),
        WARNING: MappingProxyType({"de": "Warnung", "en": "Warning"}),
        NOTE: MappingProxyType({"de": "Hinweis", "en": "Note"}),
    }
)
