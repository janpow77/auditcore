"""DPIA documentation aligned with the EDPB template (2026, version 1.0).

The EDPB template leaves the risk method open and fixes what a DPIA has to
document. Schema 2 profiles carry the corresponding catalogues; this module
validates the additional documentation of an assessment and derives
non-blocking hints. Section numbers refer to the template and its explainer
(adopted on 10 March 2026 for public consultation). Schema 1 profiles reject
every field handled here, so their results stay exactly as before.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from .errors import ValidationError
from .model import Assessment
from .rules import DECISION_REJECTED, RECOMMENDATION_RELEASE, RuleProfile

IMPLEMENTED = "umgesetzt"
_ACCEPTANCE_SECTIONS = (
    ("acceptance_inherent", "Abschnitt 4.1.c, Risiko vor Maßnahmen"),
    ("acceptance_residual", "Abschnitt 4.2.b, Restrisiko"),
)


def reject_edpb_fields(given: Mapping[str, object], rules: RuleProfile) -> None:
    """Refuse EDPB documentation for a schema 1 profile instead of ignoring it."""
    names = sorted(name for name, value in given.items() if value not in (None, {}, (), []))
    if names:
        raise ValidationError(
            f"{', '.join(names)} kennt nur ein Profil nach der EDSA-Vorlage (Schema 2); "
            f"Profil {rules.id} {rules.version} gehört zu Schema 1."
        )


def _iso_date(key: str, value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValidationError(
            f"'{key}' ist als Datum JJJJ-MM-TT anzugeben, war: {value!r}."
        ) from exc


def parse_dossier(raw: Mapping[str, object], rules: RuleProfile) -> dict[str, str]:
    """Validate the DPIA master data (template sections 0.4, 0.5, 1.1.c, 1.4, 2.2.b).

    Unknown keys, non-text values, invalid dates and unknown choices are
    rejected; empty values are dropped.
    """
    if not isinstance(raw, Mapping):
        raise ValidationError("Die Angaben zur Folgenabschätzung sind als Zuordnung zu übergeben.")
    fields = {f.key: f for f in rules.dossier_fields}
    result: dict[str, str] = {}
    for key, value in raw.items():
        field = fields.get(str(key))
        if field is None:
            raise ValidationError(f"Unbekanntes Feld der Folgenabschätzung: {key!r}.")
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValidationError(f"'{field.title}' muss Text sein.")
        text = value.strip()
        if not text:
            continue
        if field.kind == "date":
            text = _iso_date(field.title, text)
        elif field.kind == "choice" and text not in dict(field.choices):
            raise ValidationError(
                f"'{field.title}': unbekannte Auswahl {text!r}. Zulässig sind: "
                f"{', '.join(k for k, _ in field.choices)}."
            )
        result[field.key] = text
    return result


def parse_measure_status(
    raw: Mapping[str, object], rules: RuleProfile
) -> dict[str, dict[str, str]]:
    """Implementation status per catalogue measure (template 2.3 and 4.2.a).

    Accepts ``{measure: status}`` or ``{measure: {"status": ..., "note": ...}}``.
    """
    if not isinstance(raw, Mapping):
        raise ValidationError("Der Umsetzungsstand ist als Zuordnung Maßnahme → Stand anzugeben.")
    known = {m.key for m in rules.measures}
    result: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        if key not in known:
            raise ValidationError(f"Unbekannte Maßnahme im Umsetzungsstand: {key!r}.")
        entry = {"status": value} if isinstance(value, str) else value
        if not isinstance(entry, Mapping) or set(entry) - {"status", "note"}:
            raise ValidationError(
                f"Umsetzungsstand zu '{key}': erwartet wird ein Stand und optional ein Hinweis."
            )
        status = entry.get("status")
        if status not in rules.implementation_states:
            raise ValidationError(
                f"Umsetzungsstand zu '{key}': unbekannter Stand {status!r}. Zulässig sind: "
                f"{', '.join(rules.implementation_states)}."
            )
        note = entry.get("note") or ""
        if not isinstance(note, str):
            raise ValidationError(f"Hinweis zum Umsetzungsstand von '{key}' muss Text sein.")
        result[str(key)] = {"status": str(status), "note": note.strip()}
    return result


_ACTION_PLAN_FIELDS = frozenset({"activity", "responsible", "due", "measure"})


def _action_plan_entry(index: int, item: object, known: set[str]) -> dict[str, str]:
    """One plan entry: activity and responsible required, due date and measure optional."""
    if not isinstance(item, Mapping) or set(item) - _ACTION_PLAN_FIELDS:
        raise ValidationError(
            f"Maßnahmenplan, Eintrag {index}: erwartet werden activity, responsible, "
            "optional due und measure."
        )
    entry: dict[str, str] = {}
    for name in ("activity", "responsible"):
        value = item.get(name)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"Maßnahmenplan, Eintrag {index}: '{name}' fehlt.")
        entry[name] = value.strip()
    due = item.get("due")
    if due not in (None, ""):
        if not isinstance(due, str):
            raise ValidationError(f"Maßnahmenplan, Eintrag {index}: Termin muss Text sein.")
        entry["due"] = _iso_date("Termin", due.strip())
    measure = item.get("measure")
    if measure not in (None, ""):
        if measure not in known:
            raise ValidationError(
                f"Maßnahmenplan, Eintrag {index}: unbekannte Maßnahme {measure!r}."
            )
        entry["measure"] = str(measure)
    return entry


def parse_action_plan(raw: Sequence[object], rules: RuleProfile) -> tuple[dict[str, str], ...]:
    """Plan to add and review measures (template 4.2.c): activity, responsible, due date."""
    if isinstance(raw, (str, bytes, Mapping)) or not isinstance(raw, Sequence):
        raise ValidationError("Der Maßnahmenplan ist als Liste zu übergeben.")
    known = {m.key for m in rules.measures}
    return tuple(_action_plan_entry(index, item, known) for index, item in enumerate(raw, 1))


def _titles(rules: RuleProfile, keys: Sequence[str]) -> str:
    return "; ".join(rules.measure(k).title for k in keys)


def _used_measures(assessment: Assessment) -> list[str]:
    """Measures of all scenarios in first-use order, each once."""
    used: list[str] = []
    for scenario in assessment.scenarios:
        for key in scenario.measures:
            if key not in used:
                used.append(key)
    return used


def _measure_hints(assessment: Assessment, rules: RuleProfile, used: Sequence[str]) -> list[str]:
    """Implementation status and action plan of the measures the scenarios rely on."""
    hints: list[str] = []
    status = assessment.measure_status
    without = [k for k in used if k not in status]
    if without:
        hints.append(
            f"Für diese Maßnahmen ist kein Umsetzungsstand angegeben: {_titles(rules, without)} "
            "(EDSA-Vorlage 2026, Abschnitt 4.2.a)."
        )
    open_ = [k for k in used if k in status and status[k].get("status") != IMPLEMENTED]
    planned = {item.get("measure") for item in assessment.action_plan}
    unplanned = [k for k in open_ if k not in planned]
    if unplanned:
        hints.append(
            "Diese Maßnahmen mindern das Risiko, sind aber noch nicht umgesetzt und stehen "
            f"nicht im Maßnahmenplan: {_titles(rules, unplanned)} (Abschnitt 4.2.c)."
        )
    if open_ and assessment.decision == RECOMMENDATION_RELEASE:
        hints.append(
            "Die Verarbeitung soll ohne Auflagen freigegeben werden, obwohl Maßnahmen, auf "
            "denen die Risikominderung beruht, noch nicht umgesetzt sind. Zu prüfen ist eine "
            "Freigabe mit Auflagen (Abschnitt 6)."
        )
    return hints


def _scenario_hints(assessment: Assessment) -> list[str]:
    """Risk source and acceptance of every scenario (sections 3.1, 4.1 and 4.2)."""
    hints: list[str] = []
    no_source = [str(i) for i, s in enumerate(assessment.scenarios, 1) if not s.risk_source]
    if no_source:
        hints.append(
            f"Szenario {', '.join(no_source)}: Die Risikoquelle ist nicht beschrieben "
            "(Abschnitte 3.1 und 4.1.a)."
        )
    if assessment.decision == DECISION_REJECTED:
        return hints
    for name, sections in _ACCEPTANCE_SECTIONS:
        unrated = [
            str(i)
            for i, scenario in enumerate(assessment.scenarios, 1)
            if getattr(scenario, name) is None
        ]
        if unrated:
            hints.append(
                f"Szenario {', '.join(unrated)}: Es ist nicht festgehalten, ob das Risiko "
                f"hinnehmbar ist ({sections})."
            )
    return hints


def _category_hints(assessment: Assessment, rules: RuleProfile) -> list[str]:
    """Areas of the catalogue without any measure that has an implementation status."""
    status = assessment.measure_status
    covered = {rules.measure(k).category for k in status if rules.measure(k).category}
    offered = {m.category for m in rules.measures}
    missing = [
        title
        for key, (title, _) in rules.measure_categories.items()
        if key in offered and key not in covered
    ]
    if not (assessment.scenarios and missing):
        return []
    return [
        "Für diese Bereiche ist keine Maßnahme mit Umsetzungsstand dokumentiert: "
        + "; ".join(missing)
        + " (Abschnitt 2.3)."
    ]


def edpb_hints(assessment: Assessment, rules: RuleProfile) -> tuple[str, ...]:
    """Non-blocking notes where the documentation falls short of the EDPB template."""
    used = _used_measures(assessment)
    return (
        *_measure_hints(assessment, rules, used),
        *_scenario_hints(assessment),
        *_category_hints(assessment, rules),
    )
