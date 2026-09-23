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
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from html import unescape
from typing import Any

from ._html import links, page_text

SOURCE_ID = "property.zvg"
PROFILE_VERSION = "2026.09.1"
BASE = "https://www.zvg-portal.de/index.php"

MOJIBAKE_REPLACEMENTS = {
    "Ã¤": "ä",
    "Ã¶": "ö",
    "Ã¼": "ü",
    "Ã„": "Ä",
    "Ã–": "Ö",
    "Ãœ": "Ü",
    "ÃŸ": "ß",
    "Ã©": "é",
    "Ãè": "è",
    "Â°": "°",
    "Â²": "²",
    "Â³": "³",
    "Â½": "½",
    "Â": "",
    "\u009f": "",
}
MOJIBAKE_MARKERS = ("Ã", "Â", "\u009f", "�")

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

#: Objektart-Klassifikation; Reihenfolge = Priorität (wie im Original).
TYPE_RULES: list[tuple[str, str]] = [
    ("wohn_geschaeftshaus", r"wohn-?\s*und\s*gesch[äa]fts|gesch[äa]ftshaus"),
    ("mfh", r"mehrfamilien|mehrere wohnungen|\bwohnungen\b|wohnhaus mit \d|\bmfh\b"),
    ("rh", r"reihenhaus|reihenmittelhaus|reihenendhaus|reihenh[äa]us"),
    ("dhh", r"doppelhaus"),
    ("etw", r"eigentumswohnung|wohnungseigentum|\bwohnung\b|\betw\b"),
    ("efh", r"einfamilienhaus|einfamilien|\befh\b|wohnhaus"),
    ("ladenlokal", r"ladenlokal|\bladen\b|einzelhandel"),
    ("gastronomie", r"gastronom|restaurant|gastst[äa]tte|hotel|pension"),
    ("buero", r"b[üu]ro|praxis|kanzlei"),
    ("halle_lager", r"halle|lagerhalle|\blager\b|produktion|werkstatt"),
    ("gewerbe", r"gewerbe|betriebsgrundst"),
    (
        "grundstueck",
        r"unbebaut|baugrundst|ackerland|land-?\s*und\s*forst|gr[üu]nland|gartenland|\bgrundst[üu]ck\b",
    ),  # noqa: E501
    ("garage_stellplatz", r"\bgarage|stellplatz|tiefgarage"),
]


# --------------------------------------------------------------------------- #
# Text and numbers
# --------------------------------------------------------------------------- #
def fix_mojibake(text: str | None) -> str:
    """Repair typical UTF-8/Latin-1 mis-decodings conservatively."""
    if not text:
        return ""
    out = text
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        out = out.replace(bad, good)
    if any(marker in out for marker in MOJIBAKE_MARKERS):
        try:
            repaired = out.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
            if repaired and sum(repaired.count(m) for m in MOJIBAKE_MARKERS) < sum(
                out.count(m) for m in MOJIBAKE_MARKERS
            ):
                out = repaired
        except UnicodeError:  # pragma: no cover - errors="ignore" never raises
            pass
    return out


def clean(text: str | None) -> str:
    """Unescape, repair mojibake, NFC-normalise and collapse whitespace."""
    if not text:
        return ""
    text = fix_mojibake(unescape(text))
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text).strip()


def decode_portal_bytes(content: bytes) -> str:
    """Decode a portal response with the fewest mojibake markers (utf-8, cp1252, latin-1).

    Original: ``decode_portal_response(httpx.Response)``; here on plain bytes so
    that any injected transport can be used.
    """
    candidates: list[str] = []
    for encoding in ("utf-8", "cp1252", "iso-8859-1"):
        try:
            candidates.append(content.decode(encoding))
        except UnicodeDecodeError:
            continue
    if not candidates:  # pragma: no cover - iso-8859-1 decodes every byte string
        return fix_mojibake(content.decode("utf-8", errors="replace"))

    def score(value: str) -> tuple[int, int]:
        marker_count = sum(value.count(marker) for marker in MOJIBAKE_MARKERS)
        replacement_count = value.count("�")
        return marker_count + replacement_count * 3, replacement_count

    return fix_mojibake(min(candidates, key=score))


