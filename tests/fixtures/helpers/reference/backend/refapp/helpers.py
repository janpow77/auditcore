"""Reference implementation of every shared helper contract (test fixture)."""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

EMPTY = "—"
BERLIN = ZoneInfo("Europe/Berlin")
CURRENCY = re.compile(r"€|\bEUR\b", re.IGNORECASE)
DATE_ONLY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
IBAN_LENGTHS = {
    "AT": 20,
    "BE": 16,
    "CH": 21,
    "DE": 22,
    "ES": 24,
    "FR": 27,
    "GB": 22,
    "IT": 27,
    "LU": 20,
    "NL": 18,
}
SEPARATORS = {"de": (".", ","), "en": (",", ".")}


def _pattern(group: str, decimal: str) -> re.Pattern[str]:
    g, d = re.escape(group), re.escape(decimal)
    return re.compile(rf"^-?(\d{{1,3}}({g}\d{{3}})+|\d+)({d}\d+)?$")


def _auto_mode(text: str) -> str | None:
    last_dot, last_comma = text.rfind("."), text.rfind(",")
    if last_dot >= 0 and last_comma >= 0:
        return "de" if last_comma > last_dot else "en"
    sep = "." if last_dot >= 0 else "," if last_comma >= 0 else ""
    if not sep:
        return "de"
    if text.count(sep) == 1 and len(text) - text.index(sep) - 1 == 3:
        return None
    if text.count(sep) > 1:
        return "de" if sep == "." else "en"
    return "en" if sep == "." else "de"


STRICT_DE = re.compile(r"^-?(\d{1,3}(\.\d{3})+|\d+)(,\d{1,2})?$")
SINGLE_GROUP = re.compile(r"^-?\d{1,3}\.\d{3}$")
SPACES = re.compile("[\u00a0\u202f]")


def _clean(text: str) -> str:
    cleaned = SPACES.sub(" ", CURRENCY.sub("", text)).replace("\u2212", "-").strip()
    cleaned = re.sub(r"^-\s+", "-", cleaned)
    return re.sub(r"(?<=\d) (?=\d{3}\b)", "", cleaned)


def parse_number(text: object, mode: str = "de") -> Decimal | None:
    if not isinstance(text, str):
        return None
    cleaned = _clean(text)
    if mode == "de":
        if SINGLE_GROUP.match(cleaned) or not STRICT_DE.match(cleaned):
            return None
        return Decimal(cleaned.replace(".", "").replace(",", "."))
    chosen = _auto_mode(cleaned) if mode == "auto" else mode
    if chosen not in SEPARATORS:
        return None
    group, decimal = SEPARATORS[chosen]
    if not _pattern(group, decimal).match(cleaned):
        return None
    return Decimal(cleaned.replace(group, "").replace(decimal, "."))


def _is_empty(value: object) -> bool:
    return value is None or value == "" or (isinstance(value, float) and math.isnan(value))


def _group(number: str) -> str:
    whole, _, fraction = number.partition(".")
    sign = "-" if whole.startswith("-") else ""
    digits = whole.lstrip("-")
    grouped = f"{int(digits):,}".replace(",", ".")
    return f"{sign}{grouped},{fraction}" if fraction else f"{sign}{grouped}"


def format_money(value: object) -> str:
    if _is_empty(value):
        return EMPTY
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except ArithmeticError:
        return EMPTY
    return f"{_group(str(amount))} €"


def _moment(value: object) -> datetime | date | None:
    if isinstance(value, datetime):
        return value.astimezone(BERLIN)
    if not isinstance(value, str) or not value:
        return None
    match = DATE_ONLY.match(value)
    if match:
        return date(int(match[1]), int(match[2]), int(match[3]))
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(BERLIN)
    except ValueError:
        return None


def format_date(value: object) -> str:
    moment = _moment(value)
    return moment.strftime("%d.%m.%Y") if moment else EMPTY


def format_datetime(value: object) -> str:
    moment = _moment(value)
    return moment.strftime("%d.%m.%Y, %H:%M") if isinstance(moment, datetime) else EMPTY


def format_filesize(size: object) -> str:
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        return EMPTY
    if size < 1024:
        return f"{size} B"
    value, index = float(size), 0
    units = ("KB", "MB", "GB", "TB")
    while True:
        value /= 1024
        if value < 1024 or index == len(units) - 1:
            break
        index += 1
    unit = units[index]
    text = f"{value:.1f}".replace(".", ",")
    return f"{text.removesuffix(',0')} {unit}"


def _mod97(text: str) -> int:
    return int("".join(str(int(char, 36)) for char in text)) % 97


def iban_valid(text: object) -> bool:
    if not isinstance(text, str):
        return False
    iban = text.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", iban):
        return False
    if IBAN_LENGTHS.get(iban[:2]) != len(iban):
        return False
    return _mod97(iban[4:] + iban[:4]) == 1


def lei_valid(text: object) -> bool:
    if not isinstance(text, str):
        return False
    lei = text.upper()
    return bool(re.fullmatch(r"[A-Z0-9]{18}\d{2}", lei)) and _mod97(lei) == 1


def csv_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value).replace(".", ",")
    text = str(value)
    if text[:1] in ("=", "+", "-", "@", "\t", "\r"):
        text = "'" + text
    if any(char in text for char in ';"\n\r'):
        text = '"' + text.replace('"', '""') + '"'
    return text


def csv_document(rows: list[list[object]]) -> str:
    return "﻿" + "".join(";".join(csv_cell(cell) for cell in row) + "\r\n" for row in rows)
