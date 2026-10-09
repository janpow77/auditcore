"""DOCX parts for jump targets, internal links, table of contents and pictures.

Headings with an anchor get a Word bookmark, links are ``w:hyperlink`` with
``w:anchor`` (direct formatting, no extra style), the table of contents is a
list of such links (Word's navigation pane uses the heading styles). Pictures
become media parts (deduplicated by content) drawn inline with DrawingML;
the namespaces are declared on the drawing so the document root stays as
before.
"""

from __future__ import annotations

import hashlib
from xml.sax.saxutils import quoteattr

from . import _wordml as wml
from .resolve import RContents, RHeading, RImage

_EMU_PER_CM = 360_000
_LINK = '<w:color w:val="0563C1"/><w:u w:val="single"/>'
_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"


def bookmark_name(anchor: str) -> str:
    """Word bookmark name (letters, digits, underscore, at most 40 characters)."""
    name = "ac_" + anchor.replace("-", "_")
    return name if len(name) <= 40 else "ac_" + hashlib.sha256(anchor.encode()).hexdigest()[:30]


def heading(node: RHeading, number: int) -> str:
    """Heading paragraph, wrapped in a bookmark when it has an anchor."""
    runs = wml.runs(node.text)
    if node.anchor:
        name = bookmark_name(node.anchor)
        runs = (
            f'<w:bookmarkStart w:id="{number}" w:name="{name}"/>{runs}'
            f'<w:bookmarkEnd w:id="{number}"/>'
        )
    return f'<w:p><w:pPr><w:pStyle w:val="Heading{node.level}"/></w:pPr>{runs}</w:p>'


def link(text: str, anchor: str, indent: int = 0) -> str:
    """Paragraph that jumps to ``anchor``."""
    props = f'<w:pPr><w:ind w:left="{indent}"/></w:pPr>' if indent else ""
    target = bookmark_name(anchor)
    return (
        f'<w:p>{props}<w:hyperlink w:anchor="{target}" w:history="1">'
        f"{wml.runs(text, _LINK)}</w:hyperlink></w:p>"
    )


def contents(node: RContents) -> str:
    """Title and one linked line per heading, indented by level."""
    title = f"<w:p>{wml.runs(node.title, '<w:b/>')}</w:p>"
    lines = "".join(link(text, anchor, (level - 1) * 360) for level, text, anchor in node.entries)
    return title + lines


class Media:
    """Picture parts of one document: relationship id, part name and bytes."""

    def __init__(self) -> None:
        self.parts: list[tuple[str, str, bytes]] = []
        self._ids: dict[str, str] = {}

    def add(self, node: RImage) -> str:
        """Relationship id of the picture (one part per distinct content)."""
        digest = hashlib.sha256(node.image.data).hexdigest()
        if digest not in self._ids:
            number = len(self.parts) + 1
            extension = "png" if node.image.kind == "png" else "jpeg"
            rid = f"rIdImg{number}"
            self.parts.append((rid, f"media/image{number}.{extension}", node.image.data))
            self._ids[digest] = rid
        return self._ids[digest]

    @property
    def extensions(self) -> tuple[str, ...]:
        """Distinct file extensions (content types)."""
        return tuple(sorted({target.rsplit(".", 1)[1] for _, target, _ in self.parts}))


def picture(node: RImage, rid: str, number: int, max_width_cm: float) -> str:
    """Inline picture paragraph (aspect ratio kept, at most the text width)."""
    width_cm, height_cm = node.size_cm(max_width_cm)
    cx, cy = round(width_cm * _EMU_PER_CM), round(height_cm * _EMU_PER_CM)
    align = f'<w:pPr><w:jc w:val="{node.align}"/></w:pPr>' if node.align != "left" else ""
    extent = f'cx="{cx}" cy="{cy}"'
    graphic = (
        f'<a:graphic xmlns:a="{_A}"><a:graphicData uri="{_PIC}"><pic:pic xmlns:pic="{_PIC}">'
        f'<pic:nvPicPr><pic:cNvPr id="{number}" name="Bild {number}"/><pic:cNvPicPr/>'
        f'</pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/>'
        f'</a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext {extent}/>'
        '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        "</a:graphicData></a:graphic>"
    )
    inline = (
        f'<wp:inline xmlns:wp="{_WP}" distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent {extent}/><wp:docPr id="{number}" name="Bild {number}"'
        f" descr={quoteattr(node.alt)}/><wp:cNvGraphicFramePr>"
        f'<a:graphicFrameLocks xmlns:a="{_A}" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f"{graphic}</wp:inline>"
    )
    return f"<w:p>{align}<w:r><w:drawing>{inline}</w:drawing></w:r></w:p>"
