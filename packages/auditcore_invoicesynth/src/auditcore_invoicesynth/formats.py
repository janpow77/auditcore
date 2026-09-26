"""Deutsche und englische Zahlen-, Währungs- und Datumsformate samt Rücklesung.

Die Formatierung erzeugt die gedruckte Zeichenkette (Ziel-JSON enthält das
Gedruckte). Die Rücklesung (``parse_*``) normalisiert Gedrucktes und
Modellausgaben für die Bewertung: Beträge als ``Decimal`` auf den Cent, Datum
ISO, Kennungen groß und ohne Leerzeichen.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Literal

AmountStyle = Literal["de_grouped", "de_plain", "de_space", "en_grouped"]
CurrencyStyle = Literal["suffix_code", "suffix_symbol", "prefix_symbol", "prefix_code", "none"]
DateStyle = Literal["de_numeric", "de_short", "de_long", "iso", "en_long"]

AMOUNT_STYLES: tuple[AmountStyle, ...] = ("de_grouped", "de_plain", "de_space", "en_grouped")
CURRENCY_STYLES: tuple[CurrencyStyle, ...] = (
    "suffix_code",
    "suffix_symbol",
    "prefix_symbol",
    "prefix_code",
    "none",
)
DATE_STYLES: tuple[DateStyle, ...] = ("de_numeric", "de_short", "de_long", "iso", "en_long")

MONTHS_DE = (
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)
MONTHS_AT = {1: "Jänner"}
MONTHS_EN = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
CENT = Decimal("0.01")


def cents(value: Decimal) -> Decimal:
    """Kaufmännisch auf den Cent runden."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def format_amount(value: Decimal, style: AmountStyle) -> str:
    """Betrag ohne Währung in der gewählten Schreibweise."""
    value = cents(value)
    sign = "-" if value < 0 else ""
    whole, fraction = f"{abs(value):.2f}".split(".")
    groups = [whole[max(0, i - 3) : i] for i in range(len(whole), 0, -3)][::-1]
    if style == "de_grouped":
        text = ".".join(groups) + "," + fraction
    elif style == "de_plain":
        text = whole + "," + fraction
    elif style == "de_space":
        text = " ".join(groups) + "," + fraction
    elif style == "en_grouped":
        text = ",".join(groups) + "." + fraction
    else:
        raise ValueError(f"Unbekannte Betragsschreibweise: {style}")
    return sign + text


def format_money(
    value: Decimal, style: AmountStyle, currency_style: CurrencyStyle, currency: str = "EUR"
) -> str:
    """Betrag mit Währung vor oder nach dem Betrag (``EUR``/``€``) oder ohne."""
    amount = format_amount(value, style)
    symbol = "€" if currency == "EUR" else currency
    if currency_style == "suffix_code":
        return f"{amount} {currency}"
    if currency_style == "suffix_symbol":
        return f"{amount} {symbol}"
    if currency_style == "prefix_symbol":
        return f"{symbol} {amount}"
    if currency_style == "prefix_code":
        return f"{currency} {amount}"
    if currency_style == "none":
        return amount
    raise ValueError(f"Unbekannte Währungsschreibweise: {currency_style}")


def format_rate(rate: Decimal, *, variant: int = 0) -> str:
    """Steuersatz: ``19 %``, ``19%`` oder ``19,0 %``."""
    whole = f"{rate.normalize():f}"
    if variant % 3 == 1:
        return f"{whole}%"
    if variant % 3 == 2:
        return f"{rate:.1f}".replace(".", ",") + " %"
    return f"{whole} %"


def format_date(value: date, style: DateStyle, *, country: str = "DE") -> str:
    """Datum als ``15.01.2026``, ``15.1.26``, ``15. Januar 2026``, ISO oder englisch."""
    if style == "de_numeric":
        return value.strftime("%d.%m.%Y")
    if style == "de_short":
        return f"{value.day}.{value.month}.{value.year % 100:02d}"
    if style == "de_long":
        month = MONTHS_AT.get(value.month) if country == "AT" else None
        return f"{value.day}. {month or MONTHS_DE[value.month - 1]} {value.year}"
    if style == "iso":
        return value.isoformat()
    if style == "en_long":
        return f"{MONTHS_EN[value.month - 1]} {value.day}, {value.year}"
    raise ValueError(f"Unbekannte Datumsschreibweise: {style}")


