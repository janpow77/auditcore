"""Guided wizard on the same versioned record as the free register editor.

The wizard is optional: in ``gefuehrt`` mode it leads step by step through the
questions, in ``frei`` mode every step is reachable. Both modes read and write
the register activity: wizard answers (``assistent.antworten``) keep value,
justification, author, time and origin; confirmed answers are written to their
register field. "Unklar" is a value of its own and becomes a task; it is never
turned into "Nein". Suggestions from templates or AI stay unconfirmed and are
not written to the register until a person confirms them. Answers to questions
that became hidden no longer act on the register (GUI-03).
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from .errors import ConflictError, ValidationError
from .provenance import CONFIRMED, ORIGINS, is_confirmed
from .wizard_catalog import (
    KIND_NUMBER,
    KIND_TABLE,
    KIND_TEXT,
    KIND_YES_NO,
    NO,
    NOT_APPLICABLE,
    UNCLEAR,
    YES,
    Condition,
    QuestionDef,
    StepDef,
    WizardCatalog,
)
from .wizard_values import check_typed, from_register, to_register

MODE_GUIDED = "gefuehrt"
MODE_FREE = "frei"
MODES = (MODE_GUIDED, MODE_FREE)
STATE_KEY = "assistent"
_REGISTER = "register:"


@dataclass(frozen=True)
class WizardAnswer:
    """Stored answer with its provenance."""

    value: str
    justification: str
    by: str
    at: str
    origin: str

    @property
    def confirmed(self) -> bool:
        """True if a person entered or confirmed the answer."""
        return is_confirmed(self.origin)

    def to_dict(self) -> dict[str, str]:
        """JSON form inside ``assistent.antworten``."""
        return {k: str(getattr(self, k)) for k in ("value", "justification", "by", "at", "origin")}


def _state(activity: Mapping[str, object]) -> Mapping[str, object]:
    state = activity.get(STATE_KEY)
    return state if isinstance(state, Mapping) else {}


def stored_answers(activity: Mapping[str, object]) -> dict[str, WizardAnswer]:
    """Wizard answers of an activity."""
    raw = _state(activity).get("antworten")
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(k): WizardAnswer(
            str(v.get("value", "")),
            str(v.get("justification", "")),
            str(v.get("by", "")),
            str(v.get("at", "")),
            str(v.get("origin", CONFIRMED)),
        )
        for k, v in raw.items()
        if isinstance(v, Mapping)
    }


def _register_value(question: QuestionDef, activity: Mapping[str, object]) -> str | None:
    """Value already present in the register (free editing), as a wizard value."""
    if not question.target.startswith(_REGISTER):
        return None
    value = activity.get(question.target.removeprefix(_REGISTER))
    if question.kind in (KIND_NUMBER, KIND_TABLE):
        return from_register(question, value)
    if isinstance(value, bool):
        return YES if value else NO
    if isinstance(value, str) and value.strip():
        return value
    return None


def current_values(
    catalog: WizardCatalog,
    activity: Mapping[str, object],
    context: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Answer, register or DPIA value per question; unanswered questions are absent.

    ``context`` carries values the wizard shares with the DPIA record
    (``assessment:<field>``), so texts entered there count here as well.
    """
    answers = stored_answers(activity)
    known = context or {}
    values: dict[str, str] = {}
    for question in catalog.questions:
        if question.id in answers:
            values[question.id] = answers[question.id].value
            continue
        found = _register_value(question, activity) or known.get(question.target)
        if found:
            values[question.id] = found
    return values


def _visible(
    condition: Condition | None, values: Mapping[str, str], context: Mapping[str, str]
) -> bool:
    if condition is None:
        return True
    if condition.question is not None:
        return values.get(condition.question) in condition.values
    return context.get(condition.context or "", "") in condition.values


def visible_questions(
    catalog: WizardCatalog, activity: Mapping[str, object], context: Mapping[str, str]
) -> dict[str, tuple[QuestionDef, ...]]:
    """Visible questions per visible step."""
    values = current_values(catalog, activity, context)
    result: dict[str, tuple[QuestionDef, ...]] = {}
    for step in catalog.steps:
        if _visible(step.show_if, values, context):
            result[step.id] = tuple(
                q for q in step.questions if _visible(q.show_if, values, context)
            )
    return result


