"""Exports of the REST interface: HTML print view, Markdown and CSV.

HTML comes from the library renderers (``render_register_html``,
``render_assessment_html``) and serves as print view for "Als PDF speichern".
CSV follows the shared contracts ``csv-cell``/``csv-document``
(``contracts/common-cases``): separator ``;``, UTF-8 BOM, CRLF and the prefix
``'`` in front of texts that start with ``= + - @``, tab or CR (protection
against formula injection).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from auditcore_common.filenames import export_filename

from ..export import render_assessment_html, render_register_html

EXPORT_FORMATS = ("html", "markdown", "csv")
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
_MEDIA = {
    "html": "text/html; charset=utf-8",
    "markdown": "text/markdown; charset=utf-8",
    "csv": "text/csv; charset=utf-8",
}
_EXTENSION = {"html": "html", "markdown": "md", "csv": "csv"}


@dataclass(frozen=True)
class ExportFile:
    """File answer of an export."""

    filename: str
    media_type: str
    content: bytes


def csv_cell(value: object) -> str:
    """One CSV cell (contract ``csv-cell``)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, int | float):
        return str(value).replace(".", ",")
    text = str(value)
    if text.startswith(_FORMULA_START):
        text = "'" + text
    if any(char in text for char in ';"\n\r'):
        return '"' + text.replace('"', '""') + '"'
    return text


def csv_document(rows: Sequence[Sequence[object]]) -> str:
    """Whole CSV file with BOM and CRLF (contract ``csv-document``)."""
    return "﻿" + "".join(";".join(csv_cell(c) for c in row) + "\r\n" for row in rows)


def _md(value: object) -> str:
    """Markdown table cell: no line breaks, escaped pipes and markup."""
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "ja" if value else "nein"
    text = " ".join(str(value).split())
    for char in "\\`*_[]<>#|":
        text = text.replace(char, "\\" + char)
    return text


def _file(stem: str, fmt: str, content: str) -> ExportFile:
    return ExportFile(export_filename(stem, _EXTENSION[fmt]), _MEDIA[fmt], content.encode("utf-8"))


Json = Mapping[str, object]


def _obj(value: object) -> Json:
    """Nested JSON object of a report (empty if missing)."""
    return value if isinstance(value, Mapping) else {}


def _objs(value: object) -> list[Json]:
    """List of JSON objects of a report (other entries are skipped)."""
    return [v for v in value if isinstance(v, Mapping)] if isinstance(value, list) else []


def _activities(report: Json) -> list[Json]:
    return [a for group in _objs(report.get("departments")) for a in _objs(group.get("activities"))]


def register_markdown(report: Json) -> str:
    """Register as Markdown: version, cover sheet, one section per activity, open issues."""
    meta, cover = _obj(report.get("meta")), _obj(report.get("cover"))
    lines = [
        "# Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO)",
        "",
        f"Fassung {meta.get('version')} – {meta.get('status')} · Profil "
        f"{meta.get('profile_id')} {meta.get('profile_version')}",
        "",
        f"- Verantwortlicher: {_md(_obj(cover.get('verantwortlicher')).get('name'))}",
        f"- Datenschutzbeauftragte/r: {_md(_obj(cover.get('dsb')).get('name'))}",
    ]
    columns = _objs(report.get("columns"))
    for activity in _activities(report):
        lines += ["", f"## {_md(activity.get('name'))}", "", "| Angabe | Inhalt |", "|---|---|"]
        lines += [
            f"| {_md(c.get('title'))} | {_md(activity.get(str(c.get('key'))))} |" for c in columns
        ]
    issues = _objs(report.get("issues"))
    lines += ["", "## Hinweise der Vollständigkeitsprüfung", ""]
    lines += [
        f"- {'Pflicht' if i.get('blocking') else 'Hinweis'}: {_md(i.get('message'))}"
        for i in issues
    ]
    if not issues:
        lines.append("- Keine offenen Angaben.")
    return "\n".join(lines) + "\n"


def register_csv(report: Json) -> str:
    """Register as CSV: one row per activity, columns as in the profile."""
    columns = [("referat", "Referat")]
    columns += [(str(c.get("key")), str(c.get("title"))) for c in _objs(report.get("columns"))]
    rows: list[list[object]] = [[title for _, title in columns]]
    rows += [[a.get(key) for key, _ in columns] for a in _activities(report)]
    return csv_document(rows)


def register_export(report: Json, fmt: str) -> ExportFile:
    """Register report in one of :data:`EXPORT_FORMATS`."""
    stem = f"verarbeitungsverzeichnis_fassung_{_obj(report.get('meta')).get('version')}"
    if fmt == "html":
        return _file(stem, fmt, render_register_html(report))
    if fmt == "markdown":
        return _file(stem, fmt, register_markdown(report))
    return _file(stem, fmt, register_csv(report))


def _risk_lines(report: Json) -> list[str]:
    lines = [
        "",
        "## Risikoszenarien",
        "",
        "| Szenario | brutto | netto | Stufe |",
        "|---|---|---|---|",
    ]
    for s in _objs(_obj(report.get("risk")).get("scenarios")):
        cells = (_md(s.get("description")), s.get("gross"), s.get("net"), _md(s.get("net_band")))
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    return lines


def assessment_markdown(report: Json) -> str:
    """Assessment as Markdown: subject, threshold analysis, risk, proposal, decision."""
    meta, decision = _obj(report.get("meta")), _obj(report.get("decision"))
    lines = [
        "# Datenschutz-Folgenabschätzung (Art. 35 DSGVO)",
        "",
        f"{_md(meta.get('activity_name'))} – Fassung {meta.get('version')} "
        f"({meta.get('status_text')})",
        "",
        "## Verarbeitungstätigkeit",
        "",
    ]
    fields = _objs(_obj(report.get("subject")).get("fields"))
    lines += [f"- {f.get('title')}: {_md(f.get('value'))}" for f in fields]
    lines += ["", "## Schwellwertanalyse", "", _md(_obj(report.get("screening")).get("reasoning"))]
    lines += _risk_lines(report)
    lines += ["", "## Vorschlag", "", _md(_obj(report.get("proposal")).get("recommendation_text"))]
    title = decision.get("decision_title") or decision.get("decision")
    lines += ["", "## Entscheidung", "", _md(title)]
    return "\n".join(lines) + "\n"


def assessment_export(report: Json, fmt: str) -> ExportFile:
    """Assessment report as HTML print view or Markdown."""
    meta = _obj(report.get("meta"))
    stem = f"dsfa_{meta.get('activity_id')}_fassung_{meta.get('version')}"
    if fmt == "html":
        return _file(stem, fmt, render_assessment_html(report))
    return _file(stem, fmt, assessment_markdown(report))
