"""ZVG-Portal (Justizportal der Länder): notices of forced auctions.

Profile ``property.zvg`` — characterized from ``janpow77/versteigerung@e4ad7af``
``backend/app/crawler/zvg_crawler.py``. Values keep the semantics of the
source: ``market_value`` is the court-assessed *Verkehrswert* in EUR (not a
rent, not an offer price), ``living_area_sqm`` the living area stated in the
notice, the address parts come from "Objekt/Lage" with "Beschreibung" as a
second finding. Nothing here is harmonised with the rental portals.

Access: robots.txt of www.zvg-portal.de disallows ``/index.php?button=showZvg*``
and ``showAnhang*`` — exactly the detail and attachment pages. The result
list (``POST index.php?button=Suchen``) is not disallowed. See the catalog.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser

from ._html import links, page_text
from ._zvg_address import (
    HOUSE_NO,
    RE_NOT_STREET,
    RE_STREET_PREPOSITION,
    STREET_SUFFIX,
    Address,
    expand_street,
    extract_address,
    normalized_street,
)
from ._zvg_text import (
    MOJIBAKE_MARKERS,
    MOJIBAKE_REPLACEMENTS,
    TYPE_RULES,
    classify_type,
    clean,
    decode_portal_bytes,
    extract_market_value,
    fix_mojibake,
    legacy_parse_de_number,
    parse_de_number,
    parse_money_amount,
)

SOURCE_ID = "property.zvg"
PROFILE_VERSION = "2026.09.1"
BASE = "https://www.zvg-portal.de/index.php"

MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "maerz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

#: Amtsgerichte je Land (``ger_id`` → Name), wie im Original aus dem Portal übernommen.
COURTS_HE: dict[str, str] = {
    "M1401": "Alsfeld",
    "M1305": "Bad Hersfeld",
    "M1202": "Bad Homburg v. d. Höhe",
    "M1905": "Bad Schwalbach",
    "M1102": "Bensheim",
    "M1801": "Biedenkopf",
    "M1402": "Büdingen",
    "M1103": "Darmstadt",
    "M1104": "Dieburg",
    "M1702": "Dillenburg",
    "M1705": "Dillenburg Zweigstelle Herborn",
    "M1602": "Eschwege",
    "M1803": "Frankenberg (Eder)",
    "M1201": "Frankfurt am Main",
    "M1405": "Friedberg (Hessen)",
    "M1603": "Fritzlar",
    "M1105": "Fürth",
    "M1301": "Fulda",
    "M1501": "Gelnhausen",
    "M1406": "Gießen",
    "M1106": "Groß-Gerau",
    "M1502": "Hanau",
    "M1307": "Hünfeld",
    "M1903": "Idstein",
    "M1607": "Kassel",
    "M1605": "Kassel Zweigstelle Hofgeismar",
    "M1807": "Kirchhain",
    "M1203": "Königstein im Taunus",
    "M1608": "Korbach",
    "M1111": "Lampertheim",
    "M1112": "Langen (Hessen)",
    "M1706": "Limburg a. d. Lahn",
    "M1809": "Marburg",
    "M1609": "Melsungen",
    "M1113": "Michelstadt",
    "M1114": "Offenbach am Main",
    "M1904": "Rüdesheim am Rhein",
    "M1107": "Rüsselsheim",
    "M1812": "Schwalmstadt",
    "M1117": "Seligenstadt",
    "M1709": "Weilburg",
    "M1710": "Wetzlar",
    "M1906": "Wiesbaden",
}
COURTS_RP: dict[str, str] = {"T2304": "Mainz"}
LAND_BY_COURT: dict[str, str] = {**{c: "he" for c in COURTS_HE}, **{c: "rp" for c in COURTS_RP}}
COURT_NAMES: dict[str, str] = {**COURTS_HE, **COURTS_RP}
KERN_COURTS = [
    "M1201",
    "M1906",
    "M1103",
    "M1114",
    "M1607",
    "M1406",
    "M1502",
    "M1301",
    "M1706",
    "M1809",
    "T2304",
]


# --------------------------------------------------------------------------- #
# Result list and detail page
# --------------------------------------------------------------------------- #
@dataclass
class ZvgNotice:
    """One published notice (original ``Verfahren``, without coordinates)."""

    zvg_id: str
    land: str
    court_id: str
    file_number: str = ""
    court_name: str = ""
    title: str = ""
    description: str = ""
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    city: str | None = None
    alt_street: str | None = None
    alt_house_number: str | None = None
    living_area_sqm: float | None = None
    build_year: int | None = None
    market_value: float | None = None
    property_type: str = "sonstige"
    termin: datetime | None = None
    termin_location: str | None = None
    detail_url: str = ""
    documents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """JSON view (``termin`` as ISO text)."""
        data = asdict(self)
        data["termin"] = self.termin.isoformat() if self.termin else None
        return data


def detail_url(zvg_id: str, land: str) -> str:
    """Public detail address of a notice (robots.txt: disallowed for crawlers)."""
    return f"{BASE}?button=showZvg&zvg_id={zvg_id}&land_abk={land}"


def parse_listing_akten(html: str, land: str) -> dict[str, str]:
    """``zvg_id`` → Aktenzeichen from a result list (entries without file number are dropped)."""
    out: dict[str, str] = {}
    for href_text in _anchor_texts(html):
        href, text = href_text
        m = re.search(r"showZvg&zvg_id=(\d+)&land_abk=" + re.escape(land), href)
        if not m:
            continue
        zid = m.group(1)
        akm = re.search(r"(\d{1,4}\s*[KL]\s*\d+/\d{2,4})", text)
        if akm:
            out[zid] = clean(akm.group(1))
    return out


def listing_ids(html: str, land: str) -> list[str]:
    """All ``zvg_id`` of a result list, with or without file number, first occurrence first."""
    seen: dict[str, None] = {}
    for href, _ in _anchor_texts(html):
        m = re.search(r"showZvg&zvg_id=(\d+)&land_abk=" + re.escape(land), href)
        if m:
            seen.setdefault(m.group(1), None)
    return list(seen)


class _AnchorParser(HTMLParser):
    """Links with their visible text; script/style/template content is skipped."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.found: list[tuple[str, list[str]]] = []
        self.open: list[int] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "template"):
            self.skip += 1
        if tag != "a":
            return
        href = None
        for name, value in attrs:
            if name == "href":
                href = value or ""
        if href is None:
            self.open.append(-1)
            return
        self.found.append((href, []))
        self.open.append(len(self.found) - 1)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "template") and self.skip:
            self.skip -= 1
        if tag == "a" and self.open:
            self.open.pop()

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        for index in self.open:
            if index >= 0:
                self.found[index][1].append(data)


