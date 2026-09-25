"""Outcome sections of the HTML assessment report: decision, notes, sources."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

from .html_common import text
from .rules import DECISION_REJECTED


def _decision_rows(proposal: Mapping[str, Any], decision: Mapping[str, Any]) -> list[str]:
    """Proposal, reasoning, decision, conditions and deviation."""
    parts = [
        "<h2>5. Vorschlag, Entscheidung und Beteiligung</h2><table>",
        f"<tr><th style='width:32%'>Vorschlag des Systems</th>"
        f"<td>{text(proposal['recommendation_text'])}</td></tr>",
        f"<tr><th>Begründung</th><td>{text(proposal['reasoning'])}</td></tr>",
        f"<tr><th>Berechnung</th><td class='klein'>{text(proposal['calculation'])}</td></tr>",
        "<tr><th>Entscheidung</th><td>"
        f"{text(decision.get('decision_title') or decision['decision'], 'noch offen')}</td></tr>",
    ]
    if decision.get("conditions"):
        parts.append(
            "<tr><th>Bedingungen vor Beginn der Verarbeitung</th><td>"
            + "<br>".join(f"{i}. {text(c)}" for i, c in enumerate(decision["conditions"], 1))
            + "</td></tr>"
        )
    if decision.get("deviation"):
        parts.append(
            f"<tr><th>Abweichung vom Vorschlag</th>"
            f"<td>{text(decision['deviation_justification'])}</td></tr>"
        )
    return parts


def _dpo_rows(report: Mapping[str, Any], dpo: Mapping[str, Any]) -> list[str]:
    """Request (documentation mode), vote, statement, conclusion and leadership."""
    parts: list[str] = []
    if report.get("release_mode"):
        requested = (
            f"am {text(dpo.get('requested_on'))} bei {text(dpo.get('requested_from'))}"
            f" (erfasst von {text(dpo.get('requested_by'))})"
            if dpo.get("requested_on")
            else "nicht dokumentiert"
        )
        parts.append(f"<tr><th>Stellungnahme eingeholt</th><td>{requested}</td></tr>")
    parts += [
        f"<tr><th>Datenschutzbeauftragte/r</th><td>{text(dpo['vote_text'])}"
        f" ({text(dpo['by'])}, {text(dpo['at'])})</td></tr>",
        f"<tr><th>Stellungnahme</th><td>{text(dpo['statement'])}</td></tr>",
    ]
    if dpo.get("conclusion"):
        parts.append(
            f"<tr><th>Umgang mit der Stellungnahme</th><td>{text(dpo['conclusion'])}</td></tr>"
        )
    if dpo.get("leadership_presented_to"):
        parts.append(
            f"<tr><th>Der Behördenleitung vorgelegt</th>"
            f"<td>{text(dpo['leadership_presented_to'])} am "
            f"{text(dpo['leadership_presented_at'])}</td></tr>"
        )
    return parts


def _consultation_rows(
    report: Mapping[str, Any], proposal: Mapping[str, Any], decision: Mapping[str, Any]
) -> list[str]:
    """Recorded consultation, or the missing one, and the consultation notice."""
    parts: list[str] = []
    consultation = report.get("consultation")
    if consultation:
        ground = (
            f"<br><span class='klein'>Grund: {text(consultation['ground_title'])} "
            f"({text(consultation['ground_reference'])})</span>"
            if consultation.get("ground_title")
            else ""
        )
        parts.append(
            f"<tr><th>Konsultation der Aufsichtsbehörde</th><td>{text(consultation['authority'])}"
            f", {text(consultation['consulted_on'])}: {text(consultation['result'])}"
            + ground
            + "</td></tr>"
        )
    elif proposal.get("consultation_required") and decision["decision"] != DECISION_REJECTED:
        parts.append(
            "<tr class='blockierend'><th>Konsultation der Aufsichtsbehörde</th>"
            f"<td>erforderlich ({text(proposal.get('consultation_reference'))}), "
            "noch nicht dokumentiert</td></tr>"
        )
    notice = proposal.get("consultation_notice") or {}
    if not consultation and notice and notice.get("status") != "erforderlich" and notice["text"]:
        label = "Hinweis zur Konsultation" + ("" if notice.get("final") else " (vorläufig)")
        parts.append(f"<tr><th>{escape(label)}</th><td>{text(notice['text'])}</td></tr>")
    return parts


def _lifecycle_rows(life: Mapping[str, Any]) -> list[str]:
    released = (
        f"{text(life['released_by'])} am {text(life['released_at'])}"
        if life.get("released_by")
        else "noch nicht freigegeben"
    )
    return [
        f"<tr><th>Erstellt</th><td>{text(life['created_by'])} am {text(life['created_at'])}"
        f"; bearbeitet von {text(life['editors'])}</td></tr>",
        "<tr><th>Freigegeben</th><td>" + released + "</td></tr></table>",
    ]


def html_decision(report: Mapping[str, Any]) -> list[str]:
    """Section 5: proposal, decision, DPO, consultation, lifecycle."""
    proposal = report["proposal"]
    decision = report["decision"]
    dpo = report["dpo"]
    life = report["lifecycle"]
    return [
        *_decision_rows(proposal, decision),
        *_dpo_rows(report, dpo),
        *_consultation_rows(report, proposal, decision),
        *_lifecycle_rows(life),
    ]


def html_issues_and_changes(report: Mapping[str, Any]) -> list[str]:
    """Review notes and changes compared with the predecessor."""
    proposal = report["proposal"]
    parts: list[str] = []
    issues = proposal.get("issues") or []
    hints = (report.get("edpb") or {}).get("hints") or []
    if issues or hints:
        parts.append("<h2>Prüfhinweise</h2><ul>")
        for issue in issues:
            mark = " (blockiert die Freigabe)" if issue.get("blocking") else ""
            parts.append(f"<li>{text(issue.get('message'))}{escape(mark)}</li>")
        for hint in hints:
            parts.append(f"<li>{text(hint)}</li>")
        parts.append("</ul>")
    changes = report.get("changes_to_predecessor") or []
    if changes:
        parts.append(
            "<h2>Änderungen gegenüber der Vorfassung</h2><table>"
            "<tr><th>Angabe</th><th>Vorher</th><th>Nachher</th></tr>"
        )
        for change in changes:
            parts.append(
                f"<tr><td>{text(change.get('bezeichnung'))}</td>"
                f"<td>{text(change.get('vorher'))}</td>"
                f"<td>{text(change.get('nachher'))}</td></tr>"
            )
        parts.append("</table>")
    return parts


def html_open_at_release(report: Mapping[str, Any]) -> list[str]:
    """Checks that were open when the version was released (documentation mode)."""
    points = report.get("release_open_points") or []
    if not report.get("release_mode") or not report["lifecycle"].get("released_by"):
        return []
    if not points:
        return ["<h2>Bei der Freigabe offen</h2><p>Keine offenen Punkte.</p>"]
    parts = [
        "<h2>Bei der Freigabe offen</h2><p class='klein'>Die Freigabe war trotz dieser Punkte "
        "möglich; sie sind hier dokumentiert.</p><ul>"
    ]
    parts.extend(f"<li>{text(p)}</li>" for p in points)
    parts.append("</ul>")
    return parts


def html_sources(report: Mapping[str, Any]) -> list[str]:
    """Guidelines and templates the profile relies on (EDPB template 0.5)."""
    edpb = report.get("edpb")
    if not edpb:
        return []
    parts = [
        "<h2>Grundlagen der Abschätzung</h2><table><tr><th>Quelle</th><th>Stand</th>"
        "<th>Verwendet für</th></tr>"
    ]
    for source in edpb["sources"]:
        parts.append(
            f"<tr><td>{text(source['issuer'])}: {text(source['title'])}"
            f"<br><span class='klein'>{text(source['reference'])}</span></td>"
            f"<td>{text(source['date'])}; {text(source['status'])}</td>"
            f"<td>{text(source['used_for'])}</td></tr>"
        )
    parts.append("</table>")
    return parts
