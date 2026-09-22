"""Prüfergebnisse / Immutable, serializable verification records."""

from dataclasses import dataclass, field
from enum import StrEnum


class CheckStatus(StrEnum):
    """Prüfstatus / Distinguishes observed success from missing evidence."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_EXECUTED = "NOT_EXECUTED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_APPLICABLE_WITH_REASON = "NOT_APPLICABLE_WITH_REASON"
    PASS_WITH_DEVIATION = "PASS_WITH_DEVIATION"


@dataclass(frozen=True)
class CheckResult:
    """Einzelbefund / Finding without sensitive matched content."""

    code: str
    status: CheckStatus
    message: str
    path: str = ""
    line: int = 0
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    """Validierung / Aggregate retaining every individual finding."""

    checks: tuple[CheckResult, ...] = field(default_factory=tuple)

    @property
    def valid(self) -> bool:
        """Erfolg / Return whether all required checks actually passed."""
        return bool(self.checks) and all(
            c.status in {CheckStatus.PASS, CheckStatus.NOT_APPLICABLE_WITH_REASON}
            for c in self.checks
        )
