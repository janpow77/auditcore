"""Static types shared by the modules; no runtime behaviour.

``JsonValue`` describes what the ``to_dict`` views return: JSON-compatible
values, with read-only containers so that tuples and frozen profile mappings
fit without copying. Both are defined in ``auditcore_common.json_values``.
"""

from __future__ import annotations

from auditcore_common.json_values import JsonObject, JsonValue

__all__ = ["JsonObject", "JsonValue"]