def parse_de_number(s: str) -> float | None:
    """``'945,80'`` → 945.8, ``'2015'`` → 2015.0; no money heuristic."""
    m = re.search(r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:,\d{1,2})?)", s)
    if not m:
        return None
    val = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(val)
    except ValueError:  # pragma: no cover - the pattern only admits digits
        return None


def parse_money_amount(s: str) -> float | None:
    """Portal money amounts: ``667.000,00``, ``65.000,-`` and ``80,000,-`` (= 80 000 EUR)."""
    token = clean(s)
    if not token:
        return None
    token = token.replace("€", "").replace("EUR", "")
    token = re.sub(r"\s+", "", token)
    token = re.sub(r",-+$", "", token)
    token = token.strip(".,;-:()")
    if not token:
        return None
    if "." in token and "," in token:
        normalized = token.replace(".", "").replace(",", ".")
    elif "." in token:
        normalized = token.replace(".", "")
    elif "," in token:
        head, tail = token.rsplit(",", 1)
        normalized = head + tail if len(tail) == 3 else head + "." + tail
    else:
        normalized = token
    try:
        return float(normalized)
    except ValueError:
        return None


_MONEY_TOKEN = r"\d{1,3}(?:[\.\s]\d{3})+(?:,\d{1,2})?|\d+,\d{2,3}|\d{2,}"


def extract_market_value(vw_block: str) -> float | None:
    """Verkehrswert from the "Verkehrswert in" section.

    An explicit *Gesamtverkehrswert* wins; otherwise all amounts followed by
    ``€``/``EUR`` are summed. Text after *Sicherheitsleistung*, *Kassenzeichen*,
    *Gerichtskasse* or *IBAN* is cut off first. Amounts without a currency sign
    are not recognised (source behavior, PS-L03).
    """
    block = clean(vw_block)
    if not block:
        return None
    block = re.split(
        r"Sicherheitsleistung|Kassenzeichen|Gerichtskasse|IBAN", block, maxsplit=1, flags=re.I
    )[0]
    total = re.search(
        rf"Gesamtverkehrswert[^0-9]{{0,40}}(?P<amount>{_MONEY_TOKEN})(?:\s*(?:,-)?\s*(?:€|EUR))?",
        block,
        re.I,
    )
    if total:
        return parse_money_amount(total.group("amount"))
    amounts: list[float] = []
    for match in re.finditer(rf"(?P<amount>{_MONEY_TOKEN})\s*(?:,-)?\s*(?:€|EUR)", block, re.I):
        value = parse_money_amount(match.group("amount"))
        if value is not None:
            amounts.append(value)
    if amounts:
        return round(sum(amounts), 2)
    return None


def classify_type(text: str) -> str:
    """Canonical property type code (``efh``, ``etw``, …, ``sonstige``)."""
    low = text.lower()
    for code, pat in TYPE_RULES:
        if re.search(pat, low):
            return code
    return "sonstige"


# --------------------------------------------------------------------------- #
# Addresses
# --------------------------------------------------------------------------- #
STREET_SUFFIX = (
    r"(?:stra(?:ße|sse)|str\.?|weg|platz|allee|gasse|ring|damm|ufer|pfad|"
    r"steig|berg|markt|hof|chaussee|promenade|wiesen|feld|acker|grund|litt)"
)
HOUSE_NO = r"\d+\s*[a-zA-Z]?(?:\s*[-+/,]\s*\d+\s*[a-zA-Z]?)*"
RE_NOT_STREET = re.compile(
    r"(?i)\b(?:flur(?:stück)?|gemarkung|grundbuch|blatt|band|gew\.?|zimmer|whg\.?|wohnung)\b"
)
RE_STREET_PREPOSITION = re.compile(
    r"(?i)^(?:am|an|auf|im|in|bei|beim|zum|zur|unterm?|vorm?|hinterm?)\b"
)

Address = tuple[str | None, str | None, str | None, str | None]


