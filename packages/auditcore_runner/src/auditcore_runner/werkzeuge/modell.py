"""Tool catalog model, check profiles and the repository file ``.auditcore-runner.toml``.

A tool is a command plus a parser. An external orchestrator (e.g. MegaLinter
or Trunk) is registered like any tool whose parser is ``sarif``; the package
then normalises, filters, caches and reports its findings.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import cast

AREAS = ("python", "js", "sicherheit", "struktur", "doku", "gui", "gpu", "extern", "codemod")
STAGES = ("autofix", "codemod", "pruefen")
TRIGGERS = ("lokal", "pr", "nacht", "fuell")
REPO_FILE = ".auditcore-runner.toml"


@dataclass(frozen=True)
class Cost:
    cpus: int = 1
    minutes: int = 1
    gpu: bool = False


@dataclass(frozen=True)
class Tool:
    """One checker. ``command`` runs in the repository root; ``{ausgabe}`` is the report file."""

    name: str
    area: str
    command: tuple[str, ...]
    parser: str
    fix_command: tuple[str, ...] = ()
    cost: Cost = field(default_factory=Cost)
    install: str = ""
    version_command: tuple[str, ...] = ()
    applies_to: tuple[str, ...] = ()
    output_file: str = ""
    success_codes: tuple[int, ...] = (0, 1)
    stage: str = "pruefen"
    network: bool = False

    @property
    def can_fix(self) -> bool:
        return bool(self.fix_command)


@dataclass(frozen=True)
class ToolSetting:
    """Per-profile override: on/off, time limit and order."""

    enabled: bool = True
    timeout_seconds: int = 600
    priority: int = 50


@dataclass(frozen=True)
class CheckProfile:
    name: str
    tools: tuple[str, ...]
    triggers: tuple[str, ...] = ("lokal", "pr")
    timeout_seconds: int = 1800
    max_findings: int = 200
    autofix: bool = False
    settings: dict[str, ToolSetting] = field(default_factory=dict)

    def setting(self, tool: str) -> ToolSetting:
        return self.settings.get(tool, ToolSetting())

    def ordered_tools(self) -> list[str]:
        active = [t for t in self.tools if self.setting(t).enabled]
        return sorted(active, key=lambda t: (self.setting(t).priority, self.tools.index(t)))


DEFAULT_PROFILES: dict[str, CheckProfile] = {
    "schnell": CheckProfile("schnell", ("ruff", "gitleaks"), ("lokal",), 300, autofix=True),
    "pr": CheckProfile(
        "pr", ("ruff", "mypy", "pytest", "gitleaks", "eslint", "zizmor", "actionlint", "codegate"), ("lokal", "pr")
    ),
    "voll": CheckProfile(
        "voll", ("ruff", "mypy", "pytest", "gitleaks", "eslint", "zizmor", "actionlint", "codegate"), ("nacht",), 5400
    ),
    "sicherheit": CheckProfile("sicherheit", ("ruff", "gitleaks", "zizmor", "actionlint"), ("pr", "nacht")),
    "gui": CheckProfile("gui", ("eslint",), ("lokal", "pr")),
    "gpu": CheckProfile("gpu", ("pytest",), ("fuell",), 1800),
    "fuell": CheckProfile("fuell", ("pytest", "codegate"), ("fuell", "nacht"), 3600),
}


class RepoConfigError(ValueError):
    """``.auditcore-runner.toml`` does not follow the schema."""


def _setting(raw: object, where: str) -> ToolSetting:
    if not isinstance(raw, dict):
        raise RepoConfigError(f"{where}: Tabelle erwartet")
    data = cast(dict[str, object], raw)
    enabled, timeout, priority = data.get("aktiv", True), data.get("zeitlimit_s", 600), data.get("prioritaet", 50)
    if not isinstance(enabled, bool) or not isinstance(timeout, int) or not isinstance(priority, int):
        raise RepoConfigError(f"{where}: aktiv (bool), zeitlimit_s, prioritaet (Zahl)")
    return ToolSetting(enabled, timeout, priority)


def _texts(data: dict[str, object], key: str, where: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = data.get(key, list(default))
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise RepoConfigError(f"{where}.{key}: Liste von Texten erwartet")
    return tuple(cast(list[str], value))


def _number(data: dict[str, object], key: str, where: str, default: int) -> int:
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise RepoConfigError(f"{where}.{key}: ganze Zahl erwartet")
    return value


def _profile(name: str, raw: object, base: CheckProfile | None) -> CheckProfile:
    where = f"pruefprofile.{name}"
    if not isinstance(raw, dict):
        raise RepoConfigError(f"{where}: Tabelle erwartet")
    data = cast(dict[str, object], raw)
    start = base or CheckProfile(name, ())
    tools = _texts(data, "werkzeuge", where, start.tools)
    triggers = _texts(data, "ausloeser", where, start.triggers)
    unknown = [t for t in triggers if t not in TRIGGERS]
    if unknown:
        raise RepoConfigError(f"{where}.ausloeser: unbekannt {', '.join(unknown)}")
    settings_raw = data.get("werkzeug", {})
    settings = dict(start.settings)
    if isinstance(settings_raw, dict):
        settings.update({k: _setting(v, f"{where}.werkzeug.{k}") for k, v in settings_raw.items()})
    autofix = data.get("autofix", start.autofix)
    return replace(
        start,
        tools=tools,
        triggers=triggers,
        timeout_seconds=_number(data, "zeitlimit_s", where, start.timeout_seconds),
        max_findings=_number(data, "max_befunde", where, start.max_findings),
        autofix=autofix if isinstance(autofix, bool) else start.autofix,
        settings=settings,
    )


def load_repo_profiles(root: Path) -> dict[str, CheckProfile]:
    """Built-in profiles, overridden or extended by the repository's TOML file."""
    profiles = dict(DEFAULT_PROFILES)
    path = root / REPO_FILE
    if not path.exists():
        return profiles
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    section = data.get("pruefprofile", {})
    if not isinstance(section, dict):
        raise RepoConfigError("pruefprofile: Tabelle erwartet")
    for name, raw in section.items():
        profiles[name] = _profile(name, raw, profiles.get(name))
    return profiles


