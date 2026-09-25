"""Legal Entity Identifier (ISO 17442): 18 alphanumerics, two check digits, MOD 97-10."""

from __future__ import annotations

import re

from auditcore_identifiers.checksums import is_ascii_alnum, mod97, mod97_check_digits, prepare
from auditcore_identifiers.result import CheckResult, IdentifierKind, Reason, invalid, valid

_KIND = IdentifierKind.LEI
_FORMAT = re.compile(r"[A-Z0-9]{18}[0-9]{2}", re.ASCII)
_TOKEN = re.compile(r"(?<![A-Z0-9])[A-Z0-9]{18}[0-9]{2}(?![A-Z0-9])", re.ASCII)


def check_lei(value: object) -> CheckResult:
    """Strict LEI check: length 20, format, ISO 7064 MOD 97-10 over all 20 characters."""
    text = prepare(_KIND, value)
    if isinstance(text, CheckResult):
        return text
    if not is_ascii_alnum(text):
        return invalid(_KIND, value, Reason.INVALID_CHARACTERS,
                       "LEI enthält unzulässige Zeichen (nur A–Z, 0–9)")
    if len(text) != 20:
        return invalid(_KIND, value, Reason.INVALID_LENGTH,
                       f"LEI muss 20 Zeichen haben, nicht {len(text)}",
                       details={"length": len(text)})
    if _FORMAT.fullmatch(text) is None:
        return invalid(_KIND, value, Reason.INVALID_FORMAT,
                       "Die letzten beiden LEI-Stellen müssen Ziffern sein")
    if mod97(text) != 1:
        return invalid(_KIND, value, Reason.INVALID_CHECKSUM, "LEI-Prüfziffer ist falsch")
    return valid(_KIND, value, text, details={"lou_prefix": text[:4]})


def lei_check_digits(prefix: str) -> str:
    """Two check digits for an 18-character LEI prefix (for test data)."""
    base = prefix.strip().upper()
    if len(base) != 18 or not is_ascii_alnum(base):
        raise ValueError("Ein LEI-Präfix besteht aus 18 Ziffern oder Großbuchstaben.")
    return mod97_check_digits(base)


def extract_lei(text: object) -> str | None:
    """First LEI with correct check digits in a free-text field (e.g. ``"LEI: …"``)."""
    if not isinstance(text, str):
        return None
    for token in _TOKEN.findall(text.upper()):
        if check_lei(token).valid:
            return str(token)
    return None
