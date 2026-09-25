"""Static types shared by the modules; no runtime behaviour.

``JsonValue`` describes what the ``to_dict`` views return: JSON-compatible
values, with read-only containers so that tuples and frozen profile mappings
fit without copying.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias

JsonValue: TypeAlias = (
    str | int | float | bool | None | Sequence["JsonValue"] | Mapping[str, "JsonValue"]
)
#: A ``to_dict`` view.
JsonObject: TypeAlias = dict[str, JsonValue]
