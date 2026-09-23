"""DOCX-Synopse (Extra ``docx-render``: python-docx).

Unveränderte Darstellung aus ``rendering.py`` des Originals: Querformat,
vierspaltige Tabelle (Fundstelle, bisherige/neue Fassung, Grund),
Gruppenzeilen, Wortmarkierung, Vermerk-Gliederung mit ``{{vergleich}}``,
nicht teilbare Tabellenzeilen, Seitenzahlen und konsolidierte Arbeitsfassung
bei der Gesetzessynopse. Zeitangaben werden in der lokalen Zeitzone des
Prozesses formatiert (wie im Original). Die Bibliothek liefert nur den
Renderer; ``auditcore_reporting`` 0.2.0 kennt keine DOCX-Ausgabe.
"""

from __future__ import annotations

import difflib
from datetime import datetime
from pathlib import Path
from typing import Any

from auditcore_documents.errors import DependencyError
from auditcore_documents.model import CompareRow, ComparisonResult

NAVY = "14006E"
TINT = "E6EFFF"
HEADER_FILL = "BACBFF"
REMOVED = "B91C1C"
ADDED = "166534"


def _format_timestamp(value: Any) -> str:
    if not value:
        return "unbekannt"
    try:
        if isinstance(value, (int, float)):
            parsed = datetime.fromtimestamp(value)
        else:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.astimezone().strftime("%d.%m.%Y, %H:%M")
    except (ValueError, TypeError, OSError):
        return str(value)


def _zeile_zusammenhalten(zeile: Any) -> None:
    """Verhindert, dass eine Tabellenzeile am Seitenumbruch zerrissen wird.

    Ohne dieses Flag brach Word die Zeile mitten im Satz um: Die Fundstelle
    stand dann auf der einen Seite, die Hälfte des Textes auf der nächsten,
    und die Fundstellenspalte der Folgeseite blieb leer. In einem Vermerk
    ist eine Textstelle ohne zugehörige Fundstelle wertlos.

    Ist eine Zeile höher als eine Seite, teilt Word sie trotzdem — dieser
    Rückfall ist gewollt, sonst ginge der Inhalt ganz verloren.
    """

    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    eigenschaften = zeile._tr.get_or_add_trPr()
    nicht_teilen = OxmlElement("w:cantSplit")
    nicht_teilen.set(qn("w:val"), "true")
    eigenschaften.append(nicht_teilen)


def _shade(cell: Any, color: str) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:color"), "auto")
    shading.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(shading)


def _set_cell_margins(cell: Any, value: int = 100) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tc_pr = cell._tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for edge in ("top", "start", "bottom", "end"):
        node = margins.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _add_word_highlight(paragraph: Any, old: str, new: str, side: str) -> None:
    from docx.shared import RGBColor

    matcher = difflib.SequenceMatcher(None, (old or "").split(), (new or "").split())
    old_tokens = (old or "").split()
    new_tokens = (new or "").split()
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            tokens = old_tokens[i1:i2] if side == "old" else new_tokens[j1:j2]
            color = None
        elif side == "old" and tag in {"replace", "delete"}:
            tokens = old_tokens[i1:i2]
            color = REMOVED
        elif side == "new" and tag in {"replace", "insert"}:
            tokens = new_tokens[j1:j2]
            color = ADDED
        else:
            continue
        if not tokens:
            continue
        if paragraph.runs:
            paragraph.add_run(" ")
        run = paragraph.add_run(" ".join(tokens))
        if color:
            run.bold = True
            run.font.color.rgb = RGBColor.from_string(color)
            if side == "old":
                run.font.strike = True


def _add_labeled_value(paragraph: Any, label: str, value: str) -> None:
    if not value:
        return
    if paragraph.text:
        paragraph.add_run("\n")
    label_run = paragraph.add_run(f"{label}: ")
    label_run.bold = True
    paragraph.add_run(value)


