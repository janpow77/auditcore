"""Package-wise coverage ratchet backed by ``quality/baseline.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from auditcore.tools.quality.codegate import discover_packages
from auditcore.tools.quality.codegate_ratchet import Baseline, packages_of

COVERAGE = "coverage_percent"
COVERAGE_JUSTIFICATION = "coverage_ausnahme_begruendung"


@dataclass(frozen=True)
class CoverageVerdict:
    """Comparison result for one package's statement coverage."""

    package: str
    baseline: float
    current: float
    status: str
    message: str

    def to_dict(self) -> dict[str, object]:
        """Serialize for the machine-readable report."""
        return dict(self.__dict__)


def _package_roots(root: Path) -> list[tuple[str, Path]]:
    roots = [
        (package.name, package.path.resolve())
        for package in discover_packages(root)
        if package.kind == "python"
    ]
    return sorted(roots, key=lambda item: len(item[1].parts), reverse=True)


def read_package_coverage(
    root: Path, path: Path, selected: set[str] | None = None
) -> dict[str, float]:
    """Aggregate a coverage.py JSON report by discovered Python package."""
    report = json.loads(path.read_text(encoding="utf-8"))
    totals: dict[str, list[int]] = {}
    roots = [
        (name, source) for name, source in _package_roots(root) if not selected or name in selected
    ]
    for filename, data in report.get("files", {}).items():
        relative = Path(filename)
        candidates = [relative] if relative.is_absolute() else [root / relative]
        if selected and len(roots) == 1 and not relative.is_absolute():
            candidates.append(roots[0][1].parent / relative)
        source = next(
            (
                candidate.resolve()
                for candidate in candidates
                if any(
                    candidate.resolve().is_relative_to(package_root) for _, package_root in roots
                )
            ),
            candidates[0].resolve(),
        )
        package = (
            next(iter(selected))
            if selected and len(selected) == 1
            else next(
                (name for name, package_root in roots if source.is_relative_to(package_root)), None
            )
        )
        if package is None:
            continue
        summary = data.get("summary", {})
        statements = int(summary.get("num_statements", 0))
        covered = int(summary.get("covered_lines", 0))
        aggregate = totals.setdefault(package, [0, 0])
        aggregate[0] += covered
        aggregate[1] += statements
    return {
        package: round(covered * 100 / statements, 2) if statements else 100.0
        for package, (covered, statements) in totals.items()
    }


def recorded_coverage(baseline: Baseline) -> dict[str, float]:
    """Return package coverage values recorded in the shared baseline."""
    result = {}
    for package, entry in packages_of(baseline).items():
        value = entry.get(COVERAGE) if isinstance(entry, dict) else None
        if isinstance(value, int | float):
            result[package] = float(value)
    return result


def compare_coverage(
    current: dict[str, float], baseline: Baseline, selected: set[str] | None = None
) -> list[CoverageVerdict]:
    """Fail on regressions and on improvements not yet recorded in the baseline."""
    recorded = recorded_coverage(baseline)
    verdicts = []
    packages = set(current) | set(recorded)
    for package in sorted(packages if not selected else packages & selected):
        old, new = recorded.get(package), current.get(package)
        if old is None:
            verdicts.append(
                CoverageVerdict(package, 100.0, new or 0.0, "FAIL", "Coverage-Baseline fehlt")
            )
        elif new is None:
            verdicts.append(
                CoverageVerdict(package, old, 0.0, "FAIL", "Paket fehlt im Coverage-Bericht")
            )
        elif new < old:
            message = f"gesunken von {old:.2f}% auf {new:.2f}%"
            verdicts.append(CoverageVerdict(package, old, new, "FAIL", message))
        elif new > old:
            message = "gestiegen: Baseline im selben PR anheben (--update-baseline)"
            verdicts.append(CoverageVerdict(package, old, new, "FAIL", message))
        else:
            verdicts.append(CoverageVerdict(package, old, new, "PASS", "unverändert"))
    return verdicts


def compare_coverage_reference(
    baseline: Baseline, reference: Baseline | None, selected: set[str] | None = None
) -> list[CoverageVerdict]:
    """Reject a lowered committed threshold unless it has an explicit reason."""
    if reference is None:
        return []
    current, previous = recorded_coverage(baseline), recorded_coverage(reference)
    verdicts = []
    for package, old in previous.items():
        if selected and package not in selected:
            continue
        new = current.get(package, 0.0)
        if new >= old:
            continue
        entry = packages_of(baseline).get(package, {})
        reason = entry.get(COVERAGE_JUSTIFICATION, "") if isinstance(entry, dict) else ""
        status = "WARN" if str(reason).strip() else "FAIL"
        message = f"ABSENKUNG {old:.2f}% -> {new:.2f}%"
        message += f", begründet: {reason}" if reason else f" ohne {COVERAGE_JUSTIFICATION}"
        verdicts.append(CoverageVerdict(package, old, new, status, message))
    return verdicts


def update_coverage(baseline: Baseline, current: dict[str, float]) -> Baseline:
    """Raise coverage thresholds; never lower or invent measurements."""
    packages = {name: dict(entry) for name, entry in packages_of(baseline).items()}
    recorded = recorded_coverage(baseline)
    bootstrap = not recorded
    for package, value in current.items():
        initial = value if bootstrap or package in packages else 100.0
        entry = packages.setdefault(package, {})
        # A genuinely new package starts at the standard of 100%, not at its
        # first (possibly incomplete) measurement. Existing packages may adopt
        # their first measurement during the one-time rollout.
        entry[COVERAGE] = max(recorded.get(package, initial), value)
    return {**baseline, "packages": dict(sorted(packages.items()))}
