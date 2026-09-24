"""Report data and dependency-free renderers (JSON, HTML).

Report builders return plain JSON-compatible dictionaries so any consumer
renderer can use them. Excel and PDF output are optional extras in
:mod:`auditcore_dataprotection.excel` and :mod:`auditcore_dataprotection.pdf`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from html import escape
from typing import Any

from .edpb import edpb_hints
from .model import Assessment, RegisterVersion
from .register import check_register, group_by_department
from .rules import DECISION_REJECTED, RuleProfile

REPORT_SCHEMA = "auditcore_dataprotection.report/1"
SNAPSHOT_FIELDS = (
    ("name", "Verarbeitungstätigkeit"),
    ("zweck", "Zweck"),
    ("ermaechtigungsgrundlage", "Rechtsgrundlage"),
    ("kategorien_betroffene", "Kategorien betroffener Personen"),
    ("kategorien_daten", "Kategorien der Daten"),
    ("kategorien_empfaenger", "Empfänger"),
    ("drittlandtransfer", "Übermittlung in ein Drittland"),
    ("besondere_kategorien", "Besondere Kategorien nach Artikel 9"),
    ("daten_art10", "Daten nach Artikel 10"),
    ("anzahl_betroffene", "Zahl der betroffenen Personen"),
)
ANSWER_TEXT = {"ja": "Ja", "nein": "Nein", "unbekannt": "unbekannt", None: "nicht beantwortet"}


def _plain(value: Any) -> Any:
    """Convert records, enums, mappings and datetimes to JSON-compatible values."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_plain(v) for v in value]
        return sorted(items) if isinstance(value, (set, frozenset)) else items
    return value


