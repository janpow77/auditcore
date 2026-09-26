"""Report data of assessments and registers as JSON-compatible documents.

The builders return plain dictionaries so any consumer renderer can use them;
the documents are the JSON output boundary of the library and therefore typed
``dict[str, Any]``.
"""

from __future__ import annotations

import json
import warnings
from collections.abc import Mapping, Sequence
from typing import Any

from auditcore_common.json_values import jsonable

from .edpb import edpb_hints
from .model import Assessment, RegisterVersion
from .register_content import check_register, group_by_department
from .rules import RuleProfile

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


def _plain(value: object) -> Any:
    """Records, enums, mappings, sets and datetimes as JSON-compatible values."""
    return jsonable(value, enums=True, dataclasses=True, sets=True)


def plain(value: object) -> Any:
    """Veraltet: ``auditcore_common.json_values.jsonable(value, enums=True,
    dataclasses=True, sets=True)`` (gleiches Ergebnis)."""
    warnings.warn(
        "auditcore_dataprotection.report_data.plain ist veraltet; "
        "auditcore_common.json_values.jsonable(enums=True, dataclasses=True, sets=True) "
        "verwenden.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _plain(value)


# ---------------------------------------------------------------------------
# Assessment report
# ---------------------------------------------------------------------------


def _meta(assessment: Assessment, profile: RuleProfile, tenant_label: str) -> dict[str, object]:
    status = assessment.status.value
    profile_info: dict[str, object] = {
        "id": profile.id,
        "version": profile.version,
        "fingerprint": profile.fingerprint,
        "status": profile.status,
        "legal_status": profile.legal_status,
        "regime": profile.regime,
        "regime_title": profile.regime_title,
        "regime_notice": profile.regime_notice,
    }
    if profile.edpb:
        profile_info["schema"] = profile.schema
    return {
        "tenant_id": assessment.tenant_id,
        "tenant_label": tenant_label,
        "assessment_id": assessment.assessment_id,
        "register_id": assessment.register_id,
        "register_version": assessment.register_version,
        "activity_id": assessment.activity_id,
        "activity_name": assessment.activity_name,
        "version": assessment.version,
        "status": status,
        "status_text": profile.status_texts.get(status, status),
        "locked": assessment.locked,
        "predecessor_id": assessment.predecessor_id,
        "profile": profile_info,
        "recorded_profile": {
            "id": assessment.profile_id,
            "version": assessment.profile_version,
            "fingerprint": assessment.profile_fingerprint,
        },
        "norms": dict(profile.norms),
    }


def _questions(assessment: Assessment, profile: RuleProfile) -> list[dict[str, object]]:
    """Every screening question in block order with its answer."""
    questions: list[dict[str, object]] = []
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
    return questions


def _screening(assessment: Assessment, profile: RuleProfile) -> dict[str, object]:
    screening = assessment.proposal.get("screening") or {}
    return {
        "questions": _questions(assessment, profile),
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
    }


def _proposal(proposal: Mapping[str, Any]) -> dict[str, object]:
    notice = (
        {"consultation_notice": _plain(proposal["consultation_notice"])}
        if proposal.get("consultation_notice")
        else {}
    )
    return {
        "recommendation": proposal.get("recommendation"),
        "recommendation_text": proposal.get("recommendation_text"),
        "reasoning": proposal.get("reasoning"),
        "consultation_required": proposal.get("consultation_required"),
        "consultation_reference": proposal.get("consultation_reference"),
        "calculation": proposal.get("calculation"),
        "profile": _plain(proposal.get("profile")),
        "issues": _plain(proposal.get("issues") or []),
        "trace": _plain(proposal.get("trace") or []),
        **notice,
    }


def _decision(assessment: Assessment, profile: RuleProfile) -> dict[str, object]:
    decision: dict[str, object] = {
        "decision": assessment.decision,
        "deviation": assessment.deviation,
        "deviation_justification": assessment.deviation_justification,
        "decided_by": assessment.decided_by,
        "decided_at": _plain(assessment.decided_at),
    }
    if profile.edpb:
        decision["decision_title"] = profile.decision_titles.get(assessment.decision or "", None)
        decision["conditions"] = list(assessment.conditions)
    return decision


def _dpo(assessment: Assessment, profile: RuleProfile) -> dict[str, object]:
    dpo: dict[str, object] = {
        "vote": assessment.dpo_vote,
        "vote_text": profile.vote_texts.get(assessment.dpo_vote or "", "noch offen"),
        "statement": assessment.dpo_statement,
        "by": assessment.dpo_by,
        "at": _plain(assessment.dpo_at),
        "conclusion": assessment.dpo_conclusion,
        "conclusion_by": assessment.dpo_conclusion_by,
        "leadership_presented_to": assessment.leadership_presented_to,
        "leadership_presented_at": _plain(assessment.leadership_presented_at),
    }
    if profile.edpb and profile.documentation_mode:
        dpo["requested_from"] = assessment.dpo_requested_from
        dpo["requested_on"] = assessment.dpo_requested_on
        dpo["requested_by"] = assessment.dpo_requested_by
    return dpo


def _consultation(assessment: Assessment, profile: RuleProfile) -> dict[str, object] | None:
    """Recorded consultation; its ground only for schema 2 profiles, with title."""
    consultation = assessment.consultation
    if not consultation:
        return None
    data: dict[str, object] = _plain(consultation)
    if not profile.edpb:
        # Schema 1 reports stay exactly as before.
        data.pop("ground", None)
    elif consultation.ground:
        title, reference = profile.consultation_grounds[consultation.ground]
        data["ground_title"] = title
        data["ground_reference"] = reference
    return data


def _lifecycle(assessment: Assessment) -> dict[str, object]:
    return {
        "created_by": assessment.created_by,
        "created_at": _plain(assessment.created_at),
        "updated_at": _plain(assessment.updated_at),
        "editors": list(assessment.editors),
        "released_by": assessment.released_by,
        "released_at": _plain(assessment.released_at),
        "revision": assessment.revision,
    }


def assessment_report(
    assessment: Assessment, profile: RuleProfile, *, tenant_label: str = ""
) -> dict[str, Any]:
    """Complete report data of one assessment version (Art. 35 Abs. 7 DSGVO).

    Schema 2 profiles add the decision title, conditions, the EDPB section and,
    in documentation mode, the DPO request and the points open at release.
    """
    snapshot = assessment.activity_snapshot
    edpb = _edpb_section(assessment, profile) if profile.edpb else None
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "kind": "assessment",
        "meta": _meta(assessment, profile, tenant_label),
        "subject": {
            "fields": [
                {"key": key, "title": title, "value": _plain(snapshot.get(key))}
                for key, title in SNAPSHOT_FIELDS
            ],
            "snapshot": _plain(snapshot),
        },
        "screening": _screening(assessment, profile),
        "necessity": {
            "necessity": assessment.necessity,
            "proportionality": assessment.proportionality,
            "data_subject_view": assessment.data_subject_view,
        },
        "risk": _plain(assessment.proposal.get("risk")),
        "scenarios": [s.to_dict() for s in assessment.scenarios],
        "proposal": _proposal(assessment.proposal),
        "decision": _decision(assessment, profile),
        "dpo": _dpo(assessment, profile),
        "consultation": _consultation(assessment, profile),
        "lifecycle": _lifecycle(assessment),
        "changes_to_predecessor": _plain(list(assessment.changes_to_predecessor)),
    }
    if edpb is None:
        return report
    if profile.documentation_mode:
        report["release_mode"] = profile.release_mode
        report["release_open_points"] = list(assessment.release_open_points)
    report["edpb"] = edpb
    return report


