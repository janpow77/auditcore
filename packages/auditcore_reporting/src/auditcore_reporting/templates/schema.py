"""Data contract of a template: a checked subset of JSON Schema (draft 2020-12).

Supported keywords are listed in :data:`KEYWORDS`; a schema using any other
keyword is rejected when the template is defined, so the contract never
promises a check that does not happen. ``pattern`` is left out on purpose
(user-supplied regular expressions are a denial-of-service risk).
"""

from __future__ import annotations

import math
import operator
from collections.abc import Callable, Iterator, Mapping
from datetime import date, datetime

from .errors import Issue, TemplateError

KEYWORDS = frozenset(
    {
        "$schema", "$id", "title", "description", "examples", "default", "type",
        "properties", "required", "additionalProperties", "items", "enum", "const",
        "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minLength",
        "maxLength", "minItems", "maxItems", "format",
    }
)  # fmt: skip
TYPES = ("object", "array", "string", "number", "integer", "boolean", "null")
FORMATS = ("date", "date-time")
MAX_ISSUES = 50


def _types(schema: Mapping[str, object]) -> tuple[str, ...]:
    kind = schema.get("type")
    if kind is None:
        return ()
    if isinstance(kind, str):
        return (kind,)
    return tuple(str(k) for k in kind) if isinstance(kind, (list, tuple)) else ()


def _check_keywords(schema: Mapping[str, object], where: str) -> None:
    unknown = sorted(set(schema) - KEYWORDS)
    if unknown:
        raise TemplateError(f"{where}: nicht unterstützte Schlüsselwörter {unknown}.")
    kind = schema.get("type")
    if kind is not None and not isinstance(kind, (str, list)):
        raise TemplateError(f"{where}.type: Text oder Liste erwartet.")
    for name in _types(schema):
        if name not in TYPES:
            raise TemplateError(f"{where}.type: unbekannter Typ {name!r}.")
    if schema.get("format") not in (None, *FORMATS):
        raise TemplateError(f"{where}.format: nur {FORMATS} werden geprüft.")
    if schema.get("additionalProperties", False) not in (True, False):
        raise TemplateError(f"{where}.additionalProperties: nur true oder false.")


def check_schema(schema: object, where: str = "schema") -> None:
    """Reject unsupported keywords, unknown types and malformed sub-schemas."""
    if not isinstance(schema, Mapping):
        raise TemplateError(f"{where}: Schema muss ein Objekt sein.")
    _check_keywords(schema, where)
    properties = schema.get("properties", {})
    if not isinstance(properties, Mapping):
        raise TemplateError(f"{where}.properties: Objekt erwartet.")
    for name, child in properties.items():
        check_schema(child, f"{where}.properties.{name}")
    required = schema.get("required", [])
    if not isinstance(required, list) or not set(required) <= set(properties):
        raise TemplateError(f"{where}.required: nur Namen aus 'properties'.")
    if "items" in schema:
        check_schema(schema["items"], f"{where}.items")


def subschema(schema: Mapping[str, object], path: list[str]) -> Mapping[str, object] | None:
    """Schema of the value at ``path`` (object properties only) or ``None``."""
    current: Mapping[str, object] = schema
    for segment in path:
        properties = current.get("properties")
        if not isinstance(properties, Mapping) or segment not in properties:
            return None
        current = properties[segment]
    return current


def item_schema(schema: Mapping[str, object]) -> Mapping[str, object] | None:
    """Schema of the list items, if ``schema`` describes an array."""
    items = schema.get("items")
    return items if isinstance(items, Mapping) else None


