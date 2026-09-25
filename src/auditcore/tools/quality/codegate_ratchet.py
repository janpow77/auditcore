"""Ratchet the code-quality metrics against a committed baseline.

Rules (per package and metric):

* current > baseline  -> FAIL (the metric grew).
* current < baseline  -> FAIL until the baseline is lowered in the same change
  (``--update-baseline``), so the improvement can never be lost again.
* a package missing from the baseline has the baseline 0 for every metric.
* raising a baseline value needs ``ausnahme_begruendung[metric]``; every raise
  against the reference revision is reported visibly, an unjustified one fails.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404
from dataclasses import dataclass
from pathlib import Path

from auditcore.tools.quality.codegate_python import PackageMeasurement

SCHEMA_VERSION = 1
JUSTIFICATION = "ausnahme_begruendung"
VERSION_BOUND_METRICS = {"mypy_strict_errors": "mypy"}

Baseline = dict[str, object]


@dataclass(frozen=True)
class Verdict:
    """Comparison result of one package metric."""

    package: str
    metric: str
    baseline: int
    current: int
    status: str
    message: str

    def to_dict(self) -> dict[str, object]:
        """Serialize for the machine-readable report."""
        return dict(self.__dict__)


def empty_baseline() -> Baseline:
    """Return a new baseline document without packages."""
    return {"schema_version": SCHEMA_VERSION, "tool_versions": {}, "packages": {}}


def load_baseline(path: Path) -> Baseline:
    """Read a baseline file; a missing file means the empty baseline."""
    if not path.is_file():
        return empty_baseline()
    return parse_baseline(path.read_text(encoding="utf-8"))


def parse_baseline(text: str) -> Baseline:
    """Parse and minimally validate a baseline document."""
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported code-quality baseline schema")
    if not isinstance(data.get("packages"), dict):
        raise ValueError("Baseline requires a 'packages' object")
    return data


def packages_of(baseline: Baseline) -> dict[str, dict[str, object]]:
    """Return the package table of a baseline."""
    packages = baseline.get("packages", {})
    return packages if isinstance(packages, dict) else {}


def metrics_of(baseline: Baseline, package: str) -> dict[str, int]:
    """Return the recorded metrics of one package (empty for new packages)."""
    entry = packages_of(baseline).get(package, {})
    metrics = entry.get("metrics", {}) if isinstance(entry, dict) else {}
    return {str(k): int(v) for k, v in metrics.items()} if isinstance(metrics, dict) else {}


def justification(baseline: Baseline, package: str, metric: str) -> str:
    """Return the documented reason for a raised metric, if any."""
    entry = packages_of(baseline).get(package, {})
    reasons = entry.get(JUSTIFICATION, {}) if isinstance(entry, dict) else {}
    reason = reasons.get(metric, "") if isinstance(reasons, dict) else ""
    return str(reason).strip()


def recorded_versions(baseline: Baseline) -> dict[str, str]:
    """Return the tool versions the baseline was measured with."""
    versions = baseline.get("tool_versions", {})
    return {str(k): str(v) for k, v in versions.items()} if isinstance(versions, dict) else {}


def _version_mismatch(metric: str, baseline: Baseline, versions: dict[str, str]) -> bool:
    """True only if the baseline recorded a different version of the measuring tool."""
    tool = VERSION_BOUND_METRICS.get(metric)
    recorded = recorded_versions(baseline).get(tool or "")
    return tool is not None and recorded is not None and recorded != versions.get(tool)


def _verdict(package: str, metric: str, old: int, new: int, soft: bool) -> Verdict:
    if new == old:
        return Verdict(package, metric, old, new, "PASS", "unverändert")
    if new > old:
        status = "WARN" if soft else "FAIL"
        message = f"gestiegen von {old} auf {new}"
        if soft:
            message += " (Werkzeugversion abweichend; Baseline mit --update-baseline erneuern)"
        return Verdict(package, metric, old, new, status, message)
    message = f"gesunken von {old} auf {new}: Baseline im selben PR absenken (--update-baseline)"
    return Verdict(package, metric, old, new, "WARN" if soft else "FAIL", message)


def compare(
    measurements: list[PackageMeasurement],
    baseline: Baseline,
    versions: dict[str, str],
    *,
    complete: bool,
) -> list[Verdict]:
    """Compare measured counts against the baseline (``complete``: all packages measured)."""
    verdicts = []
    for measurement in measurements:
        recorded = metrics_of(baseline, measurement.name)
        for metric, current in sorted(measurement.metrics.items()):
            # New packages must meet every standard, whatever the tool version.
            soft = bool(recorded) and _version_mismatch(metric, baseline, versions)
            old = recorded.get(metric, 0)
            verdicts.append(_verdict(measurement.name, metric, old, current, soft))
    if complete:
        measured = {measurement.name for measurement in measurements}
        for package in sorted(set(packages_of(baseline)) - measured):
            message = "Paket nicht mehr vorhanden: Baseline-Eintrag mit --update-baseline entfernen"
            verdicts.append(Verdict(package, "*", 0, 0, "FAIL", message))
    return verdicts


def baseline_from_git(root: Path, ref: str, relative: str) -> Baseline | None:
    """Load the baseline of a reference revision (``None``: file did not exist there)."""
    process = subprocess.run(  # nosec B603 B607
        ["git", "-C", str(root), "show", f"{ref}:{relative}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode == 0:
        return parse_baseline(process.stdout)
    verify = subprocess.run(  # nosec B603 B607
        ["git", "-C", str(root), "rev-parse", "--verify", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if verify.returncode != 0:
        raise ValueError(f"Reference revision not available: {ref}")
    return None


def raises(baseline: Baseline, reference: Baseline | None) -> list[Verdict]:
    """Report every baseline value that is higher than in the reference revision."""
    if reference is None:
        message = "Erstanlage der Baseline: Referenz ohne Baseline, Anhebungsprüfung entfällt"
        return [Verdict("*", "*", 0, 0, "WARN", message)]
    verdicts = []
    for package in sorted(packages_of(baseline)):
        before = metrics_of(reference, package)
        for metric, value in sorted(metrics_of(baseline, package).items()):
            if before and metric not in before:
                message = f"Einführung der Metrik mit Erstwert {value}"
                verdicts.append(Verdict(package, metric, 0, value, "WARN", message))
                continue
            old = before.get(metric, 0)
            if value <= old:
                continue
            reason = justification(baseline, package, metric)
            if reason:
                message = f"ANHEBUNG {old} -> {value}, begründet: {reason}"
                verdicts.append(Verdict(package, metric, old, value, "WARN", message))
            else:
                message = f"ANHEBUNG {old} -> {value} ohne {JUSTIFICATION}"
                verdicts.append(Verdict(package, metric, old, value, "FAIL", message))
    return verdicts


def _updated_metrics(
    measurement: PackageMeasurement, baseline: Baseline, versions: dict[str, str]
) -> tuple[dict[str, int], dict[str, str]]:
    recorded = metrics_of(baseline, measurement.name)
    metrics = dict(recorded)
    reasons: dict[str, str] = {}
    for metric, current in measurement.metrics.items():
        if recorded and metric not in recorded:
            # A metric introduced after the package was recorded: first measurement.
            metrics[metric] = current
            continue
        old = recorded.get(metric, 0)
        if current > old and _version_mismatch(metric, baseline, versions):
            tool = VERSION_BOUND_METRICS[metric]
            before = recorded_versions(baseline).get(tool, "unbekannt")
            reasons[metric] = f"Werkzeugwechsel {tool} {before} -> {versions.get(tool)}"
        metrics[metric] = current if metric in reasons else min(current, old)
    return metrics, reasons


def update_baseline(
    baseline: Baseline,
    measurements: list[PackageMeasurement],
    versions: dict[str, str],
    *,
    complete: bool,
) -> Baseline:
    """Lower (never raise) the baseline to the measured values.

    Only a changed tool version may raise a version-bound metric; that raise is
    recorded with an automatic justification so the gate reports it visibly.
    """
    packages = {name: dict(entry) for name, entry in packages_of(baseline).items()}
    if complete:
        measured = {measurement.name for measurement in measurements}
        packages = {name: entry for name, entry in packages.items() if name in measured}
    for measurement in measurements:
        metrics, reasons = _updated_metrics(measurement, baseline, versions)
        entry = dict(packages.get(measurement.name, {}))
        entry["metrics"] = dict(sorted(metrics.items()))
        if reasons:
            existing = entry.get(JUSTIFICATION, {})
            merged = dict(existing) if isinstance(existing, dict) else {}
            entry[JUSTIFICATION] = {**merged, **reasons}
        packages[measurement.name] = entry
    merged_versions = {**recorded_versions(baseline), **versions}
    return {
        **baseline,
        "schema_version": SCHEMA_VERSION,
        "tool_versions": dict(sorted(merged_versions.items())),
        "packages": dict(sorted(packages.items())),
    }


def initial_baseline(measurements: list[PackageMeasurement], versions: dict[str, str]) -> Baseline:
    """Record today's state once; later changes go through the ratchet."""
    baseline = empty_baseline()
    baseline["tool_versions"] = dict(sorted(versions.items()))
    baseline["packages"] = {
        m.name: {"metrics": dict(sorted(m.metrics.items()))}
        for m in sorted(measurements, key=lambda item: item.name)
    }
    return baseline


def write_baseline(path: Path, baseline: Baseline) -> None:
    """Write the baseline deterministically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