def _check_value(question: QuestionDef, value: str, justification: str) -> None:
    """Closed value sets, "nicht anwendbar" and values that need a reason."""
    if value == NOT_APPLICABLE:
        if not question.na_allowed:
            raise ValidationError(f"{question.id}: „nicht anwendbar“ ist hier nicht vorgesehen.")
        if not justification.strip():
            raise ValidationError(f"{question.id}: „nicht anwendbar“ braucht eine Begründung.")
        return
    allowed = question.allowed_values
    if allowed and value not in allowed:
        raise ValidationError(f"{question.id}: zulässig sind {', '.join(allowed)}.")
    check_typed(question, value)
    if question.kind == KIND_TEXT and not value.strip():
        raise ValidationError(f"{question.id}: die Antwort ist leer; „unklar“ statt leer angeben.")
    if value in question.justify_values and not justification.strip():
        raise ValidationError(f"{question.id}: die Antwort „{value}“ ist zu begründen.")


def _register_target_value(question: QuestionDef, answer: WizardAnswer) -> object:
    """Register representation; unclear and unconfirmed answers leave it open."""
    if not answer.confirmed or answer.value in (UNCLEAR, NOT_APPLICABLE):
        return None
    if question.kind == KIND_YES_NO:
        return answer.value == YES
    return to_register(question, answer.value)


def _apply_targets(
    catalog: WizardCatalog, data: dict[str, object], context: Mapping[str, str]
) -> None:
    """Write register targets of visible answers and clear those of hidden ones."""
    answers = stored_answers(data)
    visible = {q.id for qs in visible_questions(catalog, data, context).values() for q in qs}
    for question_id, answer in answers.items():
        question = catalog.find(question_id)
        if question is None or not question.target.startswith(_REGISTER):
            continue
        field = question.target.removeprefix(_REGISTER)
        if question_id in visible:
            data[field] = _register_target_value(question, answer)
        elif data.get(field) == _register_target_value(question, answer):
            data[field] = None


def record_answer(
    catalog: WizardCatalog,
    activity: Mapping[str, object],
    context: Mapping[str, str],
    question_id: str,
    answer: WizardAnswer,
) -> dict[str, object]:
    """New activity data with the answer stored and its register target applied."""
    question = catalog.question(question_id)
    if answer.origin not in ORIGINS:
        raise ValidationError(f"Unbekannte Herkunft „{answer.origin}“.")
    visible = visible_questions(catalog, activity, context)
    if not any(question in qs for qs in visible.values()):
        raise ConflictError(
            f"{question_id}: die Frage ist nach den bisherigen Angaben ausgeblendet."
        )
    _check_value(question, answer.value, answer.justification)
    data = copy.deepcopy(dict(activity))
    state = dict(_state(data))
    raw = state.get("antworten")
    answers: dict[str, object] = dict(raw) if isinstance(raw, Mapping) else {}
    answers[question_id] = answer.to_dict()
    state["antworten"] = answers
    data[STATE_KEY] = state
    _apply_targets(catalog, data, context)
    return data


def confirm_answer(
    catalog: WizardCatalog,
    activity: Mapping[str, object],
    context: Mapping[str, str],
    question_id: str,
    actor: str,
    at: datetime,
) -> dict[str, object]:
    """A person adopts a template or AI suggestion; only then it acts (T-33)."""
    answers = stored_answers(activity)
    if question_id not in answers:
        raise ValidationError(f"{question_id}: es gibt keinen Vorschlag zu bestätigen.")
    old = answers[question_id]
    confirmed = WizardAnswer(old.value, old.justification, actor, at.isoformat(), CONFIRMED)
    return record_answer(catalog, activity, context, question_id, confirmed)


def _step_status(
    questions: tuple[QuestionDef, ...],
    answers: Mapping[str, WizardAnswer],
    values: Mapping[str, str],
) -> str:
    """``vollstaendig``, ``klaerung`` (unclear or unconfirmed) or ``offen``."""
    status = "vollstaendig"
    for question in questions:
        answer = answers.get(question.id)
        if answer is not None and (answer.value == UNCLEAR or not answer.confirmed):
            return "klaerung"
        if question.required and question.id not in values:
            status = "offen"
    return status


def _task(step_id: str, question: QuestionDef, kind: str) -> dict[str, str]:
    return {"step": step_id, "question": question.id, "kind": kind, "number": question.number}


def tasks(
    catalog: WizardCatalog, activity: Mapping[str, object], context: Mapping[str, str]
) -> tuple[dict[str, str], ...]:
    """Open work from the wizard: unclear, unconfirmed and missing required answers."""
    answers = stored_answers(activity)
    values = current_values(catalog, activity, context)
    found: list[dict[str, str]] = []
    for step_id, questions in visible_questions(catalog, activity, context).items():
        for question in questions:
            answer = answers.get(question.id)
            if answer is not None and answer.value == UNCLEAR:
                found.append(_task(step_id, question, "unklar"))
            elif answer is not None and answer.value in question.task_if:
                found.append(_task(step_id, question, "offene_punkte"))
            elif answer is not None and not answer.confirmed:
                found.append(_task(step_id, question, "unbestaetigt"))
            elif question.required and question.id not in values:
                found.append(_task(step_id, question, "fehlt"))
    return tuple(found)


