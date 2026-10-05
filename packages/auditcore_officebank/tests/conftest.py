"""Synthetische Konfigurationen; keine echten Rechner-, Netz- oder Projektangaben."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

HOST_TOML = """
schema = "auditcore-officebank/rechner/1"

[vm]
name = "testgast"
backend = "utm"

[austausch]
bind = "192.0.2.1"
port = 8765

[autor]
kopfkommentar = "Erstellt von Beispiel. Kontakt: beispiel@example.invalid"

[mcp.endpunkte.oeffentlich]
url = "https://mcp.example.invalid/mcp"
token = "beispiel-mcp"

[upload]
lieferung = "beispiel-remote:lieferungen"
"""

PROJECT_TOML = """
schema = "auditcore-officebank/projekt/1"

[projekt]
kuerzel = "P-DEMO"
host = "access"

[module]
reihenfolge = ["modBasis", "modAuswertung"]
modulliste = "MODULLISTE.md"

[datenschutz]
"""


@pytest.fixture
def host_file(tmp_path: Path) -> Path:
    path = tmp_path / "profil.toml"
    path.write_text(HOST_TOML, encoding="utf-8")
    return path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    root = tmp_path / "projekt"
    root.mkdir()
    (root / ".officebank.toml").write_text(PROJECT_TOML, encoding="utf-8")
    return root


@pytest.fixture
def host_data() -> dict[str, object]:
    return tomllib.loads(HOST_TOML)


@pytest.fixture
def project_data() -> dict[str, object]:
    return tomllib.loads(PROJECT_TOML)
