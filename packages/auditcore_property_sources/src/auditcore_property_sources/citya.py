"""citya.com: rental offers of the property manager Citya (schema.org OfferCatalog).

Profile ``property.citya`` — characterized from
``janpow77/wohnungsmonitor@76571bf`` ``citya_export.py`` (``katalog``,
``gesamtzahl``, ``normalise``, ``ist_wohnraum``, ``_zahl``).

Price semantics: the list names one amount and no statement whether charges
are included; it is kept as ``kaltmiete`` with ``preisart: "unklar"``. Rooms
and area are read from the title ("… de 3 pièces de 58.02m² à …"); parking,
commercial premises and land are excluded as not residential.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping

from ._types import JSON

SOURCE_ID = "property.citya"
PROFILE_VERSION = "2026.09.1"
BASE = "https://www.citya.com"
SEARCH = BASE + "/annonces/location/{dep}?page={seite}"
QUELLE = "citya"
DEPARTEMENTS = {
    "67": ("bas-rhin-67", "Bas-Rhin"),
    "68": ("haut-rhin-68", "Haut-Rhin"),
    "57": ("moselle-57", "Moselle"),
    "88": ("vosges-88", "Vosges"),
    "54": ("meurthe-et-moselle-54", "Meurthe-et-Moselle"),
}
KINDS = {
    "appartement": "Wohnung",
    "studio": "Wohnung",
    "duplex": "Wohnung",
    "loft": "Wohnung",
    "maisonnette": "Wohnung",
    "maison": "Haus",
    "villa": "Haus",
    "chalet": "Haus",
    "ferme": "Haus",
}
NOT_RESIDENTIAL = (
    "parking",
    "garage",
    "box",
    "cave",
    "local professionnel",
    "local commercial",
    "local d'activit",
    "bureau",
    "entrep",
    "fonds de commerce",
    "terrain",
    "forêt",
    "foret",
    "cellier",
    "emplacement",
    "commerce",
)

_CATALOG = re.compile(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", re.S)
_ROOMS = re.compile(r"de\s+([\d.,]+)\s*pi[èe]ce", re.I)
_AREA = re.compile(r"de\s+([\d.,]+)\s*m²", re.I)
_KIND = re.compile(r"location\s+(appartement|maison|studio|duplex|villa)", re.I)


def search_url(department_path: str, page: int) -> str:
    """Result page of one département (``/annonces/location/bas-rhin-67?page=N``)."""
    return SEARCH.format(dep=department_path, seite=page)


def number(value: JSON) -> float | None:
    if value is None:
        return None
    try:
        return round(float(str(value).replace(",", ".").replace(" ", "")), 2)
    except ValueError:
        return None


def catalog(doc: str) -> list[dict[str, JSON]]:
    """Offers of the first JSON-LD block with ``offers`` (original ``katalog``)."""
    for block in _CATALOG.findall(doc):
        try:
            d = json.loads(block)
        except ValueError:
            continue
        if isinstance(d, dict) and d.get("offers"):
            offers: list[dict[str, JSON]] = d["offers"]
            return offers
    return []


def total(doc: str) -> int:
    """Stated number of properties ("362 biens")."""
    m = re.search(r"(\d+)\s*biens", doc)
    return int(m.group(1)) if m else 0


def is_residential(title: str | None) -> bool:
    """Whether the title means a flat or a house (original ``ist_wohnraum``)."""
    t = (title or "").lower()
    head = t.split(" de ")[0]
    return not any(w in head for w in NOT_RESIDENTIAL)


def normalise(
    offer: Mapping[str, JSON], dep_name: str, dep_code: str | None = None
) -> dict[str, JSON]:
    """Offer in the stock format (original ``normalise``)."""
    item = offer.get("itemOffered") or {}
    address = item.get("address") or {}
    title = item.get("name") or ""
    url = offer.get("url") or ""
    kennung = url.rstrip("/").split("/")[-1] or title[:40]

    def found(pattern: re.Pattern[str]) -> str | None:
        m = pattern.search(title)
        return m.group(1) if m else None

    rooms = number(found(_ROOMS))
    area = number(found(_AREA))
    kind = (found(_KIND) or "").lower()
    price = number(offer.get("price"))
    return {
        "id": f"citya:{kennung}",
        "quelle": QUELLE,
        "titel": title.strip() or "Angebot ohne Bezeichnung",
        "gesellschaft": "Citya Immobilier",
        "objektart": KINDS.get(kind, "unbekannt"),
        "strasse": "",
        "plz": address.get("postalCode"),
        "bezirk": dep_name,
        "departement": dep_code,
        "ortsteil": address.get("addressLocality"),
        "gemeinde": address.get("addressLocality"),
        "gemeinde_code": None,
        "lat": None,
        "lon": None,
        "zimmer": rooms,
        "flaeche_qm": area,
        "kaltmiete": price,
        "preisart": "unklar",
        "nebenkosten": None,
        "weitere_kosten": None,
        "gesamtmiete": None,
        "kalt_pro_qm": round(price / area, 2) if price and area else None,
        "warm_pro_qm": None,
        "wbs": None,
        "etage": None,
        "etagen_gesamt": None,
        "baujahr": None,
        "heizung": "unbekannt",
        "energiekennwert": None,
        "energieausweis": None,
        "baeder": None,
        "bezugsfertig_ab": None,
        "eingestellt_am": None,
        "geaendert_am": None,
        "ausstattung": "",
        "beschreibung": "",
        "expose_url": url,
        "bild_url": None,
    }
