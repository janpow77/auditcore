"""Results of the DSFA calculation: issues, screening, risk and the proposal.

All results are immutable and serialise to JSON-compatible dictionaries that
always name the calculation version and the profile identity they used.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

CALCULATION_VERSION = "auditcore_dataprotection.calculation/1"


@dataclass(frozen=True)
class Issue:
    """Completeness or plausibility note; ``blocking`` issues prevent a release."""

    code: str
    message: str
    blocking: bool
    subject: str = ""

    def to_dict(self) -> dict[str, str | bool]:
        """JSON-serialisable form of the issue."""
        return {
            "code": self.code,
            "message": self.message,
            "blocking": self.blocking,
            "subject": self.subject,
        }


@dataclass(frozen=True)
class ScreeningResult:
    """Result of the threshold analysis with open questions and trace."""

    outcome: str
    points: int
    points_threshold: int
    hard_triggers: tuple[str, ...]
    point_criteria: tuple[str, ...]
    fria_required: bool | None
    unanswered: tuple[str, ...]
    unknown: tuple[str, ...]
    reasoning: str
    trace: tuple[Mapping[str, object], ...]

    @property
    def complete(self) -> bool:
        """True if every question has an explicit yes or no answer."""
        return not self.unanswered and not self.unknown

    def to_dict(self) -> dict[str, object]:
        """Screening part of :meth:`Proposal.to_dict` (without the trace)."""
        return {
            "outcome": self.outcome,
            "points": self.points,
            "points_threshold": self.points_threshold,
            "hard_triggers": list(self.hard_triggers),
            "point_criteria": list(self.point_criteria),
            "fria_required": self.fria_required,
            "unanswered": list(self.unanswered),
            "unknown": list(self.unknown),
            "complete": self.complete,
            "reasoning": self.reasoning,
        }


@dataclass(frozen=True)
class ScenarioResult:
    """Gross and net risk of one scenario with measure effects."""

    index: int
    dimension: str
    dimension_title: str
    sdm: bool
    description: str
    gross_severity: int
    gross_likelihood: int
    gross: int
    gross_band: str
    measures: tuple[str, ...]
    measure_titles: tuple[str, ...]
    reduction_severity: int
    reduction_likelihood: int
    net_severity: int
    net_likelihood: int
    net: int
    net_band: str
    explicit_residual: tuple[str, ...]
    residual_justification: str
    edpb: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Scenario part of :meth:`Proposal.to_dict`; schema 2 fields follow the rest."""
        return {
            "index": self.index,
            "dimension": self.dimension,
            "dimension_title": self.dimension_title,
            "sdm": self.sdm,
            "description": self.description,
            "gross_severity": self.gross_severity,
            "gross_likelihood": self.gross_likelihood,
            "gross": self.gross,
            "gross_band": self.gross_band,
            "measures": list(self.measures),
            "measure_titles": list(self.measure_titles),
            "reduction_severity": self.reduction_severity,
            "reduction_likelihood": self.reduction_likelihood,
            "net_severity": self.net_severity,
            "net_likelihood": self.net_likelihood,
            "net": self.net,
            "net_band": self.net_band,
            "explicit_residual": list(self.explicit_residual),
            "residual_justification": self.residual_justification,
            **dict(self.edpb),
        }


@dataclass(frozen=True)
class RiskResult:
    """Risk of all scenarios with maxima and plausibility issues."""

    scenarios: tuple[ScenarioResult, ...]
    gross_maximum: int
    net_maximum: int
    net_band: str
    issues: tuple[Issue, ...]
    method: str | None = None
    gross_band: str | None = None
    floored: tuple[int, ...] = ()

    @property
    def assessed(self) -> bool:
        """True if at least one scenario was assessed."""
        return bool(self.scenarios)

    def to_dict(self) -> dict[str, object]:
        """Risk part of :meth:`Proposal.to_dict`; the matrix method only for schema 2."""
        data: dict[str, object] = {
            "gross_maximum": self.gross_maximum,
            "net_maximum": self.net_maximum,
            "net_band": self.net_band,
            "scenarios": [s.to_dict() for s in self.scenarios],
        }
        if self.method is not None:
            data.update(method=self.method, gross_band=self.gross_band, floored=list(self.floored))
        return data


@dataclass(frozen=True)
class Proposal:
    """Reasoned recommendation; ``recommendation`` is one of the profile decisions
    or ``unvollstaendig``."""

    profile: Mapping[str, str]
    regime: str
    screening: ScreeningResult
    risk: RiskResult | None
    recommendation: str
    recommendation_text: str
    reasoning: str
    consultation_required: bool
    consultation_reference: str
    issues: tuple[Issue, ...]
    calculation: str = CALCULATION_VERSION
    trace: tuple[Mapping[str, object], ...] = field(default_factory=tuple)
    #: DP-C21: only for profiles with a ``consultation_notice`` section. The
    #: proposal never carries the final notice; see ``finalize_consultation``.
    consultation_notice: Mapping[str, object] | None = None

    @property
    def blocking_issues(self) -> tuple[Issue, ...]:
        """Issues that prevent a release."""
        return tuple(i for i in self.issues if i.blocking)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable proposal including trace and profile identity.

        The result is the stored JSON document of an assessment (``Assessment.proposal``).
        """
        notice = (
            {}
            if self.consultation_notice is None
            else {"consultation_notice": dict(self.consultation_notice)}
        )
        return {
            "calculation": self.calculation,
            "profile": dict(self.profile),
            "regime": self.regime,
            "recommendation": self.recommendation,
            "recommendation_text": self.recommendation_text,
            "reasoning": self.reasoning,
            "consultation_required": self.consultation_required,
            "consultation_reference": self.consultation_reference,
            **notice,
            "issues": [i.to_dict() for i in self.issues],
            "screening": self.screening.to_dict(),
            "risk": None if self.risk is None else self.risk.to_dict(),
            "trace": [dict(t) for t in self.trace],
        }
