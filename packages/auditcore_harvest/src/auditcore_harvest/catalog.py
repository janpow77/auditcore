"""Versioned source catalogue (``auditcore_harvest.catalog/1``).

One entry per source profile: origin (repository, commit, path, symbols),
existing consumers, target package, authentication need, licence/access
review, secret-free configuration schema, fixtures and the *actual* test
status. ``implementation`` and ``live_test`` are separate on purpose: a
catalogue entry alone means neither "implemented" nor "live tested".
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources

from .errors import ConfigError
from .model import JSON

CATALOG_SCHEMA = "auditcore_harvest.catalog/1"

IMPLEMENTATION = frozenset({"SUPPORTED", "PLANNED", "LEGACY_ONLY"})
LIVE_TEST = frozenset({"PASS", "FAIL", "NOT_EXECUTED", "NOT_CONFIGURED"})
REVIEW = frozenset({"REVIEWED", "REVIEW_REQUIRED", "UNKNOWN"})
AUTH = frozenset({"none", "api_key", "basic", "token", "unknown"})
_ID = re.compile(r"[a-z][a-z0-9_]*\.[a-z0-9][a-z0-9_.-]*")
_SECRET_WORDS = ("password", "secret", "token", "apikey", "api_key")


@dataclass(frozen=True)
class CatalogEntry:
    """One validated catalogue entry (read-only view of the JSON)."""

    data: Mapping[str, JSON]

    @property
    def source_id(self) -> str:
        """Stable ``family.source`` identifier."""
        return str(self.data["source_id"])

    @property
    def implementation(self) -> str:
        """``SUPPORTED``, ``PLANNED`` or ``LEGACY_ONLY``."""
        return str(self.data["implementation"]["status"])

    @property
    def live_test(self) -> str:
        """Last actual live test status."""
        return str(self.data["live_test"]["status"])


def _check_config_schema(schema: object, where: str) -> None:
    if not isinstance(schema, Mapping) or schema.get("type") != "object":
        raise ConfigError(f"{where}: config_schema muss ein JSON-Schema-Objekt sein.")
    for name, spec in (schema.get("properties") or {}).items():
        if not isinstance(spec, Mapping):
            raise ConfigError(f"{where}: Eigenschaft {name} ungültig.")
        if "default" in spec and any(w in name.lower() for w in _SECRET_WORDS):
            raise ConfigError(f"{where}: Geheimnisfeld '{name}' darf keinen Wert enthalten.")
        if spec.get("secret") is True and "default" in spec:
            raise ConfigError(f"{where}: Geheimnisfeld '{name}' darf keinen Wert enthalten.")


def _validate_origins(origins: object, where: str) -> None:
    if not isinstance(origins, list):
        raise ConfigError(f"{where}: origins muss eine Liste sein.")
    for origin in origins:
        if not re.fullmatch(r"[0-9a-f]{40}|UNKNOWN", str(origin["commit"])):
            raise ConfigError(f"{where}: Commit muss vollständiger SHA oder UNKNOWN sein.")
        for key in ("repository", "path"):
            if not isinstance(origin[key], str) or not origin[key]:
                raise ConfigError(f"{where}: origin.{key} fehlt.")


def _validate_status(entry: Mapping[str, JSON], where: str) -> None:
    checks = (
        (entry["auth"], AUTH, "auth"),
        (entry["implementation"]["status"], IMPLEMENTATION, "implementation.status"),
        (entry["live_test"]["status"], LIVE_TEST, "live_test.status"),
        (entry["licence_access"]["status"], REVIEW, "licence_access.status"),
    )
    for value, allowed, name in checks:
        if value not in allowed:
            raise ConfigError(f"{where}: {name} unbekannt.")
    if entry["implementation"]["status"] == "SUPPORTED" and not entry["fixtures"]:
        raise ConfigError(f"{where}: SUPPORTED ohne Fixtures.")
    if entry["live_test"]["status"] in ("PASS", "FAIL") and not entry["live_test"].get("date"):
        raise ConfigError(f"{where}: Live-Test ohne Datum.")


def _validate_entry(entry: Mapping[str, JSON], index: int, seen: set[str]) -> CatalogEntry:
    where = f"Quelle {index}"
    try:
        source_id = entry["source_id"]
        if not isinstance(source_id, str) or not _ID.fullmatch(source_id):
            raise ConfigError(f"{where}: ungültige source_id {source_id!r}.")
        if source_id in seen:
            raise ConfigError(f"{where}: source_id {source_id} doppelt.")
        seen.add(source_id)
        where = source_id
        for key in ("title", "family", "target_package"):
            if not isinstance(entry[key], str) or not entry[key]:
                raise ConfigError(f"{where}: '{key}' fehlt.")
        _validate_origins(entry["origins"], where)
        _validate_status(entry, where)
        if not isinstance(entry["consumers"], list) or not isinstance(entry["fixtures"], list):
            raise ConfigError(f"{where}: consumers/fixtures müssen Listen sein.")
        _check_config_schema(entry["config_schema"], where)
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"{where}: Pflichtfeld fehlt oder hat falschen Typ ({exc}).") from exc
    return CatalogEntry(entry)


def validate_catalog(data: Mapping[str, JSON]) -> tuple[CatalogEntry, ...]:
    """Validate the catalogue document; raise ``ConfigError`` with the first problem."""
    if data.get("schema") != CATALOG_SCHEMA:
        raise ConfigError("Unbekanntes Katalogschema.")
    if not isinstance(data.get("version"), str):
        raise ConfigError("Katalogversion fehlt.")
    entries = data.get("sources")
    if not isinstance(entries, list) or not entries:
        raise ConfigError("Katalog enthält keine Quellen.")
    seen: set[str] = set()
    return tuple(_validate_entry(entry, index, seen) for index, entry in enumerate(entries))


def load_catalog(name: str = "sources.json") -> tuple[CatalogEntry, ...]:
    """Load and validate a packaged catalogue file."""
    if "/" in name or "\\" in name:
        raise ConfigError("Katalogname ohne Pfadanteile angeben.")
    entry = resources.files("auditcore_harvest.catalogs").joinpath(name)
    if not entry.is_file():
        raise ConfigError(f"Katalog {name} nicht vorhanden.")
    return validate_catalog(json.loads(entry.read_text(encoding="utf-8")))


def summary(entries: tuple[CatalogEntry, ...]) -> dict[str, dict[str, int]]:
    """Counts by implementation status, live test status and family."""
    result: dict[str, dict[str, int]] = {"implementation": {}, "live_test": {}, "family": {}}
    for entry in entries:
        for key, value in (
            ("implementation", entry.implementation),
            ("live_test", entry.live_test),
            ("family", str(entry.data["family"])),
        ):
            result[key][value] = result[key].get(value, 0) + 1
    return result
