"""Einstellungsvertrag für Web, CLI und Jupyter (aus ``configuration.py``).

Bereinigung und Schichtung (Abteilung → persönlich → Lauf) entsprechen dem
Original. Anders als dort liest die Bibliothek weder Umgebungsvariablen noch
das Benutzerverzeichnis: Laden und Speichern verlangen einen ausdrücklichen
Pfad (Standardpfad des Originals siehe :mod:`auditcore_documents.legacy`).
"""

from __future__ import annotations

import json
import re
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


def _sanitise_layout(value: object, *, memo: bool) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    if "header_text" in value:
        result["header_text"] = _clean_text(
            value["header_text"], limit=2000, fallback="Vermerk" if memo else "Text"
        )
    if "font_family" in value:
        result["font_family"] = _clean_text(
            value["font_family"], limit=80, fallback="Hessen Gellix"
        )
    for key, minimum, maximum, fallback in (
        ("body_font_size_pt", 8.0, 18.0, 10.0),
        ("heading_font_size_pt", 10.0, 24.0, 14.0),
        ("line_spacing", 1.0, 2.0, 1.0),
        ("page_margin_cm", 1.0, 4.0, 2.0),
    ):
        if key in value:
            try:
                parsed = float(value[key])
            except (TypeError, ValueError):
                parsed = fallback
            result[key] = max(minimum, min(maximum, parsed))
    if "accent_color" in value:
        color = _clean_text(value["accent_color"], limit=7, fallback="#14006E")
        result["accent_color"] = color.upper() if HEX_COLOR_RE.fullmatch(color) else "#14006E"
        if not result["accent_color"].startswith("#"):
            result["accent_color"] = f"#{result['accent_color']}"
    if "footer_text" in value:
        result["footer_text"] = _clean_text(value["footer_text"], limit=500)
    for key in ("show_page_numbers", "show_file_metadata"):
        if key in value:
            result[key] = bool(value[key])
    if memo and "outline" in value:
        outline = value["outline"]
        if isinstance(outline, str):
            outline = outline.splitlines()
        if not isinstance(outline, list):
            outline = []
        cleaned = [
            _clean_text(item, limit=160) for item in outline[:20] if _clean_text(item, limit=160)
        ]
        if not any("{{vergleich}}" in item for item in cleaned):
            cleaned.append("Festgestellte Änderungen {{vergleich}}")
        result["outline"] = cleaned or list(DEFAULT_MEMO_OUTLINE)
    return result


def sanitise_settings(values: object) -> dict[str, Any]:
    """Nur bekannte Schlüssel, Werte begrenzt; ungültige Auswahlwerte → Vorgabe.

    Wie im Original führen nicht in ``int`` wandelbare Werte für
    ``threshold``/``retention_days`` zu ``ValueError``/``TypeError``.
    """
    if not isinstance(values, dict):
        return {}
    result = {key: values[key] for key in ALLOWED_KEYS if key in values}
    if "output_profile" in result and result["output_profile"] not in {"memo", "text"}:
        result["output_profile"] = "memo"
    if "memo_layout" in result:
        result["memo_layout"] = _sanitise_layout(result["memo_layout"], memo=True)
    if "text_layout" in result:
        result["text_layout"] = _sanitise_layout(result["text_layout"], memo=False)
    if "model" in result:
        result["model"] = _clean_text(result["model"], limit=160)
    if "threshold" in result:
        result["threshold"] = max(70, min(100, int(result["threshold"])))
    if "retention_days" in result:
        result["retention_days"] = max(1, min(3650, int(result["retention_days"])))
    if "mode" in result and result["mode"] not in {"auto", "checklist", "text"}:
        result["mode"] = "auto"
    if "comparison_type" in result and result["comparison_type"] not in {
        "standard",
        "article_law",
    }:
        result["comparison_type"] = "standard"
    for key in (
        "generate_reasons",
        "include_answers",
        "include_notes",
        "include_editorial",
        "highlight_words",
    ):
        if key in result:
            result[key] = bool(result[key])
    if "output_sections" in result:
        sections = result["output_sections"]
        if not isinstance(sections, list):
            sections = []
        result["output_sections"] = [
            section
            for section in dict.fromkeys(str(item) for item in sections)
            if section in ALLOWED_SECTIONS
        ] or ["changed", "removed", "added", "moved"]
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

    def effective_path(path: str) -> Any:
        current: Any = effective
        for part in path.split("."):
            current = current.get(part) if isinstance(current, dict) else None
        return current

    def assign_path(path: str, value: Any) -> None:
        parts = path.split(".")
        current = effective
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    def apply_layer(source: str, values: dict[str, Any], prefix: str = "") -> None:
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
