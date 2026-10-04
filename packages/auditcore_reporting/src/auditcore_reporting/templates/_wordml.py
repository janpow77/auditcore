"""Static WordprocessingML parts and the deterministic ZIP writer (standard library).

All parts are generated from escaped values; nothing is parsed. The ZIP has a
fixed entry order, fixed timestamps and fixed permissions, so identical input
gives byte-identical files.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Sequence
from datetime import datetime
from xml.sax.saxutils import escape, quoteattr

from .design import DesignProfile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
DECLARATION = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
_DOC_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml"
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def write_zip(entries: Sequence[tuple[str, bytes]]) -> bytes:
    """Deterministic ZIP: given order, fixed time, mode 0644, deflate level 6."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in entries:
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=6)
    return buffer.getvalue()


def attr(value: str) -> str:
    """Escaped, quoted XML attribute value."""
    return quoteattr(value)


def text(value: str) -> str:
    """Escaped XML text."""
    return escape(value)


def runs(value: str, props: str = "") -> str:
    """One run with line breaks and tabs; ``props`` is the run formatting (``<w:b/>`` …)."""
    parts: list[str] = []
    for index, line in enumerate(value.split("\n")):
        if index:
            parts.append("<w:br/>")
        for position, chunk in enumerate(line.split("\t")):
            if position:
                parts.append("<w:tab/>")
            if chunk:
                parts.append(f'<w:t xml:space="preserve">{text(chunk)}</w:t>')
    formatting = f"<w:rPr>{props}</w:rPr>" if props else ""
    return f"<w:r>{formatting}{''.join(parts)}</w:r>" if parts else ""


def content_types(with_header: bool, pictures: Sequence[str] = ()) -> bytes:
    """``[Content_Types].xml``; ``pictures`` are the media extensions (``png``, ``jpeg``)."""
    parts = [
        ("/word/document.xml", f"{_DOC_TYPE}.document.main+xml"),
        ("/word/styles.xml", f"{_DOC_TYPE}.styles+xml"),
        ("/word/settings.xml", f"{_DOC_TYPE}.settings+xml"),
        ("/word/numbering.xml", f"{_DOC_TYPE}.numbering+xml"),
        ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        (
            "/docProps/app.xml",
            "application/vnd.openxmlformats-officedocument.extended-properties+xml",
        ),
    ]
    if with_header:
        parts += [
            ("/word/header1.xml", f"{_DOC_TYPE}.header+xml"),
            ("/word/footer1.xml", f"{_DOC_TYPE}.footer+xml"),
        ]
    overrides = "".join(f"<Override PartName={attr(n)} ContentType={attr(t)}/>" for n, t in parts)
    return (
        DECLARATION
        + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + '<Default Extension="rels"'
        ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        + '<Default Extension="xml" ContentType="application/xml"/>'
        + "".join(f'<Default Extension="{e}" ContentType="image/{e}"/>' for e in pictures)
        + overrides
        + "</Types>"
    ).encode("utf-8")


def _relationships(items: Sequence[tuple[str, str, str]]) -> bytes:
    body = "".join(
        f'<Relationship Id="{rid}" Type={attr(kind)} Target={attr(target)}/>'
        for rid, kind, target in items
    )
    return (DECLARATION + f'<Relationships xmlns="{PKG_RELS}">{body}</Relationships>').encode()


def package_rels() -> bytes:
    """``_rels/.rels``."""
    return _relationships(
        [
            ("rId1", f"{_REL}/officeDocument", "word/document.xml"),
            (
                "rId2",
                "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
                "docProps/core.xml",
            ),
            ("rId3", f"{_REL}/extended-properties", "docProps/app.xml"),
        ]
    )


def document_rels(with_header: bool, pictures: Sequence[tuple[str, str]] = ()) -> bytes:
    """``word/_rels/document.xml.rels``; ``pictures`` as (relationship id, target)."""
    items = [
        ("rId1", f"{_REL}/styles", "styles.xml"),
        ("rId2", f"{_REL}/settings", "settings.xml"),
        ("rId3", f"{_REL}/numbering", "numbering.xml"),
    ]
    if with_header:
        items += [
            ("rId4", f"{_REL}/header", "header1.xml"),
            ("rId5", f"{_REL}/footer", "footer1.xml"),
        ]
    items += [(rid, f"{_REL}/image", target) for rid, target in pictures]
    return _relationships(items)


