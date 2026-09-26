"""Normalisierung, Seitenzusammenführung und Textabgleich der Donut-Felder (Plan 2a)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from auditcore_common.numeric import parse_percent_rate
from auditcore_common.text import compact_upper

from auditcore_documents.pipeline.stages.postprocess import parse_amount
from auditcore_documents.pipeline.stages.validation import VAT_ID_PATTERNS

#: Donut names of the shared helpers (same objects as in ``auditcore_common``).
rate = parse_percent_rate
compact = compact_upper

ALLOWED_VAT_RATES = {
    "DE": frozenset({Decimal(19), Decimal(7), Decimal(0)}),
    "AT": frozenset({Decimal(20), Decimal(13), Decimal(10), Decimal(0)}),
}
MONTHS = {
    name: number
    for number, names in enumerate(
        (
            ("januar", "jänner", "january"),
            ("februar", "february"),
            ("märz", "maerz", "march"),
            ("april",),
            ("mai", "may"),
            ("juni", "june"),
            ("juli", "july"),
            ("august",),
            ("september",),
            ("oktober", "october"),
            ("november",),
            ("dezember", "december"),
        ),
        1,
    )
    for name in names
}
#: Kernfelder: ein unbestätigter oder widersprüchlicher Wert führt zur Prüfung.
TEXT_CONFIRMED_FIELDS = (
    "invoice_number",
    "date",
    "net_amount",
    "vat_amount",
    "total",
    "iban",
    "vat_id",
)
CORE_FIELDS = (*TEXT_CONFIRMED_FIELDS, "vat_rates")
AMOUNTS = ("net_amount", "vat_amount", "total")
CENT = Decimal("0.01")


# --------------------------------------------------------------------------- Normalisierung
def clean_amount(raw: str) -> str:
    """Währung und Leerzeichen-Tausendergruppen entfernen (``1 234,56 €`` → ``1234,56``)."""
    text = raw.replace("EUR", "").replace("€", "").replace("\u00a0", " ").strip()
    sign = "-" if text.startswith("-") else ""
    text = text.lstrip("-").strip()
    if re.fullmatch(r"\d{1,3}(?: \d{3})+(?:[.,]\d{2})?", text):
        text = text.replace(" ", "")
    return sign + text


def amount(raw: str) -> Decimal | None:
    """Betrag gebietsschemabewusst (D5) als ``Decimal`` auf den Cent; mehrdeutig → ``None``."""
    text = clean_amount(raw)
    negative = text.startswith("-")
    value, state = parse_amount(text.lstrip("-"))
    if value is None or state != "ok":
        return None
    result = Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    return -result if negative else result


def iso_date(raw: str) -> str | None:
    text = " ".join(raw.strip().split())
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    match = re.fullmatch(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\s+(\d{4})", text) or re.fullmatch(
        r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", text
    )
    if match:
        groups = match.groups()
        day_text, month_text = (groups[0], groups[1]) if groups[0].isdigit() else groups[1::-1]
        month = MONTHS.get(month_text.casefold())
        if month:
            try:
                return date(int(groups[2]), month, int(day_text)).isoformat()
            except ValueError:
                return None
    return None


def de_vat_check_digit(first_eight: str) -> int:
    product = 10
    for char in first_eight:
        total = (int(char) + product) % 10 or 10
        product = (2 * total) % 11
    check = 11 - product
    return 0 if check == 10 else check


def at_uid_check_digit(first_seven: str) -> int:
    digits = [int(c) for c in first_seven]
    total = sum(d if i % 2 == 0 else (2 * d) // 10 + (2 * d) % 10 for i, d in enumerate(digits))
    return (10 - (total + 4) % 10) % 10


def vat_id_check(vat_id: str) -> str | None:
    """Fehlertext oder ``None``: Format je Land, Prüfziffer für DE und AT."""
    country = vat_id[:2]
    pattern = VAT_ID_PATTERNS.get(country)
    if pattern is None:
        return f"USt-IdNr.-Land unbekannt: {country}"
    if not re.match(pattern, vat_id):
        return "USt-IdNr.-Format ungültig"
    if country == "DE" and de_vat_check_digit(vat_id[2:10]) != int(vat_id[10]):
        return "USt-IdNr.-Prüfziffer ungültig"
    if country == "AT" and at_uid_check_digit(vat_id[3:10]) != int(vat_id[10]):
        return "UID-Prüfziffer ungültig"
    return None


# --------------------------------------------------------------------------- Seiten
def combine_pages(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Kopffelder: erste Fundstelle; Summen/Bankfelder: letzte Seite mit ``total``."""
    combined: dict[str, Any] = {}
    sums_page = next((p for p in reversed(pages) if "total" in p.get("fields", {})), None)
    for page in pages:
        for key, value in page.get("fields", {}).items():
            if isinstance(value, dict) and isinstance(combined.get(key), dict):
                for child, child_value in value.items():
                    combined[key].setdefault(child, child_value)
            else:
                combined.setdefault(key, value)
    if sums_page is not None:
        for key in ("net_amount", "vat_lines", "total", "iban", "bic"):
            if key in sums_page["fields"]:
                combined[key] = sums_page["fields"][key]
    return combined


def combine_confidence(pages: list[dict[str, Any]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for page in pages:
        for key, value in (page.get("field_confidence") or {}).items():
            result[key] = min(result.get(key, 1.0), float(value))
    return result


# --------------------------------------------------------------------------- Textabgleich
def text_amounts(text: str) -> set[Decimal]:
    found: set[Decimal] = set()
    for token in re.findall(r"\d{1,3}(?:[ .,]\d{3})*(?:[.,]\d{2})|\d+[.,]\d{2}", text):
        value = amount(token)
        if value is not None:
            found.add(value)
    return found


def text_dates(text: str) -> set[str]:
    found = set()
    patterns = (
        r"\d{1,2}\.\d{1,2}\.\d{2,4}",
        r"\d{4}-\d{2}-\d{2}",
        r"\d{1,2}\.\s*[A-Za-zÄÖÜäöü]+\s+\d{4}",
        r"[A-Za-z]+\s+\d{1,2},\s*\d{4}",
    )
    for pattern in patterns:
        for token in re.findall(pattern, text):
            value = iso_date(token)
            if value:
                found.add(value)
    return found


def confirmed_in_text(
    name: str, value: Any, text: str, parts: Sequence[Decimal | None] | None = None
) -> bool:
    """Kommt der Wert (bzw. jede Steuerzeile) im unabhängig gelesenen Text vor?"""
    if not text:
        return False
    if name == "vat_amount" and parts:
        found = text_amounts(text)
        return all(part is not None and part in found for part in parts)
    if name in AMOUNTS:
        return Decimal(str(value)).quantize(CENT) in text_amounts(text)
    if name in {"date", "supply_date", "due_date"}:
        return value in text_dates(text)
    if name in {"iban", "vat_id", "bic"}:
        return str(value) in compact(text)
    if name == "vat_rates":
        rates = {rate(token) for token in re.findall(r"\d{1,2}(?:[.,]\d)?\s*%", text)}
        return bool(value) and all(r in rates for r in value)
    return bool(value) and str(value) in " ".join(text.split())