def load_codemods(root: Path) -> tuple[Tool, ...]:
    """Codemods aus ``[codemods]`` in ``.auditcore-runner.toml``.

    ``libcst = ["paket.modul.Klasse", …]`` ergibt je Eintrag einen Codemod über
    ``libcst-tool codemod``; ``befehle = [["prog", "arg"], …]`` beliebige
    Umschreib-Befehle. Codemods laufen nach den Autofixern und vor der Prüfung.
    """
    path = root / REPO_FILE
    if not path.exists():
        return ()
    section = tomllib.loads(path.read_text(encoding="utf-8")).get("codemods", {})
    if not isinstance(section, dict):
        raise RepoConfigError("codemods: Tabelle erwartet")
    tools: list[Tool] = []
    for name in _texts(section, "libcst", "codemods", ()):
        fix = ("libcst-tool", "codemod", "--no-format", name, ".")
        tools.append(Tool(f"libcst:{name}", "codemod", (), "keine", fix_command=fix, stage="codemod"))
    commands = section.get("befehle", [])
    if not isinstance(commands, list) or not all(isinstance(c, list) and c for c in commands):
        raise RepoConfigError("codemods.befehle: Liste von Befehlslisten erwartet")
    for number, command in enumerate(cast(list[list[object]], commands), 1):
        argv = tuple(str(part) for part in command)
        tools.append(Tool(f"codemod:{number}", "codemod", (), "keine", fix_command=argv, stage="codemod"))
    return tuple(tools)


def apply_machine_settings(profile: CheckProfile, overrides: dict[str, ToolSetting]) -> CheckProfile:
    """Machine-level switches from the UI win over repository defaults."""
    return replace(profile, settings={**profile.settings, **overrides})
