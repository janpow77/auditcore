"""Question catalogue of the guided wizard (steps W01 to W12), packaged as data.

The catalogue is data, not code. Each question names its answer kind, help
text ("Warum wird das gefragt?"), an optional visibility condition and the
target it writes to: a register field (``register:<field>``), a screening
question of the selected rule profile (``screening:<key>``) or a DPIA text
(``assessment:<field>``). Step W09 receives the screening questions of the
profile, so the wizard and the threshold analysis share one set of answers.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from importlib.resources import files
from typing import cast

from .errors import ProfileError
from .rules import RuleProfile

KIND_YES_NO = "ja_nein_unklar"
KIND_TEXT = "text"
KIND_CHOICE = "auswahl"
KIND_IMPLEMENTATION = "umsetzung"
KIND_NUMBER = "zahl"
KIND_TABLE = "tabelle"
KINDS = frozenset(
    {KIND_YES_NO, KIND_TEXT, KIND_CHOICE, KIND_IMPLEMENTATION, KIND_NUMBER, KIND_TABLE}
)

YES, NO, UNCLEAR = "ja", "nein", "unklar"
NOT_APPLICABLE = "nicht_anwendbar"
IMPLEMENTATION_VALUES = ("nicht_begonnen", "geplant", "umgesetzt", "wirksam_nachgewiesen")

CATALOG_FILE = "wizard-2026.10.2.json"
SCREENING_STEP = "W09"

_Json = Mapping[str, object]


@dataclass(frozen=True)
class Condition:
    """Show only if a question answer or a context value is one of ``values``."""

    question: str | None
    context: str | None
    values: tuple[str, ...]


@dataclass(frozen=True)
class QuestionDef:
    """One wizard question."""

    id: str
    text: str
    kind: str
    target: str
    help: str
    required: bool
    na_allowed: bool
    choices: tuple[tuple[str, str], ...] = ()
    show_if: Condition | None = None
    justify_values: tuple[str, ...] = ()
    reference: str = ""
    #: Display number in the decision tree (e.g. "5.4.1") and nesting depth.
    number: str = ""
    depth: int = 0
    #: Hints as bullet points; ``reference`` is the "Fundstelle".
    hints: tuple[str, ...] = ()
    #: Columns of a table answer: (key, title, required).
    columns: tuple[tuple[str, str, bool], ...] = ()

    @property
    def allowed_values(self) -> tuple[str, ...]:
        """Closed value set of yes/no, choice and implementation questions."""
        if self.kind == KIND_YES_NO:
            return (YES, NO, UNCLEAR)
        if self.kind == KIND_IMPLEMENTATION:
            return IMPLEMENTATION_VALUES
        if self.kind == KIND_CHOICE:
            return tuple(key for key, _ in self.choices)
        return ()

    def to_dict(self) -> dict[str, object]:
        """JSON form for the user interface."""
        return {
            "id": self.id,
            "text": self.text,
            "kind": self.kind,
            "target": self.target,
            "help": self.help,
            "required": self.required,
            "na_allowed": self.na_allowed,
            "choices": [{"key": k, "title": t} for k, t in self.choices],
            "justify_values": list(self.justify_values),
            "reference": self.reference,
            "number": self.number,
            "depth": self.depth,
            "hints": list(self.hints),
            "columns": [{"key": k, "title": t, "required": r} for k, t, r in self.columns],
        }


@dataclass(frozen=True)
class StepDef:
    """One wizard step with its questions."""

    id: str
    title: str
    goal: str
    questions: tuple[QuestionDef, ...]
    show_if: Condition | None = None


@dataclass(frozen=True)
class WizardCatalog:
    """Steps in order; question ids are unique across all steps."""

    version: str
    source: str
    steps: tuple[StepDef, ...]

    def find(self, question_id: str) -> QuestionDef | None:
        """Question by id or ``None`` (answers of earlier catalogue versions)."""
        for step in self.steps:
            for question in step.questions:
                if question.id == question_id:
                    return question
        return None

    def question(self, question_id: str) -> QuestionDef:
        """Question by id or ``ProfileError``."""
        found = self.find(question_id)
        if found is None:
            raise ProfileError(f"Unbekannte Frage „{question_id}“ im Assistenten.")
        return found

    def step(self, step_id: str) -> StepDef:
        """Step by id or ``ProfileError``."""
        for step in self.steps:
            if step.id == step_id:
                return step
        raise ProfileError(f"Unbekannter Schritt „{step_id}“ im Assistenten.")

    @property
    def questions(self) -> tuple[QuestionDef, ...]:
        """All questions in step order."""
        return tuple(q for s in self.steps for q in s.questions)


def _condition(raw: object) -> Condition | None:
    if raw is None:
        return None
    data = cast(_Json, raw)
    values = tuple(str(v) for v in cast(Sequence[object], data["in"]))
    question = data.get("question")
    context = data.get("context")
    if (question is None) == (context is None):
        raise ProfileError("Eine Bedingung nennt genau eine Frage oder einen Kontextwert.")
    return Condition(
        None if question is None else str(question),
        None if context is None else str(context),
        values,
    )


def _question(raw: _Json) -> QuestionDef:
    kind = str(raw["kind"])
    if kind not in KINDS:
        raise ProfileError(f"Unbekannte Antwortart „{kind}“.")
    choices = tuple(
        (str(c["key"]), str(c["title"])) for c in cast(Sequence[_Json], raw.get("choices") or ())
    )
    return QuestionDef(
        id=str(raw["id"]),
        text=str(raw["text"]),
        kind=kind,
        target=str(raw.get("target") or ""),
        help=str(raw.get("help") or ""),
        required=bool(raw.get("required", True)),
        na_allowed=bool(raw.get("na_allowed", False)),
        choices=choices,
        show_if=_condition(raw.get("show_if")),
        justify_values=tuple(
            str(v) for v in cast(Sequence[object], raw.get("justify_values") or ())
        ),
        reference=str(raw.get("reference") or ""),
        number=str(raw.get("number") or ""),
        hints=tuple(str(h) for h in cast(Sequence[object], raw.get("hints") or ())),
        columns=tuple(
            (str(c["key"]), str(c["title"]), bool(c.get("required", False)))
            for c in cast(Sequence[_Json], raw.get("columns") or ())
        ),
    )


def _with_depth(questions: tuple[QuestionDef, ...]) -> tuple[QuestionDef, ...]:
    """Nesting depth from the chain of parent questions (decision branches)."""
    depth: dict[str, int] = {}
    result = []
    for q in questions:
        parent = q.show_if.question if q.show_if is not None else None
        depth[q.id] = depth.get(parent, -1) + 1 if parent else 0
        result.append(replace(q, depth=depth[q.id]))
    return tuple(result)


def _step(raw: _Json) -> StepDef:
    return StepDef(
        id=str(raw["id"]),
        title=str(raw["title"]),
        goal=str(raw.get("goal") or ""),
        questions=_with_depth(tuple(_question(q) for q in cast(Sequence[_Json], raw["questions"]))),
        show_if=_condition(raw.get("show_if")),
    )


def catalog_from_dict(data: _Json) -> WizardCatalog:
    """Validate and build a catalogue; duplicate ids raise ``ProfileError``."""
    try:
        steps = tuple(_step(s) for s in cast(Sequence[_Json], data["steps"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ProfileError(f"Fragenkatalog des Assistenten ist fehlerhaft: {exc!r}") from exc
    ids = [q.id for s in steps for q in s.questions]
    if len(ids) != len(set(ids)):
        raise ProfileError("Doppelte Fragekennungen im Assistenten.")
    known = set(ids)
    for question in (q for s in steps for q in s.questions):
        condition = question.show_if
        if condition is not None and condition.question and condition.question not in known:
            raise ProfileError(f"{question.id}: Bedingung verweist auf unbekannte Frage.")
    return WizardCatalog(str(data["version"]), str(data.get("source") or ""), steps)


def load_catalog() -> WizardCatalog:
    """The packaged catalogue."""
    text = files("auditcore_dataprotection.catalogs").joinpath(CATALOG_FILE).read_text("utf-8")
    return catalog_from_dict(cast(_Json, json.loads(text)))


def catalog_for(profile: RuleProfile, base: WizardCatalog | None = None) -> WizardCatalog:
    """Catalogue with the screening questions of the profile inserted into W09."""
    catalog = base or load_catalog()
    screening = tuple(
        QuestionDef(
            id=f"{SCREENING_STEP}:{q.key}",
            text=q.text,
            kind=KIND_YES_NO,
            target=f"screening:{q.key}",
            help=q.explanation,
            required=True,
            na_allowed=False,
            reference=q.reference,
            number=f"9.2.{index}",
            depth=1,
            hints=(q.explanation,) if q.explanation else (),
        )
        for index, q in enumerate(profile.questions, start=1)
    )
    steps = tuple(
        replace(s, questions=(*s.questions[:1], *screening, *s.questions[1:]))
        if s.id == SCREENING_STEP
        else s
        for s in catalog.steps
    )
    return replace(catalog, steps=steps)
