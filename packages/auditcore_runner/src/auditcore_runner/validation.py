"""One validation for CLI and web UI: a profile must be consistent and fit its machine."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

from .hardware import HostFacts
from .profile import (
    AUTH_KINDS,
    BACKENDS,
    CHANGE_SOURCES,
    CLASS_KINDS,
    CLASS_NAME,
    EGRESS_MODES,
    GPU_ACCESS,
    SCOPES,
    SYNC_MODES,
    TARGET_SOURCES,
    Auth,
    Profile,
    RunnerClass,
    Scaling,
    Target,
)
from .werkzeuge.modell import DEFAULT_PROFILES

LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
DOCKER_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$")
REPO = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$")
ORG = re.compile(r"^[A-Za-z0-9-]+$")
BRIDGE = re.compile(r"^[a-z0-9-]{1,15}$")
HOSTNAME = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
META_KEYS = ("api", "web", "git", "packages", "actions", "pages", "importer", "dependabot", "hooks")
IMAGE = re.compile(r"^[a-z0-9][a-z0-9._/:@-]{0,254}$")


@dataclass(frozen=True)
class Problem:
    """A finding; ``field`` is the path in the profile file."""

    field: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"feld": self.field, "meldung": self.message}


class Findings(list[Problem]):
    def add(self, field: str, message: str) -> None:
        self.append(Problem(field, message))

    def within(self, field: str, value: float, low: float, high: float) -> None:
        if not low <= value <= high:
            self.add(field, f"muss zwischen {low:g} und {high:g} liegen (ist {value:g})")


def _path_like(value: str) -> bool:
    return value.startswith(("/", "~/"))


def _target(found: Findings, target: Target) -> None:
    if target.scope not in SCOPES:
        found.add("ziel.art", "repo oder org")
    pattern = REPO if target.scope == "repo" else ORG
    if not pattern.fullmatch(target.name):
        found.add("ziel.name", "Form <owner>/<repo>" if target.scope == "repo" else "Organisationsname")
    prefixes = [p for p in target.known_runner_prefixes if not LABEL.fullmatch(p.rstrip("-"))]
    if prefixes:
        found.add("ziel.bekannte_runner", "ungültige Präfixe: " + ", ".join(prefixes))
    bad = [r for r in target.watched_repos if not REPO.fullmatch(r)]
    if bad:
        found.add("ziel.repos_beobachten", "ungültig: " + ", ".join(bad))
    found.within("ziel.runner_gruppe", target.runner_group_id, 1, 10**9)


def _auth(found: Findings, auth: Auth, target: Target) -> None:
    if auth.kind not in AUTH_KINDS:
        found.add("auth.art", "gh, pat oder app")
    if auth.kind == "pat" and not _path_like(auth.token_file):
        found.add("auth.token_datei", "Pfad zur Token-Datei (absolut oder ~/…) erwartet")
    if auth.kind == "app":
        if auth.app_id <= 0 or auth.installation_id <= 0:
            found.add("auth", "app_id und installation_id der GitHub App angeben")
        if not _path_like(auth.app_key_file):
            found.add("auth.app_schluessel_datei", "Pfad zum privaten Schlüssel erwartet")
    if target.scope == "org" and auth.kind == "gh":
        found.add("auth.art", "Organisations-Runner brauchen pat oder app")


def _class(found: Findings, name: str, runner_class: RunnerClass) -> None:
    field = f"klassen.{name}"
    if not CLASS_NAME.fullmatch(name):
        found.add(field, "Klassenname: a–z, 0–9, Bindestrich, höchstens 31 Zeichen")
    if runner_class.kind not in CLASS_KINDS:
        found.add(f"{field}.art", "cpu oder gpu")
    if runner_class.kind == "cpu" and runner_class.vram_mb:
        found.add(f"{field}.vram_mb", "nur für Klassen der Art gpu")
    found.within(f"{field}.cpus", runner_class.cpus, 1, 64)
    found.within(f"{field}.speicher_gb", runner_class.memory_gb, 1, 256)
    found.within(f"{field}.max_instanzen", runner_class.max_instances, 0, 32)
    found.within(f"{field}.leise_max", runner_class.quiet_max, -1, 32)
    found.within(f"{field}.min_instanzen", runner_class.min_instances, 0, runner_class.max_instances)
    found.within(f"{field}.vram_mb", runner_class.vram_mb, 0, 262144)
    found.within(f"{field}.cpu_shares", runner_class.cpu_shares, 2, 1024)
    found.within(f"{field}.nice", runner_class.nice, 0, 19)
    found.within(f"{field}.io_gewicht", runner_class.io_weight, 1, 10000)
    if "self-hosted" not in runner_class.labels:
        found.add(f"{field}.labels", "Label self-hosted fehlt")
    bad = [label for label in runner_class.labels if not LABEL.fullmatch(label)]
    if bad or len(set(runner_class.labels)) != len(runner_class.labels):
        found.add(f"{field}.labels", "ungültig oder doppelt: " + ", ".join(bad or ["Dublette"]))
    volume = runner_class.uv_cache_volume
    if volume and not DOCKER_NAME.fullmatch(volume):
        found.add(f"{field}.uv_cache_volume", "ungültiger Volume-Name")


def _budget(found: Findings, profile: Profile, facts: HostFacts) -> None:
    active = [c for c in profile.classes.values() if c.enabled]
    cpus = sum(c.cpus * c.max_instances for c in active)
    memory = sum(c.memory_gb * c.max_instances for c in active)
    cpu_budget = facts.cpu_count - profile.reserve_cpus
    memory_budget = facts.memory_mb // 1024 - profile.reserve_memory_gb
    if cpus > cpu_budget:
        found.add("klassen", f"{cpus} CPUs zugesagt, verfügbar {cpu_budget} (Kerne minus Reserve)")
    if memory > memory_budget:
        found.add("klassen", f"{memory} GB zugesagt, verfügbar {memory_budget} GB (RAM minus Reserve)")


def _gpus(found: Findings, profile: Profile, facts: HostFacts) -> None:
    present = {g.uuid for g in facts.gpus}
    for index, gpu in enumerate(profile.gpus):
        if gpu.uuid not in present:
            found.add(f"gpus[{index}].uuid", "Karte auf diesem Rechner nicht gefunden")
        if gpu.runner_class not in profile.gpu_classes():
            found.add(f"gpus[{index}].klasse", "Klasse der Art gpu erwartet: " + ", ".join(profile.gpu_classes()))
    for name in profile.gpu_classes():
        runner_class = profile.classes.get(name)
        cards = len(profile.gpus_of(name))
        if runner_class and runner_class.enabled and runner_class.max_instances > cards:
            found.add(f"klassen.{name}.max_instanzen", f"höchstens {cards} (erlaubte Karten)")
        largest = max((g.vram_mb for g in profile.gpus_of(name)), default=0)
        if runner_class and runner_class.enabled and runner_class.vram_mb > largest:
            found.add(f"klassen.{name}.vram_mb", f"größer als jede erlaubte Karte ({largest} MB)")


def _network(found: Findings, profile: Profile) -> None:
    network = profile.network
    if not DOCKER_NAME.fullmatch(network.name):
        found.add("netz.name", "ungültiger Netzname")
    if not BRIDGE.fullmatch(network.bridge):
        found.add("netz.bruecke", "höchstens 15 Zeichen, a–z, 0–9, Bindestrich")
    try:
        subnet = ipaddress.ip_network(network.subnet)
    except ValueError:
        found.add("netz.subnetz", "kein gültiges Subnetz")
        return
    if not subnet.is_private or subnet.prefixlen > 28:
        found.add("netz.subnetz", "privates Subnetz mit mindestens /28 erwartet")
    if network.firewall_required and not network.enabled:
        found.add("netz.sperre_pflicht", "Netzsperre verlangt ein aktives Netz")
    _egress(found, profile)


def _egress(found: Findings, profile: Profile) -> None:
    network = profile.network
    if network.egress not in EGRESS_MODES:
        found.add("netz.egress", "aus oder allowlist")
    if network.egress == "allowlist" and not network.enabled:
        found.add("netz.egress", "Allowlist verlangt ein aktives Netz")
    bad_hosts = [h for h in network.egress_hosts if not HOSTNAME.fullmatch(h)]
    if bad_hosts:
        found.add("netz.egress_hosts", "keine Hostnamen: " + ", ".join(bad_hosts))
    bad_keys = [k for k in network.egress_github_meta if k not in META_KEYS]
    if bad_keys:
        found.add("netz.egress_github_meta", "unbekannt: " + ", ".join(bad_keys))
    if not network.egress_ports or any(not 1 <= port <= 65535 for port in network.egress_ports):
        found.add("netz.egress_ports", "Ports 1–65535 erwartet")


def _scaling(found: Findings, scaling: Scaling) -> None:
    found.within("skalierung.leerlauf_minuten", scaling.idle_minutes, 1, 240)
    found.within("skalierung.interaktive_karten_leerlauf_minuten", scaling.interactive_card_idle_minutes, 1, 240)
    found.within("skalierung.anteil_bei_nutzung", scaling.share_while_active, 0.0, 1.0)
    found.within("skalierung.swap_sperre_gb", scaling.swap_lock_gb, 0.0, 1024.0)
    found.within("skalierung.swap_einlagerung_max_s", scaling.swap_in_max_per_s, 0.0, 1_000_000.0)
    found.within("skalierung.ram_frei_min_gb", scaling.min_free_memory_gb, 0.0, 1024.0)
    found.within("skalierung.last_je_kern_max", scaling.load_per_core_max, 0.1, 8.0)
    found.within("skalierung.temperatur_max_c", scaling.temperature_max_c, 40.0, 110.0)
    found.within("skalierung.volllast_von", scaling.full_power_from_hour, 0, 23)
    found.within("skalierung.volllast_bis", scaling.full_power_to_hour, 0, 24)
    found.within("skalierung.freie_reserve", scaling.spare_idle_runners, 0, 8)
    found.within("skalierung.haltezeit_s", scaling.hold_seconds, 0, 86400)
    found.within("skalierung.intervall_s", scaling.interval_seconds, 5, 3600)
    thermal = scaling.thermal
    found.within("skalierung.thermik.abstand_c", thermal.margin_c, 0.0, 30.0)
    if thermal.enabled and not thermal.url.startswith(("http://", "https://")):
        found.add("skalierung.thermik.url", "http(s)-Adresse erwartet")
    if thermal.enabled and not (thermal.throttling_paths or thermal.temperature_paths or thermal.mode_path):
        found.add("skalierung.thermik.felder", "mindestens ein Feld zuordnen")


def _priorities(found: Findings, profile: Profile) -> None:
    known = set(profile.classes) | set(DEFAULT_PROFILES)
    names = [p.name for p in profile.priorities]
    for index, priority in enumerate(profile.priorities):
        if priority.name not in known:
            found.add(f"prioritaeten[{index}].klasse", "unbekannte Klasse bzw. unbekanntes Prüfprofil")
        found.within(f"prioritaeten[{index}].rang", priority.rank, 1, 100)
        found.within(f"prioritaeten[{index}].min", priority.minimum, 0, 32)
    if len(set(names)) != len(names):
        found.add("prioritaeten", "Eintrag doppelt")


def _scale_set(found: Findings, profile: Profile) -> None:
    for name in profile.classes:
        if not LABEL.fullmatch(profile.scale_set_name(name)):
            found.add("scale_set.name_praefix", f"ergibt ungültigen Scale-Set-Namen für {name}")
    if not profile.scale_set.runner_group.strip():
        found.add("scale_set.runner_gruppe", "Name der Runner-Gruppe erwartet")
    if profile.backend == "scaleset" and profile.target.scope == "repo" and profile.scale_set.runner_group != "default":
        found.add("scale_set.runner_gruppe", "Repositories kennen nur die Gruppe „default“")


def validate(profile: Profile, facts: HostFacts) -> list[Problem]:
    """All findings; an empty list means the profile may be applied."""
    found = Findings()
    _target(found, profile.target)
    _auth(found, profile.auth, profile.target)
    if not IMAGE.fullmatch(profile.image):
        found.add("image", "ungültiger Image-Name")
    if profile.sync not in SYNC_MODES:
        found.add("sync", "aus oder flow-agent")
    if profile.change.source not in CHANGE_SOURCES:
        found.add("aenderung.quelle", "lokal oder flow-agent")
    if profile.backend not in BACKENDS:
        found.add("backend", "verfügbar: " + ", ".join(BACKENDS))
    if profile.gpu_access not in GPU_ACCESS:
        found.add("gpu_zugriff", "cdi oder gpus")
    _scale_set(found, profile)
    if profile.source.kind not in TARGET_SOURCES:
        found.add("soll_quelle.art", "statisch, lokal oder datei")
    if profile.source.kind == "datei" and not _path_like(profile.source.file):
        found.add("soll_quelle.datei", "Pfad erwartet")
    found.within("reserve.cpus", profile.reserve_cpus, 0, 256)
    found.within("reserve.speicher_gb", profile.reserve_memory_gb, 0, 1024)
    for name, runner_class in profile.classes.items():
        _class(found, name, runner_class)
    _budget(found, profile, facts)
    _gpus(found, profile, facts)
    _network(found, profile)
    _scaling(found, profile.scaling)
    _priorities(found, profile)
    indices = {g.index for g in facts.gpus}
    bad = [i for i in profile.scaling.interactive_cards if i not in indices]
    if bad:
        found.add("skalierung.interaktive_karten", "Karten nicht vorhanden: " + ", ".join(map(str, bad)))
    return list(found)
