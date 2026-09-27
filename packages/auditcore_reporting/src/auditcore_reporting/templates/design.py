"""Exchangeable design profiles (fonts, colours, margins, header and footer texts).

The library ships only the neutral profile ``neutral-v1``. An authority's
corporate design is a profile of the application (``design_from_dict``),
never hard-wired here; logos and master documents stay with the application.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, fields

from .errors import TemplateError

#: PDF base fonts that need no font file (WinAnsi covers ä, ö, ü, ß, €, „ “ –).
PDF_FONTS = ("Helvetica", "Times-Roman", "Courier")
_HEX = re.compile(r"[0-9A-F]{6}")
_ID = re.compile(r"[a-z][a-z0-9-]{1,63}")


@dataclass(frozen=True)
class DesignProfile:
    """Layout values shared by the DOCX, PDF and HTML renderers."""

    id: str = "neutral-v1"
    version: str = "1.0.0"
    label: str = "Neutral"
    font_family: str = "Arial"
    pdf_font: str = "Helvetica"
    font_size_pt: float = 11.0
    heading_sizes_pt: tuple[float, float, float] = (16.0, 13.0, 11.5)
    accent_color: str = "1F3864"
    table_header_fill: str = "D9E2F3"
    margin_cm: float = 2.5
    header_text: str = ""
    footer_text: str = ""
    page_numbers: bool = True

    def __post_init__(self) -> None:
        if not _ID.fullmatch(self.id):
            raise TemplateError(f"Gestaltungsprofil: ungültige Kennung {self.id!r}.")
        for name in ("accent_color", "table_header_fill"):
            if not _HEX.fullmatch(getattr(self, name)):
                raise TemplateError(
                    f"Gestaltungsprofil {self.id}: {name} als RRGGBB (Großbuchstaben)."
                )
        if self.pdf_font not in PDF_FONTS:
            raise TemplateError(f"Gestaltungsprofil {self.id}: pdf_font aus {PDF_FONTS}.")
        if not 6 <= self.font_size_pt <= 24 or not 1 <= self.margin_cm <= 5:
            raise TemplateError(f"Gestaltungsprofil {self.id}: Schriftgröße 6–24 pt, Rand 1–5 cm.")
        if len(self.heading_sizes_pt) != 3 or not all(6 <= s <= 36 for s in self.heading_sizes_pt):
            raise TemplateError(f"Gestaltungsprofil {self.id}: drei Überschriftgrößen 6–36 pt.")
        if not self.font_family.strip() or len(self.font_family) > 80 or "<" in self.font_family:
            raise TemplateError(f"Gestaltungsprofil {self.id}: ungültige Schriftart.")

    def to_dict(self) -> dict[str, object]:
        """JSON form (REST catalogue)."""
        data = {f.name: getattr(self, f.name) for f in fields(self)}
        data["heading_sizes_pt"] = list(self.heading_sizes_pt)
        return data


NEUTRAL_DESIGN = DesignProfile()


def design_from_dict(data: Mapping[str, object]) -> DesignProfile:
    """Profile from JSON; unknown keys are rejected, missing keys keep the neutral value."""
    known = {f.name for f in fields(DesignProfile)}
    unknown = sorted(set(data) - known)
    if unknown:
        raise TemplateError(f"Gestaltungsprofil: unbekannte Felder {unknown}.")
    values = dict(data)
    if "heading_sizes_pt" in values:
        sizes = values["heading_sizes_pt"]
        if not isinstance(sizes, (list, tuple)):
            raise TemplateError("Gestaltungsprofil: heading_sizes_pt als Liste.")
        values["heading_sizes_pt"] = tuple(float(s) for s in sizes)
    try:
        return DesignProfile(**values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TemplateError(f"Gestaltungsprofil: {exc}") from exc
