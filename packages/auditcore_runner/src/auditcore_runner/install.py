"""Turn a profile into systemd user units, Docker network/image and root scripts.

``plan`` computes every file change without touching the system; ``apply_*``
helpers write files and run commands. Running jobs are never interrupted:
surplus instances stay enabled and rest, because the supervisor re-reads the
profile and the pool before every registration.
"""

from __future__ import annotations

import difflib
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from string import Template

from .profile import Profile, config_dir, default_profile_path, state_dir

UNIT_PREFIX = "auditcore-runner"
FIREWALL_MARKER = Path("/run/auditcore-ci-firewall.ok")
HELPER_UNITS = ("status.service", "status.timer", "regler.service")


def data_text(*parts: str) -> str:
    return files("auditcore_runner").joinpath("data", *parts).read_text(encoding="utf-8")


def unit_dir() -> Path:
    return Path.home() / ".config" / "systemd" / "user"


def root_dir() -> Path:
    return config_dir() / "root"


def program_path() -> str:
    """Absolute path of the console script, so units work without PATH."""
    found = shutil.which("auditcore-runner")
    return found or f"{sys.executable} -m auditcore_runner"


def unit_name(runner_class: str, instance: int | None = None) -> str:
    suffix = "" if instance is None else str(instance)
    return f"{UNIT_PREFIX}-{runner_class}@{suffix}.service"


@dataclass(frozen=True)
class FileChange:
    path: Path
    old: str | None
    new: str
    mode: int = 0o644

    @property
    def changed(self) -> bool:
        return self.old != self.new

    def diff(self) -> str:
        before = (self.old or "").splitlines(keepends=True)
        after = self.new.splitlines(keepends=True)
        label = str(self.path)
        return "".join(difflib.unified_diff(before, after, label + " (alt)", label + " (neu)"))


@dataclass(frozen=True)
class Step:
    """A command apply would run (shown in dry runs)."""

    command: tuple[str, ...]
    reason: str

    def text(self) -> str:
        return " ".join(self.command)


def _read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _render(name: str, **values: str) -> str:
    return Template(data_text("templates", name)).safe_substitute(values)


def render_unit(profile: Profile, runner_class: str, profile_path: Path) -> str:
    settings = profile.classes[runner_class]
    pool_path = profile.pool_path()
    return _render(
        "runner@.service",
        klasse=runner_class,
        profil=str(profile_path),
        pool=str(pool_path) if pool_path else "",
        programm=program_path(),
        nice=str(settings.nice),
        cpu_gewicht="idle" if settings.nice >= 19 else "100",
        io_gewicht=str(settings.io_weight),
    )


EGRESS_SET = "auditcore-ci-egress"


def _egress_install(base: Path, enabled: bool) -> str:
    if not enabled:
        return "rm -f /etc/systemd/system/auditcore-ci-egress.service /etc/systemd/system/auditcore-ci-egress.timer"
    return "\n".join(
        [
            "for tool in ipset jq curl; do",
            '  command -v "$tool" >/dev/null || { echo "Egress-Allowlist braucht $tool" >&2; exit 1; }',
            "done",
            f'install -m 0644 "{base / "auditcore-ci-egress.service"}" /etc/systemd/system/auditcore-ci-egress.service',
            f'install -m 0644 "{base / "auditcore-ci-egress.timer"}" /etc/systemd/system/auditcore-ci-egress.timer',
            "systemctl daemon-reload",
            "systemctl enable --now auditcore-ci-egress.timer",
        ]
    )


def render_firewall(profile: Profile) -> dict[str, str]:
    """Root scripts for the network lock and egress allowlist; written for the user, never executed here."""
    network, base = profile.network, root_dir()
    allowlist = network.egress == "allowlist"
    values = {
        "netz": network.name,
        "subnetz": network.subnet,
        "bruecke": network.bridge,
        "pfad": str(base / "auditcore-ci-firewall.sh"),
        "skript": str(base / "auditcore-ci-firewall.sh"),
        "unit": str(base / "auditcore-ci-firewall.service"),
        "egress": network.egress,
        "ipset": EGRESS_SET,
        "egress_ports": ",".join(str(port) for port in network.egress_ports),
        "egress_hosts": " ".join(shlex.quote(host) for host in network.egress_hosts),
        "egress_meta": " ".join(shlex.quote(key) for key in network.egress_github_meta),
        "egress_installieren": _egress_install(base, allowlist),
    }
    scripts = {
        "auditcore-ci-firewall.sh": _render("firewall.sh", **values),
        "auditcore-ci-firewall.service": _render("auditcore-ci-firewall.service", **values),
        "firewall-installieren.sh": _render(
            "firewall-installieren.sh", **{**values, "pfad": str(base / "firewall-installieren.sh")}
        ),
    }
    if allowlist:
        scripts["auditcore-ci-egress.service"] = _render("auditcore-ci-egress.service", **values)
        scripts["auditcore-ci-egress.timer"] = data_text("templates", "auditcore-ci-egress.timer")
    return scripts


