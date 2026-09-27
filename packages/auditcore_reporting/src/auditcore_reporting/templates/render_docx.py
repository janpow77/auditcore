"""DOCX rendering of a resolved document (standard library only, deterministic).

Produces a new, macro-free WordprocessingML package: headings as Word
heading styles (navigation pane, table of contents), bullet lists, tables
with repeated header rows, key data, page breaks, header and footer with
page numbers. Template id, version, fingerprint and data hash are recorded
in the document properties (``dc:description``).
"""

from __future__ import annotations

from . import _wordml as wml
from .design import NEUTRAL_DESIGN, DesignProfile
from .resolve import (
    Node,
    ResolvedDocument,
    RFields,
    RHeading,
    RList,
    RPageBreak,
    RParagraph,
    RTable,
)

_A4 = (11906, 16838)
_JC = {"left": "left", "right": "right", "center": "center"}


def _runs(value: str, bold: bool = False) -> str:
    props = "<w:rPr><w:b/></w:rPr>" if bold else ""
    parts: list[str] = []
    for index, line in enumerate(value.split("\n")):
        if index:
            parts.append("<w:br/>")
        for position, chunk in enumerate(line.split("\t")):
            if position:
                parts.append("<w:tab/>")
            if chunk:
                parts.append(f'<w:t xml:space="preserve">{wml.text(chunk)}</w:t>')
    return f"<w:r>{props}{''.join(parts)}</w:r>" if parts else ""


def _paragraph(value: str, style: str = "", align: str = "", bold: bool = False) -> str:
    props = f'<w:pStyle w:val="{style}"/>' if style else ""
    props += f'<w:jc w:val="{_JC[align]}"/>' if align and align != "left" else ""
    return f"<w:p>{f'<w:pPr>{props}</w:pPr>' if props else ''}{_runs(value, bold)}</w:p>"


def _cell(value: str, width: int, align: str, fill: str = "", bold: bool = False) -> str:
    shade = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
    return (
        f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shade}</w:tcPr>'
        f"{_paragraph(value, align=align, bold=bold)}</w:tc>"
    )


