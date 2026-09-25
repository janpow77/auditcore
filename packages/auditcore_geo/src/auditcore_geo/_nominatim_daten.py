"""Nominatim ohne Netz und ohne Harvest-Kern: Bedingungen, Anfragen und Trefferdaten.

:mod:`auditcore_geo.nominatim` gibt alle öffentlichen Namen dieses Moduls
wieder aus; nur dort wird ``auditcore_harvest`` importiert.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from urllib.parse import urlsplit

OEFFENTLICHER_ENDPUNKT = "https://nominatim.openstreetmap.org"
NUTZUNGSBEDINGUNGEN_URL = "https://operations.osmfoundation.org/policies/nominatim/"
NAMENSNENNUNG = "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright"
#: Mindestabstand zweier Anfragen am öffentlichen Endpunkt (Sekunden).
MINDESTABSTAND_EINMALIG_S = 1.0
#: Läufe über einen Tag oder regelmäßig: höchstens 4 Anfragen je Minute.
MINDESTABSTAND_REGELMAESSIG_S = 15.0
#: Entscheidung vom 23.09.2026 (vom Nutzer delegiert): höchstens 1 000 Anfragen je
#: Tag und Consumer am öffentlichen Endpunkt; darüber eigene Instanz oder Import.
OEFFENTLICH_TAGESGRENZE = 1000
LAUFARTEN = ("einmalig", "regelmaessig")
STRUKTUR_FELDER = ("street", "city", "county", "state", "country", "postalcode")
#: Standardkennungen von HTTP-Bibliotheken und Browsern identifizieren keine Anwendung.
_STANDARDKENNUNG = re.compile(
    r"^\s*(python-requests|python-urllib|python-httpx|httpx|aiohttp|curl|wget|"
    r"java|go-http-client|okhttp|mozilla/5\.0)\b",
    re.IGNORECASE,
)
_LAENDERCODES = re.compile(r"^[a-z]{2}(,[a-z]{2})*$")
_ANFRAGE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")


@dataclass(frozen=True)
class Anfrage:
    """Eine Geocodieranfrage mit stabiler Kennung des Consumers."""

    anfrage_id: str
    q: str | None = None
    strukturiert: Mapping[str, str] | None = None

    def parameter(self) -> dict[str, str]:
        """Suchparameter (Freitext ``q`` oder strukturierte Felder)."""
        if self.q is not None:
            return {"q": self.q}
        return dict(sorted((self.strukturiert or {}).items()))


def ist_oeffentlicher_endpunkt(basis_url: str) -> bool:
    """Wird der Dienst der OSMF angesprochen (für den die Nutzungsbedingungen gelten)?"""
    return (urlsplit(basis_url).hostname or "").lower() == "nominatim.openstreetmap.org"


def _zahl(wert: object) -> float | None:
    """Endliche Zahl aus einem JSON-Wert (Zahl oder Text), sonst ``None``."""
    if not isinstance(wert, (int, float, str)):
        return None
    try:
        zahl = float(wert)
    except ValueError:
        return None
    return zahl if math.isfinite(zahl) else None


def _rahmen(box: object) -> dict[str, float | None] | None:
    """``boundingbox`` (Süd, Nord, West, Ost) nur, wenn alle vier Werte Zahlen sind."""
    if not isinstance(box, Sequence) or isinstance(box, str) or len(box) != 4:
        return None
    werte = [_zahl(v) for v in box]
    if not all(w is not None for w in werte):
        return None
    return dict(zip(("sued", "nord", "west", "ost"), werte, strict=True))


def _ein_treffer(
    rang: int, eintrag: Mapping[str, object], lat: float, lon: float
) -> dict[str, object]:
    return {
        "rang": rang,
        "lat": lat,
        "lon": lon,
        "achsenfolge": "lat_lon",
        "anzeigename": eintrag.get("display_name"),
        "osm_typ": eintrag.get("osm_type"),
        "osm_id": eintrag.get("osm_id"),
        "kategorie": eintrag.get("category", eintrag.get("class")),
        "typ": eintrag.get("type"),
        "adresstyp": eintrag.get("addresstype"),
        "place_rank": eintrag.get("place_rank"),
        "importance": _zahl(eintrag.get("importance")),
        "rahmen": _rahmen(eintrag.get("boundingbox")),
        "adresse": eintrag.get("address") if isinstance(eintrag.get("address"), Mapping) else None,
    }