def _type_ok(value: object, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    expected: dict[str, type | tuple[type, ...]] = {
        "object": Mapping, "array": list, "string": str, "boolean": bool, "null": type(None),
    }  # fmt: skip
    return isinstance(value, expected[name])


def _format_ok(value: str, name: object) -> bool:
    try:
        if name == "date":
            date.fromisoformat(value)
        elif name == "date-time":
            datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _scalar(value: object, schema: Mapping[str, object], path: str) -> Iterator[Issue]:
    enum = schema.get("enum")
    if isinstance(enum, (list, tuple)) and value not in enum:
        yield Issue(path, f"muss einer der Werte {list(enum)} sein")
    if "const" in schema and value != schema["const"]:
        yield Issue(path, f"muss {schema['const']!r} sein")
    if isinstance(value, str):
        yield from _string(value, schema, path)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield from _number(float(value), schema, path)


def _string(value: str, schema: Mapping[str, object], path: str) -> Iterator[Issue]:
    minimum, maximum = schema.get("minLength"), schema.get("maxLength")
    if isinstance(minimum, int) and len(value) < minimum:
        yield Issue(path, f"mindestens {minimum} Zeichen")
    if isinstance(maximum, int) and len(value) > maximum:
        yield Issue(path, f"höchstens {maximum} Zeichen")
    if "format" in schema and not _format_ok(value, schema["format"]):
        label = "ISO-Datum (JJJJ-MM-TT)" if schema["format"] == "date" else "ISO-Zeitpunkt"
        yield Issue(path, f"muss ein {label} sein")


def _number(value: float, schema: Mapping[str, object], path: str) -> Iterator[Issue]:
    if not math.isfinite(value):
        yield Issue(path, "muss eine endliche Zahl sein")
        return
    bounds: tuple[tuple[str, Callable[[float, float], bool], str], ...] = (
        ("minimum", operator.ge, "mindestens"),
        ("maximum", operator.le, "höchstens"),
        ("exclusiveMinimum", operator.gt, "größer als"),
        ("exclusiveMaximum", operator.lt, "kleiner als"),
    )
    for key, holds, label in bounds:
        limit = schema.get(key)
        if isinstance(limit, (int, float)) and not holds(value, float(limit)):
            yield Issue(path, f"muss {label} {limit} sein")


def _object(
    value: Mapping[str, object], schema: Mapping[str, object], path: str
) -> Iterator[Issue]:
    properties = schema.get("properties", {})
    assert isinstance(properties, Mapping)
    required = schema.get("required", ())
    for name in required if isinstance(required, (list, tuple)) else ():
        if name not in value:
            yield Issue(f"{path}.{name}", "Pflichtangabe fehlt")
    for name, child in value.items():
        if name in properties:
            yield from _validate(child, properties[name], f"{path}.{name}")
        elif schema.get("additionalProperties", False) is False:
            yield Issue(f"{path}.{name}", "ist im Datenvertrag nicht vorgesehen")


def _array(value: list[object], schema: Mapping[str, object], path: str) -> Iterator[Issue]:
    minimum, maximum = schema.get("minItems"), schema.get("maxItems")
    if isinstance(minimum, int) and len(value) < minimum:
        yield Issue(path, f"mindestens {minimum} Einträge")
    if isinstance(maximum, int) and len(value) > maximum:
        yield Issue(path, f"höchstens {maximum} Einträge")
    items = item_schema(schema)
    if items is not None:
        for index, entry in enumerate(value):
            yield from _validate(entry, items, f"{path}[{index}]")


def _validate(value: object, schema: Mapping[str, object], path: str) -> Iterator[Issue]:
    types = _types(schema)
    if types and not any(_type_ok(value, name) for name in types):
        yield Issue(path, f"Typ {' oder '.join(types)} erwartet")
        return
    yield from _scalar(value, schema, path)
    if isinstance(value, Mapping):
        yield from _object(value, schema, path)
    elif isinstance(value, list):
        yield from _array(value, schema, path)


def validate(data: object, schema: Mapping[str, object]) -> tuple[Issue, ...]:
    """All issues (at most :data:`MAX_ISSUES`) of ``data`` against ``schema``."""
    issues: list[Issue] = []
    for issue in _validate(data, schema, "$"):
        issues.append(issue)
        if len(issues) >= MAX_ISSUES:
            break
    return tuple(issues)
