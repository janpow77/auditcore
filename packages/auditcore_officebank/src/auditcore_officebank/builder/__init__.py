"""Inkrementeller Build nur aus committeten Ständen (Etappe 4, Plan Kap. 2.6).

Heißt `builder` statt `build`, weil `build/` im Repo ignoriert wird.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

InputKind = Literal["module", "query", "text", "data"]


@dataclass(frozen=True)
class BuildInput:
    """Eine Build-Eingabe mit Pfad im Repo und SHA-256 des committeten Inhalts."""

    path: str
    sha256: str
    kind: InputKind


__all__ = ["BuildInput", "InputKind"]
