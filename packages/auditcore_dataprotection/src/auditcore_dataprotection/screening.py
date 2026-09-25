"""Threshold analysis: hard triggers, EDPB points and the FRIA marker.

Open answers never count as "no": an incomplete survey keeps the outcome
``unvollstaendig`` unless a hard trigger or the point threshold already
decides it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .answers import Answer, AnswerValue, parse_answers
from .results import ScreeningResult
from .rules import EFFECT_FRIA, EFFECT_HARD, EFFECT_POINT, Question, RuleProfile

SCREENING_REQUIRED = "pflicht"
SCREENING_NOT_REQUIRED = "keine_pflicht"
SCREENING_INCOMPLETE = "unvollstaendig"

_FRIA_REASONING = (
    " Zusätzlich handelt es sich um ein Hochrisiko-KI-System; die "
    "Grundrechte-Folgenabschätzung nach Art. 27 der Verordnung (EU) "
    "2024/1689 ist zu erstellen und darf mit dieser Abschätzung "
    "verbunden werden (Art. 27 Abs. 4)."
)


def _hard_trigger_reasoning(profile: RuleProfile, hard: Sequence[str]) -> str:
    """Reasoning when at least one hard trigger was answered with yes."""
    references = "; ".join(profile.question(k).reference for k in hard)
    if profile.regime == "hdsig_ji":
        return (
            f"Die Datenschutz-Folgenabschätzung ist durchzuführen "
            f"({profile.norm('pflicht')}). Erfüllt ist: {references}. "
            "Der Dritte Teil des HDSIG kennt die Regelbeispiele des Art. 35 "
            "Abs. 3 DSGVO und die Liste nach Abs. 4 nicht; sie werden hier "
            "als strengerer Maßstab angewandt, weil die Abgrenzung beider "
            "Rechtsakte auf europäischer Ebene nicht geklärt ist."
        )
    if len(hard) == 1:
        return (
            "Die Datenschutz-Folgenabschätzung ist durchzuführen, weil "
            f"1 Muss-Kriterium bejaht wurde: {references}."
        )
    return (
        "Die Datenschutz-Folgenabschätzung ist durchzuführen, weil "
        f"{len(hard)} Muss-Kriterien bejaht wurden: {references}."
    )


def _screening_outcome(
    profile: RuleProfile, hard: Sequence[str], score: int, unanswered: int, unknown: int
) -> tuple[str, str]:
    """Outcome and reasoning of the threshold analysis; open answers never count as no."""
    threshold = profile.points_threshold
    if hard:
        return SCREENING_REQUIRED, _hard_trigger_reasoning(profile, hard)
    if score >= threshold:
        return SCREENING_REQUIRED, (
            f"Es sind {score} der neun {profile.criteria_label} erfüllt. "
            f"Ab {threshold} Kriterien ist "
            "regelmäßig von einem voraussichtlich hohen Risiko auszugehen "
            "(WP 248 rev.01); die Folgenabschätzung ist durchzuführen."
        )
    if unanswered or unknown:
        return SCREENING_INCOMPLETE, (
            f"Die Schwellwertanalyse ist unvollständig: {unanswered} Fragen sind "
            f"unbeantwortet und {unknown} als unbekannt gekennzeichnet. Bisher sind "
            f"{score} der neun Kriterien bejaht. Ein Ergebnis wird erst nach vollständiger "
            "Erhebung vorgeschlagen; eine fehlende Angabe gilt nicht als Nein."
        )
    return SCREENING_NOT_REQUIRED, (
        f"Kein Muss-Kriterium ist erfüllt und es sind {score} der neun "
        f"{profile.criteria_label} bejaht, also "
        f"weniger als {threshold}. Eine Folgenabschätzung ist damit "
        "nicht erforderlich; das Ergebnis ist gleichwohl zu dokumentieren "
        f"({profile.norm('nachweis')})."
    )


@dataclass
class _Tally:
    """Answers sorted by effect while walking the questions in profile order."""

    hard: list[str] = field(default_factory=list)
    points: list[str] = field(default_factory=list)
    unanswered: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    fria_yes: bool = False
    fria_open: bool = False
    trace: list[dict[str, object]] = field(default_factory=list)

    def count(self, question: Question, answer: Answer | None) -> None:
        """Record one question; only an explicit yes counts for its effect."""
        if answer is None or answer.value is AnswerValue.UNKNOWN:
            (self.unanswered if answer is None else self.unknown).append(question.key)
            self.fria_open = self.fria_open or question.effect == EFFECT_FRIA
            return
        if answer.value is not AnswerValue.YES:
            return
        self.trace.append(
            {
                "step": "criterion",
                "question": question.key,
                "effect": question.effect,
                "reference": question.reference,
            }
        )
        if question.effect == EFFECT_HARD:
            self.hard.append(question.key)
        elif question.effect == EFFECT_POINT:
            self.points.append(question.key)
        elif question.effect == EFFECT_FRIA:
            self.fria_yes = True

    @property
    def fria(self) -> bool | None:
        """FRIA marker: yes, open (``None``) or no."""
        return True if self.fria_yes else (None if self.fria_open else False)


def screen(profile: RuleProfile, answers: Mapping[str, object]) -> ScreeningResult:
    """Evaluate hard triggers, EDSA points and the FRIA marker in profile order."""
    parsed = parse_answers(answers, profile)
    tally = _Tally()
    for question in profile.questions:
        tally.count(question, parsed.get(question.key))
    score = len(tally.points)
    outcome, reasoning = _screening_outcome(
        profile, tally.hard, score, len(tally.unanswered), len(tally.unknown)
    )
    if tally.fria_yes:
        reasoning += _FRIA_REASONING
    tally.trace.append(
        {
            "step": "screening",
            "outcome": outcome,
            "points": score,
            "threshold": profile.points_threshold,
            "open": len(tally.unanswered) + len(tally.unknown),
        }
    )
    return ScreeningResult(
        outcome=outcome,
        points=score,
        points_threshold=profile.points_threshold,
        hard_triggers=tuple(tally.hard),
        point_criteria=tuple(tally.points),
        fria_required=tally.fria,
        unanswered=tuple(tally.unanswered),
        unknown=tuple(tally.unknown),
        reasoning=reasoning,
        trace=tuple(tally.trace),
    )
