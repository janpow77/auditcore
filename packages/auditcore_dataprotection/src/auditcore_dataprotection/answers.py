"""Survey input of a DPIA: answers and risk scenarios, validated at the boundary.

Unknown keys, non-boolean answers, values outside the scale and duplicate
criteria or measures are rejected instead of being skipped. Missing or unknown
answers never count as "no".
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TypedDict, cast

from .errors import ValidationError
from .rules import RuleProfile


class AnswerValue(StrEnum):
    """Explicit three-valued answer; ``UNKNOWN`` is never treated as ``NO``."""

    YES = "ja"
    NO = "nein"
    UNKNOWN = "unbekannt"


@dataclass(frozen=True)
class Answer:
    """Answer of the responsible department with its justification."""

    value: AnswerValue
    justification: str = ""

    def to_dict(self) -> dict[str, str]:
        """JSON-serialisable form of the answer."""
        return {"value": self.value.value, "justification": self.justification}


#: Scenario fields that only schema 2 profiles accept (EDPB template, section 4).
EDPB_SCENARIO_FIELDS = (
    "risk_source",
    "modulating_factors",
    "acceptance_inherent",
    "acceptance_residual",
    "acceptance_note",
)
_SCENARIO_FIELDS = frozenset(
    {
        "dimension",
        "description",
        "severity",
        "likelihood",
        "measures",
        "residual_severity",
        "residual_likelihood",
        "residual_justification",
        *EDPB_SCENARIO_FIELDS,
    }
)
_ANSWER_FIELDS = frozenset({"ja", "value", "begruendung", "justification"})


@dataclass(frozen=True)
class Scenario:
    """Risk scenario of one protection dimension, gross and optionally explicit net."""

    dimension: str
    description: str
    severity: int
    likelihood: int
    measures: tuple[str, ...] = ()
    residual_severity: int | None = None
    residual_likelihood: int | None = None
    residual_justification: str = ""
    risk_source: str = ""
    modulating_factors: str = ""
    acceptance_inherent: str | None = None
    acceptance_residual: str | None = None
    acceptance_note: str = ""

    def to_dict(self) -> dict[str, object]:
        """JSON-serialisable form of the scenario.

        The schema 2 fields (EDPB template 4.1) appear only when they are set,
        so schema 1 scenarios serialise exactly as before.
        """
        data: dict[str, object] = {
            "dimension": self.dimension,
            "description": self.description,
            "severity": self.severity,
            "likelihood": self.likelihood,
            "measures": list(self.measures),
            "residual_severity": self.residual_severity,
            "residual_likelihood": self.residual_likelihood,
            "residual_justification": self.residual_justification,
        }
        for name in EDPB_SCENARIO_FIELDS:
            value = getattr(self, name)
            if value not in (None, ""):
                data[name] = value
        return data


class EdpbScenarioFields(TypedDict):
    """Validated schema 2 scenario fields (EDPB template, section 4.1)."""

    risk_source: str
    modulating_factors: str
    acceptance_note: str
    acceptance_inherent: str | None
    acceptance_residual: str | None


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------


def _answer_from_mapping(key: str, raw: Mapping[object, object]) -> Answer:
    """``{"ja"|"value": ..., "begruendung"|"justification": ...}``."""
    unexpected = set(raw) - _ANSWER_FIELDS
    if unexpected:
        raise ValidationError(
            f"Antwort zu '{key}' enthält unbekannte Felder: "
            f"{', '.join(sorted(cast('set[str]', unexpected)))}."
        )
    justification = raw.get("justification", raw.get("begruendung", "")) or ""
    if not isinstance(justification, str):
        raise ValidationError(f"Die Begründung zu '{key}' muss Text sein.")
    inner = _answer(key, raw["value"] if "value" in raw else raw.get("ja"))
    return Answer(inner.value, justification)


def _answer(key: str, raw: object) -> Answer:
    if isinstance(raw, Answer):
        return raw
    if isinstance(raw, AnswerValue):
        return Answer(raw)
    if raw is None:
        return Answer(AnswerValue.UNKNOWN)
    if isinstance(raw, bool):
        return Answer(AnswerValue.YES if raw else AnswerValue.NO)
    if isinstance(raw, str) and raw in {v.value for v in AnswerValue}:
        return Answer(AnswerValue(raw))
    if isinstance(raw, Mapping):
        return _answer_from_mapping(key, raw)
    raise ValidationError(
        f"Antwort zu '{key}' muss ja/nein (True/False) oder ausdrücklich unbekannt sein, "
        f"war: {raw!r}. Zeichenketten wie 'false' werden nicht umgedeutet."
    )


def parse_answers(raw: Mapping[str, object], profile: RuleProfile) -> dict[str, Answer]:
    """Validate answers keyed by question.

    Accepted values: ``True``/``False``, ``None``/``"unbekannt"`` (explicit
    unknown), ``"ja"``/``"nein"``, :class:`Answer`, or a mapping with ``ja`` or
    ``value`` and an optional ``begruendung``/``justification``.

    Raises:
        ValidationError: not a mapping, unknown question keys or non-boolean values.
    """
    if not isinstance(raw, Mapping):
        raise ValidationError("Antworten sind als Zuordnung Frage → Antwort zu übergeben.")
    known = set(profile.question_keys)
    unknown_keys = sorted(str(k) for k in raw if k not in known)
    if unknown_keys:
        raise ValidationError(
            f"Unbekannte Fragen für Profil {profile.id} {profile.version}: "
            f"{', '.join(unknown_keys)}."
        )
    return {key: _answer(key, value) for key, value in raw.items()}


def parse_answer_list(
    items: Iterable[tuple[str, object]], profile: RuleProfile
) -> dict[str, Answer]:
    """Validate ``(key, answer)`` pairs; a criterion given twice is an error."""
    collected: dict[str, object] = {}
    duplicates: list[str] = []
    for key, value in items:
        if key in collected:
            duplicates.append(key)
        collected[key] = value
    if duplicates:
        raise ValidationError(
            f"Kriterien sind mehrfach beantwortet: {', '.join(sorted(set(duplicates)))}. "
            "Jede Frage darf genau einmal beantwortet werden."
        )
    return parse_answers(collected, profile)


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def _level(value: object, label: str, profile: RuleProfile) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(
            f"{label} muss eine ganze Zahl von {profile.scale_min} bis {profile.scale_max} sein, "
            f"war: {value!r}."
        )
    if not profile.scale_min <= value <= profile.scale_max:
        raise ValidationError(
            f"{label} ist auf einer Skala von {profile.scale_min} bis {profile.scale_max} "
            f"einzustufen, war: {value}."
        )
    return value


def _optional_level(value: object, label: str, profile: RuleProfile) -> int | None:
    return None if value is None else _level(value, label, profile)


def _scenario_measures(
    index: int, raw: Mapping[str, object], profile: RuleProfile
) -> tuple[str, ...]:
    """Catalogue measures of a scenario; unknown or repeated measures are refused."""
    measures = raw.get("measures") or ()
    if isinstance(measures, str) or not isinstance(measures, Sequence):
        raise ValidationError(f"Risikoszenario {index}: Maßnahmen sind als Liste anzugeben.")
    known = {m.key for m in profile.measures}
    unknown = sorted({str(m) for m in measures if m not in known})
    if unknown:
        raise ValidationError(f"Risikoszenario {index}: unbekannte Maßnahmen {', '.join(unknown)}.")
    if len(set(measures)) != len(measures):
        raise ValidationError(
            f"Risikoszenario {index}: eine Maßnahme ist mehrfach angegeben; sie wirkt nur einmal."
        )
    return tuple(str(m) for m in measures)


def _scenario_mapping(index: int, raw: object) -> Mapping[str, object]:
    """Raw scenario as a mapping with known fields only."""
    if isinstance(raw, Scenario):
        raw = raw.to_dict()
    if not isinstance(raw, Mapping):
        raise ValidationError(f"Risikoszenario {index} ist keine Zuordnung.")
    unexpected = set(raw) - _SCENARIO_FIELDS
    if unexpected:
        raise ValidationError(
            f"Risikoszenario {index} enthält unbekannte Felder: "
            f"{', '.join(sorted(cast('set[str]', unexpected)))}."
        )
    return raw


def _scenario(index: int, raw: object, profile: RuleProfile) -> Scenario:
    data = _scenario_mapping(index, raw)
    dimension = data.get("dimension")
    if dimension not in profile.dimensions:
        raise ValidationError(f"Risikoszenario {index}: unbekanntes Schutzziel {dimension!r}.")
    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ValidationError(f"Risikoszenario {index} braucht eine Beschreibung.")
    measures = _scenario_measures(index, data, profile)
    justification = data.get("residual_justification") or ""
    if not isinstance(justification, str):
        raise ValidationError(f"Risikoszenario {index}: Begründung des Restwerts muss Text sein.")
    extra = _edpb_scenario_fields(index, data, profile)
    severity = _level(data.get("severity"), "Schwere", profile)
    likelihood = _level(data.get("likelihood"), "Eintrittswahrscheinlichkeit", profile)
    return Scenario(
        dimension=str(dimension),
        description=description.strip(),
        severity=severity,
        likelihood=likelihood,
        measures=measures,
        residual_severity=_optional_level(data.get("residual_severity"), "Rest-Schwere", profile),
        residual_likelihood=_optional_level(
            data.get("residual_likelihood"), "Rest-Wahrscheinlichkeit", profile
        ),
        residual_justification=justification.strip(),
        **extra,
    )


def _edpb_text(index: int, name: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"Risikoszenario {index}: '{name}' muss Text sein.")
    return value.strip()


def _edpb_acceptance(index: int, value: object, profile: RuleProfile) -> str | None:
    if value is not None and value not in profile.acceptance_levels:
        raise ValidationError(
            f"Risikoszenario {index}: unbekannte Bewertung {value!r}. Zulässig sind: "
            f"{', '.join(profile.acceptance_levels)}."
        )
    return None if value is None else str(value)


def _edpb_scenario_fields(
    index: int, raw: Mapping[str, object], profile: RuleProfile
) -> EdpbScenarioFields:
    """Validate risk source, modulating factors and acceptance (schema 2 only)."""
    given = {
        name: raw.get(name) for name in EDPB_SCENARIO_FIELDS if raw.get(name) not in (None, "")
    }
    if given and not profile.edpb:
        raise ValidationError(
            f"Risikoszenario {index}: {', '.join(sorted(given))} kennt nur ein Profil nach "
            "der EDSA-Vorlage (Schema 2)."
        )
    return {
        "risk_source": _edpb_text(index, "risk_source", given.get("risk_source", "")),
        "modulating_factors": _edpb_text(
            index, "modulating_factors", given.get("modulating_factors", "")
        ),
        "acceptance_note": _edpb_text(index, "acceptance_note", given.get("acceptance_note", "")),
        "acceptance_inherent": _edpb_acceptance(index, given.get("acceptance_inherent"), profile),
        "acceptance_residual": _edpb_acceptance(index, given.get("acceptance_residual"), profile),
    }


def parse_scenarios(raw: Iterable[object], profile: RuleProfile) -> tuple[Scenario, ...]:
    """Validate risk scenarios strictly against the profile scale and catalogues."""
    if isinstance(raw, (str, bytes, Mapping)):
        raise ValidationError("Risikoszenarien sind als Liste zu übergeben.")
    return tuple(_scenario(i, item, profile) for i, item in enumerate(raw, start=1))
