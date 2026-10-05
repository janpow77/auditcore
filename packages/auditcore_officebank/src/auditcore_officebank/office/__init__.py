"""Office-Automation für Excel (Windows und macOS), Access und Word.

Geplant für Etappe 3 (Plan, Kap. 2.2–2.4). Eine xlsm wird nur über das
Excel-Objektmodell geändert; openpyxl (Extra ``[xlsx]``) ist nur lesend erlaubt.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class ModuleSet:
    """Geordnete Menge von VBA-Modulen aus einem Quellordner (Bearbeitungsfassung ASCII)."""

    names: tuple[str, ...]
    source_dir: Path
    encoding: Literal["ascii"] = "ascii"


__all__ = ["ModuleSet"]
