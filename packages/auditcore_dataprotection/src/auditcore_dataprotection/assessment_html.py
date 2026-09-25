"""Self-contained, escaped HTML report of assessment report data."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

from .assessment_html_outcome import (
    html_decision,
    html_issues_and_changes,
    html_open_at_release,
    html_sources,
)
from .html_common import STYLE, text

ANSWER_TEXT = {"ja": "Ja", "nein": "Nein", "unbekannt": "unbekannt", None: "nicht beantwortet"}


def _html_head_and_subject(report: Mapping[str, Any]) -> list[str]:
    """Title, profile identity and section 1 (subject)."""
    meta = report["meta"]
    profile = meta["profile"]
    norms = meta.get("norms") or {}
    parts = [
        "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>",
        f"<title>Datenschutz-Folgenabschätzung – {text(meta['activity_name'])}</title>",
        STYLE,
        "</head><body>",
        "<h1>Datenschutz-Folgenabschätzung</h1>",
        f"<p class='klein'>{text(norms.get('dsfa'))} &middot; {text(profile['regime_title'])}"
        + (f" &middot; {text(meta['tenant_label'])}" if meta.get("tenant_label") else "")
        + "</p>",
        f"<p class='klein'>Regelprofil {text(profile['id'])} Version {text(profile['version'])}"
        f" (Fingerprint {text(profile['fingerprint'][:16])}…); "
        f"{text(profile['legal_status'])}</p>",
        "<h2>1. Gegenstand der Verarbeitung</h2><table>",
    ]
    for field in report["subject"]["fields"]:
        parts.append(
            f"<tr><th style='width:32%'>{text(field['title'])}</th>"
            f"<td>{text(field['value'])}</td></tr>"
        )
    parts.append(
        f"<tr><th>Fassung</th><td>Nummer {text(meta['version'])}, Stand "
        f"{text(meta['status_text'])}; beruht auf Fassung {text(meta['register_version'])} "
        "des Verzeichnisses von Verarbeitungstätigkeiten</td></tr>"
    )
    edpb = report.get("edpb")
    if edpb:
        parts.append(f"<tr><th>Anlass der Abschätzung</th><td>{text(edpb['occasion'])}</td></tr>")
        for item in edpb["dossier"]:
            parts.append(
                f"<tr><th>{text(item['title'])}</th><td>{text(item['value'])}"
                f"<br><span class='klein'>{text(item['reference'])}</span></td></tr>"
            )
    parts.append("</table>")
    return parts


def _html_screening(report: Mapping[str, Any]) -> list[str]:
    """Section 2: every screening question and the result."""
    profile = report["meta"]["profile"]
    screening = report["screening"]
    parts: list[str] = []
    parts.append("<h2>2. Schwellwertanalyse</h2>")
    if profile.get("regime_notice"):
        parts.append(f"<div class='hinweis'>{text(profile['regime_notice'])}</div>")
    current_block = None
    for q in screening["questions"]:
        if q["block"] != current_block:
            if current_block is not None:
                parts.append("</table>")
            current_block = q["block"]
            parts.append(
                f"<h3>{text(q['block_title'])}</h3><table><tr><th style='width:52%'>Frage</th>"
                "<th style='width:10%'>Antwort</th><th style='width:20%'>Fundstelle</th>"
                "<th>Begründung</th></tr>"
            )
        parts.append(
            f"<tr><td>{text(q['text'])}</td><td>{text(ANSWER_TEXT.get(q['answer']))}</td>"
            f"<td class='klein'>{text(q['reference'])}</td>"
            f"<td>{text(q['justification'], '')}</td></tr>"
        )
    if current_block is not None:
        parts.append("</table>")
    parts.append(f"<div class='hinweis'><b>Ergebnis:</b> {text(screening['reasoning'])}</div>")
    if not screening["complete"]:
        parts.append(
            "<div class='hinweis blockierend'>Unvollständig: "
            f"{len(screening['unanswered'])} unbeantwortet, {len(screening['unknown'])} "
            "als unbekannt gekennzeichnet. Fehlende Angaben gelten nicht als Nein.</div>"
        )
    if screening.get("fria_required"):
        parts.append(
            "<p><b>Hinweis:</b> Hochrisiko-KI-System nach Anhang III der Verordnung (EU) "
            "2024/1689; die Grundrechte-Folgenabschätzung nach Artikel 27 ist zusätzlich "
            "zu erstellen.</p>"
        )
    return parts


def _html_necessity(report: Mapping[str, Any]) -> list[str]:
    """Section 3: necessity, proportionality, data subjects' view."""
    parts: list[str] = []
    nec = report["necessity"]
    parts += [
        "<h2>3. Notwendigkeit und Verhältnismäßigkeit</h2><table>",
        f"<tr><th style='width:28%'>Notwendigkeit</th><td>{text(nec['necessity'])}</td></tr>",
        f"<tr><th>Verhältnismäßigkeit</th><td>{text(nec['proportionality'])}</td></tr>",
        "<tr><th>Standpunkt der betroffenen Personen</th><td>"
        f"{text(nec['data_subject_view'], 'nicht eingeholt')}</td></tr></table>",
        "<h2>4. Risiken und vorgesehene Maßnahmen</h2>",
    ]
    return parts


