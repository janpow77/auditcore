"""Escaping and styles shared by the HTML views of reports."""

from __future__ import annotations

from html import escape


def text(value: object, empty: str = "–") -> str:
    """Escaped display text; empty values as ``empty``, flags as Ja/Nein, lists joined."""
    if value is None or value == "":
        return escape(empty)
    if value is True:
        return "Ja"
    if value is False:
        return "Nein"
    if isinstance(value, (list, tuple)):
        return escape(", ".join(str(v) for v in value)) or escape(empty)
    return escape(str(value))


STYLE = (
    "<style>@page { size: A4; margin: 2cm 2cm 2cm 2.5cm; }"
    "body { font-family: Arial, sans-serif; font-size: 10pt; color: #000; }"
    "h1 { font-size: 15pt; } h2 { font-size: 12pt; margin-top: 7mm;"
    " border-bottom: 0.5pt solid #888; } h3 { font-size: 10.5pt; }"
    "table { width: 100%; border-collapse: collapse; margin-top: 2mm; }"
    "th, td { border: 0.5pt solid #999; padding: 1.5mm; text-align: left;"
    " vertical-align: top; font-size: 9pt; } th { background: #e8eaf0; }"
    ".klein { font-size: 8pt; color: #444; }"
    ".hinweis { background: #f4f4f4; padding: 2mm; margin-top: 2mm; }"
    ".blockierend { background: #fbe9e7; }</style>"
)
