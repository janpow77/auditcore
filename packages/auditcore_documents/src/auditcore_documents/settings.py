"""Einstellungsvertrag für Web, CLI und Jupyter (aus ``configuration.py``).

Bereinigung und Schichtung (Abteilung → persönlich → Lauf) entsprechen dem
Original. Anders als dort liest die Bibliothek weder Umgebungsvariablen noch
das Benutzerverzeichnis: Laden und Speichern verlangen einen ausdrücklichen
Pfad (Standardpfad des Originals siehe :mod:`auditcore_documents.legacy`).
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

DEFAULT_MEMO_OUTLINE = [
    "Anlass",
    "Sachverhalt",
    "Festgestellte Änderungen {{vergleich}}",
    "Bewertung",
    "Vorschlag",
]

DEFAULT_LAYOUT: dict[str, Any] = {
    "header_text": "",
    "font_family": "Hessen Gellix",
    "body_font_size_pt": 10.0,
    "heading_font_size_pt": 14.0,
    "line_spacing": 1.0,
    "page_margin_cm": 2.0,
    "accent_color": "#14006E",
    "footer_text": "",
    "show_page_numbers": True,
    "show_file_metadata": True,
}

DEFAULT_SETTINGS: dict[str, Any] = {
    "output_profile": "memo",
    "memo_layout": {
        **DEFAULT_LAYOUT,
        "header_text": "Vermerk",
        "outline": DEFAULT_MEMO_OUTLINE,
    },
    "text_layout": {
        **DEFAULT_LAYOUT,
        "header_text": "Text",
    },
    "model": "",
    "threshold": 85,
    "retention_days": 30,
    "mode": "auto",
    "comparison_type": "standard",
    "generate_reasons": False,
    "include_answers": True,
    "include_notes": True,
    "include_editorial": False,
    "highlight_words": True,
    "output_sections": ["changed", "removed", "added", "moved"],
}

ALLOWED_KEYS = frozenset(DEFAULT_SETTINGS)
ALLOWED_SECTIONS = frozenset({"changed", "removed", "added", "moved", "unchanged"})
HEX_COLOR_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")


def _clean_text(value: object, *, limit: int, fallback: str = "") -> str:
    text = str(value or "").replace("\x00", "").strip()
    return text[:limit] or fallback


def _bounded(minimum: float, maximum: float, fallback: float) -> Callable[[object, bool], float]:
    """Zahl in ``[minimum, maximum]``; nicht wandelbare Werte → ``fallback``."""

    def clean(value: object, memo: bool) -> float:
        try:
            parsed = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            parsed = fallback
        return max(minimum, min(maximum, parsed))

    return clean


def _accent_color(value: object) -> str:
    color = _clean_text(value, limit=7, fallback="#14006E")
    color = color.upper() if HEX_COLOR_RE.fullmatch(color) else "#14006E"
    return color if color.startswith("#") else f"#{color}"


def _outline(value: object) -> list[str]:
    outline = value.splitlines() if isinstance(value, str) else value
    if not isinstance(outline, list):
        outline = []
    cleaned = [
        _clean_text(item, limit=160) for item in outline[:20] if _clean_text(item, limit=160)
    ]
    if not any("{{vergleich}}" in item for item in cleaned):
        cleaned.append("Festgestellte Änderungen {{vergleich}}")
    return cleaned or list(DEFAULT_MEMO_OUTLINE)


#: Layoutschlüssel in Ausgabereihenfolge mit Bereinigung (Wert, Vermerkprofil) → Wert.
LAYOUT_CLEANERS: tuple[tuple[str, Callable[[object, bool], object]], ...] = (
    (
        "header_text",
        lambda v, memo: _clean_text(v, limit=2000, fallback="Vermerk" if memo else "Text"),
    ),
    ("font_family", lambda v, memo: _clean_text(v, limit=80, fallback="Hessen Gellix")),
    ("body_font_size_pt", _bounded(8.0, 18.0, 10.0)),
    ("heading_font_size_pt", _bounded(10.0, 24.0, 14.0)),
    ("line_spacing", _bounded(1.0, 2.0, 1.0)),
    ("page_margin_cm", _bounded(1.0, 4.0, 2.0)),
    ("accent_color", lambda v, memo: _accent_color(v)),
    ("footer_text", lambda v, memo: _clean_text(v, limit=500)),
    ("show_page_numbers", lambda v, memo: bool(v)),
    ("show_file_metadata", lambda v, memo: bool(v)),
)


def _sanitise_layout(value: object, *, memo: bool) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {
        key: clean(value[key], memo) for key, clean in LAYOUT_CLEANERS if key in value
    }
    if memo and "outline" in value:
        result["outline"] = _outline(value["outline"])
    return result


def _choice(allowed: frozenset[str], default: str) -> Callable[[object], object]:
    """Auswahlwert oder Vorgabe (nicht hashbare Werte → ``TypeError`` wie im Original)."""
    return lambda value: value if value in allowed else default


def _output_sections(value: object) -> list[str]:
    sections = value if isinstance(value, list) else []
    return [
        section
        for section in dict.fromkeys(str(item) for item in sections)
        if section in ALLOWED_SECTIONS
    ] or ["changed", "removed", "added", "moved"]


#: Einstellungsbereinigung in der Prüfreihenfolge des Originals.
SETTING_CLEANERS: dict[str, Callable[[Any], object]] = {
    "output_profile": _choice(frozenset({"memo", "text"}), "memo"),
    "memo_layout": lambda v: _sanitise_layout(v, memo=True),
    "text_layout": lambda v: _sanitise_layout(v, memo=False),
    "model": lambda v: _clean_text(v, limit=160),
    "threshold": lambda v: max(70, min(100, int(v))),
    "retention_days": lambda v: max(1, min(3650, int(v))),
    "mode": _choice(frozenset({"auto", "checklist", "text"}), "auto"),
    "comparison_type": _choice(frozenset({"standard", "article_law"}), "standard"),
    **dict.fromkeys(
        (
            "generate_reasons",
            "include_answers",
            "include_notes",
            "include_editorial",
            "highlight_words",
        ),
        bool,
    ),
    "output_sections": _output_sections,
}


def sanitise_settings(values: object) -> dict[str, Any]:
    """Nur bekannte Schlüssel, Werte begrenzt; ungültige Auswahlwerte → Vorgabe.

    Wie im Original führen nicht in ``int`` wandelbare Werte für
    ``threshold``/``retention_days`` zu ``ValueError``/``TypeError``.
    """
    if not isinstance(values, dict):
        return {}
    result = {key: values[key] for key in ALLOWED_KEYS if key in values}
    for key, clean in SETTING_CLEANERS.items():
        if key in result:
            result[key] = clean(result[key])
    return result


def _deep_merge(target: dict[str, Any], values: dict[str, Any]) -> None:
    for key, value in values.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = deepcopy(value)


def load_settings(path: Path) -> dict[str, Any]:
    """Vorgaben, überlagert von der bereinigten Datei; fehlende Datei → Vorgaben."""
    if not path.is_file():
        return deepcopy(DEFAULT_SETTINGS)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Einstellungsdatei ist ungültig: {exc}") from exc
    result = deepcopy(DEFAULT_SETTINGS)
    _deep_merge(result, sanitise_settings(payload))
    return result


def settings_json(values: object) -> tuple[dict[str, Any], str]:
    """Bereinigte Einstellungen und ihr Dateiinhalt (ohne Dateizugriff)."""
    clean = deepcopy(DEFAULT_SETTINGS)
    _deep_merge(clean, sanitise_settings(values))
    return clean, json.dumps(clean, ensure_ascii=False, indent=2) + "\n"


def save_settings(values: object, path: Path) -> dict[str, Any]:
    """Atomar über eine temporäre Datei schreiben (wie im Original)."""
    clean, content = settings_json(values)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
    return clean


def merge_settings(
    department: object, personal: object, run: object
) -> tuple[dict[str, Any], dict[str, str]]:
    """Wirksame Einstellungen und Herkunft je Pfad (department/personal/run)."""
    effective = deepcopy(DEFAULT_SETTINGS)
    sources: dict[str, str] = {}

    def effective_path(path: str) -> object:
        current: object = effective
        for part in path.split("."):
            current = current.get(part) if isinstance(current, dict) else None
        return current

    def assign_path(path: str, value: object) -> None:
        parts = path.split(".")
        current = effective
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    def apply_layer(source: str, values: Mapping[str, object], prefix: str = "") -> None:
        for key, value in values.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and isinstance(effective_path(path), dict):
                apply_layer(source, value, path)
            else:
                assign_path(path, deepcopy(value))
                sources[path] = source

    for source, raw in (("department", department), ("personal", personal), ("run", run)):
        apply_layer(source, sanitise_settings(raw))
    return effective, sources
