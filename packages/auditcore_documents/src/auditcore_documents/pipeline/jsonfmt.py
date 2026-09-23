"""Kompakte JSON-Darstellung wie ``pydantic.BaseModel.model_dump_json``.

Die Stufen-Hashes des Originals entstehen aus ``artifacts.model_dump_json()``.
Um sie ohne pydantic bytegleich zu reproduzieren, schreibt diese Funktion
kompaktes JSON (``,``/``:`` ohne Leerzeichen, UTF-8 ohne Escapes) und
formatiert Gleitkommazahlen wie pydantic-core: Exponent ohne ``+`` und ohne
führende Nullen (``1e-7`` statt ``1e-07``); ``inf``/``nan`` werden ``null``.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from enum import Enum
from typing import Any

_EXPONENT = re.compile(r"e([+-]?)0*(\d+)$")


def _float(value: float) -> str:
    if math.isnan(value) or math.isinf(value):
        return "null"
    text = repr(value)
    return _EXPONENT.sub(lambda m: "e" + ("-" if m.group(1) == "-" else "") + m.group(2), text)


def dumps_compact(value: Any) -> str:
    """JSON wie pydantic-core; unbekannte Typen führen zu ``TypeError``."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, Enum):
        return dumps_compact(value.value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _float(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, datetime):
        return json.dumps(value.isoformat().replace("+00:00", "Z"))
    if isinstance(value, date):
        return json.dumps(value.isoformat())
    if isinstance(value, Mapping):
        return (
            "{"
            + ",".join(
                json.dumps(str(key), ensure_ascii=False) + ":" + dumps_compact(item)
                for key, item in value.items()
            )
            + "}"
        )
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return "[" + ",".join(dumps_compact(item) for item in value) + "]"
    raise TypeError(f"Nicht serialisierbar: {type(value).__name__}")
