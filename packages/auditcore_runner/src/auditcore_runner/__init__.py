"""auditcore_runner – self-hosted GitHub runners and a local check bench.

Manages ephemeral GitHub Actions runners on a machine (profile, systemd user
units, runner image, isolated Docker network), scales them from local signals
or an external regulator, and runs a configurable catalogue of checkers
locally with unified, baseline-filtered findings.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .profile import Profile, RunnerClass
from .regeln import Decision, Signals, ThermalState, decide, smooth
from .validation import Problem, validate

__all__ = [
    "ThermalState",
    "Decision",
    "Problem",
    "Profile",
    "RunnerClass",
    "Signals",
    "__version__",
    "decide",
    "smooth",
    "validate",
]
