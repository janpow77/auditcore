"""DOCX rendering of a resolved document (standard library only, deterministic).

Produces a new, macro-free WordprocessingML package: headings as Word
heading styles (navigation pane, table of contents), bullet lists, tables
with repeated header rows, key data, page breaks, header and footer with
page numbers. Template id, version, fingerprint and data hash are recorded
in the document properties (``dc:description``).
"""

from __future__ import annotations

from . import _wordml as wml
from .design import NEUTRAL_DESIGN, DesignProfile, page_orientation
from .options import DEFAULT_OPTIONS, RenderOptions
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


def _widths(total: int, weights: tuple[float, ...], count: int) -> list[int]:
    if not weights:
        return [total // count] * count
    scale = sum(weights)
    return [int(total * weight / scale) for weight in weights]


def _borders(kind: str) -> tuple[str, str]:
    """Table style reference and explicit borders for ``grid``, ``horizontal``, ``none``."""
    if kind == "grid":
        return '<w:tblStyle w:val="TableGrid"/>', ""
    if kind == "none":
        return "", ""
    lines = "".join(
        f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        for side in ("top", "bottom", "insideH")
    )
    return "", f"<w:tblBorders>{lines}</w:tblBorders>"


def _row(cells: str, header: bool = False) -> str:
    props = "<w:cantSplit/><w:tblHeader/>" if header else "<w:cantSplit/>"
    return f"<w:tr><w:trPr>{props}</w:trPr>{cells}</w:tr>"


def _table(node: RTable, width: int, design: DesignProfile) -> str:
    widths = _widths(width, node.widths, len(node.aligns))
    fill = node.header_fill or design.table_header_fill
    head = "".join(
        _cell(h, w, a, fill, True)
        for h, w, a in zip(node.headers, widths, node.aligns, strict=True)
    )
    body = "".join(
        _row(
            "".join(
                _cell(
                    value,
                    w,
                    a,
                    node.fills[r][c] if node.fills else "",
                    bool(node.bold and node.bold[r][c]),
                )  # fmt: skip
                for c, (value, w, a) in enumerate(zip(row, widths, node.aligns, strict=True))
            )
        )
        for r, row in enumerate(node.rows)
    )
    return _frame(width, widths, node.borders, _row(head, header=True) + body)


def _fields(node: RFields, width: int) -> str:
    widths = [width * 3 // 10, width * 7 // 10]
    body = "".join(
        _row(_cell(label, widths[0], "left", bold=True) + _cell(value, widths[1], "left"))
        for label, value in node.rows
    )
    return _frame(width, widths, "none", body)


def _frame(width: int, widths: list[int], borders: str, rows: str) -> str:
    style, lines = _borders(borders)
    columns = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    return (
        f'<w:tbl><w:tblPr>{style}<w:tblW w:w="{width}" w:type="dxa"/>{lines}'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0"'
        ' w:noHBand="0" w:noVBand="1"/></w:tblPr>'
        f"<w:tblGrid>{columns}</w:tblGrid>{rows}</w:tbl>"
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
        return _table(node, width, design)
    if isinstance(node, RFields):
        return _fields(node, width)
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


def _page(orientation: str) -> tuple[int, int]:
    return (_A4[1], _A4[0]) if orientation == "landscape" else _A4


def _section(design: DesignProfile, with_header: bool, orientation: str) -> str:
    margin = round(design.margin_cm * 567)
    refs = (
        '<w:headerReference w:type="default" r:id="rId4"/>'
        '<w:footerReference w:type="default" r:id="rId5"/>'
        if with_header
        else ""
    )
    width, height = _page(orientation)
    orient = ' w:orient="landscape"' if orientation == "landscape" else ""
    return (
        f'<w:sectPr>{refs}<w:pgSz w:w="{width}" w:h="{height}"{orient}/>'
        f'<w:pgMar w:top="{margin}" w:right="{margin}" w:bottom="{margin}" w:left="{margin}"'
        ' w:header="709" w:footer="709" w:gutter="0"/></w:sectPr>'
    )


def provenance(document: ResolvedDocument) -> str:
    """One-line provenance recorded in every output format."""
    return (
        f"Vorlage {document.template_id} {document.template_version}; "
        f"Fingerabdruck {document.template_fingerprint[:16]}; Datenhash {document.data_sha256[:16]}"
    )


def render_docx(
    document: ResolvedDocument,
    design: DesignProfile = NEUTRAL_DESIGN,
    options: RenderOptions = DEFAULT_OPTIONS,
) -> bytes:
    """DOCX bytes; identical document, profile and options give identical bytes."""
    orientation = page_orientation(document.orientation, design)
    width = _page(orientation)[0] - 2 * round(design.margin_cm * 567)
    with_header = bool(design.header_text or design.footer_text or design.page_numbers)
    body = "".join(_node(node, width, design) for node in document.nodes)
    xml = (
        wml.DECLARATION + f'<w:document xmlns:w="{wml.W}" xmlns:r="{wml.R}"><w:body>'
        f"{body}{_section(design, with_header, orientation)}</w:body></w:document>"
    )
    entries = [
        ("[Content_Types].xml", wml.content_types(with_header)),
        ("_rels/.rels", wml.package_rels()),
        (
            "docProps/core.xml",
            wml.core(
                options.document_title(document.title),
                provenance(document),
                options.author,
                options.created_utc,
            ),
        ),
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