def hidden_answers(
    catalog: WizardCatalog, activity: Mapping[str, object], context: Mapping[str, str]
) -> tuple[str, ...]:
    """Answers kept for history whose question is hidden now; they no longer act."""
    visible = {q.id for qs in visible_questions(catalog, activity, context).values() for q in qs}
    return tuple(sorted(set(stored_answers(activity)) - visible))


def _mode_and_step(activity: Mapping[str, object], steps: list[str]) -> tuple[str, str]:
    state = _state(activity)
    mode = str(state.get("modus") or MODE_GUIDED)
    step = str(state.get("schritt") or (steps[0] if steps else ""))
    return mode, step if step in steps else (steps[0] if steps else "")


def view(
    catalog: WizardCatalog, activity: Mapping[str, object], context: Mapping[str, str]
) -> dict[str, object]:
    """Everything the user interface needs to render the wizard or the free editor."""
    visible = visible_questions(catalog, activity, context)
    answers = stored_answers(activity)
    values = current_values(catalog, activity, context)
    mode, current = _mode_and_step(activity, list(visible))
    steps = [_step_view(catalog.step(sid), qs, answers, values) for sid, qs in visible.items()]
    order = list(visible)
    index = order.index(current) if current in order else 0
    return {
        "catalog_version": catalog.version,
        "mode": mode,
        "current_step": current,
        "previous_step": order[index - 1] if index > 0 else None,
        "next_step": order[index + 1] if index + 1 < len(order) else None,
        "steps": steps,
        "tasks": list(tasks(catalog, activity, context)),
        "hidden_answers": list(hidden_answers(catalog, activity, context)),
    }


def _step_view(
    step: StepDef,
    questions: tuple[QuestionDef, ...],
    answers: Mapping[str, WizardAnswer],
    values: Mapping[str, str],
) -> dict[str, object]:
    return {
        "id": step.id,
        "title": step.title,
        "goal": step.goal,
        "status": _step_status(questions, answers, values),
        "questions": [
            {
                **q.to_dict(),
                "value": values.get(q.id),
                "answer": None if q.id not in answers else answers[q.id].to_dict(),
            }
            for q in questions
        ],
    }


def navigate(
    catalog: WizardCatalog,
    activity: Mapping[str, object],
    context: Mapping[str, str],
    *,
    mode: str,
    step: str,
) -> dict[str, object]:
    """Switch mode or step; guided mode moves one step forward or back to visited steps."""
    if mode not in MODES:
        raise ValidationError(f"Unbekannter Modus „{mode}“; zulässig: {', '.join(MODES)}.")
    order = list(visible_questions(catalog, activity, context))
    if step not in order:
        raise ValidationError(f"Schritt „{step}“ ist nicht verfügbar.")
    old_mode, current = _mode_and_step(activity, order)
    state = dict(_state(activity))
    seen = state.get("besucht")
    visited = [s for s in seen if isinstance(s, str)] if isinstance(seen, list) else []
    if mode == MODE_GUIDED and old_mode == MODE_GUIDED:
        allowed = {*visited, current, *order[order.index(current) + 1 : order.index(current) + 2]}
        if step not in allowed:
            raise ConflictError(
                "Im geführten Modus geht es schrittweise weiter; für freie Navigation "
                "den freien Modus wählen."
            )
    data = copy.deepcopy(dict(activity))
    state.update(modus=mode, schritt=step, besucht=sorted({*visited, current, step}))
    data[STATE_KEY] = state
    return data


def screening_answers(activity: Mapping[str, object]) -> dict[str, dict[str, str]]:
    """Confirmed W09 answers for the threshold analysis; "unklar" becomes "unbekannt"."""
    result: dict[str, dict[str, str]] = {}
    for question_id, answer in stored_answers(activity).items():
        if not question_id.startswith("W09:") or not answer.confirmed:
            continue
        value = "unbekannt" if answer.value == UNCLEAR else answer.value
        result[question_id.removeprefix("W09:")] = {
            "value": value,
            "justification": answer.justification,
        }
    return result


def assessment_texts(catalog: WizardCatalog, activity: Mapping[str, object]) -> dict[str, str]:
    """Confirmed DPIA texts (``assessment:<field>``) entered in the wizard."""
    result: dict[str, str] = {}
    for question_id, answer in stored_answers(activity).items():
        question = catalog.find(question_id)
        if (
            question is not None
            and question.target.startswith("assessment:")
            and answer.confirmed
            and answer.value not in (UNCLEAR, NOT_APPLICABLE)
        ):
            result[question.target.removeprefix("assessment:")] = answer.value
    return result
