"""JSON views of profiles, register versions and assessments for the UI.

The views only rearrange what the library computed (content checks, proposal,
open points); they add no rule of their own.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from auditcore_common.json_values import jsonable

from ..assessment import AssessmentService
from ..model import Assessment, RegisterVersion
from ..register_content import COUNT_FIELDS, FLAG_FIELDS, REQUIRED_TEXT, check_register
from ..rules import RuleProfile
from .contract import CONTRACT, JsonObject

#: Activity fields outside the profile's register columns (labels of the source forms).
EXTRA_COLUMNS = (
    ("referat", "Referat / Abteilung", ""),
    (
        "besondere_kategorien",
        "Besondere Kategorien personenbezogener Daten",
        "Art. 9 Abs. 1 DSGVO",
    ),
    ("daten_art10", "Daten über strafrechtliche Verurteilungen und Straftaten", "Art. 10 DSGVO"),
    ("anzahl_betroffene", "Zahl der betroffenen Personen", "Art. 35 Abs. 3 lit. b DSGVO"),
)


def _plain(value: object) -> object:
    return jsonable(value, enums=True, dataclasses=True, sets=True)


def _object(value: Mapping[str, object]) -> JsonObject:
    """JSON-compatible copy of a mapping (records, enums and datetimes as plain values)."""
    return cast(JsonObject, _plain(value))


def _kind(key: str) -> str:
    if key in FLAG_FIELDS:
        return "flag"
    if key in COUNT_FIELDS:
        return "count"
    return "text"


def register_columns(profile: RuleProfile) -> list[JsonObject]:
    """Fields of an activity in form order with kind, requirement and legal reference."""
    columns = [(k, t, profile.register_references.get(k, "")) for k, t in profile.register_columns]
    columns[1:1] = [EXTRA_COLUMNS[0]]
    columns.extend(EXTRA_COLUMNS[1:])
    return [
        {"key": key, "title": title, "reference": ref, "kind": _kind(key)}
        | {"required": key in REQUIRED_TEXT}
        for key, title, ref in columns
    ]


def _screening_view(profile: RuleProfile) -> JsonObject:
    blocks = [
        {
            "key": key,
            "title": title,
            "questions": [
                {
                    "key": q.key,
                    "text": q.text,
                    "reference": q.reference,
                    "effect": q.effect,
                    "explanation": q.explanation,
                }
                for q in profile.questions
                if q.block == key
            ],
        }
        for key, title in profile.blocks
    ]
    return {"blocks": blocks, "points_threshold": profile.points_threshold}


def _risk_view(profile: RuleProfile) -> JsonObject:
    def levels(values: Mapping[int, str]) -> list[JsonObject]:
        return [{"value": k, "label": v} for k, v in sorted(values.items())]

    return {
        "scale_min": profile.scale_min,
        "scale_max": profile.scale_max,
        "severity_levels": levels(profile.severity_levels),
        "likelihood_levels": levels(profile.likelihood_levels),
        "dimensions": [{"key": k, "title": v} for k, v in profile.dimensions.items()],
        "measures": [
            {
                "key": m.key,
                "title": m.title,
                "category": m.category,
                "reduces_severity": m.reduces_severity,
                "reduces_likelihood": m.reduces_likelihood,
            }
            for m in profile.measures
        ],
        "bands": [band.label for band in profile.bands],
        "method": profile.risk_method,
    }


def profile_view(profile: RuleProfile) -> JsonObject:
    """``GET /profile``: everything the forms need, taken from the rule profile."""
    return {
        "contract": CONTRACT,
        "profile": {
            "id": profile.id,
            "version": profile.version,
            "fingerprint": profile.fingerprint,
            "regime": profile.regime,
            "regime_title": profile.regime_title,
            "release_mode": profile.release_mode,
        },
        "register": {"columns": register_columns(profile)},
        "screening": _screening_view(profile),
        "risk": _risk_view(profile),
        "decisions": [
            {"key": key, "title": profile.decision_titles.get(key, key)}
            for key in profile.decisions
        ],
        "dossier_fields": [
            {
                "key": f.key,
                "title": f.title,
                "kind": f.kind,
                "required": f.required,
                "choices": [{"key": k, "title": t} for k, t in f.choices],
            }
            for f in profile.dossier_fields
        ],
    }


def version_summary(version: RegisterVersion) -> JsonObject:
    """One line of the version history."""
    return _object(
        {
            "version": version.version,
            "status": version.status,
            "created_by": version.created_by,
            "created_at": version.created_at,
            "released_by": version.released_by,
            "released_at": version.released_at,
            "activities": len(version.activities),
        }
    )


def version_view(version: RegisterVersion, profile: RuleProfile) -> JsonObject:
    """A register version with content and the library's content check."""
    return version_summary(version) | _object(
        {
            "revision": version.revision,
            "locked": version.locked,
            "content": version.content,
            "content_hash": version.content_hash,
            "editors": list(version.editors),
            "predecessor_version": version.predecessor_version,
            "issues": [i.to_dict() for i in check_register(version.content, profile)],
        }
    )


