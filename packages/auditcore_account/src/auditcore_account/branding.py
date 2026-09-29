"""Corporate Design: geprüfter Schriftkatalog, Farben und referenzierte Logo-Varianten."""

import re
from collections.abc import Mapping
from dataclasses import dataclass

from .errors import require


@dataclass(frozen=True)
class Font:
    id: str
    label: str
    css_family: str
    document_family: str


FONTS = (
    Font("system", "Systemschrift", "system-ui, sans-serif", "Helvetica"),
    Font("sans", "Sans Serif", "'DejaVu Sans', sans-serif", "DejaVu Sans"),
    Font("serif", "Serif", "'DejaVu Serif', serif", "DejaVu Serif"),
)
DEFAULT_BRANDING = {
    "primary": "#1f5f8b",
    "accent": "#174a6d",
    "text_on_primary": "#ffffff",
    "heading_font": "system",
    "body_font": "system",
    "logo_light": "",
    "logo_dark": "",
    "logo_document": "",
    "document_header": "",
    "document_footer": "",
}


def luminance(color: str) -> float:
    require(bool(re.fullmatch(r"#[0-9a-fA-F]{6}", color)), "invalid", "Farbe als #RRGGBB angeben.")
    channels = [int(color[n : n + 2], 16) / 255 for n in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))


def contrast(first: str, second: str) -> float:
    values = sorted((luminance(first), luminance(second)))
    return (values[1] + 0.05) / (values[0] + 0.05)


def validate_branding(values: Mapping[str, str], fonts: tuple[Font, ...] = FONTS) -> dict[str, str]:
    require(not set(values) - set(DEFAULT_BRANDING), "unknown_field", "Unbekanntes Designfeld.")
    result = DEFAULT_BRANDING | dict(values)
    for field in ("primary", "accent", "text_on_primary"):
        luminance(result[field])
    for field in ("heading_font", "body_font"):
        require(
            result[field] in {f.id for f in fonts}, "invalid", "Schrift nicht freigegeben.", field
        )
    for color in ("primary", "accent"):
        require(
            contrast(result[color], result["text_on_primary"]) >= 4.5,
            "contrast",
            "Textkontrast muss mindestens 4,5:1 betragen.",
            color,
        )
    for field in ("document_header", "document_footer"):
        require(len(result[field]) <= 2000, "invalid", "Dokumenttext ist zu lang.", field)
    return result