def assessment_report(
    assessment: Assessment, profile: RuleProfile, *, tenant_label: str = ""
) -> dict[str, Any]:
    """Complete report data of one assessment version (Art. 35 Abs. 7 DSGVO)."""
    proposal = dict(assessment.proposal)
    screening = proposal.get("screening") or {}
    snapshot = assessment.activity_snapshot
    questions = []
    for block, title in profile.blocks:
        for q in profile.questions:
            if q.block != block:
                continue
            answer = assessment.answers.get(q.key)
            questions.append(
                {
                    "block": block,
                    "block_title": title,
                    "key": q.key,
                    "text": q.text,
                    "effect": q.effect,
                    "reference": q.reference,
                    "answer": answer.value.value if answer else None,
                    "justification": answer.justification if answer else "",
                }
            )
    consultation = assessment.consultation
    report = {
        "schema": REPORT_SCHEMA,
        "kind": "assessment",
        "meta": {
            "tenant_id": assessment.tenant_id,
            "tenant_label": tenant_label,
            "assessment_id": assessment.assessment_id,
            "register_id": assessment.register_id,
            "register_version": assessment.register_version,
            "activity_id": assessment.activity_id,
            "activity_name": assessment.activity_name,
            "version": assessment.version,
            "status": assessment.status.value,
            "status_text": profile.status_texts.get(
                assessment.status.value, assessment.status.value
            ),
            "locked": assessment.locked,
            "predecessor_id": assessment.predecessor_id,
            "profile": {
                "id": profile.id,
                "version": profile.version,
                "fingerprint": profile.fingerprint,
                "status": profile.status,
                "legal_status": profile.legal_status,
                "regime": profile.regime,
                "regime_title": profile.regime_title,
                "regime_notice": profile.regime_notice,
            },
            "recorded_profile": {
                "id": assessment.profile_id,
                "version": assessment.profile_version,
                "fingerprint": assessment.profile_fingerprint,
            },
            "norms": dict(profile.norms),
        },
        "subject": {
            "fields": [
                {"key": key, "title": title, "value": _plain(snapshot.get(key))}
                for key, title in SNAPSHOT_FIELDS
            ],
            "snapshot": _plain(snapshot),
        },
        "screening": {
            "questions": questions,
            "outcome": screening.get("outcome"),
            "points": screening.get("points"),
            "points_threshold": screening.get("points_threshold"),
            "hard_triggers": list(screening.get("hard_triggers") or []),
            "point_criteria": list(screening.get("point_criteria") or []),
            "fria_required": screening.get("fria_required"),
            "unanswered": list(screening.get("unanswered") or []),
            "unknown": list(screening.get("unknown") or []),
            "complete": bool(screening.get("complete")),
            "reasoning": screening.get("reasoning"),
        },
        "necessity": {
            "necessity": assessment.necessity,
            "proportionality": assessment.proportionality,
            "data_subject_view": assessment.data_subject_view,
        },
        "risk": _plain(proposal.get("risk")),
        "scenarios": [s.to_dict() for s in assessment.scenarios],
        "proposal": {
            "recommendation": proposal.get("recommendation"),
            "recommendation_text": proposal.get("recommendation_text"),
            "reasoning": proposal.get("reasoning"),
            "consultation_required": proposal.get("consultation_required"),
            "consultation_reference": proposal.get("consultation_reference"),
            "calculation": proposal.get("calculation"),
            "profile": _plain(proposal.get("profile")),
            "issues": _plain(proposal.get("issues") or []),
            "trace": _plain(proposal.get("trace") or []),
            **(
                {"consultation_notice": _plain(proposal["consultation_notice"])}
                if proposal.get("consultation_notice")
                else {}
            ),
        },
        "decision": {
            "decision": assessment.decision,
            "deviation": assessment.deviation,
            "deviation_justification": assessment.deviation_justification,
            "decided_by": assessment.decided_by,
            "decided_at": _plain(assessment.decided_at),
        },
        "dpo": {
            "vote": assessment.dpo_vote,
            "vote_text": profile.vote_texts.get(assessment.dpo_vote or "", "noch offen"),
            "statement": assessment.dpo_statement,
            "by": assessment.dpo_by,
            "at": _plain(assessment.dpo_at),
            "conclusion": assessment.dpo_conclusion,
            "conclusion_by": assessment.dpo_conclusion_by,
            "leadership_presented_to": assessment.leadership_presented_to,
            "leadership_presented_at": _plain(assessment.leadership_presented_at),
        },
        "consultation": _plain(consultation) if consultation else None,
        "lifecycle": {
            "created_by": assessment.created_by,
            "created_at": _plain(assessment.created_at),
            "updated_at": _plain(assessment.updated_at),
            "editors": list(assessment.editors),
            "released_by": assessment.released_by,
            "released_at": _plain(assessment.released_at),
            "revision": assessment.revision,
        },
        "changes_to_predecessor": _plain(list(assessment.changes_to_predecessor)),
    }
    if not profile.edpb:
        # Schema 1 reports stay exactly as before.
        if report["consultation"] is not None:
            report["consultation"].pop("ground", None)
        return report
    report["meta"]["profile"]["schema"] = profile.schema
    report["decision"]["decision_title"] = profile.decision_titles.get(
        assessment.decision or "", None
    )
    report["decision"]["conditions"] = list(assessment.conditions)
    if profile.documentation_mode:
        report["dpo"]["requested_from"] = assessment.dpo_requested_from
        report["dpo"]["requested_on"] = assessment.dpo_requested_on
        report["dpo"]["requested_by"] = assessment.dpo_requested_by
        report["release_mode"] = profile.release_mode
        report["release_open_points"] = list(assessment.release_open_points)
    report["edpb"] = _edpb_section(assessment, profile)
    if consultation and consultation.ground:
        title, reference = profile.consultation_grounds[consultation.ground]
        report["consultation"]["ground_title"] = title
        report["consultation"]["ground_reference"] = reference
    return report


def _edpb_section(assessment: Assessment, profile: RuleProfile) -> dict[str, Any]:
    """Documentation along the EDPB template 2026 v1.0 (schema 2 profiles only)."""
    used = {k for s in assessment.scenarios for k in s.measures}
    measures = []
    for measure in profile.measures:
        state = assessment.measure_status.get(measure.key)
        if state is None and measure.key not in used:
            continue
        category_title, category_reference = profile.measure_categories[measure.category]
        measures.append(
            {
                "key": measure.key,
                "title": measure.title,
                "legal_basis": measure.legal_basis,
                "category": measure.category,
                "category_title": category_title,
                "category_reference": category_reference,
                "status": state.get("status") if state else None,
                "status_title": profile.implementation_states.get(state["status"], "")
                if state
                else "nicht angegeben",
                "note": state.get("note", "") if state else "",
                "used_in_scenarios": measure.key in used,
            }
        )
    if not assessment.predecessor_id:
        occasion = "Erstmalige Abschätzung der Verarbeitungstätigkeit"
    elif assessment.changes_to_predecessor:
        occasion = (
            "Die Verarbeitung hat sich gegenüber der Vorfassung geändert "
            f"({profile.norm('ueberpruefung')})"
        )
    else:
        occasion = (
            "Neubewertung ohne geänderte Angaben im Verzeichnis, etwa nach einer neuen "
            f"Profilfassung oder turnusmäßig ({profile.norm('ueberpruefung')})"
        )
    return {
        "template": "EDSA, Template for DPIA 2026, Version 1.0 (Konsultationsfassung)",
        "method": profile.risk_method,
        "occasion": occasion,
        "dossier": [
            {
                "key": f.key,
                "title": f.title,
                "reference": f.reference,
                "required": f.required,
                "value": dict(f.choices).get(assessment.dossier.get(f.key, ""), None)
                if f.kind == "choice"
                else assessment.dossier.get(f.key),
            }
            for f in profile.dossier_fields
        ],
        "measures": measures,
        "action_plan": [dict(item) for item in assessment.action_plan],
        "hints": list(edpb_hints(assessment, profile)),
        "sources": [_plain(source) for source in profile.sources],
    }


