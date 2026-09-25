"""Lesen von DOCX/DOCM (WordprocessingML) – Extra ``docx`` (lxml).

Die Auswertung (Checklisten-Zeilen, Fließtext-Absätze, angenommene
Nachverfolgung) entspricht unverändert ``parsing.py`` des Originals.
Abweichend wird das XML gehärtet geparst (DC-C02) und die Größe des
entpackten Hauptteils begrenzt (DC-C03).
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

from auditcore_documents.errors import DependencyError, LimitExceededError, ParseError
from auditcore_documents.limits import ReadLimits
from auditcore_documents.model import CompareItem
from auditcore_documents.normalize import normalise_for_match

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
W = f"{{{W_NS}}}"
NS = {"w": W_NS, "w14": W14_NS}

HEADING_RE = re.compile(
    r"^(?:§+\s*\d+[a-z]?|Art(?:ikel)?\.?\s*\d+[a-z]?|Abschnitt\s+[\w.-]+|Teil\s+[\w.-]+)\b",
    re.IGNORECASE,
)

_CHANGE_TAGS = (
    "rPrChange",
    "pPrChange",
    "tblPrChange",
    "tcPrChange",
    "trPrChange",
    "sectPrChange",
    "customXmlInsRangeStart",
    "customXmlInsRangeEnd",
    "customXmlDelRangeStart",
    "customXmlDelRangeEnd",
)
_IGNORED_STABLE_IDS = {"bemerkung", "antwort", "checkbox", "datum", "text", "richtext"}


def _etree() -> Any:
    try:
        from lxml import etree
    except ImportError as exc:  # pragma: no cover - abhängig von der Umgebung
        raise DependencyError("Das Lesen von DOCX/DOCM benötigt das Extra 'docx' (lxml).") from exc
    return etree


def _parser(etree: Any) -> Any:
    """Keine DTD, keine Entitäten, kein Netz, keine übergroßen Bäume."""
    return etree.XMLParser(
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
        huge_tree=False,
        dtd_validation=False,
        remove_comments=False,
    )


def read_ooxml(path: Path, limits: ReadLimits) -> Any:
    """``word/document.xml`` gehärtet einlesen; Fehlertexte wie im Original."""
    etree = _etree()
    try:
        size = path.stat().st_size
        if size > limits.max_file_bytes:
            raise LimitExceededError(
                f"{path.name} ist größer als die zulässigen {limits.max_file_bytes} Bytes."
            )
        with zipfile.ZipFile(path) as archive:
            if "word/document.xml" not in archive.namelist():
                raise ParseError(f"{path.name} ist keine lesbare Word-Datei oder ist geschützt.")
            info = archive.getinfo("word/document.xml")
            if info.file_size > limits.max_xml_bytes:
                raise LimitExceededError(
                    f"{path.name}: word/document.xml überschreitet "
                    f"{limits.max_xml_bytes} Bytes (entpackt)."
                )
            with archive.open(info) as handle:
                payload = handle.read(limits.max_xml_bytes + 1)
            if len(payload) > limits.max_xml_bytes:
                raise LimitExceededError(
                    f"{path.name}: word/document.xml überschreitet "
                    f"{limits.max_xml_bytes} Bytes (entpackt)."
                )
        root = etree.fromstring(payload, _parser(etree))
    except ParseError:
        raise
    except (zipfile.BadZipFile, KeyError, etree.XMLSyntaxError, OSError) as exc:
        raise ParseError(
            f"{path.name} ist beschädigt, geschützt oder keine gültige DOCX-/DOCM-Datei."
        ) from exc
    doctype = root.getroottree().docinfo.doctype
    if doctype:
        # DC-C02: Das Original (lxml 5.1) löste interne Entitäten auf; Word
        # schreibt keine DTD. Eine DTD ist daher ein Fehler, keine Eingabe.
        raise ParseError(f"{path.name} enthält eine DTD und wird nicht verarbeitet.")
    return root


def accept_revisions(root: Any) -> None:
    """Nachverfolgte Einfügungen/Löschungen im Speicher annehmen (Datei bleibt unberührt)."""
    for deleted in list(root.xpath(".//w:del", namespaces=NS)):
        parent = deleted.getparent()
        if parent is not None:
            parent.remove(deleted)
    for inserted in list(root.xpath(".//w:ins", namespaces=NS)):
        parent = inserted.getparent()
        if parent is None:
            continue
        index = parent.index(inserted)
        for child in list(inserted):
            parent.insert(index, child)
            index += 1
        parent.remove(inserted)
    for tag in _CHANGE_TAGS:
        for element in list(root.iter(f"{W}{tag}")):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)


def visible_text(element: Any) -> str:
    return re.sub(r"\s+", " ", "".join(element.xpath(".//w:t/text()", namespaces=NS))).strip()


def _row_cells(row: Any) -> list[Any]:
    """Direkte Zellen und Zellen in Inhaltssteuerelementen."""
    return list(
        row.xpath(
            "./w:tc | ./w:sdt/w:sdtContent/w:tc | ./w:customXml/w:tc",
            namespaces=NS,
        )
    )


def _cell_text(cell: Any) -> tuple[str, str]:
    visible: list[str] = []
    notes: list[str] = []
    for run in cell.xpath(".//w:r", namespaces=NS):
        text = "".join(run.xpath(".//w:t/text()", namespaces=NS))
        if not text.strip():
            continue
        hidden = bool(run.xpath("./w:rPr/w:vanish", namespaces=NS))
        italic = bool(run.xpath("./w:rPr/w:i | ./w:rPr/w:iCs", namespaces=NS))
        (notes if hidden or italic else visible).append(text)
    return (
        re.sub(r"\s+", " ", "".join(visible)).strip(),
        re.sub(r"\s+", " ", "".join(notes)).strip(),
    )


def _stable_id(row: Any) -> str:
    candidates = row.xpath(
        ".//w:sdtPr/w:tag/@w:val | .//w:sdtPr/w:alias/@w:val",
        namespaces=NS,
    )
    for candidate in candidates:
        value = re.sub(r"\s+", " ", str(candidate)).strip()
        if len(value) >= 3 and value.casefold() not in _IGNORED_STABLE_IDS:
            return value[:160]
    return ""


def _checkbox_state(cell: Any) -> bool | None:
    values = cell.xpath(".//w14:checkbox/w14:checked/@w14:val", namespaces=NS)
    if values:
        return str(values[-1]).lower() in {"1", "true", "on"}
    text = visible_text(cell)
    if "☒" in text or "☑" in text:
        return True
    if "☐" in text:
        return False
    return None


def _clean_checkbox_label(text: str) -> str:
    return re.sub(r"[☐☑☒]", "", text or "").strip(" |;,")


def _question(values: list[tuple[str, str]]) -> tuple[int, str] | None:
    """Fragespalte: erste Zelle, sonst erste Zelle (außer der letzten) mit Text."""
    first = _clean_checkbox_label(values[0][0])
    if len(normalise_for_match(first)) < 3:
        for index, (candidate, _note) in enumerate(values[:-1]):
            cleaned = _clean_checkbox_label(candidate)
            if len(normalise_for_match(cleaned)) >= 3:
                return index, cleaned
        return None
    return 0, first


def _answers(cells: list[Any], values: list[tuple[str, str]], question_index: int) -> list[str]:
    """Beschriftungen angekreuzter Zellen (höchstens 160 Zeichen) außer der Frage."""
    answers: list[str] = []
    for index, cell in enumerate(cells):
        if index == question_index or not _checkbox_state(cell):
            continue
        label = _clean_checkbox_label(values[index][0])
        if label and len(label) <= 160:
            answers.append(label)
    return answers


def _comment(cells: list[Any], values: list[tuple[str, str]], question_index: int) -> str:
    """Letzte Zelle ohne Kontrollkästchen ist die Bemerkung (wenn nicht die Frage)."""
    if question_index == len(cells) - 1 or _checkbox_state(cells[-1]) is not None:
        return ""
    return _clean_checkbox_label(values[-1][0])


def checklist_items(root: Any) -> list[CompareItem]:
    """Prüffragen aus Tabellenzeilen (einspaltige Zeilen sind Abschnittstitel)."""
    items: list[CompareItem] = []
    section = ""
    for row_index, row in enumerate(root.xpath(".//w:tbl//w:tr", namespaces=NS)):
        cells = _row_cells(row)
        if not cells:
            continue
        if len(cells) == 1:
            whole_row = visible_text(row)
            if whole_row:
                section = whole_row[:240]
            continue
        values = [_cell_text(cell) for cell in cells]
        found = _question(values)
        if found is None:
            continue
        question_index, question = found
        items.append(
            CompareItem(
                source_id=str(row_index),
                section=section,
                text=question,
                answer=" | ".join(_answers(cells, values, question_index)),
                comment=_comment(cells, values, question_index),
                note=" | ".join(note for _visible, note in values if note),
                location=section or f"Prüffrage {len(items) + 1}",
                kind="checklist",
                stable_id=_stable_id(row),
                order=len(items),
            )
        )
    return items


def _is_heading(paragraph: Any, text: str) -> bool:
    style = " ".join(paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS)).casefold()
    return (
        style.startswith(("heading", "title", "überschrift", "berschrift"))
        or bool(paragraph.xpath("./w:pPr/w:outlineLvl", namespaces=NS))
        or bool(HEADING_RE.match(text))
    )


def docx_paragraphs(root: Any) -> list[tuple[str, bool]]:
    """Sichtbare Absätze des Dokumentkörpers mit Überschriftenkennzeichen."""
    paragraphs: list[tuple[str, bool]] = []
    for paragraph in root.xpath(".//w:body/w:p", namespaces=NS):
        text = visible_text(paragraph)
        if text:
            paragraphs.append((text, _is_heading(paragraph, text)))
    return paragraphs


def detect_docx_mode(root: Any) -> str:
    """Checkliste, wenn mindestens max(6, Absatzzahl) Tabellenzeilen vorliegen."""
    table_rows = len(root.xpath(".//w:tbl//w:tr", namespaces=NS))
    paragraphs = len(root.xpath(".//w:body/w:p", namespaces=NS))
    return "checklist" if table_rows >= max(6, paragraphs) else "text"
