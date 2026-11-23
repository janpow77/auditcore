"""Seitengeometrie und ausgeblendete Inhalte: CropBox, Drehung, optionale Ebenen."""

from __future__ import annotations

import contextlib
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeAlias

from auditcore_pdf.engine import fitz
from auditcore_pdf.redaction.common import Box

if TYPE_CHECKING:
    from pymupdf import Document, Page, Rect

#: (Objektnummer, Schlüssel, alte Art, alter Wert) für ``_restore_layers``
SavedKey: TypeAlias = tuple[int, str, str, str]

_RESOURCE_RULE = re.compile(r"/([^\s/<>\[\]()]+)\s*<<")


class _ViewTransform:
    """Umrechnung PDF-Koordinaten (bei CropBox = MediaBox) → Anzeige 0…1."""

    def __init__(self, page: Page):
        # Lage der CropBox in der aufgedeckten Seite. ``page.cropbox_position``
        # taugt nicht: Bei versetzter MediaBox ist dort x absolut, y relativ.
        crop, full = page.cropbox, _full_box(page)
        self.origin = fitz.Point(crop.x0 - full.x0, crop.y0 - full.y0)
        self.matrix = page.rotation_matrix
        self.view = fitz.Rect(page.rect)
        self.crop = fitz.Rect(0, 0, page.cropbox.width, page.cropbox.height)

    def _shift(self) -> tuple[float, float, float, float]:
        return (self.origin.x, self.origin.y, self.origin.x, self.origin.y)

    def to_view(self, rect: Rect | Sequence[float]) -> tuple[Box, bool]:
        local = fitz.Rect(rect) - self._shift()
        outside = not local.intersects(self.crop)
        r = local * self.matrix
        w, h = max(1.0, self.view.width), max(1.0, self.view.height)
        box = [round(r.x0 / w, 5), round(r.y0 / h, 5), round(r.x1 / w, 5), round(r.y1 / h, 5)]
        return box, outside

    def from_view(self, box: Sequence[float]) -> Rect:
        w, h = self.view.width, self.view.height
        r = fitz.Rect(box[0] * w, box[1] * h, box[2] * w, box[3] * h) * ~self.matrix
        r.normalize()
        return r + self._shift()


def _full_box(page: Page) -> Rect:
    """Die MediaBox im Koordinatensystem von ``page.cropbox``.

    PyMuPDF führt die CropBox relativ zur Oberkante der MediaBox. Bei einer
    versetzten MediaBox (etwa ``[100 100 700 900]``) sind ``page.mediabox``
    und ``page.cropbox`` deshalb nicht direkt vergleichbar.
    """
    m = page.mediabox
    return fitz.Rect(m.x0, 0, m.x1, m.height)


def _expose_full_page(page: Page) -> Rect | None:
    """CropBox vorübergehend auf die MediaBox setzen — sonst bleibt Text
    außerhalb des sichtbaren Bereichs für Suche und Schwärzung unsichtbar.
    Gibt die alte CropBox zurück, wenn sie geändert wurde."""
    full = _full_box(page)
    original = fitz.Rect(page.cropbox)
    if all(abs(a - b) < 0.01 for a, b in zip(original, full, strict=True)):
        return None
    page.set_cropbox(full)
    return original


class _LayerOpener:
    """Blendet optionale Inhalte ein und merkt sich jeden geänderten Schlüssel."""

    def __init__(self, doc: Document):
        self.doc = doc
        self.saved: list[SavedKey] = []

    def put(self, xref: int, key: str, value: str) -> None:
        kind, old = self.doc.xref_get_key(xref, key)
        self.saved.append((xref, key, kind, old))
        self.doc.xref_set_key(xref, key, value)

    def is_set(self, xref: int, key: str) -> bool:
        return bool(self.doc.xref_get_key(xref, key)[0] != "null")

    def open_rule(self, xref: int, prefix: str) -> None:
        kind = self.doc.xref_get_key(xref, prefix + "Type")[1]
        if kind == "/OCG" and self.is_set(xref, prefix + "Usage"):
            # /Usage/View/ViewState /OFF blendet die Ebene bei MuPDF aus.
            self.put(xref, prefix + "Usage", "null")
        elif kind == "/OCMD":
            if self.is_set(xref, prefix + "VE"):
                self.put(xref, prefix + "VE", "null")
            if self.doc.xref_get_key(xref, prefix + "P")[1] not in ("", "/AnyOn"):
                self.put(xref, prefix + "P", "/AnyOn")

    def open_resource_rules(self, xref: int) -> None:
        # Regeln direkt in den Ressourcen: /Properties << /MD1 << /Type /OCMD … >> >>
        for base in ("Properties", "Resources/Properties"):
            kind, value = self.doc.xref_get_key(xref, base)
            if kind != "dict" or "/OCMD" not in value and "/OCG" not in value:
                continue
            for name in set(_RESOURCE_RULE.findall(value)):
                self.open_rule(xref, f"{base}/{name}/")

    def run(self) -> None:
        cat = self.doc.pdf_catalog()
        if not self.is_set(cat, "OCProperties"):
            return
        self.put(cat, "OCProperties/D/OFF", "[]")
        self.put(cat, "OCProperties/D/BaseState", "/ON")
        for xref in range(1, self.doc.xref_length()):
            self.open_rule(xref, "")
            self.open_resource_rules(xref)


def _reveal_layers(doc: Document) -> list[SavedKey]:
    """Ausgeblendete optionale Inhalte (Ebenen) einblenden, damit ihr Text
    gefunden und geschwärzt wird. Rückgabe: alte Werte für ``_restore_layers``.

    Neben ``/D/OFF`` und ``BaseState`` zählen Sichtbarkeitsregeln (OCMD):
    ``/P /AllOff`` oder ein Ausdruck ``/VE`` können Inhalte gerade dann
    ausblenden, wenn alle Ebenen an sind. Sie werden auf „sichtbar, wenn eine
    Ebene an ist“ gestellt. Scheitert ein Schritt, bleibt das bis dahin
    Geänderte in der Rückgabe, damit es wiederhergestellt wird."""
    opener = _LayerOpener(doc)
    with contextlib.suppress(Exception):
        opener.run()
    return opener.saved


def _restore_layers(doc: Document, saved: list[SavedKey]) -> None:
    for xref, key, kind, old in reversed(saved):
        if kind == "null":
            value = "null"
        elif kind == "string":
            value = fitz.get_pdf_str(old)
        else:
            value = old
        doc.xref_set_key(xref, key, value)
    _drop_null_keys(doc, saved)


def _drop_null_keys(doc: Document, saved: list[SavedKey]) -> None:
    # xref_set_key(…, "null") schreibt „/Key null“. Das ist gleichwertig mit
    # einem fehlenden Schlüssel, verändert aber die Datei; deshalb entfernen.
    for xref in {x for x, _k, kind, _o in saved if kind == "null"}:
        try:
            src = doc.xref_object(xref, compressed=True)
            names = {
                k.rsplit("/", 1)[-1] for x, k, kind, _o in saved if x == xref and kind == "null"
            }
            alternatives = "|".join(map(re.escape, names))
            cleaned = re.sub(r"/(?:" + alternatives + r")\s*null(?=[\s/>\]])", "", src)
            if cleaned != src:
                doc.update_object(xref, cleaned)
        except Exception:
            continue
