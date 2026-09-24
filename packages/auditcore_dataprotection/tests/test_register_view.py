"""HTML view of the record of processing activities (render_register_html)."""

from __future__ import annotations

from support import ANNA, BERT, TENANT, complete_activity, register_content, world

from auditcore_dataprotection.export import register_report, render_register_html
from auditcore_dataprotection.rules import load_profile


def released_world():
    w = world()
    content = register_content(
        complete_activity(id="a1", name="Preisaufsicht <script>x</script>"),
        complete_activity(id="a2", name="Benutzerverwaltung", referat="Referat Z"),
    )
    draft = w.register.save_draft(TENANT, ANNA, content)
    released = w.register.release(TENANT, BERT, expected_revision=draft.revision)
    return w, released


def test_view_shows_version_cover_activities_and_references() -> None:
    w, version = released_world()
    profile = load_profile("auditcore.dsgvo", "2026.10.3")
    html = render_register_html(register_report(version, profile))
    for text in (
        "Verzeichnis von Verarbeitungstätigkeiten",
        "Fassung",
        "freigegeben",
        "Deckblatt",
        "Verantwortlicher",
        "Datenschutzbeauftragte/r",
        "Referat III – KPAnG-Vollzug",
        "Referat Z",
        "Zweck der Verarbeitung",
        "Art. 30 Abs. 1",
        "Benutzerverwaltung",
    ):
        assert text in html, text
    assert "<script>x" not in html and "&lt;script&gt;x" in html
    assert "Folgenabschätzung</th>" not in html


def test_view_with_overview_shows_the_dpia_state() -> None:
    w, version = released_world()
    profile = load_profile("auditcore.dsgvo", "2026.10.3")
    w.service.start(TENANT, ANNA, "a1", profile)
    rows = w.service.overview(TENANT, ANNA)
    report = register_report(version, profile, overview=rows)
    assert set(report["dsfa"]) == {"a1", "a2"}
    html = render_register_html(report)
    assert "Fassung 1, Entwurf" in html
    assert "keine Folgenabschätzung angelegt" in html


def test_report_without_overview_is_unchanged() -> None:
    w, version = released_world()
    profile = load_profile("regulierung.dsgvo", "2026.09.1")
    assert "dsfa" not in register_report(version, profile)
