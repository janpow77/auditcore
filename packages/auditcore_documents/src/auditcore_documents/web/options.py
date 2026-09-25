"""Formularfelder und Zeilenänderungen des REST-Vertrags streng prüfen.

Unbekannte Felder werden abgewiesen, damit ein Tippfehler nicht still zur
Vorgabe führt. Alle Meldungen sind deutsch und für die Oberfläche bestimmt.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from auditcore_documents.compare import CompareOptions
from auditcore_documents.profiles import PROFILES, CompareProfile

SECTIONS = ("changed", "removed", "added", "moved", "unchanged")
COMPARISON_TYPES = ("standard", "article_law")
MODES = ("auto", "checklist", "text")
BOOLEAN_FIELDS = ("include_answers", "include_notes", "include_editorial", "highlight_words")
TEXT_FIELDS = ("title", "profile", "comparison_type", "mode", "threshold", "output_sections")
FORM_FIELDS = frozenset((*BOOLEAN_FIELDS, *TEXT_FIELDS))
MAX_TITLE = 255
MAX_REASON = 4000
_TRUE = {"true", "1", "on", "yes", "ja"}
_FALSE = {"false", "0", "off", "no", "nein"}


class RequestError(Exception):
    """Vom Aufrufer behebbarer Fehler mit HTTP-Status und deutscher Meldung."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


@dataclass(frozen=True)
class CompareRequest:
    """Geprüfte Angaben eines Vergleichsauftrags."""

    title: str
    profile: CompareProfile
    options: CompareOptions


def _boolean(name: str, value: str) -> bool:
    lowered = value.strip().casefold()
    if lowered in _TRUE:
        return True
    if lowered in _FALSE:
        return False
    raise RequestError(422, f"Feld „{name}“ erwartet true oder false.")


def _choice(name: str, value: str, allowed: tuple[str, ...]) -> str:
    if value not in allowed:
        raise RequestError(422, f"Feld „{name}“ erlaubt nur: {', '.join(allowed)}.")
    return value


def _threshold(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise RequestError(422, "Die Ähnlichkeitsschwelle muss eine ganze Zahl sein.") from None
    if not 70 <= number <= 100:
        raise RequestError(422, "Die Ähnlichkeitsschwelle muss zwischen 70 und 100 liegen.")
    return number


def _sections(value: str) -> tuple[str, ...]:
    parts = tuple(dict.fromkeys(p.strip() for p in value.split(",") if p.strip()))
    if not parts:
        raise RequestError(422, "Mindestens ein Ausgabeabschnitt ist erforderlich.")
    for part in parts:
        _choice("output_sections", part, SECTIONS)
    return parts


def _profile(value: str | None, default: CompareProfile, allowed: frozenset[str]) -> CompareProfile:
    if value is None or value == "":
        return default
    if value not in allowed or value not in PROFILES:
        raise RequestError(422, f"Unbekanntes oder nicht freigegebenes Vergleichsprofil: {value}")
    return PROFILES[value]


def _title(value: str | None, fallback: str) -> str:
    title = (value or "").strip() or fallback
    if len(title) > MAX_TITLE:
        raise RequestError(422, f"Der Titel darf höchstens {MAX_TITLE} Zeichen lang sein.")
    return title


def parse_compare_fields(
    fields: Mapping[str, str],
    *,
    default_profile: CompareProfile,
    allowed_profiles: frozenset[str],
    fallback_title: str,
) -> CompareRequest:
    """Formularfelder in :class:`CompareRequest` übersetzen (Vorgaben wie im Original)."""
    unknown = sorted(set(fields) - FORM_FIELDS)
    if unknown:
        raise RequestError(422, f"Unbekannte Felder: {', '.join(unknown)}")
    flags = {name: _boolean(name, fields[name]) for name in BOOLEAN_FIELDS if name in fields}
    defaults = CompareOptions()
    sections = _sections(fields["output_sections"]) if "output_sections" in fields else None
    options = CompareOptions(
        mode=_choice("mode", fields.get("mode", "auto"), MODES),
        threshold=_threshold(fields.get("threshold", "85")),
        output_sections=sections,
        comparison_type=_choice(
            "comparison_type", fields.get("comparison_type", "standard"), COMPARISON_TYPES
        ),
        include_answers=flags.get("include_answers", defaults.include_answers),
        include_notes=flags.get("include_notes", defaults.include_notes),
        include_editorial=flags.get("include_editorial", defaults.include_editorial),
        highlight_words=flags.get("highlight_words", defaults.highlight_words),
    )
    return CompareRequest(
        title=_title(fields.get("title"), fallback_title),
        profile=_profile(fields.get("profile"), default_profile, allowed_profiles),
        options=options,
    )


@dataclass(frozen=True)
class RowUpdate:
    row_id: str
    selected: bool | None
    reason: str | None


def _row_update(entry: object) -> RowUpdate:
    if not isinstance(entry, dict) or not isinstance(entry.get("row_id"), str):
        raise RequestError(422, "Jede Zeilenänderung braucht eine Kennung „row_id“.")
    unknown = sorted(set(entry) - {"row_id", "selected", "reason"})
    if unknown:
        raise RequestError(422, f"Unbekannte Zeilenfelder: {', '.join(unknown)}")
    selected = entry.get("selected")
    reason = entry.get("reason")
    if selected is not None and not isinstance(selected, bool):
        raise RequestError(422, "„selected“ muss true oder false sein.")
    if reason is not None and (not isinstance(reason, str) or len(reason) > MAX_REASON):
        raise RequestError(422, f"„reason“ muss Text mit höchstens {MAX_REASON} Zeichen sein.")
    return RowUpdate(entry["row_id"], selected, reason)


def parse_row_updates(payload: object) -> list[RowUpdate]:
    """``{"rows": [{"row_id", "selected"?, "reason"?}]}`` prüfen."""
    if not isinstance(payload, dict) or set(payload) != {"rows"}:
        raise RequestError(422, "Erwartet wird ein Objekt mit genau dem Feld „rows“.")
    rows = payload["rows"]
    if not isinstance(rows, list):
        raise RequestError(422, "„rows“ muss eine Liste sein.")
    return [_row_update(entry) for entry in rows]
