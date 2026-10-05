"""Rechnerprofil und Projektdatei (``.officebank.toml``) mit Schemaversion.

Das **Rechnerprofil** (Standard ``~/.config/auditcore-officebank/profil.toml``)
enthält alles, was vom Rechner abhängt: VM, Austauschserver, MCP-Endpunkte,
Upload-Ziele und den Kopfkommentar des Autors. Die **Projektdatei** liegt im
Projekt-Repo und enthält nur Projektangaben. Secrets stehen in keiner der beiden
Dateien; Konfigurationen nennen nur den *Namen* eines Secrets (:class:`SecretRef`).

Etappe 0 kennt nur Schemaversion 1. Spätere Versionen werden über
:func:`migrate` angehoben; unbekannte Versionen sind ein Fehler.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from .errors import ConfigError

HOST_SCHEMA = "auditcore-officebank/rechner/1"
PROJECT_SCHEMA = "auditcore-officebank/projekt/1"
DEFAULT_HOST_PROFILE = Path("~/.config/auditcore-officebank/profil.toml")
PROJECT_FILE = ".officebank.toml"
OFFICE_HOSTS = ("excel", "access", "word")
VM_BACKENDS = ("utm",)
#: Tabellen der Projektdatei, die spätere Etappen auswerten; Etappe 0 lässt sie unberührt.
RESERVED_PROJECT_TABLES = (
    "datenschutz",
    "gast",
    "schritte",
    "dialogregeln",
    "build",
    "paket",
    "schwaerzung",
    "upload",
)

Table: TypeAlias = Mapping[str, object]


@dataclass(frozen=True)
class SecretRef:
    """Name eines Secrets in Umgebung oder Schlüsselbund, nie der Wert."""

    name: str


@dataclass(frozen=True)
class Endpoint:
    """MCP-Endpunkt mit Adresse und Verweis auf das Token."""

    url: str
    token: SecretRef


@dataclass(frozen=True)
class HostProfile:
    """Rechnerabhängige Einstellungen; gehört nie in ein Projekt-Repo."""

    vm_name: str
    vm_backend: str
    exchange_bind: str
    exchange_port: int
    author_header: str
    endpoints: Mapping[str, Endpoint]
    upload_targets: Mapping[str, str]


@dataclass(frozen=True)
class ProjectConfig:
    """Projektangaben aus ``.officebank.toml``."""

    code: str
    host: str
    source_dir: Path
    modules: tuple[str, ...]
    module_list: Path | None
    lint_profile: str
    reserved: tuple[str, ...]


def read_toml(path: Path) -> dict[str, object]:
    """Liest eine TOML-Datei; Lese- und Syntaxfehler werden zu :class:`ConfigError`."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Datei fehlt: {path.name}") from exc
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"{path.name} ist nicht lesbar: {exc}") from exc


def migrate(data: Mapping[str, object], expected: str) -> Mapping[str, object]:
    """Hebt ältere Schemaversionen an; in Fassung 0.1 gibt es nur Version 1."""
    found = data.get("schema")
    if found != expected:
        raise ConfigError(f"Schema „{found}“ wird nicht unterstützt, erwartet „{expected}“")
    return data


def _table(data: Table, key: str, *, required: bool = True) -> Table:
    value = data.get(key, None if required else {})
    if not isinstance(value, Mapping):
        raise ConfigError(f"Tabelle [{key}] fehlt oder ist keine Tabelle")
    return value


def _text(data: Table, key: str, default: str | None = None) -> str:
    value = data.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"„{key}“ fehlt oder ist kein Text")
    return value


def _choice(data: Table, key: str, allowed: tuple[str, ...]) -> str:
    value = _text(data, key)
    if value not in allowed:
        raise ConfigError(f"„{key}“ = „{value}“ ist nicht erlaubt ({', '.join(allowed)})")
    return value


def _port(data: Table) -> int:
    value = data.get("port")
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 65535:
        raise ConfigError("„port“ muss eine Ganzzahl zwischen 1 und 65535 sein")
    return value


def _endpoints(data: Table) -> dict[str, Endpoint]:
    result = {}
    for name, entry in _table(data, "endpunkte", required=False).items():
        if not isinstance(entry, Mapping):
            raise ConfigError(f"Endpunkt „{name}“ ist keine Tabelle")
        result[name] = Endpoint(_text(entry, "url"), SecretRef(_text(entry, "token")))
    return result


def parse_host_profile(data: Mapping[str, object]) -> HostProfile:
    """Prüft ein eingelesenes Rechnerprofil und gibt es typisiert zurück."""
    data = migrate(data, HOST_SCHEMA)
    vm = _table(data, "vm")
    exchange = _table(data, "austausch")
    targets = _table(data, "upload", required=False)
    return HostProfile(
        vm_name=_text(vm, "name"),
        vm_backend=_choice(vm, "backend", VM_BACKENDS),
        exchange_bind=_text(exchange, "bind"),
        exchange_port=_port(exchange),
        author_header=_text(_table(data, "autor"), "kopfkommentar"),
        endpoints=_endpoints(_table(data, "mcp", required=False)),
        upload_targets={name: _text(targets, name) for name in targets},
    )


def _modules(data: Table) -> tuple[str, ...]:
    value = data.get("reihenfolge", [])
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise ConfigError("[module] reihenfolge muss eine Liste von Modulnamen sein")
    if len(set(value)) != len(value):
        raise ConfigError("[module] reihenfolge enthält doppelte Module")
    return tuple(value)


def parse_project(data: Mapping[str, object], root: Path) -> ProjectConfig:
    """Prüft eine eingelesene Projektdatei; Pfade werden relativ zu ``root`` gelesen."""
    data = migrate(data, PROJECT_SCHEMA)
    known = {"schema", "projekt", "module", "lint", *RESERVED_PROJECT_TABLES}
    unknown = sorted(set(data) - known)
    if unknown:
        raise ConfigError(f"Unbekannte Einträge in der Projektdatei: {', '.join(unknown)}")
    project = _table(data, "projekt")
    modules = _table(data, "module", required=False)
    host = _choice(project, "host", OFFICE_HOSTS)
    module_list = modules.get("modulliste")
    if module_list is not None and not isinstance(module_list, str):
        raise ConfigError("[module] modulliste muss ein Pfad sein")
    return ProjectConfig(
        code=_text(project, "kuerzel"),
        host=host,
        source_dir=root / _text(project, "quelle", "src"),
        modules=_modules(modules),
        module_list=root / module_list if module_list else None,
        lint_profile=_text(_table(data, "lint", required=False), "profil", host),
        reserved=tuple(name for name in RESERVED_PROJECT_TABLES if name in data),
    )


def load_host_profile(path: Path = DEFAULT_HOST_PROFILE) -> HostProfile:
    """Liest das Rechnerprofil (Standardpfad im Benutzerverzeichnis)."""
    return parse_host_profile(read_toml(path.expanduser()))


def load_project(path: Path) -> ProjectConfig:
    """Liest ``.officebank.toml``; ``path`` darf die Datei oder ihr Ordner sein."""
    file = path / PROJECT_FILE if path.is_dir() else path
    return parse_project(read_toml(file), file.parent)
