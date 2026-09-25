"""Self-contained, escaped HTML view of register report data."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
from typing import Any

from .html_common import STYLE, text

REGISTER_STATUS_TEXT = {
    "entwurf": "Entwurf",
    "freigegeben": "freigegeben",
    "abgeloest": "abgelöst",
}
DSFA_STATUS_TEXT = {
    "entwurf": "Entwurf",
    "dsb_beteiligung": "DSB beteiligt",
    "freigegeben": "freigegeben",
    "abgeloest": "abgelöst",
}
DECISION_TEXT = {
    "nur_schwellwert": "keine Folgenabschätzung erforderlich",
    "freigabe": "Freigabe",
    "freigabe_mit_auflagen": "Freigabe mit Auflagen",
    "konsultation_aufsichtsbehoerde": "Konsultation der Aufsichtsbehörde",
    "verworfen": "verworfen",
}
COVER_TITLES = {
    "verantwortlicher": "Verantwortlicher",
    "dsb": "Datenschutzbeauftragte/r",
    "vertreter": "Vertreter",
}


def _cover_rows(value: object, title: str) -> list[str]:
    """Rows of the cover sheet; nested mappings become indented field lists."""
    if isinstance(value, Mapping):
        inner = "<br>".join(
            f"{text(str(k).replace('_', ' ').capitalize())}: {text(v)}"
            for k, v in value.items()
            if not isinstance(v, Mapping)
        )
        return [f"<tr><th style='width:32%'>{text(title)}</th><td>{inner or '–'}</td></tr>"]
    return [f"<tr><th style='width:32%'>{text(title)}</th><td>{text(value)}</td></tr>"]


def _dsfa_state(state: Mapping[str, Any] | None) -> str:
    if not state:
        return "keine Folgenabschätzung angelegt"
    parts = [
        f"Fassung {text(state.get('version'))}",
        text(DSFA_STATUS_TEXT.get(str(state.get("status")), state.get("status"))),
    ]
    if state.get("entscheidung"):
        decision = str(state["entscheidung"])
        parts.append(f"Entscheidung: {text(DECISION_TEXT.get(decision, decision))}")
    if state.get("freigegeben_am"):
        parts.append(f"freigegeben am {text(str(state['freigegeben_am'])[:10])}")
    if state.get("pruefung_erforderlich"):
        parts.append("<b>Überprüfung erforderlich</b>")
    return ", ".join(parts)


def _head_and_version(meta: Mapping[str, Any]) -> list[str]:
    """Title, profile identity and the version table."""
    status = REGISTER_STATUS_TEXT.get(meta["status"], meta["status"])
    replaces = (
        f"; ersetzt Fassung {text(meta['predecessor_version'])}"
        if meta.get("predecessor_version")
        else ""
    )
    released = (
        f"{text(meta['released_by'])} am {text(str(meta['released_at'])[:10])}"
        if meta.get("released_by")
        else "noch nicht freigegeben"
    )
    return [
        "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>",
        "<title>Verzeichnis von Verarbeitungstätigkeiten</title>",
        STYLE,
        "</head><body>",
        "<h1>Verzeichnis von Verarbeitungstätigkeiten</h1>",
        f"<p class='klein'>Regelprofil {text(meta['profile_id'])} Version "
        f"{text(meta['profile_version'])}; Fassung {text(meta['version'])}, {text(status)}</p>",
        "<h2>Fassung</h2><table>",
        f"<tr><th style='width:32%'>Fassung</th><td>{text(meta['version'])} ({text(status)})"
        + replaces
        + "</td></tr>",
        f"<tr><th>Erstellt</th><td>{text(meta['created_by'])} am "
        f"{text(str(meta['created_at'])[:10])}; bearbeitet von {text(meta['editors'])}</td></tr>",
        "<tr><th>Freigegeben</th><td>" + released + "</td></tr>",
        f"<tr><th>Prüfsumme des Inhalts</th><td class='klein'>{text(meta['content_hash'])}</td>"
        "</tr></table>",
    ]


def _cover(report: Mapping[str, Any]) -> list[str]:
    parts = ["<h2>Deckblatt</h2><table>"]
    cover = report.get("cover") or {}
    for key, value in cover.items():
        parts.extend(_cover_rows(value, COVER_TITLES.get(str(key), str(key).capitalize())))
    if not cover:
        parts.append("<tr><td>Kein Deckblatt erfasst.</td></tr>")
    parts.append("</table>")
    return parts


def _issues(report: Mapping[str, Any]) -> list[str]:
    issues = report.get("issues") or []
    if not issues:
        return []
    parts = ["<h2>Prüfhinweise zur Vollständigkeit</h2><ul>"]
    for issue in issues:
        mark = " (vor der Freigabe zu ergänzen)" if issue.get("blocking") else ""
        parts.append(f"<li>{text(issue.get('message'))}{escape(mark)}</li>")
    parts.append("</ul>")
    return parts


def _dsfa_cell(report: Mapping[str, Any], activity: Mapping[str, Any]) -> str:
    return _dsfa_state(report["dsfa"].get(str(activity.get("id"))))


def _overview(report: Mapping[str, Any]) -> list[str]:
    """Numbered list of all activities with department and, if given, DPIA state."""
    with_dsfa = "dsfa" in report
    parts = ["<h2>Übersicht</h2><table><tr><th>Nr.</th><th>Tätigkeit</th><th>Referat</th>"]
    if with_dsfa:
        parts.append("<th>Folgenabschätzung</th>")
    parts.append("</tr>")
    number = 0
    for dept in report.get("departments") or []:
        for activity in dept["activities"]:
            number += 1
            row = (
                f"<tr><td>{number}</td><td>{text(activity.get('name'))}</td>"
                f"<td>{text(dept['name'])}</td>"
            )
            if with_dsfa:
                row += f"<td>{_dsfa_cell(report, activity)}</td>"
            parts.append(row + "</tr>")
    parts.append("</table>")
    return parts


def _activity_table(
    report: Mapping[str, Any],
    columns: Sequence[Mapping[str, Any]],
    number: int,
    activity: Mapping[str, Any],
) -> list[str]:
    """Every field of one activity with its legal reference."""
    parts = [
        f"<h3>{number}. {text(activity.get('name'))}</h3><table>"
        "<tr><th style='width:28%'>Angabe</th><th>Inhalt</th>"
        "<th style='width:24%'>Fundstelle</th></tr>"
    ]
    for column in columns:
        parts.append(
            f"<tr><td>{text(column['title'])}</td>"
            f"<td>{text(activity.get(column['key']))}</td>"
            f"<td class='klein'>{text(column['reference'], '')}</td></tr>"
        )
    if "dsfa" in report:
        parts.append(
            "<tr><td>Folgenabschätzung</td><td>"
            f"{_dsfa_cell(report, activity)}</td>"
            "<td class='klein'>Art. 35 DSGVO / § 62 HDSIG</td></tr>"
        )
    parts.append("</table>")
    return parts


def _departments(report: Mapping[str, Any], columns: Sequence[Mapping[str, Any]]) -> list[str]:
    parts: list[str] = []
    number = 0
    for dept in report.get("departments") or []:
        parts.append(f"<h2>{text(dept['name'])}</h2>")
        for activity in dept["activities"]:
            number += 1
            parts.extend(_activity_table(report, columns, number, activity))
    return parts


def render_register_html(report: Mapping[str, Any]) -> str:
    """Self-contained, escaped HTML view of :func:`register_report` data.

    A read-only view of the record of processing activities that any
    consuming application can show or print: version and status, cover
    sheet, completeness notes, and every activity by department with all
    fields and their legal references; with ``overview`` data also the state
    of the DPIA per activity.
    """
    meta = report["meta"]
    columns = report["columns"]
    parts = [
        *_head_and_version(meta),
        *_cover(report),
        *_issues(report),
        *_overview(report),
        *_departments(report, columns),
        "<p class='klein'>Ansicht einer Fassung des Verzeichnisses. Freigegebene Fassungen "
        "sind unveränderlich; Änderungen ergeben eine neue Fassung.</p></body></html>",
    ]
    return "".join(parts)