def _html_risk(report: Mapping[str, Any]) -> list[str]:
    """Section 4: scenarios with gross and net risk."""
    norms = report["meta"].get("norms") or {}
    parts: list[str] = []
    risk = report.get("risk") or {}
    scenarios = risk.get("scenarios") or []
    if not scenarios:
        parts.append(
            "<div class='hinweis'>Es ist noch kein Risikoszenario erfasst "
            f"({text(norms.get('risiko'))}, {text(norms.get('massnahmen'))}).</div>"
        )
    else:
        parts.append(
            "<table><tr><th>Schutzziel</th><th>Szenario</th><th>Vor Maßnahmen</th>"
            "<th>Maßnahmen</th><th>Nach Maßnahmen</th></tr>"
        )
        for s in scenarios:
            explicit = " (ausdrücklich gesetzt)" if s.get("explicit_residual") else ""
            parts.append(
                f"<tr><td>{text(s['dimension_title'])}{' (SDM)' if s.get('sdm') else ''}</td>"
                f"<td>{text(s['description'])}{_scenario_details(s)}</td>"
                f"<td>Schwere {s['gross_severity']}, Wahrscheinlichkeit {s['gross_likelihood']}"
                f" = {s['gross']} ({text(s['gross_band'])})</td>"
                f"<td class='klein'>{text(s['measure_titles'])}</td>"
                f"<td>Schwere {s['net_severity']}, Wahrscheinlichkeit {s['net_likelihood']}"
                f" = {s['net']} ({text(s['net_band'])}){escape(explicit)}"
                + (
                    f"<br><span class='klein'>{text(s['residual_justification'])}</span>"
                    if s.get("residual_justification")
                    else ""
                )
                + "</td></tr>"
            )
        parts.append(
            f"</table><p class='klein'>Höchstwert vor Maßnahmen {risk.get('gross_maximum')}, "
            f"nach Maßnahmen {risk.get('net_maximum')} ({text(risk.get('net_band'))}).</p>"
        )
    edpb = report.get("edpb")
    if edpb and edpb.get("method"):
        parts.append(f"<p class='klein'>Methode: {text(edpb['method'])}</p>")
    parts.extend(_html_measures(report))
    return parts


def _scenario_details(s: Mapping[str, Any]) -> str:
    """Risk source, modulating factors, acceptance and floor of a schema 2 scenario."""
    if "net_floor" not in s:
        return ""
    lines = []
    if s.get("risk_source"):
        lines.append(f"Risikoquelle: {text(s['risk_source'])}")
    if s.get("modulating_factors"):
        lines.append(f"Umstände: {text(s['modulating_factors'])}")
    if s.get("acceptance_inherent"):
        lines.append(f"Risiko vor Maßnahmen {text(s['acceptance_inherent_title'])}")
    if s.get("acceptance_residual"):
        lines.append(f"Restrisiko {text(s['acceptance_residual_title'])}")
    if s.get("acceptance_note"):
        lines.append(text(s["acceptance_note"]))
    if s.get("net_floor"):
        lines.append(
            f"Mindeststufe {text(s['net_band'])} wegen der Schwere vor Maßnahmen "
            f"({text(s['net_floor'])})"
        )
    return "".join(f"<br><span class='klein'>{line}</span>" for line in lines)


def _html_measures(report: Mapping[str, Any]) -> list[str]:
    """Measures by area with implementation status and the action plan (schema 2)."""
    edpb = report.get("edpb")
    if not edpb:
        return []
    parts: list[str] = []
    if edpb["measures"]:
        parts.append(
            "<h3>Maßnahmen nach Bereichen und Umsetzungsstand</h3><table><tr><th>Bereich</th>"
            "<th>Maßnahme</th><th>Stand</th><th>Hinweis</th></tr>"
        )
        for m in sorted(edpb["measures"], key=lambda m: m["category_title"]):
            parts.append(
                f"<tr><td>{text(m['category_title'])}</td><td>{text(m['title'])}"
                f"<br><span class='klein'>{text(m['legal_basis'])}</span></td>"
                f"<td>{text(m['status_title'])}</td><td>{text(m['note'], '')}</td></tr>"
            )
        parts.append("</table>")
    if edpb["action_plan"]:
        parts.append(
            "<h3>Maßnahmenplan</h3><table><tr><th>Vorhaben</th><th>Verantwortlich</th>"
            "<th>Termin</th></tr>"
        )
        for item in edpb["action_plan"]:
            parts.append(
                f"<tr><td>{text(item.get('activity'))}</td>"
                f"<td>{text(item.get('responsible'))}</td><td>{text(item.get('due'))}</td></tr>"
            )
        parts.append("</table>")
    return parts


def render_assessment_html(report: Mapping[str, Any]) -> str:
    """Self-contained, escaped HTML report of :func:`assessment_report` data."""
    parts = [
        *_html_head_and_subject(report),
        *_html_screening(report),
        *_html_necessity(report),
        *_html_risk(report),
        *html_decision(report),
        *html_issues_and_changes(report),
        *html_open_at_release(report),
        *html_sources(report),
    ]
    parts.append(
        "<p class='klein'>Der Vorschlag ist eine Berechnung auf Grundlage des genannten "
        "Regelprofils und ersetzt keine fachliche oder datenschutzrechtliche Entscheidung. "
        "Freigegebene Fassungen sind unveränderlich.</p></body></html>"
    )
    return "".join(parts)
