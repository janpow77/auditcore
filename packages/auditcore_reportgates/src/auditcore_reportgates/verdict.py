"""Three-valued gate verdicts and the fail-closed release decision.

A gate that could not check anything is ``not_run``, never ``passed``. A
release is ``passed`` only when every required gate passed; one failed gate
fails the release, one gate that did not run keeps the release ``not_run``.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum


class Verdict(StrEnum):
    """Outcome of a gate."""

    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


@dataclass(frozen=True)
class Finding:
    """One concrete deviation that makes a gate fail."""

    code: str
    message: str
    location: str = ""
    expected: str = ""
    actual: str = ""


@dataclass(frozen=True)
class GateResult:
    """Result of one gate: verdict, reason when not passed, counts and findings."""

    gate: str
    verdict: Verdict
    reason: str = ""
    checked: int = 0
    findings: tuple[Finding, ...] = field(default=())

    @property
    def passed(self) -> bool:
        """``True`` only for ``Verdict.PASSED``."""
        return self.verdict is Verdict.PASSED


def decide(gate: str, checked: int, findings: Sequence[Finding], *, reason: str = "") -> GateResult:
    """Verdict from counts: findings fail, nothing checked is ``not_run``."""
    if findings:
        return GateResult(gate, Verdict.FAILED, reason or "abweichung", checked, tuple(findings))
    if checked <= 0:
        return GateResult(gate, Verdict.NOT_RUN, reason or "nichts_pruefbar", 0, ())
    return GateResult(gate, Verdict.PASSED, "", checked, ())


@dataclass(frozen=True)
class ReleaseDecision:
    """Fail-closed combination of the required gates."""

    verdict: Verdict
    failed: tuple[str, ...]
    not_run: tuple[str, ...]
    missing: tuple[str, ...]
    results: tuple[GateResult, ...]

    @property
    def released(self) -> bool:
        """``True`` only when every required gate passed."""
        return self.verdict is Verdict.PASSED


def _reject_duplicates(kind: str, names: Sequence[str]) -> None:
    counts = Counter(names)
    doubled = sorted(name for name, count in counts.items() if count > 1)
    if doubled:
        raise ValueError(f"{kind} doppelt: {', '.join(doubled)}")


def release(results: Iterable[GateResult], required: Sequence[str]) -> ReleaseDecision:
    """Combine gate results; a required gate without result counts as not run.

    Raises ``ValueError`` when ``required`` is empty (a release without any
    required gate would pass without evidence) and when a gate name occurs
    twice in ``results`` or ``required`` (one result would silently replace
    the other).
    """
    if not required:
        raise ValueError("Mindestens ein Pflicht-Gate ist anzugeben.")
    _reject_duplicates("Pflicht-Gate", required)
    results = tuple(results)
    _reject_duplicates("Gate-Ergebnis", [result.gate for result in results])
    by_gate = {result.gate: result for result in results}
    missing = tuple(gate for gate in required if gate not in by_gate)
    present = tuple(by_gate[gate] for gate in required if gate in by_gate)
    failed = tuple(r.gate for r in present if r.verdict is Verdict.FAILED)
    not_run = tuple(r.gate for r in present if r.verdict is Verdict.NOT_RUN) + missing
    if failed:
        verdict = Verdict.FAILED
    elif not_run:
        verdict = Verdict.NOT_RUN
    else:
        verdict = Verdict.PASSED
    return ReleaseDecision(verdict, failed, not_run, missing, present)
