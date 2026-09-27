"""Data lookup by dotted path and German text formatting of placeholder values.

Formatting is locale-fixed (German) and deterministic: no ``locale`` module,
no current date, no guessing of numbers or dates inside texts.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from datetime import date, datetime

from .errors import TemplateError

#: Filters usable as ``{{ pfad | filter }}``.
FILTERS = ("text", "zahl", "ganzzahl", "eur", "prozent", "datum", "ja_nein")
_PATH = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
_MISSING = object()
#: Characters XML 1.0 cannot carry (and lone surrogates); never silently dropped.
CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff\ud800-\udfff]")


def plain(value: object) -> object:
    """Mutable JSON copy: every mapping becomes ``dict``, every tuple or list ``list``."""
    if isinstance(value, Mapping):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def valid_path(path: str) -> bool:
    """Dotted identifier path such as ``vorhaben.kennung``."""
    return _PATH.fullmatch(path) is not None


def lookup(scope: Mapping[str, object], path: str) -> object:
    """Value at ``path`` or ``None`` when a segment is missing or ``null``."""
    current: object = scope
    for segment in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(segment, _MISSING)
        if current is _MISSING:
            return None
    return current


def is_filled(value: object) -> bool:
    """Not ``None``, not an empty or blank text, not an empty list or object."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def _german(number: float, digits: int) -> str:
    text = f"{number:,.{digits}f}"
    return text.replace(",", "\u0001").replace(".", ",").replace("\u0001", ".")


def _number(value: object, where: str) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TemplateError(f"{where}: Zahl erwartet, erhalten {type(value).__name__}.")
    if isinstance(value, float) and not math.isfinite(value):
        raise TemplateError(f"{where}: Zahl muss endlich sein.")
    return value


def _date(value: object, where: str) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value) if "T" in value else date.fromisoformat(value)
        except ValueError as exc:
            raise TemplateError(f"{where}: kein ISO-Datum: {value!r}.") from exc
        return parsed.strftime("%d.%m.%Y")
    raise TemplateError(f"{where}: Datum erwartet, erhalten {type(value).__name__}.")


def _plain(value: object, where: str) -> str:
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, int):
        return _german(value, 0)
    if isinstance(value, float):
        number = _number(value, where)
        return _german(number, 0 if float(number).is_integer() else 2)
    if isinstance(value, str):
        return value
    if isinstance(value, (date, datetime)):
        return _date(value, where)
    raise TemplateError(f"{where}: {type(value).__name__} kann nicht als Text eingesetzt werden.")


def checked_text(text: str, where: str) -> str:
    """``text`` unless it holds control characters XML cannot represent."""
    if CONTROL.search(text):
        raise TemplateError(f"{where}: Text enthält unzulässige Steuerzeichen.")
    return text


def format_value(value: object, filter_name: str | None, where: str) -> str:
    """Text for a placeholder; ``None`` becomes the empty text for every filter."""
    if value is None:
        return ""
    if filter_name in (None, "text"):
        return checked_text(_plain(value, where), where)
    if filter_name == "datum":
        return _date(value, where)
    if filter_name == "ja_nein":
        if not isinstance(value, bool):
            raise TemplateError(f"{where}: true oder false erwartet.")
        return "ja" if value else "nein"
    number = _number(value, where)
    if filter_name == "eur":
        return f"{_german(number, 2)} €"
    if filter_name == "prozent":
        # Fraction as in the Excel profile "0.00%": 0.125 → "12,50 %".
        return f"{_german(number * 100, 2)} %"
    if filter_name == "ganzzahl":
        return _german(round(number), 0)
    if filter_name == "zahl":
        return _german(number, 0 if float(number).is_integer() else 2)
    raise TemplateError(f"{where}: unbekannter Filter {filter_name!r}.")