def _anchor_texts(html: str) -> list[tuple[str, str]]:
    parser = _AnchorParser()
    parser.feed(html)
    parser.close()
    return [(href, " ".join(parts)) for href, parts in parser.found]


def _sections(text: str) -> tuple[str, str]:
    """ "Objekt/Lage" and "Beschreibung" of a detail page text."""
    m = re.search(r"Objekt/Lage:\s*(.*?)\s*(?:Beschreibung:|Verkehrswert)", text)
    objekt = clean(m.group(1)) if m else ""
    m = re.search(r"Beschreibung:\s*(.*?)\s*(?:Gl[äa]ubiger|Verkehrswert in)", text)
    beschr = clean(m.group(1)) if m else ""
    return objekt, beschr


def _apply_address(v: ZvgNotice, objekt: str, beschr: str) -> None:
    """ "Objekt/Lage" address first, "Beschreibung" as second finding (``alt_*``)."""
    primary = extract_address(objekt)
    secondary: Address = (
        extract_address(beschr) if beschr and beschr != objekt else (None, None, None, None)
    )
    if not primary[0] and secondary[0]:
        primary, secondary = secondary, primary
    v.street, v.house_number, v.postal_code, v.city = primary
    same_street = not secondary[0] or normalized_street(secondary[0]) == normalized_street(v.street)
    if same_street and not v.house_number:
        v.house_number = secondary[1]
    if secondary[0] and not same_street:
        v.alt_street, v.alt_house_number = secondary[0], secondary[1]


