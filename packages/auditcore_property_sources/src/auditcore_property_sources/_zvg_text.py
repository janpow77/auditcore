"""ZVG text helpers: mojibake repair, German numbers and money, Verkehrswert, object type."""

from __future__ import annotations

import re
import unicodedata
from html import unescape

from auditcore_common.numbers_de import parse_de_number as _parse_de_amount

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
    """German number text after the shared contract ``parse-number`` (mode ``de``).

    ``'945,80'`` → 945.8, ``'1234,56'`` → 1234.56, ``'2015'`` → 2015.0. The
    whole text must be the number (currency and white space allowed); at most
    two decimals; ambiguous forms such as ``'1.5'``, ``'1.234'`` or
    ``'1,234'`` and anything else give ``None``. Characterized predecessor:
    :func:`legacy_parse_de_number` (PS-C10).
    """
    value = _parse_de_amount(s)
    return None if value is None else float(value)


def legacy_parse_de_number(s: str) -> float | None:
    """Original ``zvg_crawler.parse_de_number``: first number found anywhere in ``s``.

    Kept exactly for replay and migration. Misreads numbers without thousands
    points: ``'1234,56'`` → 123.0, ``'2015'`` → 201.0 (PS-C10).
    """
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
