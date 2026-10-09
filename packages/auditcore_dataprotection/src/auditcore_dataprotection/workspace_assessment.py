"""Wizard answers that belong to the DPIA record (W09 screening, W10 texts).

They are written to the open DPIA version through :class:`AssessmentService`,
never stored a second time in the register activity.
"""

from __future__ import annotations

from dataclasses import dataclass

from .assessment import AssessmentService
from .errors import ConflictError, StaleRevisionError, ValidationError
from .model import Actor, Assessment
from .provenance import CONFIRMED

_SCREENING_VALUES = {"ja": "ja", "nein": "nein", "unklar": "unbekannt"}


@dataclass(frozen=True)
class AssessmentAnswer:
    """One answer for the DPIA record."""

    tenant_id: str
    actor: Actor
    target: str
    value: str
    justification: str
    origin: str


def answer_in_assessment(
    service: AssessmentService,
    answer: AssessmentAnswer,
    current: Assessment | None,
    expected_revision: int | None,
) -> Assessment:
    """Update the open DPIA version; unclear stays "unbekannt", never "nein"."""
    if answer.origin != CONFIRMED:
        raise ValidationError("Antworten zur Folgenabschätzung gibt nur eine Person.")
    if current is None or current.locked:
        raise ConflictError(
            "Für diese Frage ist eine offene Fassung der Folgenabschätzung anzulegen."
        )
    if expected_revision is not None and expected_revision != current.revision:
        raise StaleRevisionError("Die Folgenabschätzung wurde inzwischen geändert.")
    kind, name = answer.target.split(":", 1)
    common = (answer.tenant_id, answer.actor, current.assessment_id)
    if kind == "screening":
        if answer.value not in _SCREENING_VALUES:
            raise ValidationError("Zulässig sind ja, nein oder unklar.")
        answers: dict[str, object] = {k: a.to_dict() for k, a in current.answers.items()}
        answers[name] = {
            "value": _SCREENING_VALUES[answer.value],
            "justification": answer.justification,
        }
        return service.update(*common, expected_revision=current.revision, answers=answers)
    if not answer.value.strip():
        raise ValidationError("Die Antwort ist leer.")
    if name == "necessity":
        return service.update(*common, expected_revision=current.revision, necessity=answer.value)
    if name == "proportionality":
        return service.update(
            *common, expected_revision=current.revision, proportionality=answer.value
        )
    if name == "data_subject_view":
        return service.update(
            *common, expected_revision=current.revision, data_subject_view=answer.value
        )
    raise ValidationError(f"Unbekanntes Feld der Folgenabschätzung „{name}“.")
