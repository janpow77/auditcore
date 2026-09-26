"""Kleinanzeigen: Berlin rental ads from the result list (private and commercial offerers).

Profile ``property.kleinanzeigen`` — characterized from
``janpow77/wohnungsmonitor@76571bf`` ``kleinanzeigen_export.py``
(``parse_page``, ``brauchbar``, ``normalise``, ``_zahl``, ``_schluessel``).

Price semantics: the ad price is sometimes cold, sometimes warm; it is kept as
``kaltmiete`` with ``preisart: "unklar"``. Swaps, furnished interim lets,
shared rooms, requests and commercial space are excluded by the source's
quality filter. District names come from the consumer's official
Ortsteil → Bezirk mapping, passed explicitly (PS-C01).

Access: robots.txt of www.kleinanzeigen.de (checked 2026-09-23) disallows
``/*/preis:*`` — the original search address contains ``…/preis::700/…`` and is
therefore disallowed (HUMAN_DECISION_REQUIRED, see catalog). Ads are written
by private persons; titles and descriptions may contain personal data.
"""

from __future__ import annotations

import html
import re
from collections.abc import Mapping

from ._types import JSON

SOURCE_ID = "property.kleinanzeigen"
PROFILE_VERSION = "2026.09.1"
BASE = "https://www.kleinanzeigen.de"
SEARCH = BASE + "/s-wohnung-mieten/berlin/{seite}preis::{hoechstpreis}/c203l3331"
QUELLE = "Kleinanzeigen"

EXCLUDED = re.compile(
    r"tausch|wohnungstausch|ringtausch|swap"
    r"|m[öo]bl|teilmoebl|furnished"
    r"|zwischenmiete|befristet|auf zeit|zeitmiete|interim|tempor"
    r"|wg[- ]zimmer|wohngemeinschaft|\bwg\b|untermiete|mitbewohner"
    r"|ferienwohnung|monteur|boardinghouse|apartmenthaus"
    r"|zimmer in (?:einer|der|einem)"
    r"|gewerbe|praxis|\bb[üu]ro|atelier|ladenlokal|\bladen\b|werkstatt"
    r"|arbeitsr[äa]ume|gesch[äa]ftsr[äa]ume|lagerraum|stellplatz|garage"
    r"|coworking|kanzlei",
    re.I,
)
REQUEST = re.compile(
    r"^\s*(?:ich |wir |familie |paar )?such(?:e|en|t)\b"
    r"|\bwohnung\w*\s+(?:dringend\s+)?gesucht\b"
    r"|\bsuche\b.{0,40}\bwohnung",
    re.I,
)

_AD = re.compile(r'data-adid="(\d+)"')
_HREF = re.compile(r'data-href="(/s-anzeige/[^"]+)"')
_PLACE = re.compile(r"\b(1[0-4]\d{3})\s+([A-ZÄÖÜ][\wÄÖÜäöüß\.\- ]{2,32}?)\s*\|")
_SIZE = re.compile(r"([\d.,]{1,6})\s*m²\s*·\s*([\d,]{1,4})\s*Zi\.")
_PRICE = re.compile(r"\|\s*([\d.]{2,7})\s*€")


def search_url(max_price: int, page: int) -> str:
    """Original search address (contains ``preis::`` — disallowed by robots.txt)."""
    part = "" if page == 1 else f"seite:{page}/"
    return SEARCH.format(seite=part, hoechstpreis=max_price)


def place_key(name: str | None) -> str:
    """Comparison form of a place name ("Weissensee" = "Weißensee")."""
    s = (name or "").strip().lower()
    for a, b in (("ß", "ss"), ("ä", "ae"), ("ö", "oe"), ("ü", "ue")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]", "", s)


def district_index(ortsteile_bezirke: Mapping[str, str]) -> dict[str, str]:
    """Lookup table keyed by :func:`place_key` (original ``bezirke_laden``)."""
    return {place_key(k): v for k, v in ortsteile_bezirke.items()}


def _plain(raw: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
    t = re.sub(r"<[^>]+>", " | ", t)
    t = html.unescape(t)
    return re.sub(r"(\s*\|\s*)+", " | ", re.sub(r"\s+", " ", t)).strip()


def number(s: str | None) -> float | None:
    """``1.250`` is a thousand, ``54,5`` a decimal."""
    if not s:
        return None
    s = s.strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") == 1 and len(s.split(".")[1]) == 3:
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_page(doc: str) -> dict[str, dict[str, JSON]]:
    """All ads of a result page as raw records (original ``parse_page``)."""
    starts = [m.start() for m in _AD.finditer(doc)]
    ids = _AD.findall(doc)
    if not starts:
        return {}
    starts.append(len(doc))
    ads: dict[str, dict[str, JSON]] = {}
    for i, ident in enumerate(ids):
        raw = doc[starts[i] : starts[i + 1]]
        href = _HREF.search(raw)
        plain = _plain(raw)
        place = _PLACE.search(plain)
        size = _SIZE.search(plain)
        price = _PRICE.search(plain[size.end() :]) if size else None
        description = ""
        if place and size and size.start() > place.end():
            description = plain[place.end() : size.start()].strip(" |")
        ads[ident] = {
            "id": ident,
            "url": BASE + href.group(1) if href else None,
            "plz": place.group(1) if place else None,
            "ort": place.group(2).strip() if place else None,
            "beschreibung": description,
            "flaeche": size.group(1) if size else None,
            "zimmer": size.group(2) if size else None,
            "preis": price.group(1) if price else None,
        }
    return ads


def usable(raw: Mapping[str, JSON]) -> bool:
    """Quality filter: no requests, swaps, interim lets, shared rooms or commercial space."""
    text = raw.get("beschreibung") or ""
    title = text.split(" | ")[0]
    if REQUEST.search(title):
        return False
    return not EXCLUDED.search(text)


def normalise(raw: Mapping[str, JSON], districts: Mapping[str, str]) -> dict[str, JSON]:
    """Ad in the stock format; ``districts`` from :func:`district_index`."""
    place = (raw.get("ort") or "").strip()
    district = districts.get(place_key(place)) or (place or None)
    area = number(raw.get("flaeche"))
    price = number(raw.get("preis"))
    parts = (raw.get("beschreibung") or "").split(" | ")
    title = parts[0].strip() if parts else ""
    return {
        "id": f"ka:{raw['id']}",
        "quelle": QUELLE,
        "titel": title or "Anzeige ohne Titel",
        "gesellschaft": "privat oder gewerblich",
        "strasse": "",
        "plz": raw.get("plz"),
        "bezirk": district,
        "ortsteil_gemeldet": place or None,
        "lat": None,
        "lon": None,
        "zimmer": number(raw.get("zimmer")),
        "flaeche_qm": area,
        "kaltmiete": price,
        "preisart": "unklar",
        "nebenkosten": None,
        "weitere_kosten": None,
        "gesamtmiete": None,
        "kalt_pro_qm": round(price / area, 2) if price and area else None,
        "warm_pro_qm": None,
        "wbs": "nicht erforderlich",
        "etage": None,
        "etagen_gesamt": None,
        "baujahr": None,
        "heizung": "unbekannt",
        "energiekennwert": None,
        "energieausweis": None,
        "baeder": None,
        "bezugsfertig_ab": None,
        "eingestellt_am": None,
        "ausstattung": "",
        "expose_url": raw.get("url"),
        "erfasst_am": None,
    }
