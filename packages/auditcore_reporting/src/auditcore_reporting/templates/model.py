"""Immutable template model: text blocks, document blocks and the versioned template."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .conditions import Condition

#: Output formats; ``docx`` needs no extra, ``pdf`` needs ``[pdf]`` (reportlab).
FORMATS = ("docx", "pdf", "html")
STATUSES = ("Entwurf", "Freigegeben", "Archiviert")


@dataclass(frozen=True)
class TextBlock:
    """Textbaustein: reusable text with placeholders, optional condition and legal basis.

    ``required`` marks a Pflichtbaustein: the template must reference it.
    """

    id: str
    text: str
    title: str = ""
    condition: Condition | None = None
    required: bool = False
    legal_basis: str = ""


@dataclass(frozen=True)
class Heading:
    """Heading of level 1–3; ``anchor`` makes it a jump target (links, table of contents)."""

    text: str
    level: int = 1
    condition: Condition | None = None
    anchor: str = ""


@dataclass(frozen=True)
class Paragraph:
    """Paragraph with placeholders; line breaks are kept.

    With ``link`` the whole paragraph is an internal link to that anchor.
    """

    text: str
    condition: Condition | None = None
    link: str = ""


@dataclass(frozen=True)
class BlockRef:
    """Insert a text block (skipped when its own condition is false)."""

    block: str
    condition: Condition | None = None


@dataclass(frozen=True)
class BulletList:
    """One bullet per entry of the list at ``source``; ``item`` sees the entry as ``var``."""

    source: str
    item: str
    var: str = "eintrag"
    condition: Condition | None = None
    empty_text: str = ""


#: Table borders: full grid (default), horizontal lines only, or none.
BORDERS = ("grid", "horizontal", "none")


@dataclass(frozen=True)
class Fill:
    """Colour (RRGGBB) and emphasis of a cell or row; the first rule whose condition holds wins."""

    color: str = ""
    condition: Condition | None = None
    bold: bool = False


@dataclass(frozen=True)
class Column:
    """Table column: header and cell text (placeholders see the row as the table ``var``).

    ``width`` is a relative weight (0 = equal share), ``bold`` emphasises the
    whole column, ``fills`` colour single cells (static or by condition).
    """

    header: str
    cell: str
    align: str = "left"
    width: float = 0.0
    bold: bool = False
    fills: tuple[Fill, ...] = ()


@dataclass(frozen=True)
class Table:
    """Table with one row per list entry at ``source``."""

    source: str
    columns: tuple[Column, ...]
    var: str = "zeile"
    condition: Condition | None = None
    empty_text: str = ""
    #: Draw the header row even without rows (followed by ``empty_text``).
    header_if_empty: bool = False
    borders: str = "grid"
    #: Header colour (``""`` = design profile's ``table_header_fill``).
    header_fill: str = ""
    #: Colour of every second body row (``""`` = none).
    stripe: str = ""
    #: Row colours/emphasis by condition; cell fills take precedence.
    row_fills: tuple[Fill, ...] = ()

    @property
    def styled(self) -> bool:
        """Any cell colour or emphasis beyond the plain default table."""
        return bool(self.stripe or self.row_fills) or any(c.bold or c.fills for c in self.columns)


@dataclass(frozen=True)
class Field:
    """Label/value pair of a :class:`Fields` block."""

    label: str
    value: str


@dataclass(frozen=True)
class Fields:
    """Two-column key data (Aktenzeichen, Datum, Betreff …).

    Empty values are skipped together with their label unless ``empty`` is set;
    then the row stays and shows ``empty`` (for example ``"—"``) as its value.
    """

    rows: tuple[Field, ...]
    condition: Condition | None = None
    empty: str | None = None


@dataclass(frozen=True)
class Image:
    """Picture (PNG/JPEG): a named image of the render call or design, or base64 data.

    Exactly one of ``image`` (name) and ``source`` (data path holding base64
    or a ``data:image/…;base64,`` URI) is set. ``width_cm`` 0 = natural size
    at 96 dpi, limited to the text width.
    """

    image: str = ""
    source: str = ""
    width_cm: float = 0.0
    align: str = "left"
    alt: str = ""
    condition: Condition | None = None


@dataclass(frozen=True)
class Contents:
    """Table of contents with jumps to the headings up to ``levels`` (PDF with page numbers)."""

    title: str = "Inhalt"
    levels: int = 2
    condition: Condition | None = None


@dataclass(frozen=True)
class PageBreak:
    """Page break (DOCX, PDF); a separator in HTML."""

    condition: Condition | None = None


@dataclass(frozen=True)
class Section:
    """Abschnitt: optional title, condition and repetition over a list (``repeat``)."""

    blocks: tuple[Block, ...]
    title: str = ""
    condition: Condition | None = None
    repeat: str | None = None
    var: str = "eintrag"
    id: str = ""
    level: int = 2
    #: Jump target of the title; repetitions get ``anchor-2``, ``anchor-3`` …
    anchor: str = ""


Block = (
    Heading | Paragraph | BlockRef | BulletList | Table | Fields | PageBreak | Section | Image
    | Contents
)  # fmt: skip


@dataclass(frozen=True)
class ReportTemplate:
    """A versioned report template; ``fingerprint`` covers definition and DOCX source.

    Either ``blocks`` (structured, renders to DOCX, PDF and HTML) or ``docx``
    (Word template with placeholders and control tags, renders to DOCX) is set.
    """

    id: str
    version: str
    title: str
    description: str
    schema: Mapping[str, object]
    blocks: tuple[Block, ...]
    text_blocks: tuple[TextBlock, ...]
    conditions: Mapping[str, Condition]
    formats: tuple[str, ...]
    status: str
    sample: Mapping[str, object]
    fingerprint: str
    definition: Mapping[str, object] = field(repr=False)
    docx: bytes | None = field(default=None, repr=False)
    #: Display name without placeholders (lists, selection); ``title`` is the document title.
    name: str = ""
    #: Page orientation of the template (``""`` = design profile decides).
    orientation: str = ""
    #: PDF bookmarks (outline) for all headings.
    outline: bool = False

    def text_block(self, block_id: str) -> TextBlock | None:
        """Text block by id."""
        return next((block for block in self.text_blocks if block.id == block_id), None)
