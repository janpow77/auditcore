"""Generischer SQL-Server-Testdienst im Container (Etappe 5, Plan Kap. 2.5).

Öffentlich ist nur der generische Dienst (Entscheidung E05). Client-spezifische
Prüfpunkte stehen als privates Projektprofil im jeweiligen Projekt-Repo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MssqlService:
    """Containerdienst; der Port wird nur an ``bind_address`` gebunden, nie an alle."""

    name: str
    bind_address: str
    port: int
    data_dir: Path
    backup_dir: Path
    edition: str = "Developer"


__all__ = ["MssqlService"]