def register_state(
    draft: RegisterVersion | None,
    released: RegisterVersion | None,
    history: Sequence[RegisterVersion],
    profile: RuleProfile,
) -> JsonObject:
    """``GET /register``: open draft, current release and the history."""
    return {
        "contract": CONTRACT,
        "draft": None if draft is None else version_view(draft, profile),
        "released": None if released is None else version_view(released, profile),
        "versions": [version_summary(v) for v in history],
    }


def _assessment_summary(assessment: Assessment) -> JsonObject:
    return _object(
        {
            "id": assessment.assessment_id,
            "version": assessment.version,
            "status": assessment.status,
            "decision": assessment.decision,
            "created_at": assessment.created_at,
            "released_by": assessment.released_by,
            "released_at": assessment.released_at,
        }
    )


def _lifecycle(assessment: Assessment) -> JsonObject:
    return _object(
        {
            "created_by": assessment.created_by,
            "updated_at": assessment.updated_at,
            "editors": list(assessment.editors),
            "decision": assessment.decision,
            "deviation": assessment.deviation,
            "deviation_justification": assessment.deviation_justification,
            "conditions": list(assessment.conditions),
            "decided_by": assessment.decided_by,
            "decided_at": assessment.decided_at,
            "dpo_requested_from": assessment.dpo_requested_from,
            "dpo_requested_on": assessment.dpo_requested_on,
            "release_open_points": list(assessment.release_open_points),
        }
    )


def assessment_view(
    assessment: Assessment, service: AssessmentService, versions: Sequence[Assessment]
) -> JsonObject:
    """``GET /assessments/{id}``: survey, proposal, decision state and open points."""
    view = _assessment_summary(assessment) | _lifecycle(assessment)
    view.update(
        _object(
            {
                "contract": CONTRACT,
                "activity_id": assessment.activity_id,
                "activity_name": assessment.activity_name,
                "revision": assessment.revision,
                "locked": assessment.locked,
                "register_version": assessment.register_version,
                "profile": {"id": assessment.profile_id, "version": assessment.profile_version},
                "answers": {k: a.to_dict() for k, a in assessment.answers.items()},
                "scenarios": [s.to_dict() for s in assessment.scenarios],
                "necessity": assessment.necessity,
                "proportionality": assessment.proportionality,
                "dossier": dict(assessment.dossier),
                "proposal": dict(assessment.proposal),
                "open_points": list(service.open_points(assessment)),
                "release_blockers": list(service.release_blockers(assessment)),
                "versions": [_assessment_summary(v) for v in versions],
            }
        )
    )
    return view


def overview_view(rows: Sequence[Mapping[str, object]]) -> JsonObject:
    """``GET /assessments``: activities of the effective register with their newest DPIA."""
    return {"contract": CONTRACT, "items": _plain([dict(r) for r in rows])}
