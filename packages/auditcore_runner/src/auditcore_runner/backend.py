"""How a runner instance obtains jobs – behind one interface.

``jit`` (default): a loop that registers an ephemeral JIT runner per job via
the REST API and starts a fresh container. ``scaleset``: the same loop, but
the JIT configuration comes from the class' runner scale set and a listener
(``auditcore-runner scaleset lauschen``) limits the instances to the demand
``min(capacity, min + totalAssignedJobs)``. Units, profile, pool and status
stay the same for both.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path
from typing import Protocol

from . import nachfrage
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


def _loop_environment(profile: Profile, runner_class: str, backend_name: str) -> dict[str, str]:
    pool_path = profile.pool_path()
    gpu_class = profile.classes[runner_class].is_gpu
    return {
        "AUDITCORE_RUNNER_BACKEND": backend_name,
        "AUDITCORE_RUNNER_POOL": str(pool_path) if pool_path else "",
        "AUDITCORE_RUNNER_DEMAND": str(nachfrage.demand_path()) if backend_name == "scaleset" else "",
        "AUDITCORE_RUNNER_DEMAND_MAX_AGE": str(nachfrage.FRESH_SECONDS),
        "AUDITCORE_RUNNER_GPU_CLASS": "1" if gpu_class else "",
        "AUDITCORE_RUNNER_GPU_ACCESS": profile.gpu_access,
        "AUDITCORE_RUNNER_PROGRAM": program_path(),
    }


def _exec_supervisor(environment: dict[str, str], runner_class: str, instance: int) -> None:  # pragma: no cover
    with as_file(files("auditcore_runner").joinpath("data", "supervisor.sh")) as script:
        os.execvpe("bash", ["bash", str(script), runner_class, str(instance)], environment)  # noqa: S606 - fixed script


@dataclass(frozen=True)
class JitLoopBackend:
    """Ephemeral JIT registration per job via the REST API, implemented by ``data/supervisor.sh``."""

    name: str = "jit"

    def environment(self, profile: Profile, runner_class: str, instance: int) -> dict[str, str]:
        return _loop_environment(profile, runner_class, self.name)

    def serve(
        self, profile: Profile, profile_path: Path, runner_class: str, instance: int
    ) -> None:  # pragma: no cover - execs
        environment = {**os.environ, **self.environment(profile, runner_class, instance)}
        environment["AUDITCORE_RUNNER_PROFILE"] = str(profile_path)
        _exec_supervisor(environment, runner_class, instance)


@dataclass(frozen=True)
class ScaleSetBackend(JitLoopBackend):
    """JIT configuration from the runner scale set; demand from the listener (``scaleset lauschen``)."""

    name: str = "scaleset"


BACKENDS: dict[str, RunnerBackend] = {"jit": JitLoopBackend(), "scaleset": ScaleSetBackend()}


def backend(name: str) -> RunnerBackend:
    if name not in BACKENDS:
        raise KeyError(f"unbekanntes Runner-Backend: {name} (verfügbar: {', '.join(BACKENDS)})")
    return BACKENDS[name]
