"""HTML rendering of a resolved document (standard library, every text escaped).

The page contains no scripts, no external resources and a restrictive
Content-Security-Policy; it is meant for previews (sandboxed ``iframe``)
and as an archivable HTML version.
"""

from __future__ import annotations

from html import escape

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

_CSP = "default-src 'none'; style-src 'unsafe-inline'"


def _text(text: str) -> str:
    return escape(text).replace("\n", "<br>")


def _style(design: DesignProfile, orientation: str) -> str:
    h1, h2, h3 = design.heading_sizes_pt
    font = escape(design.font_family, quote=True).replace(";", "")
    page = "@page{size:A4 landscape}" if orientation == "landscape" else ""
    return page + (
        f"body{{font-family:'{font}',sans-serif;font-size:{design.font_size_pt}pt;"
        f"margin:{design.margin_cm}cm;line-height:1.4;color:#1a1a1a;background:#fff}}"
        f"h1,h2,h3{{color:#{design.accent_color};margin:1.2em 0 .4em}}"
        f"h1{{font-size:{h1}pt}}h2{{font-size:{h2}pt}}h3{{font-size:{h3}pt}}"
        "table{border-collapse:collapse;width:100%;margin:.6em 0}"
        "td,th{border:1px solid #808080;padding:.25em .4em;vertical-align:top}"
        f"th{{background:#{design.table_header_fill};text-align:left}}"
        ".right{text-align:right}.center{text-align:center}"
        "table.fields td{border:none;padding:.1em .6em .1em 0}table.fields"
        " td:first-child{font-weight:bold}"
        "hr.page{border:none;border-top:1px dashed #999;margin:2em 0}"
        "header,footer{color:#555;font-size:.85em}"
    )


_BORDER_STYLE = {
    "grid": "",
    "horizontal": "border-left:none;border-right:none;",
    "none": "border:none;",
}


def _cell_style(node: RTable, row: int, column: int) -> str:
    style = _BORDER_STYLE[node.borders]
    if node.fills and node.fills[row][column]:
        style += f"background:#{node.fills[row][column]};"
    if node.bold and node.bold[row][column]:
        style += "font-weight:bold;"
    return f' style="{style}"' if style else ""


def _table(node: RTable) -> str:
    head_style = _BORDER_STYLE[node.borders]
    head_style += f"background:#{node.header_fill};" if node.header_fill else ""
    head_attr = f' style="{head_style}"' if head_style else ""
    head = "".join(
        f'<th class="{align}"{head_attr}>{_text(text)}</th>'
        for text, align in zip(node.headers, node.aligns, strict=True)
    )
    body = "".join(
        "<tr>"
        + "".join(
            f'<td class="{a}"{_cell_style(node, r, c)}>{_text(value)}</td>'
            for c, (value, a) in enumerate(zip(row, node.aligns, strict=True))
        )
        + "</tr>"
        for r, row in enumerate(node.rows)
    )
    columns = ""
    if node.widths:
        total = sum(node.widths)
        columns = (
            "<colgroup>"
            + "".join(f'<col style="width:{100 * w / total:.2f}%">' for w in node.widths)
            + "</colgroup>"
        )
    return f"<table>{columns}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _node(node: Node) -> str:
    if isinstance(node, RHeading):
        return f"<h{node.level}>{_text(node.text)}</h{node.level}>"
    if isinstance(node, RParagraph):
        block = f' data-block="{escape(node.block, quote=True)}"' if node.block else ""
        return f"<p{block}>{_text(node.text)}</p>"
    if isinstance(node, RList):
        return "<ul>" + "".join(f"<li>{_text(item)}</li>" for item in node.items) + "</ul>"
    if isinstance(node, RTable):
        return _table(node)
    if isinstance(node, RFields):
        rows = "".join(f"<tr><td>{_text(k)}</td><td>{_text(v)}</td></tr>" for k, v in node.rows)
        return f'<table class="fields"><tbody>{rows}</tbody></table>'
    assert isinstance(node, RPageBreak)
    return '<hr class="page">'


def render_html(
    document: ResolvedDocument,
    design: DesignProfile = NEUTRAL_DESIGN,
    options: RenderOptions = DEFAULT_OPTIONS,
) -> str:
    """Complete HTML5 page; identical input gives an identical page."""
    header = f"<header>{_text(design.header_text)}</header>" if design.header_text else ""
    footer = f"<footer>{_text(design.footer_text)}</footer>" if design.footer_text else ""
    body = "\n".join(_node(node) for node in document.nodes)
    style = _style(design, page_orientation(document.orientation, design))
    generator = escape(f"{document.template_id} {document.template_version}", quote=True)
    meta = f'<meta name="generator" content="auditcore_reporting {generator}">'
    if options.author:
        meta += f'<meta name="author" content="{escape(options.author, quote=True)}">'
    if options.created_utc is not None:
        stamp = options.created_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        meta += f'<meta name="dcterms.created" content="{stamp}">'
    return (
        '<!DOCTYPE html>\n<html lang="de"><head><meta charset="utf-8">'
        f'<meta http-equiv="Content-Security-Policy" content="{_CSP}">{meta}'
        f"<title>{_text(options.document_title(document.title))}</title><style>{style}</style></head>"
        f"<body>{header}<main>\n{body}\n</main>{footer}</body></html>\n"
    )
