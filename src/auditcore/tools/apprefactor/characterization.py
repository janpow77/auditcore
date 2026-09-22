"""Characterize actual source in a separate Python process before migration."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from auditcore.exceptions import MigrationBlocked
from auditcore.tools.apprefactor.models import CharacterizationCase, RegressionComparison
from auditcore.tools.common import digest, read_json, write_json

# A child interpreter avoids module cache contamination between legacy and target.
_RUNNER = """
import contextlib, importlib, io, json, sys
root, reference, cases = json.loads(sys.stdin.read())
sys.path.insert(0, root)
module, name = reference.split(":", 1)
with contextlib.redirect_stdout(io.StringIO()):
    obj = importlib.import_module(module)
    for part in name.split("."):
        obj = getattr(obj, part)
    outcomes = []
    for case in cases:
        try:
            result = obj(*case["args"], **case["kwargs"])
            json.dumps(result, allow_nan=False)
            outcomes.append({"name": case["name"], "value": result, "exception": None})
        except Exception as exc:
            outcomes.append({"name": case["name"], "value": None,
                             "exception": type(exc).__module__ + "." + type(exc).__qualname__})
print(json.dumps(outcomes, allow_nan=False))
"""


def execute_cases(root: Path, reference: str, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Execute supplied cases with a timeout and no leakage of captured module output."""
    if not cases:
        raise MigrationBlocked("Characterization cases must not be empty")
    result = subprocess.run(
        [sys.executable, "-c", _RUNNER],
        input=json.dumps([str(root.resolve()), reference, cases]),
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode:
        raise MigrationBlocked("Characterization execution failed; inspect module in isolation")
    outcomes: list[dict[str, Any]] = json.loads(result.stdout)
    return outcomes


def characterize(
    root: Path, reference: str, cases: list[CharacterizationCase], output: Path, source_file: Path
) -> dict[str, Any]:
    """Persist observed golden outcomes bound to exact legacy source bytes."""
    inputs = [asdict(c) for c in cases]
    result = {
        "reference": reference,
        "cases": inputs,
        "outcomes": execute_cases(root, reference, inputs),
        "source_digest": digest(source_file.read_bytes()),
        "classification": "OBSERVED",
    }
    write_json(output, result)
    return result


def compare(root: Path, target: str, golden: Path, target_file: Path) -> RegressionComparison:
    """Compare actual replacement results to previously observed legacy behavior."""
    baseline = read_json(golden)
    current = execute_cases(root, target, baseline["cases"])
    records = [
        {"name": old["name"], "legacy": old, "replacement": new, "equal": old == new}
        for old, new in zip(baseline["outcomes"], current, strict=True)
    ]
    return RegressionComparison(
        "PASS" if records and all(r["equal"] for r in records) else "MIGRATION_BLOCKED",
        records,
        baseline["source_digest"],
        digest(target_file.read_bytes()),
    )
