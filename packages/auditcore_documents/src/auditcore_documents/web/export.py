"""Ausgaben eines gespeicherten Vergleichs: JSON, Markdown, DOCX und PDF.

JSON und Markdown brauchen nur die Standardbibliothek. DOCX und PDF nutzen
die vorhandenen Renderer (Extras ``docx-render`` und ``pdf-render``); fehlen
sie, meldet der Renderer ``DependencyError``. Die HTML- und Druckansicht
erzeugt die Oberfläche selbst aus demselben Ergebnisobjekt.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace

from auditcore_documents.compare import DEFAULT_SECTIONS
from auditcore_documents.model import CompareRow, ComparisonResult
from auditcore_documents.synopsis import STATUS_LABELS

EXPORT_FORMATS = ("json", "markdown", "docx", "pdf")
_MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]<>#|])")
_UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9ÄÖÜäöüß._-]+")


@dataclass(frozen=True)
class ExportSettings:
    """Kopf-/Fußangaben der Renderer; neutral statt ECOHESION-Vorgaben."""

    pdf_header: str = "Synopse"
    pdf_footer: str = ""
    pdf_author: str = "auditcore_documents"
    docx_profile: str = "memo"
    docx_user: str = ""


@dataclass(frozen=True)
class ExportFile:
    content: bytes
    media_type: str
    filename: str


def output_rows(result: ComparisonResult) -> list[CompareRow]:
    """Ausgewählte Zeilen der gewählten Abschnitte (Regel wie im DOCX-Renderer)."""
    sections = set(result.metadata.get("output_sections") or DEFAULT_SECTIONS)
    return [row for row in result.rows if row.selected and row.status in sections]


def _escape(text: str) -> str:
    return _MARKDOWN_SPECIAL.sub(r"\\\1", text)


def _quote(text: str, empty: str) -> str:
    lines = (text or empty).splitlines() or [empty]
    return "\n".join(f"> {_escape(line)}" if line else ">" for line in lines)


def _labels(result: ComparisonResult) -> tuple[str, str, str]:
    meta = result.metadata
    return (
        str(meta.get("old_label") or "Bisherige Fassung"),
        str(meta.get("new_label") or "Neue Fassung"),
        str(meta.get("reason_label") or "Grund"),
    )


def _row_markdown(row: CompareRow, labels: tuple[str, str, str]) -> list[str]:
    old_label, new_label, reason_label = labels
    status = STATUS_LABELS.get(row.status, row.status)
    lines = [f"### {_escape(row.location or '—')} ({status})", ""]
    lines += [f"**{old_label}:**", "", _quote(row.old_text, "nicht vorhanden"), ""]
    lines += [f"**{new_label}:**", "", _quote(row.new_text, "nicht mehr enthalten"), ""]
    for field, label in (("answer", "Antwort"), ("comment", "Bemerkung"), ("note", "Hinweis")):
        old, new = getattr(row, f"old_{field}"), getattr(row, f"new_{field}")
        if old or new:
            lines += [
                f"- {label} bisher: {_escape(old or '—')}",
                f"- {label} neu: {_escape(new or '—')}",
            ]
    if row.reason:
        lines += ["", f"**{reason_label}:** {_escape(row.reason)}"]
    return [*lines, ""]


def _header_markdown(title: str, result: ComparisonResult) -> list[str]:
    counts = (
        f"{result.changed_count} geändert · {result.removed_count} entfallen · "
        f"{result.added_count} neu · {result.moved_count} verschoben"
    )
    lines = [f"# {_escape(title)}", ""]
    lines += [f"- Bisherige Datei: {_escape(result.old_filename)} (SHA-256 {result.old_sha256})"]
    lines += [f"- Neue Datei: {_escape(result.new_filename)} (SHA-256 {result.new_sha256})"]
    lines += [
        f"- Erstellt: {result.created_at} · Vergleichsmodul {result.version}",
        f"- {counts}",
        "",
    ]
    for key in ("work_aid_notice", "pdf_notice"):
        if result.metadata.get(key):
            lines += [f"> {_escape(str(result.metadata[key]))}", ""]
    return lines


def _open_commands_markdown(result: ComparisonResult) -> list[str]:
    commands = [str(c) for c in result.metadata.get("open_commands") or []]
    if not commands:
        return []
    return ["## Offene Änderungsbefehle", "", *(f"- {_escape(c)}" for c in commands), ""]


def render_markdown(result: ComparisonResult, *, title: str) -> str:
    """Synopse als Markdown (nur ausgewählte Zeilen der Ausgabeabschnitte)."""
    labels = _labels(result)
    lines = _header_markdown(title, result)
    rows = output_rows(result)
    lines += ["## Festgestellte Änderungen", ""]
    if not rows:
        lines += ["Keine Unterschiede in den gewählten Abschnitten.", ""]
    for row in rows:
        lines += _row_markdown(row, labels)
    lines += _open_commands_markdown(result)
    return "\n".join(lines).rstrip() + "\n"


def export_filename(title: str, extension: str) -> str:
    stem = _UNSAFE_FILENAME.sub("_", title).strip("._") or "Synopse"
    return f"{stem[:80]}.{extension}"


def _render_docx(result: ComparisonResult, title: str, settings: ExportSettings) -> bytes:
    from auditcore_documents.render_docx import render_docx_bytes

    return render_docx_bytes(
        result, title=title, user=settings.docx_user, profile=settings.docx_profile
    )


def _render_pdf(result: ComparisonResult, title: str, settings: ExportSettings) -> bytes:
    from auditcore_documents.render_pdf import render_synopsis_pdf, synopsis_report

    # Der PDF-Renderer kennt keine Auswahl; er erhält nur die Ausgabezeilen.
    selected = replace(result, rows=output_rows(result))
    return render_synopsis_pdf(
        title,
        synopsis_report(selected),
        header_text=settings.pdf_header,
        footer_text=settings.pdf_footer,
        author=settings.pdf_author,
    )


def export_comparison(
    result: ComparisonResult, *, title: str, fmt: str, settings: ExportSettings
) -> ExportFile:
    """Eine Ausgabe erzeugen; ``fmt`` muss in :data:`EXPORT_FORMATS` stehen."""
    if fmt == "json":
        body = json.dumps(result.to_dict(), ensure_ascii=False, indent=2).encode("utf-8")
        return ExportFile(body, "application/json", export_filename(title, "json"))
    if fmt == "markdown":
        body = render_markdown(result, title=title).encode("utf-8")
        return ExportFile(body, "text/markdown; charset=utf-8", export_filename(title, "md"))
    if fmt == "docx":
        return ExportFile(
            _render_docx(result, title, settings),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            export_filename(title, "docx"),
        )
    if fmt == "pdf":
        body = _render_pdf(result, title, settings)
        return ExportFile(body, "application/pdf", export_filename(title, "pdf"))
    raise ValueError(f"Unbekanntes Ausgabeformat: {fmt}")