def extract_address(text: str) -> Address:
    """``(street, house_number, postal_code, city)``; only safely recognised parts."""
    src = clean(text)
    if not src:
        return None, None, None, None
    postal_code = city = None
    pm = re.search(r"\b(\d{5})\s+([^,;()]+?)(?:,|$)", src)
    if pm:
        postal_code = pm.group(1)
        city = clean(pm.group(2))
    street = house_number = None
    sm = re.search(
        rf"([^,;:()]*?{STREET_SUFFIX}[^,;:()]*?)\s+({HOUSE_NO})\s*,\s*\d{{5}}\s+",
        src,
        re.IGNORECASE,
    )
    if not sm:
        sm = re.search(rf"([A-ZÄÖÜ][^,;:()0-9]{{2,60}}?)\s+({HOUSE_NO})\s*,\s*\d{{5}}\s+", src)
        if sm and RE_NOT_STREET.search(sm.group(1)):
            sm = None
    if sm:
        street = clean(sm.group(1))
        house_number = clean(sm.group(2))[:32]
    elif postal_code:
        before_plz = src[: src.find(postal_code)]
        sm = re.search(
            rf"([^,;:()]*?{STREET_SUFFIX}[^,;:()]*?)\s+(\d+\s*[a-zA-Z]?)\s*,?\s*$",
            before_plz,
            re.IGNORECASE,
        )
        if sm:
            street = clean(sm.group(1))
            house_number = clean(sm.group(2))[:32]
        else:
            sm = re.search(r"([^,;:()]+?)\s*,\s*$", before_plz)
            if sm:
                cand = clean(sm.group(1))
                looks_like_street = bool(
                    re.search(rf"(?i){STREET_SUFFIX}\b", cand) or RE_STREET_PREPOSITION.search(cand)
                )
                if (
                    looks_like_street
                    and 3 <= len(cand) <= 60
                    and cand[0].isupper()
                    and not any(ch.isdigit() for ch in cand)
                    and len(cand.split()) <= 5
                    and not RE_NOT_STREET.search(cand)
                ):
                    street = cand
    if street and street.lower() in {"e", "str", "str.", "straße", "strasse"}:
        street = None
    if postal_code == "00000":
        postal_code = None
    return street, house_number, postal_code, city


def expand_street(street: str | None) -> str | None:
    """Write out ``…str.``/``…pl.`` abbreviations (``Graubergerstr.`` → ``Graubergerstraße``)."""
    if not street:
        return street
    s = street
    s = re.sub(r"(?i)([a-zäöüß])str\.?(?=\s|,|$)", r"\1straße", s)
    s = re.sub(r"(?i)([a-zäöüß])pl\.?(?=\s|,|$)", r"\1platz", s)
    s = re.sub(r"(?i)\bstr\.?(?=\s|,|$)", "Straße", s)
    return re.sub(r"\s+", " ", s).strip()


def normalized_street(street: str | None) -> str:
    """Comparison form of a street name (original ``_norm_street``)."""
    s = expand_street(street) or ""
    return re.sub(r"[\s.\-]", "", s).lower()


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

    def to_dict(self) -> dict[str, Any]:
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


def _anchor_texts(html: str) -> list[tuple[str, str]]:
    from html.parser import HTMLParser

    class Anchors(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.found: list[tuple[str, list[str]]] = []
            self.open: list[int] = []
            self.skip = 0

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag in ("script", "style", "template"):
                self.skip += 1
            if tag == "a":
                href = None
                for name, value in attrs:
                    if name == "href":
                        href = value or ""
                if href is not None:
                    self.found.append((href, []))
                    self.open.append(len(self.found) - 1)
                else:
                    self.open.append(-1)

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

    parser = Anchors()
    parser.feed(html)
    parser.close()
    return [(href, " ".join(parts)) for href, parts in parser.found]


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
    m = re.search(r"Objekt/Lage:\s*(.*?)\s*(?:Beschreibung:|Verkehrswert)", text)
    objekt = clean(m.group(1)) if m else ""
    m = re.search(r"Beschreibung:\s*(.*?)\s*(?:Gl[äa]ubiger|Verkehrswert in)", text)
    beschr = clean(m.group(1)) if m else ""
    v.title = objekt[:200] if objekt else (beschr[:200] if beschr else v.file_number)
    v.description = beschr or objekt

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
    for href in links(html):
        if "showAnhang" in href and "file_id=" in href:
            url = (
                href if href.startswith("http") else "https://www.zvg-portal.de/" + href.lstrip("/")
            )
            v.documents.append(url)
    v.documents = list(dict.fromkeys(v.documents))
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
    "listing_ids",
    "normalized_street",
    "parse_de_number",
    "parse_detail",
    "parse_listing_akten",
    "parse_money_amount",
    "resolve_courts",
]
