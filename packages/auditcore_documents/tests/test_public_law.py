"""Amtliche Rechtstexte: unabhängig aus den Quellen hergeleitete Erwartungen.

Diese Tests prüfen nicht gegen die Aufzeichnung, sondern gegen den Wortlaut
der Originalquellen (gesetze-im-internet.de, BGBl.), damit fachliche
Ergebnisse auch ohne Legacy-Vergleich belegt sind.
"""

from __future__ import annotations

import re
from pathlib import Path

from conftest import fixture_path, recorded_page_source

import auditcore_documents as ad

SOURCES = fixture_path("public/sources")


def _old_paragraph_11_1() -> str:
    html = (SOURCES / "kassensichv_gii_2025-06-01.html").read_bytes().decode("iso-8859-1")
    import html as html_module

    text = html_module.unescape(re.sub(r"<[^>]+>", "\n", html))
    start = text.index("(1) Für die Zertifizierung technischer Sicherheitseinrichtungen")
    return re.sub(r"\s+", " ", text[start : text.index("\n", start)]).strip()


def test_article_15_of_bgbl_2025_i_301_is_applied_exactly() -> None:
    """Art. 15: „In § 11 Absatz 1 Satz 1 wird die Angabe „§ 9 des BSI-Gesetzes“
    durch die Angabe „§ 52 des BSI-Gesetzes“ ersetzt.“"""
    result = ad.compare_files(
        fixture_path("public/KassenSichV_2025-06-01.docx"),
        fixture_path("public/BGBl-2025-I-301-Art15.docx"),
        profile=ad.LEGACY,
        options=ad.CompareOptions(comparison_type="article_law"),
    )
    old = _old_paragraph_11_1()
    assert old.count("§ 9 des BSI-Gesetzes") == 1
    assert result.metadata["recognised_commands"] == 1
    assert result.metadata["open_commands"] == []
    [row] = result.rows
    assert (row.status, row.location) == ("changed", "§ 11 Absatz 1")
    assert row.old_text == old
    assert row.new_text == old.replace("§ 9 des BSI-Gesetzes", "§ 52 des BSI-Gesetzes")
    consolidated = {
        (item["section"], item["paragraph"]): item["text"]
        for item in result.metadata["consolidated_text"]
    }
    assert consolidated[("§ 11", 1)] == row.new_text
    assert len(consolidated) == 24


def test_other_articles_on_the_official_page_do_not_touch_the_ordinance() -> None:
    """Befehle für andere Gesetze auf derselben BGBl.-Seite bleiben offen."""
    result = ad.compare_files(
        fixture_path("public/KassenSichV_2025-06-01.docx"),
        fixture_path("public/bgbl-2025-I-301-seite55.pdf"),
        profile=ad.LEGACY,
        options=ad.CompareOptions(comparison_type="article_law"),
        context=ad.ReadContext(page_source=recorded_page_source),
    )
    assert [row.location for row in result.rows] == ["§ 11 Absatz 1"]
    reasons = result.metadata["open_commands"]
    assert any(
        r.startswith("In § 3 Absatz 2") and r.endswith("[zu ersetzender Wortlaut nicht gefunden]")
        for r in reasons
    )
    assert any(
        r.startswith("In § 44b Satz 2") and r.endswith("[Befehlsart nicht unterstützt]")
        for r in reasons
    )


def test_two_official_pdf_versions_of_the_ordinance() -> None:
    """Fassung 2021 gegen Fassung 2026: § 11 Absatz 3 ist neu (Stand 14.1.2026)."""
    result = ad.compare_files(
        fixture_path("public/KassenSichV_2023-06-10.pdf"),
        fixture_path("public/KassenSichV_2026-08-27.pdf"),
        profile=ad.LEGACY,
        context=ad.ReadContext(page_source=recorded_page_source),
    )
    assert result.mode == "text"
    assert result.metadata["pdf_notice"].startswith("PDF-Dateien werden stets als Fließtext")
    added = " ".join(row.new_text for row in result.rows if row.status == "added")
    assert "Zertifizierungsverfahren aufgrund von in Satz 2 genannten Schutzprofilen" in added
    assert "26. Februar 2027" in added
    assert result.changed_count + result.removed_count + result.added_count > 0


def test_docx_versions_show_the_2026_amendments() -> None:
    result = ad.compare_files(
        fixture_path("public/KassenSichV_2025-06-01.docx"),
        fixture_path("public/KassenSichV_2026-05-06.docx"),
        profile=ad.LEGACY,
    )
    by_location = {row.location: row for row in result.rows}
    assert "§ 11 Zertifizierung, Absatz 3" in by_location
    assert by_location["§ 11 Zertifizierung, Absatz 3"].status == "added"
    # § 8 Absatz 4 wurde 2026 neu gefasst („§ 7 Absatz 4 gilt sinngemäß.“).
    changed = [r for r in result.rows if r.new_text == "(4) § 7 Absatz 4 gilt sinngemäß."]
    assert changed and changed[0].status in {"changed", "added"}


def test_identical_versions_have_no_differences() -> None:
    path = fixture_path("public/KassenSichV_2025-06-01.docx")
    result = ad.compare_files(path, path, profile=ad.LEGACY)
    assert (result.changed_count, result.removed_count, result.added_count) == (0, 0, 0)
    assert result.old_sha256 == result.new_sha256
    assert all(row.status == "unchanged" and not row.selected for row in result.rows)


def test_sources_are_the_documented_originals() -> None:
    import hashlib
    import json

    provenance = json.loads(
        (Path(__file__).parents[1] / "provenance.json").read_text(encoding="utf-8")
    )
    for name, digest in provenance["rights"]["test_data"]["sha256"].items():
        path = fixture_path("public") / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