def register_report(version: RegisterVersion, profile: RuleProfile) -> dict[str, Any]:
    """Report data of one register version with content check results."""
    content = version.content
    activities = [dict(a) for a in version.activities]
    groups = group_by_department(activities, list(content.get("referate") or []))
    return {
        "schema": REPORT_SCHEMA,
        "kind": "register",
        "meta": {
            "tenant_id": version.tenant_id,
            "register_id": version.register_id,
            "version": version.version,
            "status": version.status.value,
            "locked": version.locked,
            "content_hash": version.content_hash,
            "created_by": version.created_by,
            "created_at": _plain(version.created_at),
            "editors": list(version.editors),
            "released_by": version.released_by,
            "released_at": _plain(version.released_at),
            "predecessor_version": version.predecessor_version,
            "profile_id": profile.id,
            "profile_version": profile.version,
            "profile_fingerprint": profile.fingerprint,
        },
        "cover": _plain(content.get("deckblatt") or {}),
        "columns": [
            {"key": key, "title": title, "reference": profile.register_references.get(key, "")}
            for key, title in profile.register_columns
        ],
        "departments": [{"name": name, "activities": _plain(rows)} for name, rows in groups],
        "issues": [i.to_dict() for i in check_register(content, profile)],
    }


def overview_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """JSON-compatible copy of ``AssessmentService.overview`` rows."""
    return [_plain(dict(row)) for row in rows]


def to_json_bytes(report: Mapping[str, Any]) -> bytes:
    """Deterministic UTF-8 JSON (sorted keys, ISO dates)."""
    return (
        json.dumps(_plain(report), sort_keys=True, ensure_ascii=False, indent=1).encode("utf-8")
        + b"\n"
    )


def _text(value: Any, empty: str = "–") -> str:
    if value is None or value == "":
        return escape(empty)
    if value is True:
        return "Ja"
    if value is False:
        return "Nein"
    if isinstance(value, (list, tuple)):
        return escape(", ".join(str(v) for v in value)) or escape(empty)
    return escape(str(value))


_STYLE = (
    "<style>@page { size: A4; margin: 2cm 2cm 2cm 2.5cm; }"
    "body { font-family: Arial, sans-serif; font-size: 10pt; color: #000; }"
    "h1 { font-size: 15pt; } h2 { font-size: 12pt; margin-top: 7mm;"
    " border-bottom: 0.5pt solid #888; } h3 { font-size: 10.5pt; }"
    "table { width: 100%; border-collapse: collapse; margin-top: 2mm; }"
    "th, td { border: 0.5pt solid #999; padding: 1.5mm; text-align: left;"
    " vertical-align: top; font-size: 9pt; } th { background: #e8eaf0; }"
    ".klein { font-size: 8pt; color: #444; }"
    ".hinweis { background: #f4f4f4; padding: 2mm; margin-top: 2mm; }"
    ".blockierend { background: #fbe9e7; }</style>"
)


