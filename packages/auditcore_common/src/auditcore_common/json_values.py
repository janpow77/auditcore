"""JSON value types and conversions to JSON-compatible values.

:func:`jsonable` merges three characterized variants of the domain packages.
Every difference between them is an explicit keyword; with all keywords off
it converts mappings (keys to text), lists/tuples and dates only:

========================  =====================================================
Variant                   Call
========================  =====================================================
risk ``plain``            ``jsonable(value)``
dataprotection ``plain``  ``jsonable(value, enums=True, dataclasses=True, sets=True)``
funding ``json_safe``     ``jsonable(value, decimals=True, nan_as_none=True)``
========================  =====================================================
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TypeAlias

#: A JSON value; read-only containers so that tuples and frozen mappings fit.
JsonValue: TypeAlias = (
    str | int | float | bool | None | Sequence["JsonValue"] | Mapping[str, "JsonValue"]
)
#: A JSON object as produced by ``to_dict`` views.
JsonObject: TypeAlias = dict[str, JsonValue]


@dataclass(frozen=True)
class _Options:
    enums: bool
    dataclasses: bool
    sets: bool
    decimals: bool
    nan_as_none: bool


def jsonable(
    value: object,
    *,
    enums: bool = False,
    dataclasses: bool = False,
    sets: bool = False,
    decimals: bool = False,
    nan_as_none: bool = False,
) -> object:
    """JSON-compatible copy of ``value``; unknown types are passed on unchanged.

    Always: ``date``/``datetime`` → ISO text, mappings → ``dict`` with text keys,
    lists and tuples → ``list``. Optional variants:

    ``enums``
        ``Enum`` members → their ``value`` (not converted further).
    ``dataclasses``
        dataclass instances → converted ``asdict`` result.
    ``sets``
        ``set``/``frozenset`` → sorted list of converted items.
    ``decimals``
        ``Decimal`` → ``str(value)``.
    ``nan_as_none``
        ``float('nan')`` → ``None`` (infinities stay).
    """
    return _convert(value, _Options(enums, dataclasses, sets, decimals, nan_as_none))


def _scalar(value: object, options: _Options) -> tuple[bool, object]:
    if options.enums and isinstance(value, Enum):
        return True, value.value
    if options.decimals and isinstance(value, Decimal):
        return True, str(value)
    if isinstance(value, date):
        return True, value.isoformat()
    if options.nan_as_none and isinstance(value, float) and math.isnan(value):
        return True, None
    return False, value


def _convert(value: object, options: _Options) -> object:
    done, result = _scalar(value, options)
    if done:
        return result
    if options.dataclasses and is_dataclass(value) and not isinstance(value, type):
        return _convert(asdict(value), options)
    if isinstance(value, Mapping):
        return {str(k): _convert(v, options) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_convert(v, options) for v in value]
    if options.sets and isinstance(value, set | frozenset):
        return sorted(_convert(v, options) for v in value)  # type: ignore[type-var]
    return value


def decode_json(data: bytes | str, error: Callable[[ValueError], Exception]) -> object:
    """``json.loads`` whose ``ValueError`` becomes ``error(exc)`` chained to it."""
    try:
        return json.loads(data)
    except ValueError as exc:
        raise error(exc) from exc
