"""Erkennungsmuster mit Prüfziffern- und Kontextprüfung (IBAN, Karte, Steuer-ID …)."""

from __future__ import annotations

import datetime as _dt
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

from auditcore_pdf.redaction.common import _HARD, MANUAL_SOURCE, NER_PATTERN_ID, NER_PROPAGATED_ID


def _context_before(text: str, start: int, width: int = 40) -> str:
    return text[max(0, start - width) : start].replace(_HARD, " ")


def _iban_ok(compact: str) -> bool:
    compact = compact.upper()
    if not (15 <= len(compact) <= 34 and compact[:2].isalpha() and compact[2:4].isdigit()):
        return False
    if not compact.isalnum() or not compact.isascii():
        return False
    rearranged = compact[4:] + compact[:4]
    digits = "".join(str(int(c, 36)) for c in rearranged)
    return int(digits) % 97 == 1


def _validate_iban(text: str, start: int, end: int) -> tuple[int, int] | None:
    """Längstes Präfix aus ganzen Gruppen, das die Prüfziffer erfüllt.

    Das Muster läuft gierig über Vierergruppen und kann ein folgendes kurzes
    Wort mitnehmen („… 3201 in“); erst die Modulo-97-Prüfung entscheidet,
    wo die IBAN endet.
    """
    tokens = list(re.finditer(r"\S+", text[start:end]))
    for k in range(len(tokens), 0, -1):
        candidate_end = start + tokens[k - 1].end()
        if _iban_ok(re.sub(r"\s", "", text[start:candidate_end])):
            return start, candidate_end
    return None


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _validate_card(text: str, start: int, end: int) -> tuple[int, int] | None:
    digits = re.sub(r"\D", "", text[start:end])
    return (start, end) if 13 <= len(digits) <= 19 and _luhn_ok(digits) else None


def _tax_id_ok(digits: str) -> bool:
    """Prüfziffer der Steuer-ID (ISO 7064, MOD 11,10); erste Ziffer ≠ 0."""
    if len(digits) != 11 or digits[0] == "0":
        return False
    product = 10
    for ch in digits[:10]:
        total = (int(ch) + product) % 10 or 10
        product = (total * 2) % 11
    check = 11 - product
    if check == 10:
        check = 0
    return check == int(digits[10])


def _validate_tax_id(text: str, start: int, end: int) -> tuple[int, int] | None:
    return (start, end) if _tax_id_ok(re.sub(r"\D", "", text[start:end])) else None


_PHONE_CONTEXT = re.compile(
    r"(?i)(?:\btel\b\.?|telefon|telefonisch|\bfon\b|\bfax\b|telefax|mobil|handy|"
    r"rufnummer|\bruf\b|durchwahl|erreichbar|anruf|☎|📞)[^\n\x00]{0,30}$"
)


def _validate_phone(text: str, start: int, end: int) -> tuple[int, int] | None:
    match = text[start:end]
    digits = re.sub(r"\D", "", match)
    if not 6 <= len(digits) <= 15:
        return None
    international = match.startswith("+") or match.startswith("00")
    separated = bool(re.search(r"\d[/-]\d", match))
    # Nur durch Leerzeichen gegliederte Ziffernfolgen wie „0701 686 11“ sind
    # häufig Haushaltsstellen oder Kundennummern — dann ist ein Hinweis wie
    # „Tel.“ oder „Telefon“ kurz davor nötig.
    context = _context_before(text, start)
    if not (international or separated) and not _PHONE_CONTEXT.search(context):
        return None
    return start, end


def _validate_date(text: str, start: int, end: int) -> tuple[int, int] | None:
    try:
        day, month, year = (int(x) for x in text[start:end].split("."))
        _dt.date(year, month, day)
    except ValueError:
        return None
    return start, end


_IP_NEGATIVE_CONTEXT = re.compile(
    r"(?i)(?:version|ver\.|\bv\.?|release|build|kapitel|abschnitt|ziffer|ziff\.|"
    r"nr\.|tz\.|gliederung|punkt|anlage|randnummer|rn\.|§)\s*$"
)


def _validate_ip(text: str, start: int, end: int) -> tuple[int, int] | None:
    if any(int(octet) > 255 for octet in text[start:end].split(".")):
        return None
    if _IP_NEGATIVE_CONTEXT.search(_context_before(text, start, 25)):
        return None
    return start, end


# Kürzel vor Rechtsgrundlagen, Förderprogrammen und Normen — keine Aktenzeichen.
_FILE_REFERENCE_BLOCKLIST = {
    "VO",
    "EU",
    "EG",
    "EWG",
    "EWR",
    "RL",
    "ART",
    "ABS",
    "NR",
    "EFRE",
    "ESF",
    "ELER",
    "EGFL",
    "EMFF",
    "BGBL",
    "ABL",
    "GVBL",
    "DIN",
    "ISO",
    "EN",
    "KOM",
    "COM",
    "SEC",
    "C",
}


