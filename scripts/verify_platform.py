"""Execute the required local checks and persist exit codes plus output digests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from auditcore.tools.common import digest, now, write_json
from auditcore.tools.quality.supplychain import wheel_sbom


def main() -> None:
    """Verify the installed platform; an unavailable or failed command never becomes PASS."""
    root = Path(__file__).resolve().parents[1]
    output = root / ".auditcore/verification"
    output.mkdir(parents=True, exist_ok=True)
    environment = {
        **os.environ,
        "PATH": str(Path(sys.executable).parent) + ":" + os.environ["PATH"],
    }
    results = {}

    def check(name, command):
        """Capture bounded command evidence without copying log contents into reports."""
        with (output / f"{name}.log").open("w") as stream:
            try:
                process = subprocess.run(
                    command,
                    cwd=root,
                    env=environment,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    timeout=300,
                    check=False,
                )
                result = {
                    "status": "PASS" if process.returncode == 0 else "FAIL",
                    "exit_code": process.returncode,
                    "command": command,
                }
            except (OSError, subprocess.TimeoutExpired) as error:
                result = {
                    "status": "NOT_EXECUTED",
                    "error": type(error).__name__,
                    "command": command,
                }
        result["output_sha256"] = digest((output / f"{name}.log").read_bytes())
        results[name] = result
        write_json(output / "results.json", {"generated_at": now(), "checks": results})
        print(name, result["status"], flush=True)

    check("install", [sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    check(
        "pytest", ["pytest", "--cov=auditcore", "--cov-report=json:.auditcore/coverage.json", "-q"]
    )
    check("ruff", ["ruff", "check", "."])
    check("mypy", ["mypy", "src"])
    for command in (
        "auditcore-quality",
        "auditcore-bibquality",
        "auditcore-consolidate",
        "auditcore-refactor",
        "auditcore-deploy",
    ):
        check(command + "-help", [command, "--help"])
    check("build", [sys.executable, "-m", "build"])
    if results["build"]["status"] == "PASS":
        result = wheel_sbom(
            root / "dist/auditcore-0.1.0-py3-none-any.whl", root / "dist/auditcore-0.1.0-sbom.json"
        )
        write_json(root / "dist/supply-chain.json", result)
    for component in ("core", "quality", "consolidator", "apprefactor", "deployer"):
        path = "src/auditcore" if component == "core" else f"src/auditcore.tools.{component}"
        command = [
            "auditcore-bibquality",
            path,
            "--context",
            f"contexts/{component}.json",
            "--supply-chain-report",
            "dist/supply-chain.json",
            "--output",
            f".auditcore/{component}-selfcheck.json",
        ]
        if component == "core":
            command.append("--strict")
            if (root / ".auditcore/core-api.json").exists():
                command.extend(["--compare-api", ".auditcore/core-api.json"])
        check(component + "-selfcheck", command)
    if any(r["status"] != "PASS" for r in results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
