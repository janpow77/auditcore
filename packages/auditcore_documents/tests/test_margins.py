"""Issue #238: Seitenränder nur im Randbereich entfernen, erstes Vorkommen behalten."""

from __future__ import annotations

from pathlib import Path

import pytest

import auditcore_documents as ad
from auditcore_documents.pdftext import DEFAULT_MARGINS, LEGACY_MARGINS, MarginRules

HEADER = "Preisblatt gültig ab 01.01.2026"
TABLE = [
    "Position Menge Preis",
    "Schraube M8",
    "250",
    "Mutter M8",
    "120",
    "Summe 370,00",
    "Ende der Tabelle",
]


def page(number: int, total: int, body: list[str]) -> str:
    return "\n".join([HEADER, "Lieferant Muster GmbH", *body, f"Seite {number} von {total}"])


def pages() -> list[str]:
    return [page(1, 3, TABLE), page(2, 3, TABLE), page(3, 3, TABLE)]


def test_pure_number_inside_table_is_kept() -> None:
    cleaned = ad.remove_repeating_margins(pages())
    for lines in cleaned:
        assert "250" in lines
        assert "120" in lines


def test_page_number_at_margin_is_removed() -> None:
    cleaned = ad.remove_repeating_margins(pages())
    assert all(not line.startswith("Seite ") for lines in cleaned for line in lines)
    bare = ["Kopf", "Text eins", "Text zwei", "Text drei", "Text vier", "Text fünf", "7"]
    assert ad.remove_repeating_margins(["\n".join(bare)])[0] == bare[:-1]


def test_validity_date_in_header_kept_on_first_occurrence() -> None:
    cleaned = ad.remove_repeating_margins(pages())
    assert cleaned[0][0] == HEADER
    assert HEADER not in cleaned[1]
    assert HEADER not in cleaned[2]
    # Wiederkehrende Fußzeilen ohne Seitenzahl fallen ab der zweiten Seite ebenso weg.
    assert "Lieferant Muster GmbH" in cleaned[0]
    assert "Lieferant Muster GmbH" not in cleaned[1]


def test_without_keep_first_every_occurrence_is_removed() -> None:
    rules = MarginRules(keep_first_occurrence=False)
    cleaned = ad.remove_repeating_margins(pages(), rules)
    assert all(HEADER not in lines for lines in cleaned)
    assert all("250" in lines for lines in cleaned)


def test_repeated_line_outside_margin_is_kept() -> None:
    body = ["a", "b", "c", HEADER, "d", "e", "f"]
    cleaned = ad.remove_repeating_margins(["\n".join(["Kopf", *body]) for _ in range(3)])
    assert all(HEADER in lines for lines in cleaned)


def test_edge_lines_are_configurable() -> None:
    narrow = MarginRules(edge_lines=1)
    cleaned = ad.remove_repeating_margins(pages(), narrow)
    # Nur die erste und letzte Zeile gelten als Rand: die zweite Kopfzeile bleibt.
    assert all("Lieferant Muster GmbH" in lines for lines in cleaned)
    assert all(not line.startswith("Seite ") for lines in cleaned for line in lines)
    untouched = ad.remove_repeating_margins(pages(), MarginRules(edge_lines=0))
    assert untouched == [text.splitlines() for text in pages()]


def test_legacy_rules_reproduce_original_content_loss() -> None:
    cleaned = ad.remove_repeating_margins(pages(), LEGACY_MARGINS)
    assert all("250" not in lines and HEADER not in lines for lines in cleaned)


@pytest.mark.parametrize(
    ("value", "error"), [(-1, ValueError), (True, TypeError), (1.5, TypeError)]
)
def test_margin_rules_reject_invalid_edge_lines(value: object, error: type[Exception]) -> None:
    with pytest.raises(error):
        MarginRules(edge_lines=value)  # type: ignore[arg-type]


def test_profiles_select_margin_rules() -> None:
    assert ad.LEGACY.margin_rules is LEGACY_MARGINS
    assert ad.LEGACY_DIFFLIB.margin_rules is LEGACY_MARGINS
    assert ad.CORRECTED.margin_rules is DEFAULT_MARGINS
    assert ad.CORRECTED.result_version == "1.1.0+auditcore.2026.10.1"


def test_paragraphs_keep_table_numbers_and_header() -> None:
    texts = [text for text, _heading in ad.paragraphs_from_pdf_pages(pages())]
    joined = " ".join(texts)
    assert joined.count("250") == 3
    assert joined.count("gültig ab 01.01.2026") == 1
    assert "Seite 1 von 3" not in joined


def _synthetic_pdf(path: Path, price: str = "250") -> Path:
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    pdf = canvas.Canvas(str(path))
    table = [price if line == "250" else line for line in TABLE]
    for number in (1, 2, 3):
        lines = [HEADER, "Lieferant Muster GmbH", *table, f"Seite {number} von 3"]
        for row, line in enumerate(lines):
            pdf.drawString(72, 780 - row * 20, line)
        pdf.showPage()
    pdf.save()
    return path


def test_synthetic_pdf_through_reading(tmp_path: Path) -> None:
    pytest.importorskip("pypdf")
    path = _synthetic_pdf(tmp_path / "preisblatt.pdf")
    texts = [t for t, _h in ad.read_text_paragraphs(path, page_source=ad.pypdf_pages)]
    joined = " ".join(texts)
    assert joined.count("250") == 3
    assert joined.count("gültig ab 01.01.2026") == 1
    assert "von 3" not in joined
    legacy = " ".join(
        t
        for t, _h in ad.read_text_paragraphs(
            path, page_source=ad.pypdf_pages, margins=LEGACY_MARGINS
        )
    )
    assert "250" not in legacy and "gültig ab" not in legacy


def test_compare_profiles_apply_their_margin_rules(tmp_path: Path) -> None:
    pytest.importorskip("pypdf")
    pytest.importorskip("rapidfuzz")
    old = _synthetic_pdf(tmp_path / "alt.pdf")
    new = _synthetic_pdf(tmp_path / "neu.pdf", price="260")
    context = ad.ReadContext(page_source=ad.pypdf_pages)
    corrected = ad.compare_files(old, new, profile=ad.CORRECTED, context=context)
    legacy = ad.compare_files(old, new, profile=ad.LEGACY, context=context)
    # Der geänderte Preis mitten in der Tabelle ist nur mit den neuen Randregeln sichtbar.
    assert corrected.changed_count >= 1
    assert legacy.changed_count == 0
