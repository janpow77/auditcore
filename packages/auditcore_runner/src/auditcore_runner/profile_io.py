"""Profile file format (JSON, German keys) with schema versions and migration."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import cast

from .profile import (
    DEFAULT_EGRESS_HOSTS,
    DEFAULT_GITHUB_META,
    Auth,
    Change,
    GpuPolicy,
    Network,
    Priority,
    Profile,
    RunnerClass,
    ScaleSetSettings,
    Scaling,
    Target,
    TargetSource,
    ThermalSource,
    default_profile_path,
)
from .profile_reader import ProfileFormatError as ProfileFormatError  # re-exported
from .profile_reader import Reader

SCHEMA_PREFIX = "auditcore-runner/profil/"
CURRENT_VERSION = 2
CURRENT_SCHEMA = f"{SCHEMA_PREFIX}{CURRENT_VERSION}"

JsonObject = dict[str, object]


def _class(reader: Reader) -> RunnerClass:
    return RunnerClass(
        enabled=reader.flag("aktiv"),
        cpus=reader.integer("cpus"),
        memory_gb=reader.integer("speicher_gb"),
        max_instances=reader.integer("max_instanzen"),
        labels=reader.texts("labels"),
        cpu_shares=reader.integer("cpu_shares", 512),
        nice=reader.integer("nice", 10),
        io_weight=reader.integer("io_gewicht", 100),
        uv_cache_volume=reader.text("uv_cache_volume", ""),
        quiet_max=reader.integer("leise_max", -1),
        min_instances=reader.integer("min_instanzen", 0),
        vram_mb=reader.integer("vram_mb", 0),
    )


def _gpu(reader: Reader) -> GpuPolicy:
    return GpuPolicy(
        uuid=reader.text("uuid"),
        name=reader.text("name", ""),
        vram_mb=reader.integer("vram_mb"),
        allowed=reader.flag("erlaubt"),
        runner_class=reader.text("klasse"),
        index=reader.integer("index", 0),
    )


def _thermal(reader: Reader) -> ThermalSource:
    fields = reader.sub("felder")
    return ThermalSource(
        enabled=reader.flag("aktiv", False),
        url=reader.text("url", ""),
        throttling_paths=fields.texts("drosselung_aktiv", []),
        temperature_paths=fields.texts("temperatur", []),
        limit_paths=fields.texts("grenze", []),
        mode_path=fields.text("modus", ""),
        quiet_value=reader.text("leise_wert", ""),
        margin_c=reader.number("abstand_c", 3.0),
    )


def _indices(reader: Reader, key: str) -> tuple[int, ...]:
    value = reader.data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in value):
        raise ProfileFormatError(f"{reader.where}.{key}: Liste ganzer Zahlen erwartet")
    return tuple(cast(list[int], value))


def _scaling(reader: Reader) -> Scaling:
    return Scaling(
        interactive_priority=reader.flag("vorrang_interaktiv", False),
        idle_minutes=reader.integer("leerlauf_minuten", 10),
        share_while_active=reader.number("anteil_bei_nutzung", 0.25),
        interactive_cards=_indices(reader, "interaktive_karten"),
        interactive_card_idle_minutes=reader.integer("interaktive_karten_leerlauf_minuten", 15),
        swap_lock_gb=reader.number("swap_sperre_gb", 0.0),
        swap_in_max_per_s=reader.number("swap_einlagerung_max_s", 256.0),
        min_free_memory_gb=reader.number("ram_frei_min_gb", 4.0),
        load_per_core_max=reader.number("last_je_kern_max", 0.8),
        temperature_max_c=reader.number("temperatur_max_c", 85.0),
        full_power_from_hour=reader.integer("volllast_von", 0),
        full_power_to_hour=reader.integer("volllast_bis", 0),
        spare_idle_runners=reader.integer("freie_reserve", 1),
        hold_seconds=reader.integer("haltezeit_s", 300),
        interval_seconds=reader.integer("intervall_s", 30),
        thermal=_thermal(reader.sub("thermik")),
        gpu_shared_services=reader.texts("gpu_dienste_teilen", []),
    )


def _change(reader: Reader) -> Change:
    return Change(time=reader.text("zeit", ""), source=reader.text("quelle", "lokal"), who=reader.text("wer", ""))


def _priority(reader: Reader) -> Priority:
    return Priority(
        name=reader.text("klasse"),
        rank=reader.integer("rang"),
        preemptible=reader.flag("verdraengbar", True),
        minimum=reader.integer("min", 0),
    )


def _target(reader: Reader) -> Target:
    return Target(
        scope=reader.text("art", "repo"),
        name=reader.text("name"),
        runner_group_id=reader.integer("runner_gruppe", 1),
        watched_repos=reader.texts("repos_beobachten", []),
        known_runner_prefixes=reader.texts("bekannte_runner", []),
    )


def _auth(reader: Reader) -> Auth:
    return Auth(
        kind=reader.text("art", "gh"),
        token_file=reader.text("token_datei", ""),
        app_id=reader.integer("app_id", 0),
        app_key_file=reader.text("app_schluessel_datei", ""),
        installation_id=reader.integer("installation_id", 0),
    )


def _network(reader: Reader) -> Network:
    return Network(
        name=reader.text("name", "auditcore-ci"),
        subnet=reader.text("subnetz", "172.30.250.0/24"),
        bridge=reader.text("bruecke", "br-auditcore-ci"),
        enabled=reader.flag("aktiv", True),
        firewall_required=reader.flag("sperre_pflicht", True),
        egress=reader.text("egress", "aus"),
        egress_hosts=reader.texts("egress_hosts", list(DEFAULT_EGRESS_HOSTS)),
        egress_github_meta=reader.texts("egress_github_meta", list(DEFAULT_GITHUB_META)),
        egress_ports=reader.integers("egress_ports", [80, 443]),
    )


def _scale_set(reader: Reader) -> ScaleSetSettings:
    return ScaleSetSettings(
        name_prefix=reader.text("name_praefix", ""),
        runner_group=reader.text("runner_gruppe", "default"),
    )


def _parse_current(reader: Reader) -> Profile:
    reserve = reader.sub("reserve")
    source = reader.sub("soll_quelle")
    classes = reader.sub("klassen")
    return Profile(
        host=reader.text("rechner"),
        target=_target(reader.sub("ziel")),
        auth=_auth(reader.sub("auth")),
        image=reader.text("image"),
        backend=reader.text("backend", "jit"),
        scale_set=_scale_set(reader.sub("scale_set")),
        gpu_access=reader.text("gpu_zugriff", "cdi"),
        reserve_cpus=reserve.integer("cpus"),
        reserve_memory_gb=reserve.integer("speicher_gb"),
        network=_network(reader.sub("netz")),
        source=TargetSource(kind=source.text("art", "statisch"), file=source.text("datei", TargetSource().file)),
        scaling=_scaling(reader.sub("skalierung")),
        classes={name: _class(classes.sub(name)) for name in classes.data},
        gpus=tuple(_gpu(item) for item in reader.items("gpus")),
        priorities=tuple(_priority(item) for item in reader.items("prioritaeten")),
        version=reader.integer("version", 0),
        change=_change(reader.sub("aenderung")),
        sync=reader.text("sync", "aus"),
    )


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


MIGRATIONS = {1: _migrate_1_to_2}


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


def from_json(raw: object) -> Profile:
    data, _ = migrate(raw)
    return _parse_current(Reader(data, "profil"))


def _class_json(runner_class: RunnerClass) -> JsonObject:
    return {
        "aktiv": runner_class.enabled,
        "cpus": runner_class.cpus,
        "speicher_gb": runner_class.memory_gb,
        "min_instanzen": runner_class.min_instances,
        "max_instanzen": runner_class.max_instances,
        "leise_max": runner_class.quiet_max,
        "vram_mb": runner_class.vram_mb,
        "labels": list(runner_class.labels),
        "cpu_shares": runner_class.cpu_shares,
        "nice": runner_class.nice,
        "io_gewicht": runner_class.io_weight,
        "uv_cache_volume": runner_class.uv_cache_volume,
    }


def _thermal_json(thermal: ThermalSource) -> JsonObject:
    return {
        "aktiv": thermal.enabled,
        "url": thermal.url,
        "felder": {
            "drosselung_aktiv": list(thermal.throttling_paths),
            "temperatur": list(thermal.temperature_paths),
            "grenze": list(thermal.limit_paths),
            "modus": thermal.mode_path,
        },
        "leise_wert": thermal.quiet_value,
        "abstand_c": thermal.margin_c,
    }


def _scaling_json(scaling: Scaling) -> JsonObject:
    return {
        "vorrang_interaktiv": scaling.interactive_priority,
        "leerlauf_minuten": scaling.idle_minutes,
        "anteil_bei_nutzung": scaling.share_while_active,
        "interaktive_karten": list(scaling.interactive_cards),
        "interaktive_karten_leerlauf_minuten": scaling.interactive_card_idle_minutes,
        "swap_sperre_gb": scaling.swap_lock_gb,
        "swap_einlagerung_max_s": scaling.swap_in_max_per_s,
        "ram_frei_min_gb": scaling.min_free_memory_gb,
        "last_je_kern_max": scaling.load_per_core_max,
        "temperatur_max_c": scaling.temperature_max_c,
        "volllast_von": scaling.full_power_from_hour,
        "volllast_bis": scaling.full_power_to_hour,
        "freie_reserve": scaling.spare_idle_runners,
        "haltezeit_s": scaling.hold_seconds,
        "intervall_s": scaling.interval_seconds,
        "thermik": _thermal_json(scaling.thermal),
        "gpu_dienste_teilen": list(scaling.gpu_shared_services),
    }


def to_json(profile: Profile) -> JsonObject:
    target, auth, network = profile.target, profile.auth, profile.network
    return {
        "schema": CURRENT_SCHEMA,
        "version": profile.version,
        "aenderung": {"zeit": profile.change.time, "quelle": profile.change.source, "wer": profile.change.who},
        "sync": profile.sync,
        "rechner": profile.host,
        "ziel": {
            "art": target.scope,
            "name": target.name,
            "runner_gruppe": target.runner_group_id,
            "repos_beobachten": list(target.watched_repos),
            "bekannte_runner": list(target.known_runner_prefixes),
        },
        "auth": {
            "art": auth.kind,
            "token_datei": auth.token_file,
            "app_id": auth.app_id,
            "app_schluessel_datei": auth.app_key_file,
            "installation_id": auth.installation_id,
        },
        "image": profile.image,
        "backend": profile.backend,
        "scale_set": {"name_praefix": profile.scale_set.name_prefix, "runner_gruppe": profile.scale_set.runner_group},
        "gpu_zugriff": profile.gpu_access,
        "reserve": {"cpus": profile.reserve_cpus, "speicher_gb": profile.reserve_memory_gb},
        "netz": {
            "name": network.name,
            "subnetz": network.subnet,
            "bruecke": network.bridge,
            "aktiv": network.enabled,
            "sperre_pflicht": network.firewall_required,
            "egress": network.egress,
            "egress_hosts": list(network.egress_hosts),
            "egress_github_meta": list(network.egress_github_meta),
            "egress_ports": list(network.egress_ports),
        },
        "soll_quelle": {"art": profile.source.kind, "datei": profile.source.file},
        "skalierung": _scaling_json(profile.scaling),
        "klassen": {name: _class_json(c) for name, c in profile.classes.items()},
        "gpus": [
            {
                "index": g.index,
                "uuid": g.uuid,
                "name": g.name,
                "vram_mb": g.vram_mb,
                "erlaubt": g.allowed,
                "klasse": g.runner_class,
            }
            for g in profile.gpus
        ],
        "prioritaeten": [
            {"klasse": p.name, "rang": p.rank, "verdraengbar": p.preemptible, "min": p.minimum}
            for p in sorted(profile.priorities, key=lambda p: p.rank)
        ],
    }


def dumps(profile: Profile) -> str:
    return json.dumps(to_json(profile), indent=2, ensure_ascii=False) + "\n"


def content_hash(profile: Profile) -> str:
    """Hash of the settings only (without version and change record) – same content, same hash."""
    data = {k: v for k, v in to_json(profile).items() if k not in {"version", "aenderung"}}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def write_atomic(path: Path, text: str, mode: int = 0o644) -> None:
    """Replace a file atomically so readers never see a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def load(path: Path | None = None) -> Profile:
    target = path or default_profile_path()
    raw: object = json.loads(target.read_text(encoding="utf-8"))
    return from_json(raw)


def save(profile: Profile, path: Path | None = None) -> Path:
    target = path or default_profile_path()
    write_atomic(target, dumps(profile))
    return target
