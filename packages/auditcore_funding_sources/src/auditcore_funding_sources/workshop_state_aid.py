"""flowworkshop ``state_aid_service``: amount, date, names and SA references.

Part of the source profile ``flowworkshop.beneficiaries`` (see
:mod:`auditcore_funding_sources.workshop`, which re-exports every name here).
Behavior of ``janpow77/flowworkshop@a05bb21``, reproduced exactly.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal

from ._parsing import AmountGrammar, drop_legal_tokens
from ._parsing import detect_sa_reference as detect_sa_reference
from .profiles import load_profile

PROFILE_ID = "flowworkshop.beneficiaries"
_STRIP_TABLE = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "Ä": "ae",
        "Ö": "oe",
        "Ü": "ue",
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "å": "a",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "í": "i",
        "ì": "i",
        "î": "i",
        "ï": "i",
        "ó": "o",
        "ò": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ù": "u",
        "û": "u",
        "ç": "c",
        "ñ": "n",
        "ý": "y",
        "ł": "l",
        "ń": "n",
        "ś": "s",
        "ź": "z",
        "ż": "z",
        "č": "c",
        "š": "s",
        "ž": "z",
        "đ": "d",
    }
)
_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WORKSHOP_AMOUNT = AmountGrammar(
    empty_tokens=frozenset({"-", "—"}),
    span=re.compile(r"(.+?)\s+to\s+(.+)", re.IGNORECASE),
    lower=re.compile(r"\s*(?:less than|<)\s*(.+)", re.IGNORECASE),
    upper=re.compile(r"\s*(?:more than|>)\s*(.+)", re.IGNORECASE),
    dot_thousands=False,
)


def parse_amount(text: object) -> Decimal | None:
    """Amount from a published string; ranges yield the upper bound.

    ``'1.200.000,00'`` and ``'1,200,000'`` are both understood; an unparsable
    value is ``None`` (never ``0``). A value with only dots such as ``'1.234.567'``
    is **not** understood (``None``) — unchanged source behavior, see
    ``docs/behavior-changes.md`` (FS-W05).
    """
    if text is None:
        return None
    return _WORKSHOP_AMOUNT.parse(text)


def parse_date(text: object) -> date | None:
    """``DD/MM/YYYY``, ``YYYY-MM-DD``, ``DD.MM.YYYY`` or ``YYYY/MM/DD``."""
    if not text:
        return None
    s = str(text).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def strip_accents(text: object) -> str:
    """Diacritics and German umlauts folded for comparison."""
    if not text:
        return ""
    return str(text).translate(_STRIP_TABLE)


def normalize_company_name(text: object, *, drop_filler: bool = False) -> str:
    """Comparison form: lower case, no accents, no legal-form suffix, compact spaces."""
    if not text:
        return ""
    data = load_profile(PROFILE_ID)
    suffixes = set(data["legal_suffixes"])
    fillers = set(data["filler_words"])
    s = strip_accents(text).casefold()
    s = s.replace("&", " und ")
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return drop_legal_tokens(s, suffixes, fillers, drop_filler=drop_filler)
