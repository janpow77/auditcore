"""How a runner instance obtains jobs – behind one interface.

Today there is one backend: ``jit`` (a loop that registers an ephemeral JIT
runner per job and starts a fresh container). A later backend, e.g. a
listener for GitHub's runner scale sets, only has to implement
:class:`RunnerBackend`; units, profile, pool and status stay unchanged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path
from typing import Protocol

from .install import program_path
from .profile import Profile


class RunnerBackend(Protocol):
    @property
    def name(self) -> str:
        """Identifier used in the profile (``backend``)."""

    def environment(self, profile: Profile, runner_class: str, instance: int) -> dict[str, str]:
        """Variables for one instance (profile path, pool path, GPU …)."""

    def serve(self, profile: Profile, profile_path: Path, runner_class: str, instance: int) -> None:
        """Run the instance until stopped (normally replaces the process)."""


@dataclass(frozen=True)
class JitLoopBackend:
    """Ephemeral JIT registration per job, implemented by ``data/supervisor.sh``."""

    name: str = "jit"

    def environment(self, profile: Profile, runner_class: str, instance: int) -> dict[str, str]:
        pool_path = profile.pool_path()
        return {
            "AUDITCORE_RUNNER_POOL": str(pool_path) if pool_path else "",
            "AUDITCORE_RUNNER_GPU_CLASS": "1"
            if profile.classes[runner_class].vram_mb or profile.gpus_of(runner_class)
            else "",
            "AUDITCORE_RUNNER_PROGRAM": program_path(),
        }

    def serve(
        self, profile: Profile, profile_path: Path, runner_class: str, instance: int
    ) -> None:  # pragma: no cover - execs
        environment = {**os.environ, **self.environment(profile, runner_class, instance)}
        environment["AUDITCORE_RUNNER_PROFILE"] = str(profile_path)
        with as_file(files("auditcore_runner").joinpath("data", "supervisor.sh")) as script:
            os.execvpe("bash", ["bash", str(script), runner_class, str(instance)], environment)  # noqa: S606 - fixed script


BACKENDS: dict[str, RunnerBackend] = {"jit": JitLoopBackend()}


def backend(name: str) -> RunnerBackend:
    if name not in BACKENDS:
        raise KeyError(f"unbekanntes Runner-Backend: {name} (verfügbar: {', '.join(BACKENDS)})")
    return BACKENDS[name]
