"""inberlinwohnen.de: offers of Berlin's state-owned housing companies (Livewire snapshots).

Profile ``property.inberlinwohnen`` — characterized from
``janpow77/wohnungsmonitor@76571bf`` ``inberlinwohnen_export.py``
(``total_count``, ``learn_attributes``, ``parse_page``, ``normalise``, ``_zahl``,
``_utc``).

Price semantics: ``kaltmiete`` = ``rentNet``; ``gesamtmiete`` from the offer
table ("Gesamtmiete", including heating), else ``rentGross``, else cold rent
plus extra costs; ``weitere_kosten`` = the remainder (usually heating).
Coordinates with ``|lat − lon| < 0.5`` are discarded as unusable. Attribute
names are learned from the attribute list of the same page; the original keeps
them in a module-global dictionary, here they are passed explicitly (PS-C01).
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Iterator, Mapping
from typing import Any

SOURCE_ID = "property.inberlinwohnen"
PROFILE_VERSION = "2026.09.1"
BASE = "https://www.inberlinwohnen.de/wohnungsfinder/"
QUELLE = "inberlinwohnen"
ITEM = "apartment-finder.item.apartment-item"
ATTRIBUTES = "apartment-finder.item.partials.attributes-list"

_SNAPSHOT = re.compile(r'wire:snapshot="(.*?)"[\s>]', re.S)
_SPAN = re.compile(r"<span>(.*?)</span>", re.S)
_TAG = re.compile(r"<[^>]+>")
_GESAMT = re.compile(r"von\s+([\d.]+)\s+Angebot", re.I)


def page_url(page: int) -> str:
    """First page is the plain finder address, later pages ``?page=N``."""
    return BASE if page == 1 else f"{BASE}?page={page}"


def _unwrap(v: Any) -> Any:
    if isinstance(v, list) and len(v) == 2 and isinstance(v[1], dict) and set(v[1]) == {"s"}:
        return _unwrap(v[0])
    if isinstance(v, list):
        return [_unwrap(x) for x in v]
    if isinstance(v, dict):
        return {k: _unwrap(x) for k, x in v.items()}
    return v


def snapshots(doc: str) -> Iterator[tuple[int, int, str, Any]]:
    """``(start, end, component name, data)`` of every readable snapshot."""
    for m in _SNAPSHOT.finditer(doc):
        try:
            d = json.loads(html.unescape(m.group(1)))
        except (ValueError, TypeError):
            continue
        yield m.start(), m.end(), d.get("memo", {}).get("name", ""), _unwrap(d.get("data", {}))


def unreadable_snapshots(doc: str) -> int:
    """Number of ``wire:snapshot`` attributes that are not JSON (skipped by the original)."""
    return sum(1 for _ in _SNAPSHOT.finditer(doc)) - sum(1 for _ in snapshots(doc))


def total_count(doc: str) -> int:
    """Total number of offers stated by the portal ("von 1.203 Angeboten")."""
    m = _GESAMT.search(doc)
    return int(m.group(1).replace(".", "")) if m else 0


def text(v: Any) -> str:
    """Remove markup and resolve entities."""
    if v is None:
        return ""
    return html.unescape(_TAG.sub("", str(v))).strip()


def learn_attributes(doc: str, known: Mapping[int, str] | None = None) -> dict[int, str]:
    """Attribute id → name from the rendered attribute list, merged into ``known``."""
    learned = dict(known or {})
    for _, end, name, data in snapshots(doc):
        if name != ATTRIBUTES:
            continue
        ids = data.get("itemAttributes") or []
        close = doc.find("</div>", end)
        block = doc[end : close if close > 0 else end]
        names = [text(s) for s in _SPAN.findall(block)]
        for ident, label in zip(ids, names, strict=False):
            if label:
                learned[int(ident)] = label
    return learned


def parse_page(doc: str) -> dict[int, dict[str, Any]]:
    """All offers of a result page by portal id."""
    offers: dict[int, dict[str, Any]] = {}
    for _, _, name, data in snapshots(doc):
        if name != ITEM:
            continue
        item = data.get("item")
        if isinstance(item, dict) and item.get("id") is not None:
            offers[int(item["id"])] = item
    return offers


def number(v: Any) -> float | None:
    """German decimal notation to float; the dot is a thousands separator only with a comma."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = text(v).replace(" ", "").replace("€", "").replace("m²", "").strip()
    if not s or not re.search(r"\d", s):
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def _details(item: Mapping[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for column in item.get("details") or []:
        entries = column if isinstance(column, list) else [column]
        for e in entries:
            if isinstance(e, dict) and e.get("label"):
                flat[e["label"]] = e.get("value")
    return flat


def utc(stamp: Any) -> str | None:
    """``2026-09-04T17:59:02.000000Z`` → ``2026-09-04T17:59:02Z``."""
    if not stamp:
        return None
    s = str(stamp).replace(" ", "T")[:19]
    return s + "Z" if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", s) else None


def _per_sqm(amount: float | None, area: float | None) -> float | None:
    if amount is None or not area:
        return None
    return round(amount / area, 2)


def normalise(item: Mapping[str, Any], attributes: Mapping[int, str]) -> dict[str, Any]:
    """Offer in the stock format (original ``normalise`` with explicit attribute names)."""
    d = _details(item)
    address = item.get("address") or {}
    company = (item.get("company") or {}).get("name") or ""
    lat, lon = number(address.get("lat")), number(address.get("lon"))
    if lat is None or lon is None or abs(lat - lon) < 0.5:
        lat = lon = None
    area = number(item.get("area"))
    cold = number(item.get("rentNet"))
    extra = number(item.get("extraCosts"))
    total = number(d.get("Gesamtmiete"))
    if total is None:
        total = number(item.get("rentGross"))
    if total is None and cold is not None and extra is not None:
        total = round(cold + extra, 2)
    further = None
    if total is not None and cold is not None and extra is not None:
        rest = round(total - cold - extra, 2)
        further = rest if abs(rest) >= 0.01 else None
    street = " ".join(x for x in (address.get("street"), address.get("number")) if x).strip()
    names = [
        attributes.get(int(a["flat_attribute_id"]))
        for a in (item.get("attributes") or [])
        if isinstance(a, dict) and a.get("flat_attribute_id") is not None
    ]
    features = {n for n in names if n}
    wbs = text(d.get("WBS")) or "unbekannt"
    if wbs == "erforderlich":
        features.add("WBS erforderlich")
    return {
        "id": int(item["id"]),
        "quelle": QUELLE,
        "titel": text(item.get("title")),
        "gesellschaft": text(company),
        "strasse": street,
        "plz": text(address.get("zipCode")) or None,
        "bezirk": text(address.get("district")) or None,
        "lat": lat,
        "lon": lon,
        "zimmer": number(item.get("rooms")),
        "flaeche_qm": area,
        "kaltmiete": cold,
        "nebenkosten": extra,
        "weitere_kosten": further,
        "gesamtmiete": total,
        "kalt_pro_qm": _per_sqm(cold, area),
        "warm_pro_qm": _per_sqm(total, area),
        "wbs": wbs,
        "etage": item.get("level"),
        "etagen_gesamt": item.get("levelsTotal"),
        "baujahr": text(item.get("constructionYear")) or None,
        "heizung": text(d.get("Heizung")) or "unbekannt",
        "energiekennwert": number(d.get("Energieverbrauchskennwert")),
        "energieausweis": text(item.get("energyPassType")) or None,
        "baeder": item.get("bathrooms"),
        "bezugsfertig_ab": text(item.get("occupationDate")) or None,
        "eingestellt_am": text(d.get("Eingestellt am")) or None,
        "ausstattung": "; ".join(sorted(features)),
        "expose_url": item.get("deeplink"),
        "erfasst_am": utc(item.get("createdAt")),
    }
