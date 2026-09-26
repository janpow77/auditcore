"""Keep an automatic baseline update only when it lowers metrics.

The autofix workflow runs ``auditcore-codegate check --update-baseline``. That
command may also raise version-bound metrics (with an automatic
justification), add or drop packages, or record new tool versions. None of
that may be committed without a human. This script compares the committed
baseline with the updated one and writes a baseline that takes over *only*
decreases; tool versions stay as committed and a version-bound metric is
lowered only when its tool version is unchanged.

Exit code 0: the written baseline differs from the committed one only by
decreases (or not at all). Exit code 1: the update contained anything else;
the committed baseline is written back unchanged.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auditcore.tools.quality.codegate_ratchet import JUSTIFICATION, VERSION_BOUND_METRICS

Baseline = dict[str, object]


def _packages(baseline: Baseline) -> dict[str, dict[str, object]]:
    packages = baseline.get("packages", {})
    return packages if isinstance(packages, dict) else {}


def _metrics(entry: dict[str, object]) -> dict[str, int]:
    metrics = entry.get("metrics", {})
    return metrics if isinstance(metrics, dict) else {}


def _versions(baseline: Baseline) -> dict[str, str]:
    versions = baseline.get("tool_versions", {})
    return versions if isinstance(versions, dict) else {}


def lower_only(committed: Baseline, updated: Baseline) -> tuple[Baseline, list[str]]:
    """Return the committed baseline with all decreases applied, plus rejections."""
    rejected: list[str] = []
    old_packages, new_packages = _packages(committed), _packages(updated)
    if set(old_packages) != set(new_packages):
        rejected.append("Paketliste geändert")
    same_tool = {
        metric: _versions(committed).get(tool) == _versions(updated).get(tool)
        for metric, tool in VERSION_BOUND_METRICS.items()
    }
    result_packages: dict[str, dict[str, object]] = {}
    for name, entry in old_packages.items():
        new_entry = new_packages.get(name, entry)
        if new_entry.get(JUSTIFICATION) != entry.get(JUSTIFICATION):
            rejected.append(f"{name}: neue {JUSTIFICATION}")
        metrics = dict(_metrics(entry))
        for metric, value in _metrics(new_entry).items():
            old = metrics.get(metric)
            if old is None or value > old:
                rejected.append(f"{name}.{metric}: {old} -> {value}")
            elif value < old and same_tool.get(metric, True):
                metrics[metric] = value
        result_packages[name] = {**entry, "metrics": dict(sorted(metrics.items()))}
    return {**committed, "packages": result_packages}, rejected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("committed", type=Path, help="Baseline aus dem Commit (unverändert)")
    parser.add_argument("baseline", type=Path, help="Von --update-baseline geschriebene Datei")
    args = parser.parse_args(argv)
    committed = json.loads(args.committed.read_text(encoding="utf-8"))
    updated = json.loads(args.baseline.read_text(encoding="utf-8"))
    merged, rejected = lower_only(committed, updated)
    target = committed if rejected else merged
    text = json.dumps(target, indent=2, ensure_ascii=False) + "\n"
    args.baseline.write_text(text, encoding="utf-8")
    for reason in rejected:
        print(f"nicht übernommen: {reason}")
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