CDI_DIRS = (Path("/etc/cdi"), Path("/var/run/cdi"))


def cdi_ready(directories: tuple[Path, ...] = CDI_DIRS) -> bool:
    """A CDI specification for ``nvidia.com/gpu`` exists (``nvidia-ctk cdi generate``)."""
    for directory in directories:
        for spec in sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.json")) if directory.is_dir() else []:
            try:
                if "nvidia.com/gpu" in spec.read_text(encoding="utf-8", errors="replace"):
                    return True
            except OSError:
                continue
    return False


def hints(profile: Profile, directories: tuple[Path, ...] = CDI_DIRS) -> list[str]:
    """Prerequisites the user has to establish once (shown by install, never done here)."""
    found: list[str] = []
    uses_gpus = any(c.enabled and c.is_gpu and profile.gpus_of(name) for name, c in profile.classes.items())
    if uses_gpus and profile.gpu_access == "cdi" and not cdi_ready(directories):
        found.append(
            "GPU per CDI: einmalig `sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml` "
            "(Docker ab 28 nutzt CDI ohne weitere Einstellung)"
        )
    if profile.backend == "scaleset":
        found.append(
            "Scale-Sets: Workflows wählen sie mit `runs-on: <name>` (Namen: `auditcore-runner scaleset anzeigen`)"
        )
    return found


def firewall_command() -> str:
    """The one-liner a user runs once with root rights."""
    return f"sudo bash {root_dir() / 'firewall-installieren.sh'}"


def _helper_units(profile: Profile, profile_path: Path) -> list[tuple[str, str]]:
    values = {"programm": program_path(), "profil": str(profile_path)}
    units = [
        (f"{UNIT_PREFIX}-status.service", _render("status.service", **values)),
        (f"{UNIT_PREFIX}-status.timer", data_text("templates", "status.timer")),
        (f"{UNIT_PREFIX}-image.service", _render("image.service", **values)),
        (f"{UNIT_PREFIX}-image.timer", data_text("templates", "image.timer")),
    ]
    if profile.source.kind == "lokal":
        units.append((f"{UNIT_PREFIX}-regler.service", _render("regler.service", **values)))
    if profile.backend == "scaleset":
        units.append((f"{UNIT_PREFIX}-scaleset.service", _render("scaleset.service", **values)))
    return units


def plan(profile: Profile, profile_path: Path | None = None) -> list[FileChange]:
    """Every file ``write_changes`` would write, with old and new content."""
    path = profile_path or default_profile_path()
    changes: list[FileChange] = []
    for name in sorted(profile.classes):
        target = unit_dir() / unit_name(name)
        changes.append(FileChange(target, _read(target), render_unit(profile, name, path)))
    for name, text in _helper_units(profile, path):
        target = unit_dir() / name
        changes.append(FileChange(target, _read(target), text))
    if profile.network.enabled:
        for name, text in render_firewall(profile).items():
            target = root_dir() / name
            changes.append(FileChange(target, _read(target), text, 0o755 if name.endswith(".sh") else 0o644))
    return changes


