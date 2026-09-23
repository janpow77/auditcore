"""Legal Entity Identifier checks (ISO 17442).

The source application only checks the *format* (18 alphanumerics plus two
digits). This module keeps that check under its honest name and adds the
ISO 7064 MOD 97-10 check digit verification that ISO 17442 prescribes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_FORMAT = re.compile(r"^[A-Z0-9]{18}\d{2}$")
_TOKEN = re.compile(r"\b([A-Z0-9]{18}\d{2})\b")


@dataclass(frozen=True)
class LeiCheck:
    """Result of :func:`check_lei`; ``valid`` requires format and check digits."""

    normalized: str | None
    format_ok: bool
    checksum_ok: bool

    @property
    def valid(self) -> bool:
        """True only for a correctly formatted LEI with correct check digits."""
        return self.format_ok and self.checksum_ok


def _normalized(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value).strip().upper()


def is_lei_format(value: object) -> bool:
    """Format check only (source behavior); does not verify the check digits."""
    text = _normalized(value)
    return bool(text and _FORMAT.match(text))


def lei_checksum_ok(value: str) -> bool:
    """ISO 7064 MOD 97-10 over the 20 characters (letters A=10 … Z=35)."""
    if not _FORMAT.match(value):
        return False
    digits = "".join(str(int(character, 36)) for character in value)
    return int(digits) % 97 == 1


def check_lei(value: object) -> LeiCheck:
    """Normalise (strip, upper case) and check format and check digits."""
    text = _normalized(value)
    format_ok = bool(text and _FORMAT.match(text))
    return LeiCheck(text, format_ok, bool(text) and format_ok and lei_checksum_ok(str(text)))


def lei_check_digits(prefix: str) -> str:
    """Two check digits for an 18-character LEI prefix (for test data and validation)."""
    base = prefix.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{18}", base):
        raise ValueError("Ein LEI-Präfix besteht aus 18 Ziffern oder Großbuchstaben.")
    number = int("".join(str(int(c, 36)) for c in base + "00"))
    return f"{98 - number % 97:02d}"


def extract_lei(text: object, *, require_checksum: bool = True) -> str | None:
    """First LEI token in a free-text identifier field.

    With ``require_checksum=True`` (default of this library) tokens with wrong
    check digits are skipped; the source application accepted any token of
    the right format (``require_checksum=False``).
    """
    value = _normalized(text)
    if not value:
        return None
    candidates = [value] if _FORMAT.match(value) else _TOKEN.findall(value)
    if not require_checksum:
        return candidates[0] if candidates else None
    for candidate in candidates:
        if lei_checksum_ok(candidate):
            return str(candidate)
    return None
