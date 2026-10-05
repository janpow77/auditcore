"""Optionale Inhalte (Ebenen, OCG): ausgeblendete Ebenen für Suche und Prüfung einblenden.

MuPDF extrahiert nur sichtbare Ebenen. Text auf ausgeblendeten Ebenen bliebe daher
bei Schwärzung und Nachprüfung unsichtbar und könnte im Ausgabedokument stehen
bleiben. Die Funktionen hier blenden alle Ebenen ein und stellen die ursprüngliche
Standardkonfiguration danach wieder her.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from auditcore_pdf.engine import open_pdf

if TYPE_CHECKING:
    from pymupdf import Document


@dataclass(frozen=True)
class LayerState:
    """Gespeicherte Standardkonfiguration der optionalen Inhalte."""

    basestate: str = "ON"
    on: list[int] = field(default_factory=list)
    off: list[int] = field(default_factory=list)
    rbgroups: list[list[int]] = field(default_factory=list)


def layer_xrefs(doc: Document) -> list[int]:
    """Objektnummern aller Ebenen (OCG) des Dokuments."""
    return sorted(int(xref) for xref in (doc.get_ocgs() or {}))


def open_with_all_layers(pdf_bytes: bytes) -> tuple[Document, LayerState | None]:
    """Öffnet das PDF mit allen Ebenen eingeblendet.

    Die Sichtbarkeit wird in der Standardkonfiguration gesetzt und das Dokument neu
    geladen, weil MuPDF geänderte Sichtbarkeit erst beim Laden auswertet. Ohne
    Ebenen wird das Dokument unverändert geöffnet und ``None`` zurückgegeben.
    """
    doc = open_pdf(pdf_bytes)
    xrefs = layer_xrefs(doc)
    if not xrefs:
        return doc, None
    config = doc.get_layer(-1) or {}
    state = LayerState(
        basestate=str(config.get("basestate", "ON")),
        on=[int(x) for x in config.get("on", [])],
        off=[int(x) for x in config.get("off", [])],
        rbgroups=[[int(x) for x in group] for group in config.get("rbgroups", [])],
    )
    # Optionsgruppen (RBGroups) würden sonst nur eine Ebene je Gruppe zulassen.
    doc.set_layer(-1, basestate="ON", on=xrefs, off=[], rbgroups=[])
    revealed = bytes(doc.tobytes())
    doc.close()
    return open_pdf(revealed), state


def restore_layers(doc: Document, state: LayerState) -> None:
    """Stellt die gespeicherte Sichtbarkeit der Ebenen wieder her."""
    doc.set_layer(
        -1, basestate=state.basestate, on=state.on, off=state.off, rbgroups=state.rbgroups
    )
