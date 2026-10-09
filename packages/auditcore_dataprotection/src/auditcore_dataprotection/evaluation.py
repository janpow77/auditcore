"""Evaluation of one activity: status axes, gates, checklist and open work.

Pure function over the records the services load. The same evaluation feeds
the wizard, the work list, exports and the backend gates, so the user
interface, the REST interface and direct library calls cannot disagree.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

from .central_register import TransferRecord, transfer_status
from .change_impact import changed_fields
from .checklist import CATALOG, ChecklistItem, items_from_data
from .evidence import evidence_from_data, proven_risk, safeguards_from_data
from .gates import GateFinding, GateInput, evaluate_gates
from .model import Assessment, AssessmentStatus, RegisterVersion
from .operation_model import OperationalDecision
from .register_content import activity_changes, check_activity
from .rules import RuleProfile, load_profile
from .scope import personal_data_findings
from .status import (
    OperationStatus,
    StatusAxes,
    consultation_status,
    documentation_status,
    dpia_work_status,
    necessity_status,
    operation_status,
)
from .wizard import tasks
from .wizard_catalog import WizardCatalog


@dataclass(frozen=True)
class EvaluationInput:
    """Records of one activity as loaded by the services."""

    profile: RuleProfile
    catalog: WizardCatalog
    working: RegisterVersion
    activity: Mapping[str, object]
    released: RegisterVersion | None
    released_activity: Mapping[str, object] | None
    assessments: Sequence[Assessment]
    transfer: TransferRecord | None
    decision: OperationalDecision | None
    today: date


@dataclass(frozen=True)
class Evaluation:
    """Result of :func:`evaluate`."""

    axes: StatusAxes
    gates: tuple[GateFinding, ...]
    checklist: Mapping[str, ChecklistItem]
    register_issues: tuple[str, ...]
    open_tasks: tuple[str, ...]
    findings: tuple[str, ...]
    assessment: Assessment | None
    unproven_measures: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """JSON form for the work list and exports."""
        return {
            "status": self.axes.to_dict(),
            "sperren": [g.to_dict() for g in self.gates],
            "pruefpunkte": [
                {
                    "id": d.id,
                    "bereich": d.area,
                    "titel": d.title,
                    "zustaendig": d.owner_role,
                    "sperrt": d.blocks,
                    "nachweisarten": sorted(k.value for k in d.evidence_kinds),
                    **self.checklist[d.id].to_dict(),
                }
                for d in CATALOG
            ],
            "verzeichnisbefunde": list(self.register_issues),
            "offene_aufgaben": list(self.open_tasks),
            "hinweise": list(self.findings),
            "nicht_nachgewiesene_massnahmen": list(self.unproven_measures),
            "folgenabschaetzung": None
            if self.assessment is None
            else {
                "assessment_id": self.assessment.assessment_id,
                "version": self.assessment.version,
                "revision": self.assessment.revision,
                "status": self.assessment.status.value,
            },
        }


def wizard_context(activity: Mapping[str, object], assessment: Assessment | None) -> dict[str, str]:
    """Context values for conditional wizard steps (regime, DPIA necessity)."""
    screening = {} if assessment is None else assessment.proposal.get("screening") or {}
    dpia = str(screening.get("outcome") or "")
    if activity.get("dsfa_freiwillig") is True:
        dpia = "freiwillig"
    shared = {
        f"assessment:{name}": str(getattr(assessment, name))
        for name in ("necessity", "proportionality", "data_subject_view")
        if assessment is not None and str(getattr(assessment, name)).strip()
    }
    names = {"ja": "ja", "nein": "nein", "unbekannt": "unklar"}
    answers = {} if assessment is None else assessment.answers
    shared.update(
        {f"screening:{key}": names[answer.value.value] for key, answer in answers.items()}
    )
    return {"regime": str(activity.get("rechtsregime") or ""), "dsfa": dpia, **shared}


def _review_required(assessment: Assessment | None, data: EvaluationInput) -> bool:
    if assessment is None or assessment.status is not AssessmentStatus.RELEASED:
        return False
    return bool(activity_changes(assessment.activity_snapshot, data.activity, data.profile))


def _proof(assessment: Assessment | None, data: EvaluationInput) -> tuple[bool, tuple[str, ...]]:
    if assessment is None or not assessment.scenarios:
        return False, ()
    rules = load_profile(assessment.profile_id, assessment.profile_version)
    result = proven_risk(
        rules,
        assessment,
        safeguards_from_data(data.activity.get("schutzmassnahmen")),
        evidence_from_data(data.activity.get("nachweise")),
        data.today,
    )
    return result.planned_effect_only, result.unproven_measures


def _changed_since_release(data: EvaluationInput) -> bool:
    if data.released_activity is None or data.working is data.released:
        return False
    return bool(changed_fields(data.released_activity, data.activity))


def _operation(data: EvaluationInput, changed: bool) -> OperationStatus:
    decision = data.decision
    matches = (
        decision is not None
        and data.released is not None
        and decision.register_version == data.released.version
        and decision.content_hash == data.released.content_hash
        and not changed
    )
    return operation_status(
        None if decision is None else decision.outcome, matches_current_version=matches
    )


def evaluate(data: EvaluationInput) -> Evaluation:
    """Axes, gates, checklist, register issues and open wizard work of one activity."""
    assessment = data.assessments[0] if data.assessments else None
    issues = tuple(i.message for i in check_activity(data.activity, data.profile) if i.blocking)
    context = wizard_context(data.activity, assessment)
    open_tasks = tuple(
        f"{t['question']} ({t['kind']})" for t in tasks(data.catalog, data.activity, context)
    )
    findings = personal_data_findings(data.activity)
    changed = _changed_since_release(data)
    necessity = necessity_status(assessment, data.profile)
    planned_only, unproven = _proof(assessment, data)
    axes = StatusAxes(
        documentation=documentation_status(
            released=data.released is not None,
            blocking_issues=len(issues),
            open_tasks=len(open_tasks) + len(findings),
            changed_since_release=changed,
        ),
        necessity=necessity,
        dpia_work=dpia_work_status(
            assessment, necessity, review_required=_review_required(assessment, data)
        ),
        consultation=consultation_status(assessment, necessity, data.activity),
        transfer=transfer_status(data.transfer, data.released),
        operation=_operation(data, changed),
    )
    gates = evaluate_gates(
        GateInput(
            activity=data.activity,
            axes=axes,
            blocking_issues=(*issues, *findings),
            open_tasks=open_tasks,
            planned_effect_only=planned_only,
            unproven_measures=unproven,
            changed_since_confirmation=changed,
            dpo_statement=assessment is not None and assessment.dpo_at is not None,
        )
    )
    return Evaluation(
        axes,
        gates,
        items_from_data(data.activity.get("pruefpunkte")),
        issues,
        open_tasks,
        findings,
        assessment,
        unproven,
    )
