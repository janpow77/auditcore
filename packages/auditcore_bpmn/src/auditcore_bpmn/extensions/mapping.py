"""Generische Abbildung der Erweiterungs-Datenklassen auf XML und JSON.

Die Abbildung steht in den Feld-Metadaten, gesetzt über :func:`xml_field`:
``xml`` ist der Attribut- bzw. Elementname im FlowAudit-Schema, ``kind`` eine von

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
from dataclasses import Field, field, fields
from typing import Any, TypeVar
from xml.etree import ElementTree as ET

from ..namespaces import FLOWAUDIT_NAMESPACE, q

T = TypeVar("T")
_SEQUENCE_KINDS = ("texts", "elements", "tokens")


def xml_field(
    name: str, kind: str = "attr", *, item_type: type | None = None, bool_value: bool = False, default: Any = None
) -> Any:
    """Datenklassenfeld mit XML-Abbildung (siehe Moduldokumentation)."""
    metadata = {"xml": name, "kind": kind, "item_type": item_type, "bool": bool_value}
    if kind in _SEQUENCE_KINDS:
        return field(default=(), metadata=metadata)
    return field(default=default, metadata=metadata)


def fa(local: str) -> str:
    """Qualifizierter Name eines FlowAudit-Elements."""
    return q(FLOWAUDIT_NAMESPACE, local)


def _fields(cls: Any) -> tuple[Field[Any], ...]:
    return fields(cls)


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


def _read_value(element: ET.Element, meta: Mapping[str, Any]) -> Any:
    kind, name = meta["kind"], meta["xml"]
    if kind == "attr":
        raw = element.get(name)
        return _bool(raw) if meta["bool"] else _clean(raw)
    if kind == "tokens":
        return tuple((element.get(name) or "").split())
    if kind == "body":
        return _body(element)
    if kind == "text":
        child = element.find(fa(name))
        return _clean(child.text) if child is not None else None
    if kind == "texts":
        return tuple(text for child in element.findall(fa(name)) if (text := _clean(child.text)))
    if kind == "elements":
        return tuple(read_element(meta["item_type"], child) for child in element.findall(fa(name)))
    return None


def read_element(cls: type[T], element: ET.Element) -> T:
    """Liest ein FlowAudit-Element in die Datenklasse ``cls``."""
    values = {
        item.name: _read_value(element, item.metadata)
        for item in _fields(cls)
        if item.metadata.get("kind", "internal") != "internal"
    }
    return cls(**values)


def _write_attribute(element: ET.Element, meta: Mapping[str, Any], value: Any) -> None:
    kind, name = meta["kind"], meta["xml"]
    if kind == "attr" and isinstance(value, bool):
        element.set(name, "true" if value else "false")
    elif kind == "attr" and value not in (None, ""):
        element.set(name, str(value))
    elif kind == "tokens" and value:
        element.set(name, " ".join(value))
    elif kind == "body" and value:
        element.text = value


def _write_children(element: ET.Element, meta: Mapping[str, Any], value: Any) -> None:
    kind, name = meta["kind"], meta["xml"]
    if kind == "text" and value:
        ET.SubElement(element, fa(name)).text = value
    elif kind == "texts":
        for entry in value:
            ET.SubElement(element, fa(name)).text = entry
    elif kind == "elements":
        for entry in value:
            element.append(write_element(entry, name))


def write_element(obj: Any, tag: str) -> ET.Element:
    """Erzeugt das FlowAudit-Element ``tag`` zu einer Datenklasse (leere Werte entfallen)."""
    element = ET.Element(fa(tag))
    items = [item for item in _fields(obj) if item.metadata.get("kind", "internal") != "internal"]
    for item in items:
        _write_attribute(element, item.metadata, getattr(obj, item.name))
    for item in items:
        _write_children(element, item.metadata, getattr(obj, item.name))
    return element


def to_dict(obj: Any) -> dict[str, Any]:
    """JSON-fähige Darstellung ohne leere Werte (Schlüssel = Python-Feldnamen)."""
    result: dict[str, Any] = {}
    for item in _fields(obj):
        value = getattr(obj, item.name)
        if item.metadata.get("kind") == "elements":
            if value:
                result[item.name] = [to_dict(entry) for entry in value]
        elif isinstance(value, tuple):
            if value:
                result[item.name] = list(value)
        elif value is not None and value != "":
            result[item.name] = value
    return result


def from_dict(cls: type[T], data: Mapping[str, Any]) -> T:
    """Umkehrung von :func:`to_dict`; unbekannte Schlüssel werden abgewiesen."""
    known = {item.name: item for item in _fields(cls)}
    unknown = set(data) - set(known)
    if unknown:
        raise ValueError(f"Unbekannte Felder für {cls.__name__}: {sorted(unknown)}")
    values: dict[str, Any] = {}
    for name, value in data.items():
        kind = known[name].metadata.get("kind")
        if kind == "elements":
            values[name] = tuple(from_dict(known[name].metadata["item_type"], entry) for entry in value)
        elif kind in ("texts", "tokens"):
            values[name] = tuple(str(entry) for entry in value)
        else:
            values[name] = value
    return cls(**values)
