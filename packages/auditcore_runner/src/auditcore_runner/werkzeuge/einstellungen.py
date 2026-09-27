"""Machine-level tool switches (UI tab "Werkzeuge"): ``~/.config/auditcore-runner/werkzeuge.json``.

They override the repository's ``.auditcore-runner.toml`` on this machine only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from ..profile import config_dir
from ..profile_io import write_atomic
from .modell import ToolSetting

SCHEMA = "auditcore-runner/werkzeuge/1"


def settings_path() -> Path:
    return config_dir() / "werkzeuge.json"


class ToolSettingsError(ValueError):
    """The machine tool settings are malformed."""


def _setting(raw: object, where: str) -> ToolSetting:
    data = cast(dict[str, object], raw) if isinstance(raw, dict) else None
    if data is None:
        raise ToolSettingsError(f"{where}: Objekt erwartet")
    enabled, timeout, priority = data.get("aktiv", True), data.get("zeitlimit_s", 600), data.get("prioritaet", 50)
    if not isinstance(enabled, bool):
        raise ToolSettingsError(f"{where}.aktiv: wahr/falsch erwartet")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 10 <= timeout <= 86400:
        raise ToolSettingsError(f"{where}.zeitlimit_s: 10–86400 Sekunden")
    if isinstance(priority, bool) or not isinstance(priority, int) or not 0 <= priority <= 1000:
        raise ToolSettingsError(f"{where}.prioritaet: 0–1000")
    return ToolSetting(enabled, timeout, priority)


def parse(raw: object) -> dict[str, dict[str, ToolSetting]]:
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise ToolSettingsError(f"schema: erwartet {SCHEMA}")
    profiles = raw.get("profile", {})
    if not isinstance(profiles, dict):
        raise ToolSettingsError("profile: Objekt erwartet")
    result: dict[str, dict[str, ToolSetting]] = {}
    for profile, tools in profiles.items():
        if not isinstance(tools, dict):
            raise ToolSettingsError(f"profile.{profile}: Objekt erwartet")
        result[str(profile)] = {str(t): _setting(v, f"profile.{profile}.{t}") for t, v in tools.items()}
    return result


def load(path: Path | None = None) -> dict[str, dict[str, ToolSetting]]:
    target = path or settings_path()
    return parse(json.loads(target.read_text(encoding="utf-8"))) if target.exists() else {}


def to_json(settings: dict[str, dict[str, ToolSetting]]) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "profile": {
            profile: {
                tool: {"aktiv": s.enabled, "zeitlimit_s": s.timeout_seconds, "prioritaet": s.priority}
                for tool, s in sorted(tools.items())
            }
            for profile, tools in sorted(settings.items())
        },
    }


def save(settings: dict[str, dict[str, ToolSetting]], path: Path | None = None) -> Path:
    target = path or settings_path()
    write_atomic(target, json.dumps(to_json(settings), indent=2, ensure_ascii=False) + "\n")
    return target