def _apply_facts(v: ZvgNotice, text: str, reference_year: int) -> None:
    """Living area, plausible build year and Verkehrswert."""
    m = re.search(r"Wohnfl[äa]che[^0-9]{0,25}([\d.]+,\d+|\d+)\s*m", text)
    if m:
        v.living_area_sqm = parse_de_number(m.group(1))
    m = re.search(r"Baujahr[^0-9]{0,30}(\d{4})", text)
    if m:
        year = int(m.group(1))
        if 1700 <= year <= reference_year + 1:
            v.build_year = year
    m = re.search(r"Verkehrswert in.*?(?:Termin:|Ort der Versteigerung:|$)", text)
    value = extract_market_value(m.group(0) if m else "")
    if value is not None:
        v.market_value = round(value, 2)


def _apply_termin(v: ZvgNotice, text: str) -> None:
    """Auction date (UTC as in the source) and place."""
    m = re.search(
        r"Termin:\s*[A-Za-zäöü]+,?\s*(\d{1,2})\.\s*([A-Za-zäöü]+)\s*(\d{4}),?\s*(\d{1,2}):(\d{2})",
        text,
    )
    if m:
        day, mon, year_text, hh, mm = m.groups()
        month = MONTHS.get(mon.lower())
        if month:
            try:
                v.termin = datetime(int(year_text), month, int(day), int(hh), int(mm), tzinfo=UTC)
            except ValueError:
                v.termin = None
    m = re.search(r"Ort der Versteigerung:\s*(.*?)\s*(?:Gericht:|Exposee|Gutachten|$)", text)
    if m:
        v.termin_location = clean(m.group(1))[:400]


def _apply_documents(v: ZvgNotice, html: str) -> None:
    """Attachment links (``showAnhang`` with ``file_id``), absolute, first occurrence first."""
    for href in links(html):
        if "showAnhang" in href and "file_id=" in href:
            url = (
                href if href.startswith("http") else "https://www.zvg-portal.de/" + href.lstrip("/")
            )
            v.documents.append(url)
    v.documents = list(dict.fromkeys(v.documents))


def parse_detail(html: str, notice: ZvgNotice, *, reference_year: int) -> ZvgNotice:
    """Fill ``notice`` from a detail page (original ``parse_detail``).

    ``reference_year`` bounds a plausible *Baujahr* (1700 … reference_year + 1);
    the original uses the current calendar year (PS-C04).
    """
    text = clean(page_text(html))
    v = notice
    if not v.file_number:
        m = re.search(r"(\d{1,4}\s*[KL]\s*\d+/\d{2,4})", text)
        if m:
            v.file_number = clean(m.group(1))
    objekt, beschr = _sections(text)
    v.title = objekt[:200] if objekt else (beschr[:200] if beschr else v.file_number)
    v.description = beschr or objekt
    _apply_address(v, objekt, beschr)
    _apply_facts(v, text, reference_year)
    _apply_termin(v, text)
    _apply_documents(v, html)
    v.property_type = classify_type(f"{objekt} {beschr}")
    return v


def resolve_courts(arg: str) -> list[str]:
    """``kern``, ``he``, ``all`` or a comma list of ``ger_id``."""
    if arg == "kern":
        return list(KERN_COURTS)
    if arg == "he":
        return list(COURTS_HE)
    if arg == "all":
        return list(COURT_NAMES)
    return [c.strip() for c in arg.split(",") if c.strip()]


__all__ = [
    "BASE",
    "HOUSE_NO",
    "MONTHS",
    "MOJIBAKE_MARKERS",
    "MOJIBAKE_REPLACEMENTS",
    "RE_NOT_STREET",
    "RE_STREET_PREPOSITION",
    "STREET_SUFFIX",
    "TYPE_RULES",
    "Address",
    "COURTS_HE",
    "COURTS_RP",
    "COURT_NAMES",
    "KERN_COURTS",
    "LAND_BY_COURT",
    "PROFILE_VERSION",
    "SOURCE_ID",
    "ZvgNotice",
    "classify_type",
    "clean",
    "decode_portal_bytes",
    "detail_url",
    "expand_street",
    "extract_address",
    "extract_market_value",
    "fix_mojibake",
    "legacy_parse_de_number",
    "listing_ids",
    "normalized_street",
    "parse_de_number",
    "parse_detail",
    "parse_listing_akten",
    "parse_money_amount",
    "resolve_courts",
]
