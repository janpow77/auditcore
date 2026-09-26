"""Generische Abbildung der Erweiterungs-Datenklassen auf XML und JSON.

Die Abbildung steht in den Feld-Metadaten, gesetzt über :func:`xml_field`
bzw. :func:`xml_items`: ``xml`` ist der Attribut- oder Elementname im
FlowAudit-Schema, ``kind`` eine von

* ``attr`` – Attribut (Text; mit ``bool_value=True`` als ``true``/``false``),
* ``tokens`` – Attribut mit durch Leerzeichen getrennten Werten,
* ``body`` – Textinhalt des Elements (Rückfall: Attribut ``value``),
* ``text`` / ``texts`` – ein bzw. mehrere Kindelemente mit Textinhalt,
* ``elements`` – mehrere Kindelemente einer anderen Datenklasse,
* ``internal`` – nicht im XML.

JSON-Schlüssel sind die Python-Feldnamen; leere Werte entfallen.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import Field, field, fields, is_dataclass
from typing import TypeVar, overload
from xml.etree import ElementTree as ET

from ..namespaces import FLOWAUDIT_NAMESPACE, q

T = TypeVar("T")
_D = TypeVar("_D")
JsonObject = dict[str, object]


@overload
def xml_field(name: str, kind: str = ..., *, bool_value: bool = ...) -> None: ...


@overload
def xml_field(name: str, kind: str = ..., *, bool_value: bool = ..., default: _D) -> _D: ...


def xml_field(name: str, kind: str = "attr", *, bool_value: bool = False, default: object = None) -> object:
    """Einzelwert-Feld mit XML-Abbildung (``attr``, ``body`` oder ``text``)."""
    return field(default=default, metadata={"xml": name, "kind": kind, "item_type": None, "bool": bool_value})


def xml_items(name: str, kind: str, item_type: type | None = None) -> tuple[()]:
    """Mehrwert-Feld (``texts``, ``tokens`` oder ``elements``) mit leerem Tupel als Standard."""
    return field(default=(), metadata={"xml": name, "kind": kind, "item_type": item_type, "bool": False})


def fa(local: str) -> str:
    """Qualifizierter Name eines FlowAudit-Elements."""
    return q(FLOWAUDIT_NAMESPACE, local)


def _fields(obj: object) -> tuple[Field[object], ...]:
    if not is_dataclass(obj):
        raise TypeError(f"{obj!r} ist keine Datenklasse.")
    return fields(obj)


def _meta(item: Field[object]) -> tuple[str, str]:
    return str(item.metadata.get("xml", "")), str(item.metadata.get("kind", "internal"))


def _bool(value: str | None) -> bool | None:
    lowered = (value or "").strip().lower()
    if lowered in ("true", "1", "ja"):
        return True
    if lowered in ("false", "0", "nein"):
        return False
    return None


def _clean(value: str | None) -> str | None:
    stripped = (value or "").strip()
    return stripped or None


def _body(element: ET.Element) -> str | None:
    content = "".join(element.itertext()) if len(element) == 0 else element.text
    return _clean(content) or _clean(element.get("value"))


def _item_type(item: Field[object]) -> type:
    item_type = item.metadata.get("item_type")
    if not isinstance(item_type, type):
        raise TypeError(f"Feld {item.name} hat keinen Elementtyp.")
    return item_type


def _read_value(element: ET.Element, item: Field[object]) -> object:
    name, kind = _meta(item)
    if kind == "attr":
        raw = element.get(name)
        return _bool(raw) if item.metadata.get("bool") else _clean(raw)
    if kind == "tokens":
        return tuple((element.get(name) or "").split())
    if kind == "body":
        return _body(element)
    if kind == "text":
        child = element.find(fa(name))
        return _clean(child.text) if child is not None else None
    if kind == "texts":
        return tuple(text for child in element.findall(fa(name)) if (text := _clean(child.text)))
    return tuple(read_element(_item_type(item), child) for child in element.findall(fa(name)))


def read_element(cls: type[T], element: ET.Element) -> T:
    """Liest ein FlowAudit-Element in die Datenklasse ``cls``."""
    values = {item.name: _read_value(element, item) for item in _fields(cls) if _meta(item)[1] != "internal"}
    return cls(**values)


def _write_attribute(element: ET.Element, item: Field[object], value: object) -> None:
    name, kind = _meta(item)
    if kind == "attr" and isinstance(value, bool):
        element.set(name, "true" if value else "false")
    elif kind == "attr" and value not in (None, ""):
        element.set(name, str(value))
    elif kind == "tokens" and isinstance(value, tuple) and value:
        element.set(name, " ".join(str(v) for v in value))
    elif kind == "body" and isinstance(value, str) and value:
        element.text = value


def _write_children(element: ET.Element, item: Field[object], value: object) -> None:
    name, kind = _meta(item)
    if kind == "text" and isinstance(value, str) and value:
        ET.SubElement(element, fa(name)).text = value
    elif kind == "texts" and isinstance(value, tuple):
        for entry in value:
            ET.SubElement(element, fa(name)).text = str(entry)
    elif kind == "elements" and isinstance(value, tuple):
        for entry in value:
            element.append(write_element(entry, name))


def write_element(obj: object, tag: str) -> ET.Element:
    """Erzeugt das FlowAudit-Element ``tag`` zu einer Datenklasse (leere Werte entfallen)."""
    element = ET.Element(fa(tag))
    items = [item for item in _fields(obj) if _meta(item)[1] != "internal"]
    for item in items:
        _write_attribute(element, item, getattr(obj, item.name))
    for item in items:
        _write_children(element, item, getattr(obj, item.name))
    return element


def _json(value: object) -> object:
    if isinstance(value, tuple):
        return [_json(entry) for entry in value]
    if is_dataclass(value) and not isinstance(value, type):
        return to_dict(value)
    return value


def to_dict(obj: object) -> JsonObject:
    """JSON-fähige Darstellung ohne leere Werte (Schlüssel = Python-Feldnamen)."""
    result: JsonObject = {}
    for item in _fields(obj):
        value = getattr(obj, item.name)
        if value is not None and value != "" and value != ():
            result[item.name] = _json(value)
    return result


def _items(value: object) -> list[object]:
    if not isinstance(value, list | tuple):
        raise ValueError(f"Liste erwartet, erhalten: {value!r}")
    return list(value)


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Objekt erwartet, erhalten: {value!r}")
    return value


def _from_json(item: Field[object], value: object) -> object:
    kind = _meta(item)[1]
    if kind == "elements":
        return tuple(from_dict(_item_type(item), _mapping(entry)) for entry in _items(value))
    if kind in ("texts", "tokens"):
        return tuple(str(entry) for entry in _items(value))
    return value


def from_dict(cls: type[T], data: Mapping[str, object]) -> T:
    """Umkehrung von :func:`to_dict`; unbekannte Schlüssel werden abgewiesen."""
    known = {item.name: item for item in _fields(cls)}
    unknown = set(data) - set(known)
    if unknown:
        raise ValueError(f"Unbekannte Felder für {cls.__name__}: {sorted(unknown)}")
    return cls(**{name: _from_json(known[name], value) for name, value in data.items()})