def _fill_version_cell(
    cell: Any,
    row: CompareRow,
    side: str,
    *,
    include_answers: bool,
    include_notes: bool,
    highlight_words: bool,
) -> None:
    text = row.old_text if side == "old" else row.new_text
    answer = row.old_answer if side == "old" else row.new_answer
    comment = row.old_comment if side == "old" else row.new_comment
    note = row.old_note if side == "old" else row.new_note
    paragraph = cell.paragraphs[0]
    paragraph.clear()
    if not text:
        paragraph.add_run("nicht vorhanden" if side == "old" else "nicht mehr enthalten")
    elif highlight_words and row.status == "changed":
        _add_word_highlight(paragraph, row.old_text, row.new_text, side)
    else:
        paragraph.add_run(text)
    if include_answers:
        _add_labeled_value(paragraph, "Antwort", answer)
        _add_labeled_value(paragraph, "Bemerkung", comment)
    if include_notes:
        _add_labeled_value(paragraph, "Hinweis", note)
    if side == "old":
        for run in paragraph.runs:
            run.italic = True


def _build_document(
    result: ComparisonResult,
    *,
    title: str | None = None,
    user: str = "",
    header: str | None = None,
    profile: str = "memo",
    layout: dict[str, Any] | None = None,
) -> Any:
    try:
        from docx import Document
        from docx.enum.section import WD_ORIENT
        from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
        from docx.enum.text import WD_TAB_ALIGNMENT
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Cm, Pt, RGBColor
    except ImportError as exc:
        raise DependencyError("Die DOCX-Ausgabe benötigt python-docx.") from exc

    layout = layout or {}
    font_family = str(layout.get("font_family") or "Hessen Gellix")[:80]
    body_size = max(8.0, min(18.0, float(layout.get("body_font_size_pt", 10))))
    heading_size = max(10.0, min(24.0, float(layout.get("heading_font_size_pt", 14))))
    line_spacing = max(1.0, min(2.0, float(layout.get("line_spacing", 1))))
    margin_cm = max(1.0, min(4.0, float(layout.get("page_margin_cm", 2))))
    accent_color = str(layout.get("accent_color") or NAVY).lstrip("#").upper()
    if len(accent_color) != 6 or any(value not in "0123456789ABCDEF" for value in accent_color):
        accent_color = NAVY
    header_text = str(header if header is not None else layout.get("header_text") or "Vermerk")
    footer_text = str(layout.get("footer_text") or "")
    show_page_numbers = bool(layout.get("show_page_numbers", True))
    show_file_metadata = bool(layout.get("show_file_metadata", True))

    document = Document()
    section = document.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Cm(29.7), Cm(21)
    for attr in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, attr, Cm(margin_cm))
    normal = document.styles["Normal"]
    normal.font.name = font_family
    normal.font.size = Pt(body_size)
    normal.paragraph_format.line_spacing = line_spacing
    normal._element.rPr.rFonts.set(qn("w:ascii"), font_family)
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), font_family)
    normal._element.rPr.rFonts.set(qn("w:cs"), font_family)

    header_p = section.header.paragraphs[0]
    header_p.paragraph_format.tab_stops.clear_all()
    usable_width = section.page_width - section.left_margin - section.right_margin
    header_p.paragraph_format.tab_stops.add_tab_stop(usable_width, WD_TAB_ALIGNMENT.RIGHT)
    header_lines = [line.strip() for line in header_text.splitlines() if line.strip()]
    header_run = header_p.add_run(f"{header_lines[0] if header_lines else 'Vermerk'}\t{user}")
    header_run.font.size = Pt(9)
    header_run.font.name = font_family
    header_run.font.color.rgb = RGBColor.from_string(accent_color)
    for line in header_lines[1:]:
        run = header_p.add_run(f"\n{line}")
        run.font.size = Pt(9)
        run.font.name = font_family
        run.font.color.rgb = RGBColor.from_string(accent_color)

    footer = section.footer.paragraphs[0]
    footer.paragraph_format.tab_stops.clear_all()
    footer.paragraph_format.tab_stops.add_tab_stop(usable_width, WD_TAB_ALIGNMENT.RIGHT)
    footer.add_run(footer_text)
    if show_page_numbers:
        footer.add_run("\tSeite ")
        page = OxmlElement("w:fldSimple")
        page.set(qn("w:instr"), "PAGE")
        footer._p.append(page)
        footer.add_run(" von ")
        pages = OxmlElement("w:fldSimple")
        pages.set(qn("w:instr"), "NUMPAGES")
        footer._p.append(pages)

    title_p = document.add_paragraph()
    title_run = title_p.add_run(
        title or f"Vergleich: {result.old_filename} / {result.new_filename}"
    )
    title_run.bold = True
    title_run.font.size = Pt(heading_size)
    title_run.font.color.rgb = RGBColor.from_string(accent_color)

    if show_file_metadata:
        old_modified = _format_timestamp(result.metadata.get("old_modified_at"))
        new_modified = _format_timestamp(result.metadata.get("new_modified_at"))
        document.add_paragraph(
            f"{result.metadata.get('old_label', 'Bisherige Fassung')}: "
            f"{result.old_filename} · geändert {old_modified} · SHA-256 {result.old_sha256}\n"
            f"{result.metadata.get('new_label', 'Neue Fassung')}: "
            f"{result.new_filename} · geändert {new_modified} · SHA-256 {result.new_sha256}"
        )
    mode_label = "Checkliste" if result.mode == "checklist" else "Fließtext"
    document.add_paragraph(
        f"Dokumentart: {mode_label} · Vergleichsmodul {result.version} · "
        f"Erstellt {_format_timestamp(result.created_at)}"
    )
    notice = result.metadata.get("work_aid_notice") or (
        "Die Maschine stellt Unterschiede fest und bereitet sie auf. "
        "Sie trifft keine Prüfungsentscheidung; die Würdigung bleibt beim Prüfer."
    )
    notice_p = document.add_paragraph()
    notice_run = notice_p.add_run(str(notice))
    notice_run.italic = True

    comparison_anchor = None
    if profile == "memo":
        outline = layout.get("outline") or []
        for raw_heading in outline:
            raw_heading = str(raw_heading).strip()
            if not raw_heading:
                continue
            is_comparison = "{{vergleich}}" in raw_heading
            heading_text = raw_heading.replace("{{vergleich}}", "").strip()
            heading_p = document.add_paragraph()
            heading_run = heading_p.add_run(heading_text or "Festgestellte Änderungen")
            heading_run.bold = True
            heading_run.font.size = Pt(max(body_size + 1, heading_size - 2))
            heading_run.font.color.rgb = RGBColor.from_string(accent_color)
            if is_comparison:
                comparison_anchor = heading_p
            else:
                document.add_paragraph()

    table = document.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    widths = [Cm(4.7), Cm(7.6), Cm(7.6), Cm(5.8)]
    labels = [
        "Fundstelle",
        str(result.metadata.get("old_label") or "Bisherige Fassung"),
        str(result.metadata.get("new_label") or "Neue Fassung"),
        str(result.metadata.get("reason_label") or "Grund der Änderung"),
    ]
    for cell, label, width in zip(table.rows[0].cells, labels, widths, strict=True):
        cell.text = label
        cell.width = width
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        _shade(cell, HEADER_FILL)
        _set_cell_margins(cell)
        for run in cell.paragraphs[0].runs:
            run.bold = True
    header_props = table.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    header_props.append(repeat)
    _zeile_zusammenhalten(table.rows[0])

    unit = "Textstellen" if result.mode == "text" else "Prüffragen"
    group_labels = {
        "changed": f"I. Geänderte {unit}",
        "removed": f"II. Entfallene {unit}",
        "added": f"III. Neue {unit}",
        # Gleicher Wortlaut, andere Stelle. Eigene Gruppe, damit eine
        # Umstellung nicht als Streichung samt Neuaufnahme gelesen wird.
        "moved": f"IV. Umgestellte {unit}",
        "unchanged": f"V. Unveränderte {unit}",
        "manual": "Von Hand zu bearbeiten",
    }
    output_sections = set(
        result.metadata.get("output_sections") or ["changed", "removed", "added", "moved"]
    )
    include_answers = bool(result.metadata.get("include_answers", True))
    include_notes = bool(result.metadata.get("include_notes", True))
    highlight_words = bool(result.metadata.get("highlight_words", True))
    current_group = ""
    for row in result.rows:
        if not row.selected or row.status not in output_sections:
            continue
        if row.status != current_group:
            current_group = row.status
            gruppenzeile = table.add_row()
            _zeile_zusammenhalten(gruppenzeile)
            cells = gruppenzeile.cells
            merged = cells[0].merge(cells[3])
            merged.text = group_labels.get(row.status, row.status)
            _shade(merged, TINT)
            _set_cell_margins(merged)
            for run in merged.paragraphs[0].runs:
                run.bold = True
        datenzeile = table.add_row()
        _zeile_zusammenhalten(datenzeile)
        cells = datenzeile.cells
        for cell, width in zip(cells, widths, strict=True):
            cell.width = width
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            _set_cell_margins(cell)
        cells[0].text = row.location or "—"
        cells[0].paragraphs[0].runs[0].bold = True
        _fill_version_cell(
            cells[1],
            row,
            "old",
            include_answers=include_answers,
            include_notes=include_notes,
            highlight_words=highlight_words,
        )
        _fill_version_cell(
            cells[2],
            row,
            "new",
            include_answers=include_answers,
            include_notes=include_notes,
            highlight_words=highlight_words,
        )
        reason = row.reason
        if row.reason_source == "flowagent" and reason:
            reason = f"Maschineller Vorschlag (FlowAgent): {reason}"
        if row.reason_warning:
            reason = f"{reason}\nPrüfhinweis: {row.reason_warning}".strip()
        cells[3].text = reason

    if comparison_anchor is not None:
        comparison_anchor._p.addnext(table._tbl)

    open_commands = result.metadata.get("open_commands") or []
    if open_commands:
        heading = document.add_paragraph()
        heading_run = heading.add_run("Von Hand zu bearbeiten")
        heading_run.bold = True
        heading_run.font.color.rgb = RGBColor.from_string(accent_color)
        for command in open_commands:
            document.add_paragraph(str(command), style="List Bullet")
    if result.metadata.get("comparison_type") == "article_law":
        document.add_paragraph(
            f"Änderungsbefehle erkannt: {result.metadata.get('recognised_commands', 0)} · "
            f"offen: {result.metadata.get('open_command_count', 0)}"
        )
        consolidated = result.metadata.get("consolidated_text") or []
        if consolidated and result.metadata.get("include_consolidated_text", True):
            document.add_page_break()
            heading = document.add_paragraph()
            run = heading.add_run("Konsolidierte Arbeitsfassung (nicht amtlich)")
            run.bold = True
            run.font.size = Pt(13)
            last_section = ""
            for item in consolidated:
                if item.get("repealed"):
                    continue
                if item.get("section") != last_section:
                    last_section = str(item.get("section") or "")
                    section_p = document.add_paragraph()
                    section_run = section_p.add_run(last_section)
                    section_run.bold = True
                document.add_paragraph(str(item.get("text") or ""))

    return document


def render_docx(
    result: ComparisonResult,
    output: Path,
    *,
    title: str | None = None,
    user: str = "",
    header: str | None = None,
    profile: str = "memo",
    layout: dict[str, Any] | None = None,
) -> None:
    """Synopse als DOCX nach ``output`` schreiben (Verzeichnisse werden angelegt).

    Ungültige Layoutwerte (z. B. nicht numerische Schriftgröße) lösen wie im
    Original ``ValueError`` aus; fehlt python-docx, ``DependencyError``.
    """
    document = _build_document(
        result, title=title, user=user, header=header, profile=profile, layout=layout
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)


def render_docx_bytes(
    result: ComparisonResult,
    *,
    title: str | None = None,
    user: str = "",
    header: str | None = None,
    profile: str = "memo",
    layout: dict[str, Any] | None = None,
) -> bytes:
    """Wie :func:`render_docx`, aber als Bytes ohne Dateizugriff."""
    import io

    document = _build_document(
        result, title=title, user=user, header=header, profile=profile, layout=layout
    )
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