def _edpb_measures(assessment: Assessment, profile: RuleProfile) -> list[dict[str, object]]:
    """Measures with a status or used in a scenario, with category and status titles."""
    used = {k for s in assessment.scenarios for k in s.measures}
    measures: list[dict[str, object]] = []
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
    return measures


def _occasion(assessment: Assessment, profile: RuleProfile) -> str:
    if not assessment.predecessor_id:
        return "Erstmalige Abschätzung der Verarbeitungstätigkeit"
    if assessment.changes_to_predecessor:
        return (
            "Die Verarbeitung hat sich gegenüber der Vorfassung geändert "
            f"({profile.norm('ueberpruefung')})"
        )
    return (
        "Neubewertung ohne geänderte Angaben im Verzeichnis, etwa nach einer neuen "
        f"Profilfassung oder turnusmäßig ({profile.norm('ueberpruefung')})"
    )


def _edpb_section(assessment: Assessment, profile: RuleProfile) -> dict[str, object]:
    """Documentation along the EDPB template 2026 v1.0 (schema 2 profiles only)."""
    measures = _edpb_measures(assessment, profile)
    return {
        "template": "EDSA, Template for DPIA 2026, Version 1.0 (Konsultationsfassung)",
        "method": profile.risk_method,
        "occasion": _occasion(assessment, profile),
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


# ---------------------------------------------------------------------------
# Register report and overview
# ---------------------------------------------------------------------------


def register_report(
    version: RegisterVersion,
    profile: RuleProfile,
    *,
    overview: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Report data of one register version with content check results.

    ``overview`` (rows of ``AssessmentService.overview``) adds the state of
    the newest DPIA per activity; without it the report is unchanged.
    """
    content = version.content
    activities = [dict(a) for a in version.activities]
    groups = group_by_department(activities, list(content.get("referate") or []))
    report = {
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
    if overview is not None:
        report["dsfa"] = {
            str(row.get("id")): _plain(row.get("dsfa")) for row in overview if row.get("id")
        }
    return report


def overview_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """JSON-compatible copy of ``AssessmentService.overview`` rows."""
    return [_plain(dict(row)) for row in rows]


def to_json_bytes(report: Mapping[str, Any]) -> bytes:
    """Deterministic UTF-8 JSON (sorted keys, ISO dates)."""
    return (
        json.dumps(_plain(report), sort_keys=True, ensure_ascii=False, indent=1).encode("utf-8")
        + b"\n"
    )
