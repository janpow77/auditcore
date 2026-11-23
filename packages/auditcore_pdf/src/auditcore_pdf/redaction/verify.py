"""Fail-closed-Nachprüfung der geschwärzten Ausgabe."""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING

from auditcore_pdf.engine import fitz
from auditcore_pdf.redaction.common import _HARD, RedactionVerificationError, _clean, _flat
from auditcore_pdf.redaction.groups import _occurrences, _text_groups
from auditcore_pdf.redaction.hidden import _cleanup_info, _iter_hidden_strings
from auditcore_pdf.redaction.page_text import _PageText
from auditcore_pdf.redaction.raw_scan import _raw_contains
from auditcore_pdf.redaction.selection import Selection

if TYPE_CHECKING:
    from pymupdf import Document


def _visible_text(doc: Document, pts: list[_PageText]) -> str:
    """Lesbarer Text der Ausgabe (Seiten und versteckte Ablagen), ohne
    Groß-/Kleinschreibung, mit Wortgrenzen."""
    parts = [pt.text.replace(_HARD, "\n") for pt in pts]
    parts += [_clean(text) for _l, text, _p, _r in _iter_hidden_strings(doc)]
    return unicodedata.normalize("NFKC", "\x01".join(parts)).casefold()


def _word_in(visible: str, text: str) -> bool:
    flat = _flat(text)
    if not flat:
        return False
    body = r"\s*".join(re.escape(ch) for ch in flat)
    return re.search(r"(?<!\w)" + body + r"(?!\w)", visible) is not None


def _count_problems(
    after: dict[str, str],
    limits: dict[tuple[str, str], int],
    originals: dict[tuple[str, str], set[str]],
) -> list[str]:
    problems: list[str] = []
    for (group, key), limit in limits.items():
        found = _occurrences(after.get(group, ""), key)
        if found > limit:
            sample = min(originals[(group, key)])
            problems.append(f"„{sample[:3]}…“ noch {found - limit}× lesbar ({group})")
    return problems


def _raw_problems(
    doc: Document,
    pts: list[_PageText],
    limits: dict[tuple[str, str], int],
    originals: dict[tuple[str, str], set[str]],
) -> list[str]:
    needles = sorted(
        {
            text
            for (group, key), limit in limits.items()
            if limit == 0 and len(key) >= 4
            for text in originals[(group, key)]
        }
    )
    if not needles:
        return []
    visible = _visible_text(doc, pts)
    flat_visible = "\x01".join(_flat(part) for part in visible.split("\x01"))
    strict, in_content = _raw_contains(doc, needles)
    problems: list[str] = []
    for hit in sorted(strict | in_content):
        # Bleibt derselbe Text an anderer Stelle bewusst lesbar
        # (abgewählt), steht er zu Recht noch in der Datei. Außerhalb
        # der Inhaltsströme wird wortgenau verglichen: „Krausestr.“
        # entschuldigt einen Alternativtext „Krause“ nicht. Im
        # Inhaltsstrom genügt der Text als Teil des Sichtbaren, denn
        # dort sind Wörter oft in Stücke zerlegt.
        ok = _word_in(visible, hit) if hit in strict else _flat(hit) in flat_visible
        if not ok:
            problems.append(f"„{hit[:3]}…“ noch in den Rohdaten der Datei")
    return problems


def _verify(
    out: bytes,
    selection: Selection,
    limits: dict[tuple[str, str], int],
    originals: dict[tuple[str, str], set[str]],
) -> None:
    """Fail-closed: Je Gruppe darf jeder ausgewählte Text höchstens so oft
    vorkommen wie in ``limits``. Was vollständig geschwärzt sein soll, darf
    auch in den Rohdaten nicht mehr stehen."""
    doc = fitz.open(stream=out, filetype="pdf")
    try:
        after, pts = _text_groups(doc)
        problems = _count_problems(after, limits, originals)
        problems += _raw_problems(doc, pts, limits, originals)
        if selection.sanitize:
            info = _cleanup_info(doc)
            if info["metadata_fields"] or info["xmp"] or info["attachments"]:
                problems.append("Metadaten oder Anhänge nicht entfernt")
    finally:
        doc.close()
    if problems:
        raise RedactionVerificationError(list(dict.fromkeys(problems)))
