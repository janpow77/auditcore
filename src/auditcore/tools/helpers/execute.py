"""Run helper calls in isolated processes (Python runner script or Node/tsx)."""

from __future__ import annotations

import json
import os
import subprocess  # nosec B404
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from auditcore.tools.helpers.model import as_dict, read_json, redact
from auditcore.tools.helpers.nodetools import run_node

RUNNER = Path(__file__).with_name("pyrunner.py")
TIMEOUT = 300


@dataclass
class RunResult:
    """Raw per-call results of one runner invocation."""

    results: dict[str, object] = field(default_factory=dict)
    load_error: str = ""


def _clean(entry: object) -> object:
    """Redact error texts of one result entry (defence in depth, runners already do it)."""
    item = as_dict(entry)
    for key in ("error", "reason"):
        if isinstance(item.get(key), str):
            item[key] = redact(str(item[key]))
    if "results" in item:
        item["results"] = {k: _clean(v) for k, v in as_dict(item["results"]).items()}
    return item if item else entry


def _parse(data: object) -> RunResult:
    response = as_dict(data)
    results = {key: _clean(value) for key, value in as_dict(response.get("results")).items()}
    return RunResult(results, redact(str(response.get("load_error") or "")))


def run_python(
    request: Mapping[str, object],
    *,
    interpreter: str | None = None,
    cwd: Path | None = None,
    timezone: str = "UTC",
) -> RunResult:
    """Run :mod:`pyrunner` in a separate, isolated interpreter (``python -I``)."""
    with tempfile.TemporaryDirectory(prefix="auditcore-helpers-py-") as temp:
        output = Path(temp) / "result.json"
        env = {**os.environ, "TZ": timezone, "AUDITCORE_HELPERS_OUTPUT": str(output)}
        try:
            process = subprocess.run(  # nosec B603
                [interpreter or sys.executable, "-I", "-B", str(RUNNER)],
                input=json.dumps(request),
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=TIMEOUT,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return RunResult(load_error=f"Python-Läufer nicht ausführbar: {error}")
        if not output.is_file():
            reason = redact(process.stderr, last=True)
            return RunResult(load_error=f"Python-Läufer abgebrochen: {reason}")
        return _parse(read_json(output))


def run_typescript(request: Mapping[str, object], *, cwd: Path | None, timezone: str) -> RunResult:
    """Run ``node/run.mjs`` (tsx) with the given request (toolchain errors propagate)."""
    return _parse(run_node("run.mjs", request, cwd=cwd, env={"TZ": timezone}, timeout=TIMEOUT))


def package_root(module: Path, stop: Path) -> Path:
    """Nearest directory with ``package.json`` between ``module`` and ``stop``."""
    for parent in module.parents:
        if (parent / "package.json").is_file():
            return parent
        if parent == stop:
            break
    return stop