def _html_head_and_subject(report: Mapping[str, Any]) -> list[str]:
    """Title, profile identity and section 1 (subject)."""
    meta = report["meta"]
    profile = meta["profile"]
    norms = meta.get("norms") or {}
    parts = [
        "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>",
        f"<title>Datenschutz-Folgenabschätzung – {_text(meta['activity_name'])}</title>",
        _STYLE,
        "</head><body>",
        "<h1>Datenschutz-Folgenabschätzung</h1>",
        f"<p class='klein'>{_text(norms.get('dsfa'))} &middot; {_text(profile['regime_title'])}"
        + (f" &middot; {_text(meta['tenant_label'])}" if meta.get("tenant_label") else "")
        + "</p>",
        f"<p class='klein'>Regelprofil {_text(profile['id'])} Version {_text(profile['version'])}"
        f" (Fingerprint {_text(profile['fingerprint'][:16])}…); "
        f"{_text(profile['legal_status'])}</p>",
        "<h2>1. Gegenstand der Verarbeitung</h2><table>",
    ]
    for field in report["subject"]["fields"]:
        parts.append(
            f"<tr><th style='width:32%'>{_text(field['title'])}</th>"
            f"<td>{_text(field['value'])}</td></tr>"
        )
    parts.append(
        f"<tr><th>Fassung</th><td>Nummer {_text(meta['version'])}, Stand "
        f"{_text(meta['status_text'])}; beruht auf Fassung {_text(meta['register_version'])} "
        "des Verzeichnisses von Verarbeitungstätigkeiten</td></tr>"
    )
    edpb = report.get("edpb")
    if edpb:
        parts.append(f"<tr><th>Anlass der Abschätzung</th><td>{_text(edpb['occasion'])}</td></tr>")
        for item in edpb["dossier"]:
            parts.append(
                f"<tr><th>{_text(item['title'])}</th><td>{_text(item['value'])}"
                f"<br><span class='klein'>{_text(item['reference'])}</span></td></tr>"
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
        parts.append(f"<div class='hinweis'>{_text(profile['regime_notice'])}</div>")
    current_block = None
    for q in screening["questions"]:
        if q["block"] != current_block:
            if current_block is not None:
                parts.append("</table>")
            current_block = q["block"]
            parts.append(
                f"<h3>{_text(q['block_title'])}</h3><table><tr><th style='width:52%'>Frage</th>"
                "<th style='width:10%'>Antwort</th><th style='width:20%'>Fundstelle</th>"
                "<th>Begründung</th></tr>"
            )
        parts.append(
            f"<tr><td>{_text(q['text'])}</td><td>{_text(ANSWER_TEXT.get(q['answer']))}</td>"
            f"<td class='klein'>{_text(q['reference'])}</td>"
            f"<td>{_text(q['justification'], '')}</td></tr>"
        )
    if current_block is not None:
        parts.append("</table>")
    parts.append(f"<div class='hinweis'><b>Ergebnis:</b> {_text(screening['reasoning'])}</div>")
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
        f"<tr><th style='width:28%'>Notwendigkeit</th><td>{_text(nec['necessity'])}</td></tr>",
        f"<tr><th>Verhältnismäßigkeit</th><td>{_text(nec['proportionality'])}</td></tr>",
        "<tr><th>Standpunkt der betroffenen Personen</th><td>"
        f"{_text(nec['data_subject_view'], 'nicht eingeholt')}</td></tr></table>",
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
            f"({_text(norms.get('risiko'))}, {_text(norms.get('massnahmen'))}).</div>"
        )
    else:
        parts.append(
            "<table><tr><th>Schutzziel</th><th>Szenario</th><th>Vor Maßnahmen</th>"
            "<th>Maßnahmen</th><th>Nach Maßnahmen</th></tr>"
        )
        for s in scenarios:
            explicit = " (ausdrücklich gesetzt)" if s.get("explicit_residual") else ""
            parts.append(
                f"<tr><td>{_text(s['dimension_title'])}{' (SDM)' if s.get('sdm') else ''}</td>"
                f"<td>{_text(s['description'])}{_scenario_details(s)}</td>"
                f"<td>Schwere {s['gross_severity']}, Wahrscheinlichkeit {s['gross_likelihood']}"
                f" = {s['gross']} ({_text(s['gross_band'])})</td>"
                f"<td class='klein'>{_text(s['measure_titles'])}</td>"
                f"<td>Schwere {s['net_severity']}, Wahrscheinlichkeit {s['net_likelihood']}"
                f" = {s['net']} ({_text(s['net_band'])}){escape(explicit)}"
                + (
                    f"<br><span class='klein'>{_text(s['residual_justification'])}</span>"
                    if s.get("residual_justification")
                    else ""
                )
                + "</td></tr>"
            )
        parts.append(
            f"</table><p class='klein'>Höchstwert vor Maßnahmen {risk.get('gross_maximum')}, "
            f"nach Maßnahmen {risk.get('net_maximum')} ({_text(risk.get('net_band'))}).</p>"
        )
    edpb = report.get("edpb")
    if edpb and edpb.get("method"):
        parts.append(f"<p class='klein'>Methode: {_text(edpb['method'])}</p>")
    parts.extend(_html_measures(report))
    return parts


