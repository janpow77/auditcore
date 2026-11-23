"""Hilfsfunktionen für die Schwärzungstests (nur synthetische Daten).

Die Szenarien stammen aus den Prüfplan-Tests der Anwendung; statt der
HTTP-Schnittstelle rufen die Tests hier die Bibliothek direkt auf.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

import pymupdf as fitz
import pytest

from auditcore_pdf import redaction as R

SECRET = "erika@example.org"
DEJAVU = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

Spans = list[tuple[int, int]]
NerResult = list[Spans]


def dejavu() -> str:
    """Pfad einer einbettbaren TrueType-Schrift mit Unicode-Abdeckung.

    Bevorzugt DejaVu Sans; fehlt sie (CI-Abbild ohne Schriften), dient die in
    PyMuPDF eingebaute Ersatzschrift „cjk“ (Droid Sans Fallback, mit
    lateinischen Zeichen). So laufen die Tests überall und die Abdeckung
    hängt nicht von installierten Schriften ab."""
    if DEJAVU.exists():
        return str(DEJAVU)
    target = Path(tempfile.gettempdir()) / f"auditcore-pdf-test-font-{os.getpid()}.ttf"
    if not target.exists():
        target.write_bytes(fitz.Font("cjk").buffer)
    return str(target)


def page_text(pdf: bytes) -> str:
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        return "\n".join(p.get_text() for p in doc)


def criteria(
    patterns: Iterable[str] = (),
    terms: Iterable[str] = (),
    case_sensitive: bool = False,
    whole_word: bool = True,
) -> R.Criteria:
    return R.Criteria.from_input(list(patterns), list(terms), case_sensitive, whole_word)


def findings(
    pdf: bytes,
    patterns: Iterable[str] = (),
    terms: Iterable[str] = (),
    ner: R.NerFn | None = None,
    **kw: bool,
) -> list[R.Candidate]:
    """Fundstellen im Seitentext."""
    return R.build_plan(pdf, criteria(patterns, terms, **kw), ner).text_candidates


def redacted(
    pdf: bytes,
    patterns: Iterable[str] = (),
    terms: Iterable[str] = (),
    ner: R.NerFn | None = None,
    **kw: bool,
) -> bytes:
    """Alles schwärzen (ohne Vorschau); es muss Fundstellen geben."""
    out, _report, plan = R.redact_all(pdf, criteria(patterns, terms, **kw), ner)
    assert plan.candidates
    return out


def plan_of(
    pdf: bytes,
    patterns: Iterable[str] = (),
    terms: Iterable[str] = (),
    ner: R.NerFn | None = None,
    **kw: bool,
) -> dict:
    """Plan als JSON-Objekt, wie ihn die Oberfläche erhält."""
    plan = R.build_plan(pdf, criteria(patterns, terms, **kw), ner)
    return json.loads(json.dumps(plan.to_dict()))


def selection_payload(
    plan: dict,
    selected: Iterable[str] | None = None,
    areas: Sequence[dict] = (),
    sanitize: bool = True,
) -> dict:
    ids = [c["id"] for c in plan["candidates"]] if selected is None else list(selected)
    return {
        "sha256": plan["sha256"],
        "criteria": plan["criteria"],
        "selected": ids,
        "areas": list(areas),
        "sanitize": sanitize,
    }


def apply_with(
    pdf: bytes,
    plan: dict,
    selected: Iterable[str] | None = None,
    areas: Sequence[dict] = (),
    sanitize: bool = True,
    ner: R.NerFn | None = None,
) -> tuple[bytes, R.ApplyReport]:
    """Auswahl über JSON zurücklesen und anwenden, wie es die Anwendung tut."""
    payload = json.loads(json.dumps(selection_payload(plan, selected, areas, sanitize)))
    return R.apply_plan(pdf, R.Selection.from_dict(payload), ner)


def engine_plan(pdf: bytes, terms: Iterable[str] = (), patterns: Iterable[str] = ()) -> R.Plan:
    return R.build_plan(pdf, criteria(patterns, terms))


def engine_apply(
    pdf: bytes,
    plan: R.Plan,
    selected: Iterable[str] | None = None,
    areas: Sequence[R.Area] = (),
    sanitize: bool = True,
    ner: R.NerFn | None = None,
) -> tuple[bytes, R.ApplyReport]:
    ids = frozenset(c.id for c in plan.candidates) if selected is None else frozenset(selected)
    selection = R.Selection(plan.sha256, plan.criteria, ids, tuple(areas), sanitize)
    return R.apply_plan(pdf, selection, ner)


def make_pdf(build: Callable[[fitz.Document, fitz.Page], None]) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    build(doc, page)
    data = doc.tobytes()
    doc.close()
    return data


def raw(pdf: bytes) -> bytes:
    """Alle Objekte und entpackten Streams der Datei."""
    parts = []
    with fitz.open(stream=pdf, filetype="pdf") as d:
        for x in range(1, d.xref_length()):
            parts.append(d.xref_object(x).encode("latin-1", "replace"))
            if d.xref_is_stream(x):
                parts.append(d.xref_stream(x) or b"")
    return b"\n".join(parts)


def raw_streams(pdf: bytes) -> bytes:
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        return b"".join(
            doc.xref_stream(x) or b"" for x in range(1, doc.xref_length()) if doc.xref_is_stream(x)
        )


def raw_pages(contents: list[bytes], extra: Callable[[fitz.Document], None] | None = None) -> bytes:
    """Seiten aus rohen Inhaltsströmen mit Helvetica (WinAnsi) als /F1."""
    doc = fitz.open()
    for content in contents:
        page = doc.new_page()
        c = doc.get_new_xref()
        doc.update_object(c, "<<>>")
        doc.update_stream(c, content, new=True)
        doc.xref_set_key(page.xref, "Contents", f"{c} 0 R")
        doc.xref_set_key(
            page.xref,
            "Resources",
            "<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
            "/Encoding /WinAnsiEncoding >> >> >>",
        )
    if extra:
        extra(doc)
    data = doc.tobytes()
    doc.close()
    return data


def page_properties_key(doc: fitz.Document, page: fitz.Page) -> tuple[int, str]:
    """Wo die /Properties einer Seite liegen: (xref, Schlüsselpräfix)."""
    kind, val = doc.xref_get_key(page.xref, "Resources")
    if kind == "xref":
        return int(val.split()[0]), ""
    return page.xref, "Resources/"


def skip_redaction_below(monkeypatch: pytest.MonkeyPatch, y: float) -> None:
    """Simulierter Ausfall: Schwärzungen unterhalb von ``y`` greifen nicht."""
    orig = fitz.Page.add_redact_annot

    def patched(self, quad, *a, **k):
        if fitz.Rect(quad).y0 > y:
            return None
        return orig(self, quad, *a, **k)

    monkeypatch.setattr(fitz.Page, "add_redact_annot", patched)


# ── KI-Attrappen ────────────────────────────────────────────────


def fake_ner(*persons: str) -> R.NerFn:
    """Meldet die genannten Texte überall als Person."""

    def run(texts: list[str]) -> NerResult:
        return [
            sorted({m.span() for p in persons for m in re.finditer(re.escape(p), t)}) for t in texts
        ]

    return run


def cell_ner(*persons: str) -> R.NerFn:
    """Meldet die Texte nur, wenn sie allein stehen (eine Zelle)."""

    def run(texts: list[str]) -> NerResult:
        return [[(0, len(t))] if t in persons else [] for t in texts]

    return run


def no_frame(ner_fn: R.NerFn) -> R.NerFn:
    """KI-Attrappe ohne Bestätigung im Mustersatz."""

    def run(texts: list[str]) -> NerResult:
        return [
            [] if t.startswith("Gestern habe ich") else list(r)
            for t, r in zip(texts, ner_fn(texts), strict=True)
        ]

    return run


def lines_pdf(*pages: list[str]) -> bytes:
    doc = fitz.open()
    for lines in pages:
        page = doc.new_page()
        for y, line in enumerate(lines):
            page.insert_text((72, 72 + 16 * y), line, fontsize=9)
    return doc.tobytes()


def plan_texts(pdf: bytes, ner_fn: R.NerFn) -> list[tuple[int, str, str]]:
    plan = R.build_plan(pdf, R.Criteria(("ki_namen",), (), False, True), ner_fn)
    return sorted((c.page or 0, c.source, c.text) for c in plan.candidates)


def count(found: list[tuple[int, str, str]], source: str, text: str) -> int:
    return sum(1 for _p, s, t in found if s == source and t == text)


def propagated(found: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    return [t for t in found if t[1] == R.NER_PROPAGATED_ID]