def core(title: str, description: str, author: str = "", created: datetime | None = None) -> bytes:
    """``docProps/core.xml``; timestamps only when the caller passes ``created`` (UTC)."""
    namespaces = ""
    extra = ""
    if author:
        extra += f"<dc:creator>{text(author)}</dc:creator>"
        extra += f"<cp:lastModifiedBy>{text(author)}</cp:lastModifiedBy>"
    if created is not None:
        namespaces = (
            ' xmlns:dcterms="http://purl.org/dc/terms/"'
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        )
        stamp = created.strftime("%Y-%m-%dT%H:%M:%SZ")
        extra += "".join(
            f'<dcterms:{name} xsi:type="dcterms:W3CDTF">{stamp}</dcterms:{name}>'
            for name in ("created", "modified")
        )
    return (
        DECLARATION
        + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
        f' xmlns:dc="http://purl.org/dc/elements/1.1/"{namespaces}>'
        f"<dc:title>{text(title)}</dc:title><dc:description>{text(description)}</dc:description>"
        f"{extra}<dc:language>de-DE</dc:language></cp:coreProperties>"
    ).encode("utf-8")


def app() -> bytes:
    """``docProps/app.xml``."""
    return (
        DECLARATION
        + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        "<Application>auditcore_reporting</Application></Properties>"
    ).encode("utf-8")


def settings() -> bytes:
    """``word/settings.xml``: German language, no field update prompt."""
    return (
        DECLARATION + f'<w:settings xmlns:w="{W}"><w:defaultTabStop w:val="708"/>'
        '<w:characterSpacingControl w:val="doNotCompress"/><w:compat>'
        '<w:compatSetting w:name="compatibilityMode"'
        ' w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
        '</w:compat><w:themeFontLang w:val="de-DE"/></w:settings>'
    ).encode("utf-8")


def numbering() -> bytes:
    """``word/numbering.xml``: one bullet list definition (numId 1)."""
    level = (
        '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/>'
        '<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>'
    )
    return (
        DECLARATION + f'<w:numbering xmlns:w="{W}"><w:abstractNum w:abstractNumId="0">'
        f'<w:multiLevelType w:val="singleLevel"/>{level}</w:abstractNum>'
        '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>'
    ).encode("utf-8")


def _heading_style(level: int, size: float, color: str) -> str:
    return (
        f'<w:style w:type="paragraph" w:styleId="Heading{level}"><w:name w:val="heading {level}"/>'
        '<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
        f'<w:pPr><w:keepNext/><w:spacing w:before="{360 - level * 60}" w:after="120"/>'
        f'<w:outlineLvl w:val="{level - 1}"/></w:pPr>'
        f'<w:rPr><w:b/><w:color w:val="{color}"/><w:sz'
        f' w:val="{round(size * 2)}"/></w:rPr></w:style>'
    )


def styles(design: DesignProfile) -> bytes:
    """``word/styles.xml`` from the design profile."""
    font = attr(design.font_family)
    size = round(design.font_size_pt * 2)
    headings = "".join(
        _heading_style(level, s, design.accent_color)
        for level, s in enumerate(design.heading_sizes_pt, start=1)
    )
    border = "".join(
        f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        for side in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    return (
        DECLARATION + f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr>'
        f"<w:rFonts w:ascii={font} w:hAnsi={font} w:cs={font} w:eastAsia={font}/>"
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        '<w:lang w:val="de-DE"/></w:rPr></w:rPrDefault>'
        '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr>'
        "</w:pPrDefault></w:docDefaults>"
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/><w:qFormat/></w:style>'
        f"{headings}"
        '<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/>'
        '<w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="60"/></w:pPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Header">'
        '<w:name w:val="header"/><w:basedOn w:val="Normal"/>'
        '<w:rPr><w:sz w:val="18"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Footer">'
        '<w:name w:val="footer"/><w:basedOn w:val="Normal"/>'
        '<w:rPr><w:sz w:val="18"/></w:rPr></w:style>'
        '<w:style w:type="table" w:default="1"'
        ' w:styleId="TableNormal"><w:name w:val="Normal Table"/>'
        '<w:tblPr><w:tblCellMar><w:left w:w="108" w:type="dxa"/><w:right w:w="108" w:type="dxa"/>'
        "</w:tblCellMar></w:tblPr></w:style>"
        '<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/>'
        '<w:basedOn w:val="TableNormal"/><w:tblPr>'
        f"<w:tblBorders>{border}</w:tblBorders></w:tblPr></w:style>"
        "</w:styles>"
    ).encode("utf-8")