def _table(headers: tuple[str, ...], aligns: tuple[str, ...], rows: tuple[tuple[str, ...], ...],
           width: int, fill: str, grid: bool = True) -> str:  # fmt: skip
    widths = [width // len(aligns)] * len(aligns) if grid else [width * 3 // 10, width * 7 // 10]
    style = '<w:tblStyle w:val="TableGrid"/>' if grid else ""
    columns = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    head = ""
    if headers:
        cells = "".join(
            _cell(h, w, a, fill, True) for h, w, a in zip(headers, widths, aligns, strict=True)
        )
        head = f"<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>{cells}</w:tr>"
    body = "".join(
        "<w:tr><w:trPr><w:cantSplit/></w:trPr>"
        + "".join(
            _cell(v, w, a, bold=not grid and i == 0)
            for i, (v, w, a) in enumerate(zip(row, widths, aligns, strict=True))
        )
        + "</w:tr>"
        for row in rows
    )
    return (
        f'<w:tbl><w:tblPr>{style}<w:tblW w:w="{width}" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
        f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0"'
        ' w:noHBand="0" w:noVBand="1"/></w:tblPr>'
        f"<w:tblGrid>{columns}</w:tblGrid>{head}{body}</w:tbl>"
        '<w:p><w:pPr><w:spacing w:after="0"/></w:pPr></w:p>'
    )


def _node(node: Node, width: int, design: DesignProfile) -> str:
    if isinstance(node, RHeading):
        return _paragraph(node.text, f"Heading{node.level}")
    if isinstance(node, RParagraph):
        return _paragraph(node.text)
    if isinstance(node, RList):
        numbering = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
        return "".join(
            f'<w:p><w:pPr><w:pStyle w:val="ListBullet"/>{numbering}</w:pPr>{_runs(item)}</w:p>'
            for item in node.items
        )
    if isinstance(node, RTable):
        return _table(node.headers, node.aligns, node.rows, width, design.table_header_fill)
    if isinstance(node, RFields):
        return _table((), ("left", "left"), node.rows, width, "", grid=False)
    assert isinstance(node, RPageBreak)
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def _field(instruction: str) -> str:
    return f'<w:fldSimple w:instr=" {instruction} "><w:r><w:t>1</w:t></w:r></w:fldSimple>'


def _header_footer(design: DesignProfile, width: int) -> tuple[bytes, bytes]:
    tabs = f'<w:tabs><w:tab w:val="right" w:pos="{width}"/></w:tabs>'
    header = f'<w:p><w:pPr><w:pStyle w:val="Header"/></w:pPr>{_runs(design.header_text)}</w:p>'
    numbers = ""
    if design.page_numbers:
        numbers = (
            '<w:r><w:tab/><w:t xml:space="preserve">Seite </w:t></w:r>'
            + _field("PAGE")
            + '<w:r><w:t xml:space="preserve"> von </w:t></w:r>'
            + _field("NUMPAGES")
        )
    footer = (
        f'<w:p><w:pPr><w:pStyle w:val="Footer"/>{tabs}</w:pPr>'
        f"{_runs(design.footer_text)}{numbers}</w:p>"
    )
    namespaces = f'xmlns:w="{wml.W}" xmlns:r="{wml.R}"'
    return (
        (wml.DECLARATION + f"<w:hdr {namespaces}>{header}</w:hdr>").encode("utf-8"),
        (wml.DECLARATION + f"<w:ftr {namespaces}>{footer}</w:ftr>").encode("utf-8"),
    )


def _section(design: DesignProfile, with_header: bool) -> str:
    margin = round(design.margin_cm * 567)
    refs = (
        '<w:headerReference w:type="default" r:id="rId4"/>'
        '<w:footerReference w:type="default" r:id="rId5"/>'
        if with_header
        else ""
    )
    return (
        f'<w:sectPr>{refs}<w:pgSz w:w="{_A4[0]}" w:h="{_A4[1]}"/>'
        f'<w:pgMar w:top="{margin}" w:right="{margin}" w:bottom="{margin}" w:left="{margin}"'
        ' w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>'
    )


def provenance(document: ResolvedDocument) -> str:
    """One-line provenance recorded in every output format."""
    return (
        f"Vorlage {document.template_id} {document.template_version}; "
        f"Fingerabdruck {document.template_fingerprint[:16]}; Datenhash {document.data_sha256[:16]}"
    )


def render_docx(document: ResolvedDocument, design: DesignProfile = NEUTRAL_DESIGN) -> bytes:
    """DOCX bytes; identical document and profile give identical bytes."""
    width = _A4[0] - 2 * round(design.margin_cm * 567)
    with_header = bool(design.header_text or design.footer_text or design.page_numbers)
    body = "".join(_node(node, width, design) for node in document.nodes)
    xml = (
        wml.DECLARATION + f'<w:document xmlns:w="{wml.W}" xmlns:r="{wml.R}"><w:body>'
        f"{body}{_section(design, with_header)}</w:body></w:document>"
    )
    entries = [
        ("[Content_Types].xml", wml.content_types(with_header)),
        ("_rels/.rels", wml.package_rels()),
        ("docProps/core.xml", wml.core(document.title, provenance(document))),
        ("docProps/app.xml", wml.app()),
        ("word/document.xml", xml.encode("utf-8")),
        ("word/_rels/document.xml.rels", wml.document_rels(with_header)),
        ("word/styles.xml", wml.styles(design)),
        ("word/settings.xml", wml.settings()),
        ("word/numbering.xml", wml.numbering()),
    ]
    if with_header:
        header, footer = _header_footer(design, width)
        entries += [("word/header1.xml", header), ("word/footer1.xml", footer)]
    return wml.write_zip(entries)