_MONTH_LOOKUP = {
    **{name.casefold(): i + 1 for i, name in enumerate(MONTHS_DE)},
    **{name.casefold(): i + 1 for i, name in enumerate(MONTHS_EN)},
    "jänner": 1,
    "maerz": 3,
}


def parse_date(text: str) -> str | None:
    """Gedrucktes Datum → ISO; ``None``, wenn nicht eindeutig lesbar."""
    raw = " ".join(text.strip().split())
    patterns: list[tuple[str, str]] = [
        (r"(\d{4})-(\d{1,2})-(\d{1,2})", "ymd"),
        (r"(\d{1,2})\.(\d{1,2})\.(\d{4}|\d{2})", "dmy"),
        (r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\s+(\d{4})", "dMy"),
        (r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", "Mdy"),
    ]
    for pattern, order in patterns:
        match = re.fullmatch(pattern, raw)
        if not match:
            continue
        try:
            if order == "ymd":
                year, month, day = (int(g) for g in match.groups())
            elif order == "dmy":
                day, month = int(match[1]), int(match[2])
                year = int(match[3]) + (2000 if len(match[3]) == 2 else 0)
            elif order == "dMy":
                day, year = int(match[1]), int(match[3])
                month = _MONTH_LOOKUP.get(match[2].casefold(), 0)
            else:
                day, year = int(match[2]), int(match[3])
                month = _MONTH_LOOKUP.get(match[1].casefold(), 0)
            return date(year, month, day).isoformat()
        except ValueError:
            return None
    return None


def parse_money(text: str) -> Decimal | None:
    """Gedruckten Betrag mit oder ohne Währung lesen.

    Enthält der Text Punkt und Komma, ist das letzte Zeichen das Dezimaltrennzeichen.
    Ein einzelnes Trennzeichen vor genau zwei Ziffern ist das Dezimaltrennzeichen,
    vor genau drei Ziffern ist der Betrag mehrdeutig (``None``).
    """
    raw = text.replace("EUR", "").replace("€", "").replace(" ", " ").strip()
    negative = raw.startswith("-")
    raw = raw.lstrip("-").strip()
    if re.fullmatch(r"\d{1,3}(?: \d{3})+(?:,\d{2})?", raw):
        raw = raw.replace(" ", "")
    if not re.fullmatch(r"\d(?:[\d.,]*\d)?", raw):
        return None
    dots, commas = raw.count("."), raw.count(",")
    try:
        if dots and commas:
            decimal_sep = "," if raw.rfind(",") > raw.rfind(".") else "."
            thousands = "." if decimal_sep == "," else ","
            whole, _, fraction = raw.rpartition(decimal_sep)
            if not re.fullmatch(rf"\d{{1,3}}(?:{re.escape(thousands)}\d{{3}})*", whole):
                return None
            value = Decimal(whole.replace(thousands, "") + "." + fraction)
        elif dots + commas == 0:
            value = Decimal(raw)
        else:
            separator = "." if dots else ","
            head, _, tail = raw.rpartition(separator)
            if dots + commas == 1 and len(tail) == 2:
                value = Decimal(head + "." + tail)
            elif re.fullmatch(rf"\d{{1,3}}(?:{re.escape(separator)}\d{{3}})+", raw):
                if dots + commas == 1:
                    return None
                value = Decimal(raw.replace(separator, ""))
            else:
                return None
    except InvalidOperation:
        return None
    return cents(-value if negative else value)


def parse_rate(text: str) -> Decimal | None:
    """``19 %``/``19%``/``19,0 %`` → ``Decimal('19')``."""
    match = re.fullmatch(r"(\d{1,2})(?:[.,](\d))?\s*%?", text.strip())
    if not match:
        return None
    value = Decimal(match[1] + ("." + match[2] if match[2] else ""))
    return value.quantize(Decimal(1)) if value == value.to_integral() else value


def normalize_identifier(text: str) -> str:
    """IBAN/USt-IdNr./BIC: Großbuchstaben ohne Leerzeichen."""
    return "".join(text.split()).upper()
