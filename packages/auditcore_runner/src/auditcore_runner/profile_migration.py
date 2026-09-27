"""Migration of older profile files to the current schema (one step per version)."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from .profile import TEMPLATE_GPU_CLASSES
from .profile_reader import ProfileFormatError, Reader

SCHEMA_PREFIX = "auditcore-runner/profil/"
CURRENT_VERSION = 3
CURRENT_SCHEMA = f"{SCHEMA_PREFIX}{CURRENT_VERSION}"

JsonObject = dict[str, object]


def _migrate_1_to_2(data: JsonObject) -> JsonObject:
    """Version 1 had ``repo``/``token_datei`` at top level and ``aktivitaet``."""
    migrated = {k: v for k, v in data.items() if k not in {"repo", "token_datei", "aktivitaet"}}
    token = data.get("token_datei") or ""
    migrated["ziel"] = {"art": "repo", "name": data.get("repo", "")}
    migrated["auth"] = {"art": "pat" if token else "gh", "token_datei": token}
    migrated["soll_quelle"] = {"art": "statisch"}
    migrated["skalierung"] = dict(cast(JsonObject, data.get("aktivitaet") or {}))
    migrated["schema"] = f"{SCHEMA_PREFIX}2"
    return migrated


def _migrate_2_to_3(data: JsonObject) -> JsonObject:
    """Version 2 knew four fixed class names; version 3 names classes freely and stores ``art``.

    A class becomes ``gpu`` if it had one of the former GPU names, a VRAM need
    or cards assigned; every other class is ``cpu``.
    """
    migrated = dict(data)
    gpus = data.get("gpus")
    with_cards = {g.get("klasse") for g in gpus if isinstance(g, dict)} if isinstance(gpus, list) else set()
    classes = data.get("klassen")
    if isinstance(classes, dict):
        updated: JsonObject = {}
        for name, entry in classes.items():
            if isinstance(entry, dict) and "art" not in entry:
                vram = entry.get("vram_mb")
                gpu = name in TEMPLATE_GPU_CLASSES or name in with_cards or (isinstance(vram, int) and vram > 0)
                entry = {"art": "gpu" if gpu else "cpu", **entry}
            updated[name] = entry
        migrated["klassen"] = updated
    migrated["schema"] = f"{SCHEMA_PREFIX}3"
    return migrated


MIGRATIONS: dict[int, Callable[[JsonObject], JsonObject]] = {1: _migrate_1_to_2, 2: _migrate_2_to_3}


def schema_version(data: JsonObject) -> int:
    schema = data.get("schema")
    if not isinstance(schema, str) or not schema.startswith(SCHEMA_PREFIX):
        raise ProfileFormatError(f"schema: erwartet {SCHEMA_PREFIX}<version>")
    version = schema.removeprefix(SCHEMA_PREFIX)
    if not version.isdigit():
        raise ProfileFormatError("schema: Versionsnummer fehlt")
    return int(version)


def migrate(raw: object) -> tuple[JsonObject, list[int]]:
    """Bring older files to the current version; returns data and applied steps."""
    data = Reader(raw, "profil").data
    applied: list[int] = []
    version = schema_version(data)
    if version > CURRENT_VERSION:
        raise ProfileFormatError(f"schema: Version {version} ist neuer als dieses Paket ({CURRENT_VERSION})")
    while version < CURRENT_VERSION:
        data = MIGRATIONS[version](data)
        applied.append(version)
        version += 1
    return data, applied