def _validate_file_reference(text: str, start: int, end: int) -> tuple[int, int] | None:
    prefix = re.match(r"[A-ZÄÖÜ]+", text[start:end])
    if prefix and prefix.group(0) in _FILE_REFERENCE_BLOCKLIST:
        return None
    return start, end


#: Prüft einen Rohtreffer und liefert die bereinigte Spanne oder ``None``.
Validator: TypeAlias = Callable[[str, int, int], tuple[int, int] | None]


@dataclass(frozen=True)
class PatternSpec:
    """Ein auswählbares Erkennungsmuster."""

    label: str
    regex: str
    hint: str
    #: KI-basiert (spaCy-NER) statt Regex — kein fester Ausdruck, dafür
    #: unsicherer als die übrigen Muster.
    ai: bool = False
    flags: int = 0
    validate: Validator | None = None


PATTERNS: dict[str, PatternSpec] = {
    "iban": PatternSpec(
        "IBAN",
        r"(?<![A-Za-z0-9])[A-Za-z]{2}\d{2}(?: ?[A-Za-z0-9]){11,40}",
        "Kontonummern, auch in Vierergruppen geschrieben; nur mit gültiger Prüfziffer",
        validate=_validate_iban,
    ),
    "email": PatternSpec(
        "E-Mail-Adresse",
        r"(?<![\w.%+-])[\w.%+-]+@[\w-]+(?:\.[\w-]+)*\.[^\W\d_]{2,}(?![\w-])",
        "Adressen in Anschreiben und Verteilern",
    ),
    "telefon": PatternSpec(
        "Telefonnummer",
        r"(?<![\w/.,+-])(?:(?:\+|00)49[ /-]?(?:\(0\)[ /-]?)?[1-9]\d{1,4}|0[1-9]\d{1,4})"
        r"(?:[ /-]?\d{2,8}){1,3}(?![\w/-]|[.,]\d)",
        "deutsche Rufnummern; ohne „/“ oder „-“ nur nach „Tel.“, „Telefon“, „Fax“ o. Ä.",
        validate=_validate_phone,
    ),
    "steuer_id": PatternSpec(
        "Steuer-Identifikationsnummer",
        r"(?<![\d.,/-])(?:\d{11}|\d{2} \d{3} \d{3} \d{3})(?!\d|[.,/-]\d)",
        "11-stellige Steuer-ID; nur mit gültiger Prüfziffer",
        validate=_validate_tax_id,
    ),
    "ust_id": PatternSpec(
        "Umsatzsteuer-Identifikationsnummer",
        r"(?<![\w])DE ?\d{9}(?!\d)",
        "USt-IdNr. der Begünstigten",
    ),
    "kreditkarte": PatternSpec(
        "Kreditkartennummer",
        r"(?<![\d.,/-])\d{4}([ -]?)\d{4}\1\d{4}\1\d{4}(?!\d|[.,/-]\d)",
        "16-stellige Kartennummern; nur mit gültiger Prüfziffer (Luhn)",
        validate=_validate_card,
    ),
    "geburtsdatum": PatternSpec(
        "Datum (TT.MM.JJJJ)",
        r"(?<![\d.])(?:0?[1-9]|[12]\d|3[01])\.(?:0?[1-9]|1[0-2])\.(?:19|20)\d{2}(?![\d])",
        "z. B. Geburtsdaten — trifft alle gültigen Datumsangaben dieses Formats",
        validate=_validate_date,
    ),
    "ip_adresse": PatternSpec(
        "IP-Adresse",
        r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w]|\.\d)",
        "IPv4-Adressen aus Protokollauszügen; nicht nach „Version“ oder „Kapitel“",
        validate=_validate_ip,
    ),
    "aktenzeichen": PatternSpec(
        "Aktenzeichen",
        r"(?<![\w/-])[A-ZÄÖÜ]{1,4}[-/ ]?\d{1,6}[-/]\d{2,4}(?![\w/]|-\d)",
        "Muster wie AZ-1234/26; nicht bei Rechtsgrundlagen wie „VO 2021/1060“",
        validate=_validate_file_reference,
    ),
    NER_PATTERN_ID: PatternSpec(
        "Personennamen (KI-Erkennung)",
        "",
        "spaCy-NER statt Regex — erkennt Namen im Fließtext, ist aber "
        "unsicherer als die übrigen Muster: Vorschau vor dem Schwärzen prüfen",
        ai=True,
    ),
}


def source_label(source: str) -> str:
    """Anzeigename einer Fundstellenquelle."""
    if source.startswith("begriff:"):
        return f"Begriff „{source[8:]}“"
    if source == MANUAL_SOURCE:
        return "Bereich"
    if source == NER_PROPAGATED_ID:
        return "Namen (im Dokument nachgesucht)"
    spec = PATTERNS.get(source)
    return spec.label if spec else source
