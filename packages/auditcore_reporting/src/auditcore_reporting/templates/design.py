"""Exchangeable design profiles (fonts, colours, margins, page, header and footer texts).

The library ships only the neutral profile ``neutral-v1``. An authority's
corporate design is a profile of the application (``design_from_dict``),
never hard-wired here; logos, master documents and font files stay with the
application. TrueType fonts for the PDF output are passed as bytes
(:class:`PdfFont`); without them the PDF uses the base-14 fonts as before.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields

from .errors import TemplateError

#: PDF base fonts that need no font file (WinAnsi covers ä, ö, ü, ß, €, „ “ –).
PDF_FONTS = ("Helvetica", "Times-Roman", "Courier")
#: Page orientations (A4); a template may override the profile.
ORIENTATIONS = ("portrait", "landscape")
#: Upper bound for one font file.
MAX_FONT_BYTES = 20 * 1024 * 1024
_HEX = re.compile(r"[0-9A-F]{6}")
_ID = re.compile(r"[a-z][a-z0-9-]{1,63}")
_FONT_NAME = re.compile(r"[A-Za-z][A-Za-z0-9-]{0,63}")
#: sfnt versions reportlab reads (TrueType outlines); CFF fonts ("OTTO") are not supported.
_TTF_MAGIC = (b"\x00\x01\x00\x00", b"true")


def _checked_font_file(name: str, data: bytes, kind: str) -> None:
    if not isinstance(data, bytes) or len(data) > MAX_FONT_BYTES or data[:4] not in _TTF_MAGIC:
        raise TemplateError(
            f"Schrift {name}: {kind} muss eine TrueType-Datei (bytes, höchstens "
            f"{MAX_FONT_BYTES // (1024 * 1024)} MB) sein."
        )


@dataclass(frozen=True)
class PdfFont:
    """TrueType font for the PDF output: regular and optional bold file as bytes.

    The application supplies the files and is responsible for their licence;
    the library ships none. Without ``bold`` the regular file is used for
    headings and table headers as well.
    """

    name: str
    regular: bytes = field(repr=False)
    bold: bytes | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not _FONT_NAME.fullmatch(self.name) or self.name in PDF_FONTS:
            raise TemplateError(f"Schrift {self.name!r}: Name aus A-Z, 0-9, Bindestrich.")
        _checked_font_file(self.name, self.regular, "regular")
        if self.bold is not None:
            _checked_font_file(self.name, self.bold, "bold")

    @property
    def sha256(self) -> str:
        """Digest over both files (identifies the font in registries and the catalogue)."""
        digest = hashlib.sha256(self.regular)
        digest.update(self.bold or b"")
        return digest.hexdigest()

    def to_dict(self) -> dict[str, object]:
        """JSON form without the file contents."""
        return {"name": self.name, "sha256": self.sha256, "bold": self.bold is not None}


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
    #: ``portrait`` or ``landscape`` (A4); a template's ``orientation`` takes precedence.
    orientation: str = "portrait"
    #: TrueType fonts selectable as ``pdf_font`` (Python API only, not JSON).
    pdf_fonts: tuple[PdfFont, ...] = ()

    def __post_init__(self) -> None:
        if not _ID.fullmatch(self.id):
            raise TemplateError(f"Gestaltungsprofil: ungültige Kennung {self.id!r}.")
        for name in ("accent_color", "table_header_fill"):
            if not _HEX.fullmatch(getattr(self, name)):
                raise TemplateError(
                    f"Gestaltungsprofil {self.id}: {name} als RRGGBB (Großbuchstaben)."
                )
        self._check_layout()
        self._check_fonts()

    def _check_layout(self) -> None:
        if not 6 <= self.font_size_pt <= 24 or not 1 <= self.margin_cm <= 5:
            raise TemplateError(f"Gestaltungsprofil {self.id}: Schriftgröße 6–24 pt, Rand 1–5 cm.")
        if len(self.heading_sizes_pt) != 3 or not all(6 <= s <= 36 for s in self.heading_sizes_pt):
            raise TemplateError(f"Gestaltungsprofil {self.id}: drei Überschriftgrößen 6–36 pt.")
        if self.orientation not in ORIENTATIONS:
            raise TemplateError(f"Gestaltungsprofil {self.id}: orientation aus {ORIENTATIONS}.")

    def _check_fonts(self) -> None:
        if not self.font_family.strip() or len(self.font_family) > 80 or "<" in self.font_family:
            raise TemplateError(f"Gestaltungsprofil {self.id}: ungültige Schriftart.")
        names = [font.name for font in self.pdf_fonts]
        if len(set(names)) != len(names) or not all(isinstance(f, PdfFont) for f in self.pdf_fonts):
            raise TemplateError(f"Gestaltungsprofil {self.id}: pdf_fonts mit eindeutigen Namen.")
        if self.pdf_font not in (*PDF_FONTS, *names):
            raise TemplateError(
                f"Gestaltungsprofil {self.id}: pdf_font aus {(*PDF_FONTS, *names)}."
            )

    def pdf_font_file(self) -> PdfFont | None:
        """The TrueType font selected as ``pdf_font``, or ``None`` for a base-14 font."""
        return next((font for font in self.pdf_fonts if font.name == self.pdf_font), None)

    def to_dict(self) -> dict[str, object]:
        """JSON form (REST catalogue); font files appear as name and digest."""
        data = {f.name: getattr(self, f.name) for f in fields(self)}
        data["heading_sizes_pt"] = list(self.heading_sizes_pt)
        data["pdf_fonts"] = [font.to_dict() for font in self.pdf_fonts]
        return data


NEUTRAL_DESIGN = DesignProfile()


def page_orientation(template_orientation: str, design: DesignProfile) -> str:
    """Effective orientation: the template's if set, else the profile's."""
    return template_orientation or design.orientation


def design_from_dict(data: Mapping[str, object]) -> DesignProfile:
    """Profile from JSON; unknown keys are rejected, missing keys keep the neutral value.

    Font files cannot be expressed in JSON; ``pdf_fonts`` is only accepted
    empty (as written by :meth:`DesignProfile.to_dict` without fonts).
    """
    known = {f.name for f in fields(DesignProfile)}
    unknown = sorted(set(data) - known)
    if unknown:
        raise TemplateError(f"Gestaltungsprofil: unbekannte Felder {unknown}.")
    values = dict(data)
    if values.pop("pdf_fonts", []) not in ([], ()):
        raise TemplateError("Gestaltungsprofil: pdf_fonts nur über die Python-API (PdfFont).")
    if "heading_sizes_pt" in values:
        sizes = values["heading_sizes_pt"]
        if not isinstance(sizes, (list, tuple)):
            raise TemplateError("Gestaltungsprofil: heading_sizes_pt als Liste.")
        values["heading_sizes_pt"] = tuple(float(s) for s in sizes)
    try:
        return DesignProfile(**values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TemplateError(f"Gestaltungsprofil: {exc}") from exc
