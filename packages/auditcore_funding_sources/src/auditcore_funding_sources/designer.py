"""Source profile ``designer.beneficiaries`` / ``designer.state_aid``: separate variants.

Behavior of ``janpow77/audit_designer@030a71e``
(``core/shared/research/register/beneficiaries.py`` and ``state_aid.py``).
These parsers resemble the flowworkshop ones but are **not** identical:
``parse_amount`` understands dot-only thousands (``1.234.567``), ``bis`` ranges
and German range words, numbers and ``Decimal`` directly; ``parse_date``
accepts two-digit years and ISO with time. They remain separately named.

The source symbol names ``parse_betrag``, ``parse_satz`` and ``parse_datum``
stay available as deprecated aliases (``DeprecationWarning``) since 0.1.2.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
import warnings
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal

from ._parsing import AmountGrammar, drop_legal_tokens
from ._parsing import detect_sa_reference as detect_sa_reference
from .profiles import load_profile

PROFILE_ID = "designer.beneficiaries"
HASH_FIELDS = (
    "beneficiary_name",
    "project_name",
    "project_aktenzeichen",
    "bundesland",
    "periode",
    "fonds",
    "funded_at_raw",
    "cost_total_raw",
)
_DATE_FORMATS = ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d.%m.%y")
_RANGE_RE = re.compile(
    r"(\d\s*(?:to|bis)\s*\d)|(\bless than\b)|(\bmore than\b)|(^\s*[<>])", re.IGNORECASE
)


_DESIGNER_AMOUNT = AmountGrammar(
    empty_tokens=frozenset({"-", "–", "—"}),
    span=re.compile(r"(.+?)\s+(?:to|bis)\s+(.+)", re.IGNORECASE),
    lower=re.compile(r"\s*(?:less than|weniger als|<)\s*(.+)", re.IGNORECASE),
    upper=re.compile(r"\s*(?:more than|mehr als|>)\s*(.+)", re.IGNORECASE),
    dot_thousands=True,
)
_STATE_AID_AMOUNT = AmountGrammar(
    empty_tokens=frozenset({"-", "—"}),
    span=re.compile(r"(.+?)\s+(?:to|bis)\s+(.+)", re.IGNORECASE),
    lower=re.compile(r"\s*(?:less than|<)\s*(.+)", re.IGNORECASE),
    upper=re.compile(r"\s*(?:more than|>)\s*(.+)", re.IGNORECASE),
    dot_thousands=False,
)


def parse_amount(value: object) -> Decimal | None:
    """Amount; ``None`` when not interpretable (a ``0`` would be a claim).

    ``True`` raises like the source (FS-G01).
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return Decimal(str(value))
    return _DESIGNER_AMOUNT.parse(value)


def parse_rate(value: object) -> Decimal | None:
    """Co-financing rate in percent; values ≤ 1 without ``%`` are read as fractions."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    explicit = "%" in text or "prozent" in text.lower()
    text = text.replace("%", "").replace("\xa0", " ")
    text = re.sub(r"prozent|percent", "", text, flags=re.IGNORECASE)
    number = parse_amount(text)
    if number is None:
        return None
    if not explicit and number <= 1:
        number = number * 100
    if number < 0 or number > 100:
        return None
    return number


def parse_date(value: object) -> date | None:
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


def _for_hash(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold())


def compute_record_hash(row: Mapping[str, object], source_key: str) -> str:
    """Designer identity (32 hex); legal forms are deliberately not removed."""
    parts = [source_key] + [_for_hash(row.get(name)) for name in HASH_FIELDS]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def state_aid_parse_amount(text: object) -> Decimal | None:
    """State-aid amount (``to``/``bis`` ranges → upper bound); no dot-only thousands."""
    if text is None:
        return None
    return _STATE_AID_AMOUNT.parse(text)


def amount_is_range(value: object) -> bool:
    """Was the amount published as a range (then the stored value is an upper bound)?"""
    if not value:
        return False
    return bool(_RANGE_RE.search(str(value)))


def state_aid_parse_date(text: object) -> date | None:
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


def normalize_company_name(text: object, *, drop_filler: bool = False) -> str:
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
    return drop_legal_tokens(s, suffixes, fillers, drop_filler=drop_filler)


_DEPRECATED_ALIASES = {
    "parse_betrag": "parse_amount",
    "parse_satz": "parse_rate",
    "parse_datum": "parse_date",
}


def __getattr__(name: str) -> object:
    """Deprecated source names (0.1.1); they return the renamed function and warn."""
    replacement = _DEPRECATED_ALIASES.get(name)
    if replacement is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    warnings.warn(
        f"auditcore_funding_sources.designer.{name} ist veraltet; "
        f"stattdessen {replacement} verwenden.",
        DeprecationWarning,
        stacklevel=2,
    )
    return globals()[replacement]
