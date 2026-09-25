"""Small text normalisations shared by several packages."""

from __future__ import annotations


def group_thousands_de(value: int) -> str:
    """``1234567`` → ``"1.234.567"`` (German thousands separator)."""
    return f"{value:,}".replace(",", ".")


def compact_upper(text: str) -> str:
    """Remove all whitespace and upper-case (IBAN, BIC, VAT identifiers)."""
    return "".join(text.split()).upper()
