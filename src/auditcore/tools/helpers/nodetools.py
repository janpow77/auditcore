"""Node toolchain of ``auditcore-helpers`` (TypeScript compiler API and tsx).

The toolchain is installed once with ``npm ci`` from the lockfile shipped in
this package into a cache directory, so application repositories never need
extra dependencies. ``AUDITCORE_HELPERS_TOOLCHAIN`` overrides the location.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404
import tempfile
from collections.abc import Mapping
from pathlib import Path

from auditcore.tools.helpers.model import HelperToolError, read_json, redact, short_hash

NODE_DIR = Path(__file__).with_name("node")
MANIFEST_FILES = ("package.json", "package-lock.json")
REQUIRED_MODULES = ("typescript", "tsx")
ENV_TOOLCHAIN = "AUDITCORE_HELPERS_TOOLCHAIN"
INSTALL_TIMEOUT = 600
DEFAULT_TIMEOUT = 600


def _lock_digest() -> str:
    return short_hash((NODE_DIR / "package-lock.json").read_text(encoding="utf-8"))


def toolchain_dir() -> Path:
    """Directory holding the installed toolchain (``node_modules``)."""
    configured = os.environ.get(ENV_TOOLCHAIN)
    if configured:
        return Path(configured)
    cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return cache / "auditcore" / f"helpers-node-{_lock_digest()}"


def node_executable() -> str:
    """Path of ``node`` (raises when Node.js is missing)."""
    found = shutil.which("node")
    if not found:
        raise HelperToolError("Node.js (node) nicht gefunden; für TS/JS/Vue erforderlich")
    return found


def is_installed(directory: Path) -> bool:
    """True when all required modules are present."""
    return all(
        (directory / "node_modules" / name / "package.json").is_file() for name in REQUIRED_MODULES
    )


def ensure_toolchain() -> Path:
    """Install the toolchain from the shipped lockfile unless already present."""
    directory = toolchain_dir()
    if is_installed(directory):
        return directory
    npm = shutil.which("npm")
    if not npm:
        raise HelperToolError(
            "npm nicht gefunden; Node-Werkzeugkette kann nicht installiert werden"
        )
    directory.mkdir(parents=True, exist_ok=True)
    for name in MANIFEST_FILES:
        shutil.copyfile(NODE_DIR / name, directory / name)
    command = [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error"]
    process = subprocess.run(  # nosec B603
        command, cwd=directory, capture_output=True, text=True, check=False, timeout=INSTALL_TIMEOUT
    )
    if process.returncode != 0 or not is_installed(directory):
        raise HelperToolError(
            f"npm ci für die Werkzeugkette fehlgeschlagen: {process.stderr[-2000:]}"
        )
    return directory


def toolchain_versions(directory: Path) -> dict[str, str]:
    """Installed versions of the required modules."""
    versions = {}
    for name in REQUIRED_MODULES:
        data = read_json(directory / "node_modules" / name / "package.json")
        versions[name] = str(data.get("version", "?")) if isinstance(data, dict) else "?"
    return versions


def run_node(
    script: str,
    payload: Mapping[str, object],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> object:
    """Run one of the shipped Node scripts with a JSON request and return its JSON result."""
    directory = ensure_toolchain()
    with tempfile.TemporaryDirectory(prefix="auditcore-helpers-") as temp:
        output = Path(temp) / "result.json"
        environment = {**os.environ, **(env or {})}
        environment[ENV_TOOLCHAIN] = str(directory)
        environment["AUDITCORE_HELPERS_OUTPUT"] = str(output)
        try:
            process = subprocess.run(  # nosec B603
                [node_executable(), str(NODE_DIR / script)],
                input=json.dumps(payload),
                cwd=cwd,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise HelperToolError(f"{script}: Zeitüberschreitung nach {timeout} s") from error
        if process.returncode != 0 or not output.is_file():
            reason = redact(process.stderr, last=True)
            raise HelperToolError(f"{script} fehlgeschlagen: {reason}")
        return read_json(output)
