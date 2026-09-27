"""Runner profile of one machine: classes, limits, target source and scaling rules.

The model is independent of any repository or host; defaults are generic and
the example profiles (``data/profiles``) carry concrete machines.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

CLASS_NAMES = ("cpu", "cpu-gross", "gpu-16gb", "gpu-8gb")
GPU_CLASSES = ("gpu-16gb", "gpu-8gb")
BASE_LABELS = ("self-hosted", "linux", "x64")
TARGET_SOURCES = ("statisch", "lokal", "datei")
SCOPES = ("repo", "org")
AUTH_KINDS = ("gh", "pat", "app")
DEFAULT_IMAGE = "auditcore-runner:local"
BACKENDS = ("jit", "scaleset")
GPU_ACCESS = ("cdi", "gpus")
EGRESS_MODES = ("aus", "allowlist")
# Hosts a CI job typically needs (GitHub, PyPI, npm, container registries); GitHub's
# own ranges come from api.github.com/meta (``egress_github_meta``).
DEFAULT_EGRESS_HOSTS = (
    "github.com",
    "api.github.com",
    "codeload.github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "pypi.org",
    "files.pythonhosted.org",
    "registry.npmjs.org",
    "ghcr.io",
    "pkg-containers.githubusercontent.com",
    "registry-1.docker.io",
    "auth.docker.io",
    "production.cloudflare.docker.com",
)
DEFAULT_GITHUB_META = ("api", "web", "git", "packages", "actions")
UV_CACHE_VOLUME = "auditcore-runner-uv"


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "auditcore-runner"


def state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "auditcore-runner"


def default_profile_path() -> Path:
    return config_dir() / "profil.json"


def expand(path: str) -> Path:
    return Path(os.path.expanduser(path))


@dataclass(frozen=True)
class Target:
    """Where runners register: one repository or a whole organisation."""

    scope: str = "repo"
    name: str = ""
    runner_group_id: int = 1
    watched_repos: tuple[str, ...] = ()
    known_runner_prefixes: tuple[str, ...] = ()

    @property
    def api_base(self) -> str:
        return f"repos/{self.name}" if self.scope == "repo" else f"orgs/{self.name}"

    @property
    def queue_repos(self) -> tuple[str, ...]:
        return (self.name,) if self.scope == "repo" else self.watched_repos


@dataclass(frozen=True)
class Auth:
    """Credentials are only ever referenced by file path, never stored."""

    kind: str = "gh"
    token_file: str = ""
    app_id: int = 0
    app_key_file: str = ""
    installation_id: int = 0


@dataclass(frozen=True)
class RunnerClass:
    enabled: bool
    cpus: int
    memory_gb: int
    max_instances: int
    labels: tuple[str, ...]
    cpu_shares: int = 512
    nice: int = 10
    io_weight: int = 100
    uv_cache_volume: str = UV_CACHE_VOLUME
    quiet_max: int = -1
    min_instances: int = 0
    vram_mb: int = 0

    def cap_quiet(self) -> int:
        """Instances allowed while the thermal source reports quiet mode."""
        return self.max_instances if self.quiet_max < 0 else min(self.quiet_max, self.max_instances)


@dataclass(frozen=True)
class GpuPolicy:
    uuid: str
    name: str
    vram_mb: int
    allowed: bool
    runner_class: str
    index: int = 0


@dataclass(frozen=True)
class Network:
    name: str = "auditcore-ci"
    subnet: str = "172.30.250.0/24"
    bridge: str = "br-auditcore-ci"
    enabled: bool = True
    firewall_required: bool = True
    egress: str = "aus"
    egress_hosts: tuple[str, ...] = DEFAULT_EGRESS_HOSTS
    egress_github_meta: tuple[str, ...] = DEFAULT_GITHUB_META
    egress_ports: tuple[int, ...] = (80, 443)


@dataclass(frozen=True)
class ScaleSetSettings:
    """Backend ``scaleset``: one scale set per class, named ``<praefix>-<klasse>``."""

    name_prefix: str = ""
    runner_group: str = "default"


@dataclass(frozen=True)
class ThermalSource:
    """Optional HTTP-JSON source of throttling/temperature data (off by default).

    Field paths use dots and ``[*]`` for lists, e.g. ``gpus[*].temp``; several
    temperature paths are combined by maximum, several limits by minimum.
    """

    enabled: bool = False
    url: str = ""
    throttling_paths: tuple[str, ...] = ()
    temperature_paths: tuple[str, ...] = ()
    limit_paths: tuple[str, ...] = ()
    mode_path: str = ""
    quiet_value: str = ""
    margin_c: float = 3.0


@dataclass(frozen=True)
class Scaling:
    """Thresholds of the built-in autoscaler (target source ``lokal``); neutral defaults."""

    interactive_priority: bool = False
    idle_minutes: int = 10
    share_while_active: float = 0.25
    interactive_cards: tuple[int, ...] = ()
    interactive_card_idle_minutes: int = 15
    swap_lock_gb: float = 0.0
    swap_in_max_per_s: float = 256.0
    min_free_memory_gb: float = 4.0
    load_per_core_max: float = 0.8
    temperature_max_c: float = 85.0
    full_power_from_hour: int = 0
    full_power_to_hour: int = 0
    spare_idle_runners: int = 1
    hold_seconds: int = 300
    interval_seconds: int = 30
    thermal: ThermalSource = field(default_factory=ThermalSource)
    gpu_shared_services: tuple[str, ...] = ()


@dataclass(frozen=True)
class Priority:
    """Rank of a runner class or check profile (1 = highest); same fields as the central regulator."""

    name: str
    rank: int
    preemptible: bool = True
    minimum: int = 0


@dataclass(frozen=True)
class TargetSource:
    kind: str = "statisch"
    file: str = "~/.config/auditcore-runner/soll.json"


@dataclass(frozen=True)
class Change:
    """Who changed the profile last (shown locally and centrally)."""

    time: str = ""
    source: str = "lokal"
    who: str = ""


SYNC_MODES = ("aus", "flow-agent")
CHANGE_SOURCES = ("lokal", "flow-agent")


@dataclass(frozen=True)
class Profile:
    host: str
    target: Target = field(default_factory=Target)
    auth: Auth = field(default_factory=Auth)
    image: str = DEFAULT_IMAGE
    backend: str = "jit"
    scale_set: ScaleSetSettings = field(default_factory=ScaleSetSettings)
    gpu_access: str = "cdi"
    reserve_cpus: int = 4
    reserve_memory_gb: int = 12
    network: Network = field(default_factory=Network)
    source: TargetSource = field(default_factory=TargetSource)
    scaling: Scaling = field(default_factory=Scaling)
    classes: dict[str, RunnerClass] = field(default_factory=dict)
    gpus: tuple[GpuPolicy, ...] = ()
    priorities: tuple[Priority, ...] = ()
    version: int = 0
    change: Change = field(default_factory=Change)
    sync: str = "aus"

    def gpus_of(self, runner_class: str) -> list[GpuPolicy]:
        """Cards a GPU class may use; which one is picked is decided per job at start."""
        return [g for g in self.gpus if g.allowed and g.runner_class == runner_class]

    def runner_prefix(self) -> str:
        """Names of runners registered by this machine start with this prefix."""
        return f"{self.host}-"

    def scale_set_name(self, runner_class: str) -> str:
        """Scale set of a class; workflows select it with ``runs-on: <name>``."""
        return f"{self.scale_set.name_prefix or self.host}-{runner_class}"

    def known_prefixes(self) -> tuple[str, ...]:
        return (self.runner_prefix(), *self.target.known_runner_prefixes)

    def priority_of(self, name: str) -> Priority | None:
        return next((p for p in self.priorities if p.name == name), None)

    def pool_path(self) -> Path | None:
        """Pool file the supervisors obey, or None for static targets."""
        if self.source.kind == "statisch":
            return None
        if self.source.kind == "lokal":
            return state_dir() / "soll.json"
        return expand(self.source.file)


def with_class(profile: Profile, name: str, runner_class: RunnerClass) -> Profile:
    return replace(profile, classes={**profile.classes, name: runner_class})
