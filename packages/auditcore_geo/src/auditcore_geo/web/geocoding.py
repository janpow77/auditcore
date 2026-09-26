"""Adresssuche nur serverseitig und nur auf ausdrücklichen Anschluss (``/geocode``).

Die Schnittstelle kennt nur das Protokoll :class:`Geocoder`; ohne übergebenen
Geocoder ist die Adresssuche abgeschaltet. :class:`NominatimGeocoder`
verbindet den Nominatim-Adapter (Extra ``[geocoder]``) über den
``HarvestEngine`` von ``auditcore_harvest``: Takt, Budget und Tagesgrenze
werden vor jedem Lauf geprüft (:func:`auditcore_geo.nominatim.pruefe_laufparameter`),
Ergebnisse je Anfragetext zwischengespeichert (OSMF-Bedingung), die
Anfragen einzeln nacheinander gestellt. Transport, Uhr und Warten injiziert
der Server.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from auditcore_harvest import Clock, HarvestEngine, Sleeper, Transport


class GeocoderError(RuntimeError):
    """Adresssuche nicht möglich (Tagesgrenze, Dienstfehler)."""

    def __init__(self, message: str, *, status: int, code: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


@runtime_checkable
class Geocoder(Protocol):
    """Anschluss für die Adresssuche; ``suchen`` liefert Treffer in Dienstreihenfolge."""

    @property
    def attribution(self) -> str:
        """Pflichtnennung der Datenquelle, die die Oberfläche anzeigt."""
        ...

    def search(self, anfrage: str) -> list[dict[str, object]]:
        """Treffer ``{"rang", "lat", "lon", "anzeigename"}``; leere Liste = kein Treffer."""
        ...


def _hit(entry: Mapping[str, object]) -> dict[str, object]:
    return {
        "rang": entry.get("rang"),
        "lat": entry.get("lat"),
        "lon": entry.get("lon"),
        "anzeigename": entry.get("anzeigename"),
    }


@dataclass
class NominatimGeocoder:
    """Nominatim über ``auditcore_harvest`` (Extra ``[geocoder]``).

    ``user_agent`` muss die Anwendung identifizieren. ``basis_url`` ist der
    öffentliche Dienst, wenn nicht anders angegeben; dort gelten ≥ 1 s Abstand
    und höchstens 1 000 Anfragen je Tag (D5). ``sent_today``
    übernimmt einen Zählerstand des Servers (z. B. nach Neustart).
    """

    transport: Transport
    clock: Clock
    sleeper: Sleeper
    user_agent: str
    basis_url: str | None = None
    countrycodes: str | None = "de"
    limit: int = 5
    sent_today: int = 0
    _cache: dict[str, list[dict[str, object]]] = field(default_factory=dict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _day: str = field(default="", repr=False)
    _runs: int = field(default=0, repr=False)
    _engine: HarvestEngine | None = field(default=None, repr=False)

    @property
    def attribution(self) -> str:
        """Pflichtnennung der Daten (ODbL)."""
        from ..nominatim import NAMENSNENNUNG

        return NAMENSNENNUNG

    def _config(self, anfrage: str) -> dict[str, object]:
        config: dict[str, object] = {
            "anfragen": [{"id": "suche-1", "q": anfrage}],
            "user_agent": self.user_agent,
            "budget": 1,
            "laufart": "einmalig",
            "limit": self.limit,
        }
        if self.basis_url:
            config["basis_url"] = self.basis_url
        if self.countrycodes:
            config["countrycodes"] = self.countrycodes
        return config

    def _count_today(self) -> None:
        day = self.clock.now().date().isoformat()
        if day != self._day:
            if self._day:
                self.sent_today = 0
            self._day = day

    def search(self, anfrage: str) -> list[dict[str, object]]:
        """Eine Suche; wiederholte Anfragen kommen aus dem Zwischenspeicher."""
        key = " ".join(anfrage.split()).casefold()
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            self._count_today()
            hits = self._run(anfrage)
            self._cache[key] = hits
            return hits

    def _run(self, anfrage: str) -> list[dict[str, object]]:
        from auditcore_harvest import ConfigError, HarvestEngine
        from auditcore_harvest.memory import ListSink, MemoryStateStore, StaticCredentials

        from ..nominatim import NominatimAdapter, empfohlene_laufparameter

        config = self._config(anfrage)
        self._runs += 1
        try:
            rate, request = empfohlene_laufparameter(
                config, f"suche-{self._runs}", heute_bereits_gesendet=self.sent_today
            )
        except ConfigError as exc:
            raise GeocoderError(str(exc), status=429, code="geocoder_grenze") from exc
        if self._engine is None:
            self._engine = HarvestEngine(
                self.transport,
                StaticCredentials({}),
                MemoryStateStore(),
                self.clock,
                self.sleeper,
                rate_limit=rate,
            )
        sink = ListSink()
        result = self._engine.run(NominatimAdapter(), request, sink, config=config)
        self.sent_today += 1
        records = list(sink.records.values())
        if not records:
            raise GeocoderError(
                f"Geocoder nicht erreichbar ({result.status.value}).",
                status=502,
                code="geocoder_fehler",
            )
        normalized = records[0].normalized
        treffer = normalized.get("treffer") if isinstance(normalized, Mapping) else None
        entries: Sequence[object] = treffer if isinstance(treffer, list) else []
        return [_hit(entry) for entry in entries if isinstance(entry, Mapping)]
