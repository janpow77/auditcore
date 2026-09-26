"""bienici.com: French rental ads from the portal's JSON search (realEstateAds.json).

Profile ``property.bienici`` — characterized from
``janpow77/wohnungsmonitor@76571bf`` ``bienici_export.py`` (``normalise``,
``_datum``, ``_ortsform``, ``_adresse``, request filters of ``hole_bestand``).

Price semantics of the source: ``price`` is the warm rent (*charges
comprises*), ``charges`` the included service charge, ``rentWithoutCharges``
the cold rent; a missing cold rent is derived as ``price − charges``; without
charges the cold rent stays unknown and the price counts as warm. The
publication date 1970-01-01 means "unknown". Positions are blurred (~50 m) by
the portal.

Advertiser names (PS-C02, DECIDED 2026-09-23 by the user): the default
``advertiser_names="legacy"`` keeps the display name of private advertisers
like the original; ``advertiser_names="minimal"`` replaces it for
``accountType == "individual"`` by "Privatangebot".

Access (PS-D02, DECIDED 2026-09-23 by the user): the portal answers its own
identifier with 403, so the original sends a browser user agent.
:func:`request_headers` reproduces the original request headers; the adapter
sends them by default.
"""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.parse
from collections.abc import Mapping, Sequence
from typing import Literal

from ._types import JSON

SOURCE_ID = "property.bienici"
PROFILE_VERSION = "2026.09.1"
BASE = "https://www.bienici.com"
SEARCH = BASE + "/realEstateAds.json?filters={filter}"
AD = BASE + "/annonce/{kennung}"
AD_LONG = BASE + "/annonce/{art_geschaeft}/{ort}/{art}/{zimmer}/{kennung}"
QUELLE = "bienici"
DEFAULT_ADVERTISER_NAMES: Literal["minimal", "legacy"] = "legacy"
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)


def request_headers(user_agent: str | None = BROWSER_USER_AGENT) -> dict[str, str]:
    """Request headers of the original ``_hole`` (``user_agent=None``: no user agent)."""
    headers = {
        "Accept": "application/json",
        "Accept-Language": "fr-FR,fr;q=0.9,de;q=0.8",
        "Referer": BASE + "/recherche/location/france",
    }
    if user_agent is not None:
        headers = {"User-Agent": user_agent, **headers}
    return headers


LIGATURES = {"œ": "oe", "æ": "ae", "ø": "o", "ß": "ss", "đ": "d", "ł": "l"}
DEPARTEMENTS = {
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "57": "Moselle",
    "88": "Vosges",
    "54": "Meurthe-et-Moselle",
}
KINDS = {
    "flat": "Wohnung",
    "house": "Haus",
    "loft": "Loft",
    "townhouse": "Reihenhaus",
    "castle": "Anwesen",
}


def search_filter(
    zones: Sequence[str],
    *,
    max_price: int,
    page: int,
    page_size: int,
    min_rooms: int | None = 1,
    max_rooms: int | None = 3,
    property_types: Sequence[str] = ("flat", "house"),
) -> dict[str, JSON]:
    """Filter object exactly as the original builds it (key order included)."""
    base: dict[str, JSON] = {
        "showAllModels": False,
        "filterType": "rent",
        "propertyType": list(property_types),
        "maxPrice": max_price,
        "sortBy": "publicationDate",
        "sortOrder": "desc",
        "onTheMarket": [True],
        "zoneIdsByTypes": {"zoneIds": list(zones)},
    }
    if min_rooms is not None:
        base["minRooms"] = min_rooms
    if max_rooms is not None:
        base["maxRooms"] = max_rooms
    f = dict(base, size=page_size, page=page)
    f["from"] = (page - 1) * page_size
    return f


def search_url(filters: Mapping[str, JSON]) -> str:
    """``realEstateAds.json?filters=<url-encoded JSON>``."""
    return SEARCH.format(filter=urllib.parse.quote(json.dumps(filters)))


def place_form(name: str | None) -> str:
    """Place name in the portal's address form ("Hœrdt" → "hoerdt")."""
    t = (name or "").strip().lower()
    for a, b in LIGATURES.items():
        t = t.replace(a, b)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def ad_url(ad: Mapping[str, JSON]) -> str | None:
    """Full ad address, else the short form."""
    kennung = ad.get("id")
    if not kennung:
        return None
    kind = {"flat": "appartement", "house": "maison"}.get(ad.get("propertyType") or "")
    place = place_form(ad.get("city"))
    rooms = ad.get("roomsQuantity")
    if kind and place and isinstance(rooms, (int, float)) and rooms >= 1:
        n = int(rooms)
        pieces = "1piece" if n == 1 else f"{n}pieces"
        return AD_LONG.format(
            art_geschaeft=ad.get("adTypeFR") or "location",
            ort=place,
            art=kind,
            zimmer=pieces,
            kennung=kennung,
        )
    return AD.format(kennung=kennung)