def _scenario_details(s: Mapping[str, Any]) -> str:
    """Risk source, modulating factors, acceptance and floor of a schema 2 scenario."""
    if "net_floor" not in s:
        return ""
    lines = []
    if s.get("risk_source"):
        lines.append(f"Risikoquelle: {_text(s['risk_source'])}")
    if s.get("modulating_factors"):
        lines.append(f"Umstände: {_text(s['modulating_factors'])}")
    if s.get("acceptance_inherent"):
        lines.append(f"Risiko vor Maßnahmen {_text(s['acceptance_inherent_title'])}")
    if s.get("acceptance_residual"):
        lines.append(f"Restrisiko {_text(s['acceptance_residual_title'])}")
    if s.get("acceptance_note"):
        lines.append(_text(s["acceptance_note"]))
    if s.get("net_floor"):
        lines.append(
            f"Mindeststufe {_text(s['net_band'])} wegen der Schwere vor Maßnahmen "
            f"({_text(s['net_floor'])})"
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
                f"<tr><td>{_text(m['category_title'])}</td><td>{_text(m['title'])}"
                f"<br><span class='klein'>{_text(m['legal_basis'])}</span></td>"
                f"<td>{_text(m['status_title'])}</td><td>{_text(m['note'], '')}</td></tr>"
            )
        parts.append("</table>")
    if edpb["action_plan"]:
        parts.append(
            "<h3>Maßnahmenplan</h3><table><tr><th>Vorhaben</th><th>Verantwortlich</th>"
            "<th>Termin</th></tr>"
        )
        for item in edpb["action_plan"]:
            parts.append(
                f"<tr><td>{_text(item.get('activity'))}</td>"
                f"<td>{_text(item.get('responsible'))}</td><td>{_text(item.get('due'))}</td></tr>"
            )
        parts.append("</table>")
    return parts


def _html_decision(report: Mapping[str, Any]) -> list[str]:
    """Section 5: proposal, decision, DPO, consultation, lifecycle."""
    proposal = report["proposal"]
    decision = report["decision"]
    dpo = report["dpo"]
    life = report["lifecycle"]
    parts: list[str] = []
    parts += [
        "<h2>5. Vorschlag, Entscheidung und Beteiligung</h2><table>",
        f"<tr><th style='width:32%'>Vorschlag des Systems</th>"
        f"<td>{_text(proposal['recommendation_text'])}</td></tr>",
        f"<tr><th>Begründung</th><td>{_text(proposal['reasoning'])}</td></tr>",
        f"<tr><th>Berechnung</th><td class='klein'>{_text(proposal['calculation'])}</td></tr>",
        "<tr><th>Entscheidung</th><td>"
        f"{_text(decision.get('decision_title') or decision['decision'], 'noch offen')}</td></tr>",
    ]
    if decision.get("conditions"):
        parts.append(
            "<tr><th>Bedingungen vor Beginn der Verarbeitung</th><td>"
            + "<br>".join(f"{i}. {_text(c)}" for i, c in enumerate(decision["conditions"], 1))
            + "</td></tr>"
        )
    if decision.get("deviation"):
        parts.append(
            f"<tr><th>Abweichung vom Vorschlag</th>"
            f"<td>{_text(decision['deviation_justification'])}</td></tr>"
        )
    if report.get("release_mode"):
        requested = (
            f"am {_text(dpo.get('requested_on'))} bei {_text(dpo.get('requested_from'))}"
            f" (erfasst von {_text(dpo.get('requested_by'))})"
            if dpo.get("requested_on")
            else "nicht dokumentiert"
        )
        parts.append(f"<tr><th>Stellungnahme eingeholt</th><td>{requested}</td></tr>")
    parts += [
        f"<tr><th>Datenschutzbeauftragte/r</th><td>{_text(dpo['vote_text'])}"
        f" ({_text(dpo['by'])}, {_text(dpo['at'])})</td></tr>",
        f"<tr><th>Stellungnahme</th><td>{_text(dpo['statement'])}</td></tr>",
    ]
    if dpo.get("conclusion"):
        parts.append(
            f"<tr><th>Umgang mit der Stellungnahme</th><td>{_text(dpo['conclusion'])}</td></tr>"
        )
    if dpo.get("leadership_presented_to"):
        parts.append(
            f"<tr><th>Der Behördenleitung vorgelegt</th>"
            f"<td>{_text(dpo['leadership_presented_to'])} am "
            f"{_text(dpo['leadership_presented_at'])}</td></tr>"
        )
    consultation = report.get("consultation")
    if consultation:
        parts.append(
            f"<tr><th>Konsultation der Aufsichtsbehörde</th><td>{_text(consultation['authority'])}"
            f", {_text(consultation['consulted_on'])}: {_text(consultation['result'])}"
            + (
                f"<br><span class='klein'>Grund: {_text(consultation['ground_title'])} "
                f"({_text(consultation['ground_reference'])})</span>"
                if consultation.get("ground_title")
                else ""
            )
            + "</td></tr>"
        )
    elif proposal.get("consultation_required") and decision["decision"] != DECISION_REJECTED:
        parts.append(
            "<tr class='blockierend'><th>Konsultation der Aufsichtsbehörde</th>"
            f"<td>erforderlich ({_text(proposal.get('consultation_reference'))}), "
            "noch nicht dokumentiert</td></tr>"
        )
    notice = proposal.get("consultation_notice") or {}
    if not consultation and notice and notice.get("status") != "erforderlich" and notice["text"]:
        label = "Hinweis zur Konsultation" + ("" if notice.get("final") else " (vorläufig)")
        parts.append(f"<tr><th>{escape(label)}</th><td>{_text(notice['text'])}</td></tr>")
    parts += [
        f"<tr><th>Erstellt</th><td>{_text(life['created_by'])} am {_text(life['created_at'])}"
        f"; bearbeitet von {_text(life['editors'])}</td></tr>",
        "<tr><th>Freigegeben</th><td>"
        + (
            f"{_text(life['released_by'])} am {_text(life['released_at'])}"
            if life.get("released_by")
            else "noch nicht freigegeben"
        )
        + "</td></tr></table>",
    ]
    return parts