def instance_steps(profile: Profile) -> list[Step]:
    """Reload units and enable instances up to the maximum (never stop running ones)."""
    steps = [Step(("systemctl", "--user", "daemon-reload"), "Units neu laden")]
    steps.append(Step(("systemctl", "--user", "enable", "--now", f"{UNIT_PREFIX}-status.timer"), "Status-Datei"))
    steps.append(Step(("systemctl", "--user", "enable", "--now", f"{UNIT_PREFIX}-image.timer"), "Image aktuell halten"))
    if profile.source.kind == "lokal":
        steps.append(Step(("systemctl", "--user", "enable", "--now", f"{UNIT_PREFIX}-regler.service"), "Autoskalierer"))
        steps.append(Step(("systemctl", "--user", "try-restart", f"{UNIT_PREFIX}-regler.service"), "Regeln neu laden"))
    if profile.backend == "scaleset":
        unit = f"{UNIT_PREFIX}-scaleset.service"
        steps.append(Step(("systemctl", "--user", "enable", "--now", unit), "Scale-Set-Listener"))
        steps.append(Step(("systemctl", "--user", "try-restart", unit), "Listener mit neuem Profil"))
    for name, settings in sorted(profile.classes.items()):
        if not settings.enabled:
            continue
        for number in range(1, settings.max_instances + 1):
            steps.append(
                Step(("systemctl", "--user", "enable", "--now", unit_name(name, number)), f"{name} Nr. {number}")
            )
    return steps


def docker_steps(profile: Profile, has_image: bool, has_network: bool) -> list[Step]:
    steps: list[Step] = []
    if not has_image:
        context = str(files("auditcore_runner").joinpath("data"))
        steps.append(Step(("docker", "build", "--pull", "-t", profile.image, context), "Runner-Image bauen"))
    network = profile.network
    if network.enabled and not has_network:
        steps.append(
            Step(
                (
                    "docker",
                    "network",
                    "create",
                    "--driver",
                    "bridge",
                    "--subnet",
                    network.subnet,
                    "--opt",
                    f"com.docker.network.bridge.name={network.bridge}",
                    network.name,
                ),
                "Runner-Netz anlegen",
            )
        )
    return steps


def _quiet(command: list[str]) -> bool:
    try:
        result = subprocess.run(command, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def image_present(image: str) -> bool:
    return _quiet(["docker", "image", "inspect", image])


def network_present(name: str) -> bool:
    return _quiet(["docker", "network", "inspect", name])


def write_changes(changes: list[FileChange]) -> list[Path]:
    written: list[Path] = []
    for change in changes:
        if change.changed:
            change.path.parent.mkdir(parents=True, exist_ok=True)
            change.path.write_text(change.new, encoding="utf-8")
            change.path.chmod(change.mode)
            written.append(change.path)
    return written


def run_steps(steps: list[Step]) -> list[str]:
    """Run commands; returns error messages instead of raising."""
    errors: list[str] = []
    for step in steps:
        try:
            result = subprocess.run(list(step.command), capture_output=True, text=True, timeout=1800, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            errors.append(f"{step.text()}: {error}")
            continue
        if result.returncode != 0:
            errors.append(f"{step.text()}: {result.stderr.strip()[:300]}")
    return errors


def listed_units(pattern: str) -> list[str]:
    try:
        result = subprocess.run(
            ["systemctl", "--user", "list-units", "--all", "--plain", "--no-legend", pattern],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [line.split()[0] for line in result.stdout.splitlines() if line.strip()]


def legacy_units() -> list[str]:
    """Units of the former ci/runner setup (``auditcore-runner@N``) that would double-register."""
    return listed_units("auditcore-runner@*.service")


def uninstall_steps() -> list[Step]:
    """Stop and disable every unit of this package (running jobs end via TERM → docker stop)."""
    units = listed_units(f"{UNIT_PREFIX}-*")
    steps = [Step(("systemctl", "--user", "disable", "--now", unit), "abschalten") for unit in units]
    steps.append(Step(("systemctl", "--user", "daemon-reload"), "Units neu laden"))
    return steps


def uninstall_files(everything: bool) -> list[Path]:
    """Unit files (and with ``everything`` profile, state and root scripts)."""
    paths = sorted(unit_dir().glob(f"{UNIT_PREFIX}-*"))
    if everything:
        paths.extend([config_dir(), state_dir()])
    return paths


def remove_paths(paths: list[Path]) -> None:
    for path in paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)


def volume_steps() -> list[Step]:
    try:
        result = subprocess.run(
            ["docker", "volume", "ls", "-q", "--filter", "name=auditcore-runner-"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    volumes = [v for v in result.stdout.split() if v]
    return [Step(("docker", "volume", "rm", *volumes), "Cache-Volumes entfernen")] if volumes else []