def _num(value: JSON) -> float | None:
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    return None


def date(iso: JSON) -> str | None:
    """``2026-09-08T11:54:43.211Z`` → ``08.09.2026``; 1970-01-01 means unknown."""
    if not isinstance(iso, str) or iso.startswith("1970-01-01"):
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso)
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}" if m else None


def _position(ad: Mapping[str, JSON]) -> tuple[JSON, JSON]:
    """Blurred position, else the centroid of the blurred area."""
    position = (ad.get("blurInfo") or {}).get("position") or {}
    lat, lon = position.get("lat"), position.get("lon")
    if lat is None:
        centre = (ad.get("blurInfo") or {}).get("centroid") or {}
        lat, lon = centre.get("lat"), centre.get("lon")
    return lat, lon


def _rents(ad: Mapping[str, JSON]) -> tuple[float | None, float | None, float | None]:
    """Warm rent, charges and cold rent (derived from warm minus charges if absent)."""
    warm = _num(ad.get("price"))
    charges = _num(ad.get("charges"))
    cold = _num(ad.get("rentWithoutCharges"))
    if cold is None and warm is not None and charges is not None:
        cold = round(warm - charges, 2)
    return warm, charges, cold


def _company(ad: Mapping[str, JSON], advertiser_names: str) -> str:
    individual = ad.get("accountType") == "individual"
    if individual and advertiser_names == "minimal":
        return "Privatangebot"
    return (ad.get("accountDisplayName") or "").strip() or ("Privatangebot" if individual else "")


def _features(ad: Mapping[str, JSON]) -> str:
    return ", ".join(
        t
        for t in [
            "Aufzug" if ad.get("hasElevator") else "",
            "Keller" if ad.get("hasCellar") else "",
            "Balkon" if ad.get("hasBalcony") else "",
            "Terrasse" if ad.get("hasTerrace") else "",
            "Garten" if ad.get("hasGarden") else "",
            "Stellplatz" if (ad.get("parkingPlacesQuantity") or 0) else "",
            "möbliert" if ad.get("isFurnished") else "",
        ]
        if t
    )


def normalise(
    ad: Mapping[str, JSON],
    *,
    advertiser_names: Literal["minimal", "legacy"] = DEFAULT_ADVERTISER_NAMES,
) -> dict[str, JSON]:
    """Ad in the stock format of the consumer (original ``normalise``, PS-C02)."""
    kennung = ad.get("id")
    department = ad.get("departmentCode")
    district = ad.get("district") or {}
    insee = district.get("insee_code") or district.get("code_insee")
    lat, lon = _position(ad)
    warm, charges, cold = _rents(ad)
    area = _num(ad.get("surfaceArea"))
    kind = ad.get("propertyType")
    company = _company(ad, advertiser_names)
    return {
        "id": f"bienici:{kennung}",
        "quelle": QUELLE,
        "titel": (ad.get("title") or "").strip() or "Angebot ohne Bezeichnung",
        "gesellschaft": company,
        "objektart": KINDS.get(kind or "", kind or "unbekannt"),
        "strasse": "",
        "plz": ad.get("postalCode"),
        "bezirk": DEPARTEMENTS.get(department or "", department),
        "departement": department,
        "ortsteil": ad.get("city"),
        "gemeinde": ad.get("city"),
        "gemeinde_code": insee,
        "lat": lat,
        "lon": lon,
        "zimmer": _num(ad.get("roomsQuantity")),
        "schlafzimmer": _num(ad.get("bedroomsQuantity")),
        "flaeche_qm": area,
        "kaltmiete": cold,
        "preisart": "kalt" if cold is not None else "warm",
        "nebenkosten": charges,
        "weitere_kosten": _num(ad.get("agencyRentalFee")),
        "kaution": _num(ad.get("safetyDeposit")),
        "gesamtmiete": warm,
        "kalt_pro_qm": round(cold / area, 2) if cold and area else None,
        "warm_pro_qm": round(warm / area, 2) if warm and area else None,
        "wbs": None,
        "moebliert": bool(ad.get("isFurnished")),
        "etage": ad.get("floor"),
        "etagen_gesamt": ad.get("floorQuantity"),
        "baujahr": None,
        "heizung": ad.get("heating") or "unbekannt",
        "energiekennwert": _num(ad.get("energyValue")),
        "energieausweis": ad.get("energyClassification"),
        "baeder": _num(ad.get("bathroomsQuantity")) or _num(ad.get("showerRoomsQuantity")),
        "bezugsfertig_ab": None,
        "eingestellt_am": date(ad.get("publicationDate")),
        "eingestellt_am_iso": date(ad.get("publicationDate")) and ad.get("publicationDate"),
        "geaendert_am": date(ad.get("modificationDate")),
        "ausstattung": _features(ad),
        "expose_url": ad_url(ad),
        "bild_url": (ad.get("photos") or [{}])[0].get("url_photo"),
    }
