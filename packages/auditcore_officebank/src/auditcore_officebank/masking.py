"""Zentraler Ausgabefilter: maskiert Secrets, bevor Text ausgegeben oder abgelegt wird.

Maskiert werden Bearer-Token, ``Authorization``-Kopfzeilen sowie Werte nach
``Password=``, ``Pwd=``, ``SA_PASSWORD=``, ``token=`` und ``secret=``. Projekte
können weitere Muster ergänzen. Die Maskierung ist eine Schutzschicht, kein Ersatz
dafür, Secrets gar nicht erst in Ausgaben zu schreiben.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

MASK = "****"

_BUILTIN: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)\b(authorization)\s*:\s*[^\r\n]+"), r"\1: " + MASK),
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]+"), r"\1 " + MASK),
    (
        re.compile(
            r"(?i)\b(password|pwd|sa_password|token|secret)"
            r"(\s*[=:]\s*)(\"[^\"]*\"|'[^']*'|[^;\s,]+)"
        ),
        r"\1\2" + MASK,
    ),
)


def mask_secrets(text: str, extra: Iterable[re.Pattern[str]] = ()) -> str:
    """Gibt ``text`` mit maskierten Secrets zurück.

    ``extra`` sind zusätzliche Muster aus der Projektkonfiguration; jeder Treffer
    wird vollständig durch ``****`` ersetzt.
    """
    for pattern, replacement in _BUILTIN:
        text = pattern.sub(replacement, text)
    for pattern in extra:
        text = pattern.sub(MASK, text)
    return text
