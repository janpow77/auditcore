"""paruvendu.fr: French rental ads (private and agency) from result cards.

Profile ``property.paruvendu`` — characterized from
``janpow77/wohnungsmonitor@76571bf`` ``paruvendu_export.py`` (``_karten``,
``normalise``, ``_zahl``).

Price semantics: ``CC`` (*charges comprises*) → warm, ``HC`` (*hors charges*)
→ cold; without a mark the amount is kept as ``kaltmiete`` with
``preisart: "unklar"``. Only the municipality with the département number is
named ("Huttenheim (67)"), no street, postcode or coordinate.
"""

from __future__ import annotations

import html
import re
from typing import Any

SOURCE_ID = "property.paruvendu"
PROFILE_VERSION = "2026.09.1"
BASE = "https://www.paruvendu.fr"
SEARCH = BASE + "/immobilier/recherche/location/{art}/{dep}?px1={hoechstpreis}&p={seite}"
QUELLE = "paruvendu"
DEPARTEMENTS = {
    "67": ("bas-rhin-67", "Bas-Rhin"),
    "68": ("haut-rhin-68", "Haut-Rhin"),
    "57": ("moselle-57", "Moselle"),
    "88": ("vosges-88", "Vosges"),
    "54": ("meurthe-et-moselle-54", "Meurthe-et-Moselle"),
}
KINDS = {"appartement": "Wohnung", "maison": "Haus"}
PAGE_SIZE = 30

_ID = re.compile(r'data-id="(\d+)"')
_LINK = re.compile(r'href="(/immobilier/location/[^"?]+)"')
_TITLE = re.compile(r'title="\s*([^"]{5,120})"')
_PRICE = re.compile(
    r"([\d\u00a0\u202f ]{2,9})&euro;\s*(?:</[^>]+>\s*)*(?:<[^>]+>\s*)*(CC|HC)?", re.I
)
_PLACE = re.compile(r"([A-ZÀ-ÝŒ][\wÀ-ÿ'’\- ]{1,34}?)\s*\((\d{2})\)")
_ROOMS = re.compile(r"(\d+)\s*pi[èe]ces?", re.I)
_AREA_T = re.compile(r"([\d.,]+)\s*m²")
_ROOMS_T = re.compile(r"(\d+)\s*pi[èe]ce", re.I)
_KIND_T = re.compile(r"^\s*(Appartement|Maison|Studio|Duplex|Villa|Loft)", re.I)
_DATE = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")


def search_url(kind: str, department_path: str, max_price: int, page: int) -> str:
    """Result page (``?px1=`` price cap, ``&p=`` page, 30 cards per page)."""
    return SEARCH.format(art=kind, dep=department_path, hoechstpreis=max_price, seite=page)


def number(value: Any) -> float | None:
    if value is None:
        return None
    t = str(value).replace("\xa0", "").replace("\u202f", "").replace(" ", "").replace(",", ".")
    try:
        return round(float(t), 2)
    except ValueError:
        return None


def cards(doc: str) -> list[str]:
    """Split the result list into the single ad blocks (original ``_karten``)."""
    flat = re.sub(r"\s+", " ", doc)
    flat = re.sub(r"<script.*?</script>", " ", flat, flags=re.S)
    return flat.split('class="blocAnnonce')[1:]


def _text(block: str) -> str:
    t = re.sub(r"<[^>]+>", " | ", block)
    t = html.unescape(t)
    t = re.sub(r"(\s*\|\s*)+", " | ", t)
    return t.strip()


def normalise(block: str, dep_name: str, default_kind: str) -> dict[str, Any] | None:
    """Card in the stock format; ``None`` for cards without id or link."""
    ident = _ID.search(block)
    link = _LINK.search(block)
    if not ident or not link:
        return None
    title = ""
    for m in _TITLE.finditer(block):
        if _KIND_T.match(m.group(1)):
            title = html.unescape(m.group(1)).strip()
            break
    txt = _text(block)
    price, price_kind = None, "unklar"
    mp = _PRICE.search(block)
    if mp:
        price = number(mp.group(1))
        mark = (mp.group(2) or "").upper()
        if mark == "CC":
            price_kind = "warm"
        elif mark == "HC":
            price_kind = "kalt"
    place, dep_no = None, None
    mo = _PLACE.search(txt)
    if mo:
        place = mo.group(1).strip(" |")
        dep_no = mo.group(2)
    rooms_match = _ROOMS_T.search(title) or _ROOMS.search(txt)
    rooms = number(rooms_match.group(1)) if rooms_match else None
    area_match = _AREA_T.search(title)
    area = number(area_match.group(1)) if area_match else None
    kind_match = _KIND_T.match(title)
    kind = KINDS.get(kind_match.group(1).lower() if kind_match else default_kind, "unbekannt")
    day = None
    md = _DATE.search(txt)
    if md:
        day = f"{md.group(1)}.{md.group(2)}.{md.group(3)}"
    cold = price if price_kind in ("kalt", "unklar") else None
    warm = price if price_kind == "warm" else None
    return {
        "id": f"pv:{ident.group(1)}",
        "quelle": QUELLE,
        "titel": title or "Angebot ohne Bezeichnung",
        "gesellschaft": "",
        "objektart": kind,
        "strasse": "",
        "plz": None,
        "bezirk": DEPARTEMENTS.get(dep_no, (None, dep_name))[1] if dep_no else dep_name,
        "departement": dep_no,
        "ortsteil": place,
        "gemeinde": place,
        "gemeinde_code": None,
        "lat": None,
        "lon": None,
        "zimmer": rooms,
        "flaeche_qm": area,
        "kaltmiete": cold,
        "preisart": price_kind,
        "nebenkosten": None,
        "weitere_kosten": None,
        "gesamtmiete": warm,
        "kalt_pro_qm": round(cold / area, 2) if cold and area else None,
        "warm_pro_qm": round(warm / area, 2) if warm and area else None,
        "wbs": None,
        "etage": None,
        "etagen_gesamt": None,
        "baujahr": None,
        "heizung": "unbekannt",
        "energiekennwert": None,
        "energieausweis": None,
        "baeder": None,
        "bezugsfertig_ab": None,
        "eingestellt_am": day,
        "geaendert_am": None,
        "ausstattung": "",
        "expose_url": BASE + link.group(1),
        "bild_url": None,
    }
