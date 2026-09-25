"""Ratchet of an app's helper findings against ``.auditcore/helpers-baseline.json``.

Every finding has a line-independent key (library duplicate, lint finding,
contract violation). Like the code-quality gate:

* a key above its baseline count -> FAIL (new duplicate, pattern or violation);
* a key below its baseline count -> FAIL until ``--update-baseline`` lowers it;
* raising a baseline entry against a reference revision needs
  ``ausnahme_begruendung[key]``.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from auditcore.tools.helpers.model import (
    HelperToolError,
    as_dict,
    as_int,
    as_str,
    read_json,
    write_json,
)

SCHEMA_VERSION = 1
JUSTIFICATION = "ausnahme_begruendung"
Baseline = dict[str, object]


@dataclass(frozen=True)
class Verdict:
    """Ratchet result of one key."""

    key: str
    baseline: int
    current: int
    status: str
    message: str

    def to_dict(self) -> dict[str, object]:
        """Serialize for the JSON report."""
        return dict(self.__dict__)


def empty_baseline() -> Baseline:
    """A baseline without entries."""
    return {"schema_version": SCHEMA_VERSION, "tool": "auditcore-helpers", "entries": {}}


def parse_baseline(data: object) -> Baseline:
    """Validate a loaded baseline document."""
    document = as_dict(data)
    if document.get("schema_version") != SCHEMA_VERSION or not isinstance(
        document.get("entries"), dict
    ):
        raise HelperToolError("Nicht unterstütztes Format der Helfer-Baseline")
    return document


def load_baseline(path: Path) -> Baseline | None:
    """Read the baseline; ``None`` when the app has none yet."""
    return parse_baseline(read_json(path)) if path.is_file() else None


def entries(baseline: Baseline | None) -> Counter[str]:
    """Recorded counts per key."""
    raw = as_dict(baseline.get("entries")) if baseline else {}
    return Counter({key: as_int(value) for key, value in raw.items() if as_int(value) > 0})


def compare(current: Counter[str], baseline: Baseline, labels: dict[str, str]) -> list[Verdict]:
    """Compare current key counts with the baseline."""
    recorded = entries(baseline)
    verdicts = []
    for key in sorted(set(current) | set(recorded)):
        old, new = recorded.get(key, 0), current.get(key, 0)
        label = labels.get(key, key)
        if new > old:
            verdicts.append(Verdict(key, old, new, "FAIL", f"neu ({old} → {new}): {label}"))
        elif new < old:
            message = (
                f"behoben ({old} → {new}): Baseline im selben Stand absenken (--update-baseline)"
            )
            verdicts.append(Verdict(key, old, new, "FAIL", message))
    return verdicts


def update_baseline(baseline: Baseline, current: Counter[str]) -> Baseline:
    """Lower (never raise) every entry to the measured count."""
    recorded = entries(baseline)
    lowered = {key: min(value, current.get(key, 0)) for key, value in recorded.items()}
    reasons = as_dict(baseline.get(JUSTIFICATION))
    kept = {key: reason for key, reason in reasons.items() if lowered.get(key, 0) > 0}
    result: Baseline = {**baseline, "entries": {k: v for k, v in sorted(lowered.items()) if v > 0}}
    if kept:
        result[JUSTIFICATION] = kept
    else:
        result.pop(JUSTIFICATION, None)
    return result


def initial_baseline(current: Counter[str]) -> Baseline:
    """Record today's state once (only allowed when no baseline exists)."""
    baseline = empty_baseline()
    baseline["entries"] = dict(sorted(current.items()))
    return baseline


def write_baseline(path: Path, baseline: Baseline) -> None:
    """Write the baseline deterministically."""
    write_json(path, baseline)


def baseline_from_git(root: Path, ref: str, relative: str) -> Baseline | None:
    """Baseline of a reference revision (``None`` if the file did not exist there)."""
    process = subprocess.run(  # nosec B603 B607
        ["git", "-C", str(root), "show", f"{ref}:{relative}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        return None
    return parse_baseline(json.loads(process.stdout))


def raises(baseline: Baseline, reference: Baseline | None) -> list[Verdict]:
    """Every entry above the reference revision needs a documented reason."""
    if reference is None:
        return [Verdict("*", 0, 0, "WARN", "Erstanlage der Baseline: keine Anhebungsprüfung")]
    before = entries(reference)
    reasons = as_dict(baseline.get(JUSTIFICATION))
    verdicts = []
    for key, value in sorted(entries(baseline).items()):
        old = before.get(key, 0)
        if value <= old:
            continue
        reason = as_str(reasons.get(key)).strip()
        status = "WARN" if reason else "FAIL"
        suffix = f", begründet: {reason}" if reason else f" ohne {JUSTIFICATION}"
        text = f"ANHEBUNG {old} → {value}{suffix}"
        verdicts.append(Verdict(key, old, value, status, text))
    return verdicts


def status_of(verdicts: list[Verdict]) -> str:
    """Overall status: FAIL beats WARN beats PASS."""
    if any(v.status == "FAIL" for v in verdicts):
        return "FAIL"
    return "WARN" if any(v.status == "WARN" for v in verdicts) else "PASS"
