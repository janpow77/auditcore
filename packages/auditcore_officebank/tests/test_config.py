"""Rechnerprofil und Projektdatei: Schema, Pflichtangaben, Fehlermeldungen."""

from __future__ import annotations

from pathlib import Path

import pytest

from auditcore_officebank import (
    ConfigError,
    SecretRef,
    load_host_profile,
    load_project,
    parse_host_profile,
    parse_project,
)
from auditcore_officebank.config import read_toml


def test_host_profile_is_parsed(host_file: Path) -> None:
    profile = load_host_profile(host_file)
    assert profile.vm_name == "testgast"
    assert profile.vm_backend == "utm"
    assert profile.exchange_port == 8765
    assert profile.endpoints["oeffentlich"].token == SecretRef("beispiel-mcp")
    assert profile.upload_targets == {"lieferung": "beispiel-remote:lieferungen"}


def test_host_profile_optional_tables_may_be_missing(host_data: dict[str, object]) -> None:
    del host_data["mcp"], host_data["upload"]
    profile = parse_host_profile(host_data)
    assert profile.endpoints == {}
    assert profile.upload_targets == {}


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"schema": "auditcore-officebank/rechner/0"}, "nicht unterstützt"),
        ({"vm": "kein-tabelle"}, "[vm]"),
        ({"vm": {"name": "x", "backend": "hyperv"}}, "nicht erlaubt"),
        ({"vm": {"name": " ", "backend": "utm"}}, "„name“"),
        ({"austausch": {"bind": "192.0.2.1", "port": 0}}, "„port“"),
        ({"austausch": {"bind": "192.0.2.1", "port": True}}, "„port“"),
        ({"mcp": {"endpunkte": {"a": "url"}}}, "Endpunkt „a“"),
        ({"autor": {}}, "kopfkommentar"),
    ],
)
def test_host_profile_errors(
    host_data: dict[str, object], changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ConfigError) as caught:
        parse_host_profile({**host_data, **changes})
    assert message in str(caught.value)


def test_project_from_directory(project_dir: Path) -> None:
    project = load_project(project_dir)
    assert project.code == "P-DEMO"
    assert project.host == "access"
    assert project.source_dir == project_dir / "src"
    assert project.modules == ("modBasis", "modAuswertung")
    assert project.module_list == project_dir / "MODULLISTE.md"
    assert project.lint_profile == "access"
    assert project.reserved == ("datenschutz",)


def test_project_from_file_with_defaults(project_dir: Path) -> None:
    file = project_dir / ".officebank.toml"
    file.write_text(
        'schema = "auditcore-officebank/projekt/1"\n'
        '[projekt]\nkuerzel = "P-X"\nhost = "excel"\nquelle = "src/vba"\n'
        '[lint]\nprofil = "excel2016"\n',
        encoding="utf-8",
    )
    project = load_project(file)
    assert project.source_dir == project_dir / "src/vba"
    assert project.modules == ()
    assert project.module_list is None
    assert project.lint_profile == "excel2016"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"schema": None}, "nicht unterstützt"),
        ({"unbekannt": {}}, "Unbekannte Einträge"),
        ({"projekt": {"kuerzel": "P", "host": "powerpoint"}}, "nicht erlaubt"),
        ({"module": {"reihenfolge": "modA"}}, "Liste"),
        ({"module": {"reihenfolge": ["modA", "modA"]}}, "doppelte"),
        ({"module": {"modulliste": 3}}, "modulliste"),
    ],
)
def test_project_errors(
    project_data: dict[str, object], changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ConfigError) as caught:
        parse_project({**project_data, **changes}, Path("."))
    assert message in str(caught.value)


def test_read_toml_errors(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Datei fehlt"):
        read_toml(tmp_path / "fehlt.toml")
    broken = tmp_path / "kaputt.toml"
    broken.write_text("schema = \n", encoding="utf-8")
    with pytest.raises(ConfigError, match="nicht lesbar"):
        read_toml(broken)
