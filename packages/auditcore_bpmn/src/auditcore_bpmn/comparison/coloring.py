"""Farben aus Kennzeichen ableiten und in DI-Formen schreiben."""

from __future__ import annotations

from collections.abc import Mapping

from ..model import BpmnDocument, as_document
from ..namespaces import BIOC_NS, BPMNDI_NS, COLOR_NS, q
from ..serialize import serialize
from ..vocabulary import COLOR_PRIORITY, MARKER_COLORS
from ..writer import copy_document

_SHAPES = (q(BPMNDI_NS, "BPMNShape"), q(BPMNDI_NS, "BPMNEdge"))


def colors_from_markers(source: str | bytes | BpmnDocument) -> dict[str, tuple[str, str]]:
    """Füllung und Rand je Element aus farbgebenden Kennzeichen (Vorrang: ``COLOR_PRIORITY``)."""
    result = {}
    for element in as_document(source):
        kinds = set(element.extensions.marker_types())
        kind = next((k for k in COLOR_PRIORITY if k in kinds), None)
        if kind is not None:
            result[element.id] = MARKER_COLORS[kind]
    return result


def apply_colors(source: str | bytes | BpmnDocument, colors: Mapping[str, tuple[str, str]]) -> str:
    """Setzt ``bioc:fill``/``bioc:stroke`` und ``color:background-color``/``color:border-color``."""
    document = copy_document(source)
    for shape in document.root.iter():
        if shape.tag not in _SHAPES:
            continue
        pair = colors.get(shape.get("bpmnElement") or "")
        if pair is None:
            continue
        fill, stroke = pair
        shape.set(q(BIOC_NS, "fill"), fill)
        shape.set(q(BIOC_NS, "stroke"), stroke)
        shape.set(q(COLOR_NS, "background-color"), fill)
        shape.set(q(COLOR_NS, "border-color"), stroke)
    for prefix, uri in (("bioc", BIOC_NS), ("color", COLOR_NS)):
        if all(u != uri for _p, u in document.parsed.namespaces):
            document.parsed.namespaces.append((prefix, uri))
    return serialize(document.parsed)
