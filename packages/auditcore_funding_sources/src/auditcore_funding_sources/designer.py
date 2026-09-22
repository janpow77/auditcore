"""Source profile ``designer.beneficiaries`` / ``designer.state_aid``: separate variants.

Behavior of ``janpow77/audit_designer@030a71e``
(``core/shared/research/register/beneficiaries.py`` and ``state_aid.py``).
These parsers resemble the flowworkshop ones but are **not** identical:
``parse_betrag`` understands dot-only thousands (``1.234.567``), ``bis`` ranges
and German range words, numbers and ``Decimal`` directly; ``parse_datum``
accepts two-digit years and ISO with time. They remain separately named.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .profiles import load_profile

PROFILE_ID = "designer.beneficiaries"
HASH_FIELDS = (
    "beneficiary_name", "project_name", "project_aktenzeichen", "bundesland", "periode",
    "fonds", "funded_at_raw", "cost_total_raw",
)
_DATE_FORMATS = ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d.%m.%y")
_SA_REGEX = re.compile(r"\bSA[\s\.\-_]*(\d{4,6})(?:[/\-\.](\d{4}))?", re.IGNORECASE)
_RANGE_RE = re.compile(
    r"(\d\s*(?:to|bis)\s*\d)|(\bless than\b)|(\bmore than\b)|(^\s*[<>])", re.IGNORECASE
)


def parse_betrag(value: Any) -> Decimal | None:
    """Amount; ``None`` when not interpretable (a ``0`` would be a claim)."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return Decimal(str(value))
    text = str(value).strip()
    if not text or text in {"-", "–", "—"}:
        return None
    text = re.sub(r"[€$£¥]", "", text)
    text = re.sub(r"\b(eur|usd|gbp|chf|sek)\b", "", text, flags=re.IGNORECASE).strip()
    span = re.search(r"(.+?)\s+(?:to|bis)\s+(.+)", text, flags=re.IGNORECASE)
    if span:
        return parse_betrag(span.group(2))
    lower = re.match(r"\s*(?:less than|weniger als|<)\s*(.+)", text, flags=re.I)
    if lower:
        return parse_betrag(lower.group(1))
    upper = re.match(r"\s*(?:more than|mehr als|>)\s*(.+)", text, flags=re.I)
    if upper:
        return parse_betrag(upper.group(1))
    text = re.sub(r"\s+", "", text.replace("\xa0", " "))
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        left, _, right = text.rpartition(",")
        if len(right) in (1, 2) and right.isdigit():
            text = f"{left.replace(',', '')}.{right}"
        else:
            text = text.replace(",", "")
    elif "." in text:
        groups = text.split(".")
        if len(groups) > 1 and all(len(g) == 3 and g.isdigit() for g in groups[1:]):
            text = text.replace(".", "")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def parse_satz(value: Any) -> Decimal | None:
    """Co-financing rate in percent; values ≤ 1 without ``%`` are read as fractions."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    explicit = "%" in text or "prozent" in text.lower()
    text = text.replace("%", "").replace("\xa0", " ")
    text = re.sub(r"prozent|percent", "", text, flags=re.IGNORECASE)
    number = parse_betrag(text)
    if number is None:
        return None
    if not explicit and number <= 1:
        number = number * 100
    if number < 0 or number > 100:
        return None
    return number


def parse_datum(value: Any) -> date | None:
    """Date from original text; ISO with time uses the date part."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    for pattern in _DATE_FORMATS:
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def _for_hash(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold())


def compute_record_hash(row: Mapping[str, Any], source_key: str) -> str:
    """Designer identity (32 hex); legal forms are deliberately not removed."""
    parts = [source_key] + [_for_hash(row.get(name)) for name in HASH_FIELDS]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def state_aid_parse_amount(text: Any) -> Decimal | None:
    """State-aid amount (``to``/``bis`` ranges → upper bound); no dot-only thousands."""
    if text is None:
        return None
    value = str(text).strip()
    if not value or value in {"-", "—"}:
        return None
    value = re.sub(r"[€$£¥]", "", value)
    value = re.sub(r"\b(eur|usd|gbp|chf|sek)\b", "", value, flags=re.IGNORECASE).strip()
    span = re.search(r"(.+?)\s+(?:to|bis)\s+(.+)", value, flags=re.IGNORECASE)
    if span:
        return state_aid_parse_amount(span.group(2))
    lower = re.match(r"\s*(?:less than|<)\s*(.+)", value, flags=re.IGNORECASE)
    if lower:
        return state_aid_parse_amount(lower.group(1))
    upper = re.match(r"\s*(?:more than|>)\s*(.+)", value, flags=re.IGNORECASE)
    if upper:
        return state_aid_parse_amount(upper.group(1))
    value = re.sub(r"\s+", "", value)
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        left, _, right = value.rpartition(",")
        if len(right) in (1, 2) and right.isdigit():
            value = f"{left.replace(',', '')}.{right}"
        else:
            value = value.replace(",", "")
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def amount_is_range(value: Any) -> bool:
    """Was the amount published as a range (then the stored value is an upper bound)?"""
    if not value:
        return False
    return bool(_RANGE_RE.search(str(value)))


def state_aid_parse_date(text: Any) -> date | None:
    """``TT/MM/JJJJ`` or ISO (and two further forms)."""
    if not text:
        return None
    value = str(text).strip()
    for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    return None


def normalize_company_name(text: Any, *, drop_filler: bool = False) -> str:
    """Designer comparison form; suffix, filler and transliteration lists of the source."""
    if not text:
        return ""
    data = load_profile("designer.state_aid")
    suffixes = set(data["legal_suffixes"])
    fillers = set(data["filler_words"])
    table = str.maketrans(data["transliteration"])
    s = str(text).translate(table).casefold()
    s = s.replace("&", " und ")
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    tokens: list[str] = []
    for tok in s.split():
        compact = tok.replace(".", "").replace("-", "")
        if compact in suffixes:
            continue
        if drop_filler and compact in fillers:
            continue
        tokens.append(tok)
    return " ".join(tokens)


def detect_sa_reference(text: Any) -> tuple[str | None, str | None]:
    """``(SA.12345[/2021], case URL)`` or ``(None, None)``."""
    if not text:
        return None, None
    m = _SA_REGEX.search(str(text))
    if not m:
        return None, None
    number, suffix = m.group(1), m.group(2)
    token = f"SA.{number}/{suffix}" if suffix else f"SA.{number}"
    return token, f"https://competition-cases.ec.europa.eu/cases/{token}"
