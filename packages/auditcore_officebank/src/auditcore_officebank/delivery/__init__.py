"""Datenfreies Lieferpaket, Schwärzung und Upload (Etappe 4, Plan Kap. 2.9).

Datenfreiheit wird geprüft, nicht angenommen: hochgeladen wird nur ein Paket,
das ``liefern pruefen`` bestanden hat.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PackageSpec:
    """Inhalt und Benennung eines Lieferpakets (Dateiname ``JJJJMMTT_<Name>_<Version>``)."""

    name: str
    version: str
    date: str
    include: tuple[str, ...]
    exclude: tuple[str, ...] = ()
    layout: Mapping[str, str] = field(default_factory=dict)

    @property
    def file_stem(self) -> str:
        """Dateiname ohne Endung nach dem Muster ``JJJJMMTT_<Name>_<Version>``."""
        return f"{self.date}_{self.name}_{self.version}"


__all__ = ["PackageSpec"]
