"""Text helpers shared by the source profiles; each profile keeps its own grammar.

The amount parsers of flowworkshop and audit_designer differ in details
(range words, empty tokens, dot-only thousands). They are expressed here as
explicit :class:`AmountGrammar` values instead of copied functions, so every
difference stays visible and the shared steps exist only once.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

_CURRENCY_SYMBOLS = re.compile(r"[€$£¥]")
_CURRENCY_CODES = re.compile(r"\b(eur|usd|gbp|chf|sek)\b", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")
_SA_REGEX = re.compile(r"\bSA[\s\.\-_]*(\d{4,6})(?:[/\-\.](\d{4}))?", re.IGNORECASE)


@dataclass(frozen=True)
class AmountGrammar:
    """How one source variant reads a published amount string.

    ``span`` selects the upper bound of a range, ``lower``/``upper`` strip a
    comparison word; the captured operand is parsed again with the same
    grammar. ``dot_thousands`` accepts ``1.234.567`` (dots only).
    """

    empty_tokens: frozenset[str]
    span: re.Pattern[str]
    lower: re.Pattern[str]
    upper: re.Pattern[str]
    dot_thousands: bool

    def operand(self, text: str) -> str | None:
        """Operand of a range or comparison form, ``None`` for a plain number."""
        span = self.span.search(text)
        if span:
            return span.group(2)
        for pattern in (self.lower, self.upper):
            match = pattern.match(text)
            if match:
                return match.group(1)
        return None

    def parse(self, value: object) -> Decimal | None:
        """Parse text of this variant; ``None`` when not interpretable (never ``0``)."""
        text = str(value).strip()
        if not text or text in self.empty_tokens:
            return None
        text = strip_currency(text)
        operand = self.operand(text)
        if operand is not None:
            return self.parse(operand)
        return to_decimal(normalize_separators(text, dot_thousands=self.dot_thousands))


def strip_currency(text: str) -> str:
    """Remove currency symbols and codes, then surrounding whitespace."""
    return _CURRENCY_CODES.sub("", _CURRENCY_SYMBOLS.sub("", text)).strip()


def normalize_separators(text: str, *, dot_thousands: bool) -> str:
    """German or English grouping to a plain decimal string (whitespace removed)."""
    text = _WHITESPACE.sub("", text)
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            return text.replace(".", "").replace(",", ".")
        return text.replace(",", "")
    if "," in text:
        left, _, right = text.rpartition(",")
        if len(right) in (1, 2) and right.isdigit():
            return f"{left.replace(',', '')}.{right}"
        return text.replace(",", "")
    if dot_thousands and "." in text:
        groups = text.split(".")
        if len(groups) > 1 and all(len(g) == 3 and g.isdigit() for g in groups[1:]):
            return text.replace(".", "")
    return text


def to_decimal(text: str) -> Decimal | None:
    """``Decimal`` of a normalised string, ``None`` if it is not a number."""
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def drop_legal_tokens(
    text: str, suffixes: set[str], fillers: set[str], *, drop_filler: bool
) -> str:
    """Remove legal-form suffixes (and optionally filler words) from a folded name."""
    tokens: list[str] = []
    for token in text.split():
        compact = token.replace(".", "").replace("-", "")
        if compact in suffixes or (drop_filler and compact in fillers):
            continue
        tokens.append(token)
    return " ".join(tokens)


def detect_sa_reference(text: object) -> tuple[str | None, str | None]:
    """``(SA.12345[/2021], case URL)`` or ``(None, None)``."""
    if not text:
        return None, None
    match = _SA_REGEX.search(str(text))
    if not match:
        return None, None
    number, suffix = match.group(1), match.group(2)
    token = f"SA.{number}/{suffix}" if suffix else f"SA.{number}"
    return token, f"https://competition-cases.ec.europa.eu/cases/{token}"
