"""immobilien.de: Berlin rental offers from schema.org JSON-LD.

Profile ``property.immobilien_de`` — characterized from
``janpow77/wohnungsmonitor@76571bf`` ``immobilien_export.py``
(``parse_page``, ``_mietarten``, ``_mietart_zu``, ``normalise``).

Price semantics of the source: the JSON-LD price does not say whether it is
cold or warm rent; the type is taken from the markup next to it
("593,67 € | Kaltmiete"). ``Warmmiete`` → ``gesamtmiete``/``preisart: warm``;
``Kaltmiete``/``Nettokaltmiete`` → ``kaltmiete``/``preisart: kalt``; no
statement → ``kaltmiete`` with ``preisart: unklar``. The list names no street,
only the postcode; districts come from the consumer's official
postcode → districts mapping (``plz_bezirke``), which is passed explicitly.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence

from ._types import JSON

SOURCE_ID = "property.immobilien_de"
PROFILE_VERSION = "2026.09.1"
BASE = "https://www.immobilien.de"
SEARCH = BASE + "/mieten/wohnung/berlin/?preis_bis={hoechstpreis}&page={seite}"
QUELLE = "immobilien.de"

_LD = re.compile(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", re.S)
_MIETART = re.compile(r"([\d.]{2,7}(?:,\d{2})?)\s*€\s*\|\s*(Kaltmiete|Warmmiete|Nettokaltmiete)")


def search_url(max_price: int, page: int) -> str:
    """Result page ``page`` up to ``max_price`` (``?preis_bis=…&page=…``)."""
    return SEARCH.format(hoechstpreis=max_price, seite=page)


def ld_blocks(doc: str) -> list[str]:
    """Raw JSON-LD script contents."""
    return list(_LD.findall(doc))


def _collect(node: JSON, out: list[dict[str, JSON]]) -> None:
    if isinstance(node, dict):
        kind = node.get("@type")
        if kind and "RealEstateListing" in (kind if isinstance(kind, list) else [kind]):
            out.append(node)
        for value in node.values():
            _collect(value, out)
    elif isinstance(node, list):
        for value in node:
            _collect(value, out)


def rent_types(doc: str) -> dict[str, str]:
    """Price in German notation → rent type stated in the markup."""
    t = re.sub(r"<script.*?</script>", " ", doc, flags=re.S)
    t = re.sub(r"(\s*\|\s*)+", " | ", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", t)))
    return {p: art for p, art in _MIETART.findall(t)}


def rent_type_for(price: JSON, types: Mapping[str, str]) -> str | None:
    """Rent type of a JSON-LD price, looked up in several notations (original order)."""
    if price is None:
        return None
    try:
        wert = float(price)
    except (TypeError, ValueError):
        return None
    for notation in (
        f"{wert:,.2f}".replace(",", ".").replace(".", "#", 0),
        f"{wert:.2f}".replace(".", ","),
        f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"{wert:.0f}",
    ):
        if notation in types:
            return types[notation]
    return None


def parse_page(doc: str) -> tuple[dict[str, dict[str, JSON]], list[int]]:
    """Listings by numeric id plus the indexes of unreadable JSON-LD blocks.

    The original silently skips unreadable blocks; they are reported here so
    that an adapter can mark the page as partial (PS-C06).
    """
    types = rent_types(doc)
    listings: dict[str, dict[str, JSON]] = {}
    unreadable: list[int] = []
    for index, raw in enumerate(ld_blocks(doc)):
        try:
            data = json.loads(raw)
        except ValueError:
            unreadable.append(index)
            continue
        found: list[dict[str, JSON]] = []
        _collect(data, found)
        for listing in found:
            url = listing.get("url") or ""
            key = url.rstrip("/").split("/")[-1]
            if not key.isdigit():
                continue
            price = ((listing.get("offers") or {}).get("priceSpecification") or {}).get("price")
            listing["_mietart"] = rent_type_for(price, types)
            listings[key] = listing
    return listings, unreadable


def normalise(
    listing: Mapping[str, JSON], plz_bezirke: Mapping[str, Sequence[str]]
) -> dict[str, JSON]:
    """Listing in the stock format of the consumer (original ``normalise``)."""
    adresse = listing.get("address") or {}
    plz = adresse.get("postalCode")
    bezirke = list(plz_bezirke.get(plz or "", []))
    flaeche = (listing.get("floorSize") or {}).get("value")
    zimmer = listing.get("numberOfRooms")
    preis = ((listing.get("offers") or {}).get("priceSpecification") or {}).get("price")
    try:
        preis = float(preis) if preis is not None else None
    except (TypeError, ValueError):
        preis = None
    warm = listing.get("_mietart") == "Warmmiete"
    gestellt = listing.get("datePosted") or ""
    tag = None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", gestellt):
        j, m, t = gestellt.split("-")
        tag = f"{t}.{m}.{j}"
    kennung = (listing.get("url") or "").rstrip("/").split("/")[-1]
    return {
        "id": f"imde:{kennung}",
        "quelle": QUELLE,
        "titel": (listing.get("name") or "").strip() or "Angebot ohne Bezeichnung",
        "gesellschaft": "über immobilien.de",
        "strasse": "",
        "plz": plz,
        "bezirk": bezirke[0] if bezirke else None,
        "bezirke_moeglich": bezirke or None,
        "lat": None,
        "lon": None,
        "zimmer": float(zimmer) if isinstance(zimmer, (int, float)) else None,
        "flaeche_qm": float(flaeche) if isinstance(flaeche, (int, float)) else None,
        "kaltmiete": None if warm else preis,
        "preisart": "warm" if warm else ("kalt" if listing.get("_mietart") else "unklar"),
        "nebenkosten": None,
        "weitere_kosten": None,
        "gesamtmiete": preis if warm else None,
        "kalt_pro_qm": round(preis / flaeche, 2) if preis and flaeche and not warm else None,
        "warm_pro_qm": round(preis / flaeche, 2) if preis and flaeche and warm else None,
        "wbs": "unbekannt",
        "etage": None,
        "etagen_gesamt": None,
        "baujahr": None,
        "heizung": "unbekannt",
        "energiekennwert": None,
        "energieausweis": None,
        "baeder": None,
        "bezugsfertig_ab": None,
        "eingestellt_am": tag,
        "ausstattung": "",
        "expose_url": listing.get("url"),
        "erfasst_am": gestellt or None,
    }