def _html_issues_and_changes(report: Mapping[str, Any]) -> list[str]:
    """Review notes and changes compared with the predecessor."""
    proposal = report["proposal"]
    parts: list[str] = []
    issues = proposal.get("issues") or []
    hints = (report.get("edpb") or {}).get("hints") or []
    if issues or hints:
        parts.append("<h2>Prüfhinweise</h2><ul>")
        for issue in issues:
            mark = " (blockiert die Freigabe)" if issue.get("blocking") else ""
            parts.append(f"<li>{_text(issue.get('message'))}{escape(mark)}</li>")
        for hint in hints:
            parts.append(f"<li>{_text(hint)}</li>")
        parts.append("</ul>")
    changes = report.get("changes_to_predecessor") or []
    if changes:
        parts.append(
            "<h2>Änderungen gegenüber der Vorfassung</h2><table>"
            "<tr><th>Angabe</th><th>Vorher</th><th>Nachher</th></tr>"
        )
        for change in changes:
            parts.append(
                f"<tr><td>{_text(change.get('bezeichnung'))}</td>"
                f"<td>{_text(change.get('vorher'))}</td>"
                f"<td>{_text(change.get('nachher'))}</td></tr>"
            )
        parts.append("</table>")
    return parts


def _html_open_at_release(report: Mapping[str, Any]) -> list[str]:
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
    parts.extend(f"<li>{_text(p)}</li>" for p in points)
    parts.append("</ul>")
    return parts


def _html_sources(report: Mapping[str, Any]) -> list[str]:
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
            f"<tr><td>{_text(source['issuer'])}: {_text(source['title'])}"
            f"<br><span class='klein'>{_text(source['reference'])}</span></td>"
            f"<td>{_text(source['date'])}; {_text(source['status'])}</td>"
            f"<td>{_text(source['used_for'])}</td></tr>"
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
        *_html_decision(report),
        *_html_issues_and_changes(report),
        *_html_open_at_release(report),
        *_html_sources(report),
    ]
    parts.append(
        "<p class='klein'>Der Vorschlag ist eine Berechnung auf Grundlage des genannten "
        "Regelprofils und ersetzt keine fachliche oder datenschutzrechtliche Entscheidung. "
        "Freigegebene Fassungen sind unveränderlich.</p></body></html>"
    )
    return "".join(parts)
