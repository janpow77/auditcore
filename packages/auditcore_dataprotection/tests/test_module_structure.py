"""Module structure after the 0.4.1 refactoring: facades, aliases and shared helpers.

The behavior is covered by the characterization and contract tests; these
tests pin the new seams so that the facades keep exporting the same objects.
"""

from __future__ import annotations

import warnings
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from auditcore_dataprotection import calculation, export, legacy, register, rules
from auditcore_dataprotection.assessment_checks import release_checks
from auditcore_dataprotection.assessment_core import refuse_second_open_version
from auditcore_dataprotection.errors import ConflictError
from auditcore_dataprotection.hashing import canonical_sha256
from auditcore_dataprotection.html_common import text
from auditcore_dataprotection.legacy_report import format_datetime_de
from auditcore_dataprotection.model import Assessment, AssessmentStatus
from auditcore_dataprotection.workbook_tables import cell_value, overview_tables, yes_no

NOW = datetime(2026, 9, 25, 9, 30, tzinfo=UTC)


def _assessment(**changes: object) -> Assessment:
    profile = rules.load_profile("regulierung.dsgvo", "2026.09.1")
    base = Assessment(
        tenant_id="t",
        assessment_id="a",
        register_id="r",
        activity_id="x",
        activity_name="X",
        version=1,
        status=AssessmentStatus.DRAFT,
        profile_id=profile.id,
        profile_version=profile.version,
        profile_fingerprint=profile.fingerprint,
        register_version=1,
        activity_snapshot={},
        answers={},
        scenarios=(),
        proposal={},
        created_by="u",
        created_at=NOW,
        updated_at=NOW,
        editors=("u",),
    )
    return replace(base, **changes)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("facade", "names"),
    [
        (calculation, ["Answer", "Scenario", "Proposal", "screen", "assess_risk", "propose"]),
        (rules, ["RuleProfile", "load_profile", "profile_from_dict", "fingerprint"]),
        (register, ["RegisterService", "normalize_content", "check_activity", "content_hash"]),
        (export, ["assessment_report", "render_assessment_html", "render_register_html"]),
        (legacy, ["legacy_proposal", "legacy_report_html", "legacy_catalog_json"]),
    ],
)
def test_facades_export_every_name_they_list(facade: object, names: list[str]) -> None:
    exported = facade.__all__  # type: ignore[attr-defined]
    assert set(names) <= set(exported)
    assert all(getattr(facade, name) is not None for name in exported)


def test_german_legacy_constants_are_deprecated_aliases() -> None:
    with pytest.warns(DeprecationWarning, match="LEGACY_SCREENING_REQUIRED"):
        assert legacy.PFLICHT == legacy.LEGACY_SCREENING_REQUIRED == "pflicht"
    with pytest.warns(DeprecationWarning, match="LEGACY_SCREENING_NOT_REQUIRED"):
        assert legacy.KEINE_PFLICHT == legacy.LEGACY_SCREENING_NOT_REQUIRED == "keine_pflicht"
    with pytest.raises(AttributeError):
        legacy.NICHT_VORHANDEN  # noqa: B018
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert legacy.LEGACY_SCREENING_REQUIRED == calculation.SCREENING_REQUIRED


def test_profile_fingerprint_and_content_hash_share_the_canonical_digest() -> None:
    data = {"b": [1, "ä"], "a": {"z": None}}
    assert rules.fingerprint(data) == register.content_hash(data) == canonical_sha256(data)
    assert canonical_sha256({"a": 1, "b": 2}) == canonical_sha256({"b": 2, "a": 1})


def test_release_checks_keep_their_order_and_consultation_switch() -> None:
    profile = rules.load_profile("regulierung.dsgvo", "2026.09.1")
    blank = _assessment(proposal={"consultation_required": True})
    with_record = release_checks(blank, profile, require_consultation_record=True)
    without_record = release_checks(blank, profile, require_consultation_record=False)
    assert with_record[0] == "Vor der Freigabe ist über den Vorschlag zu entscheiden."
    assert with_record[1].startswith("Vor der Freigabe ist die oder der Datenschutzbeauftragte")
    assert with_record[2].startswith("Die Schwellwertanalyse ist unvollständig")
    assert with_record[3].startswith("Bei verbleibendem hohem Risiko")
    assert without_record == with_record[:3]


def test_a_second_open_version_is_refused() -> None:
    refuse_second_open_version([_assessment(status=AssessmentStatus.RELEASED)])
    with pytest.raises(ConflictError, match="Fassung 1 in Bearbeitung"):
        refuse_second_open_version([_assessment()])


def test_display_helpers() -> None:
    assert format_datetime_de(NOW) == "25.09.2026 09:30"
    assert format_datetime_de("2026-09-25") == "–"
    assert text(None) == "–" and text("", "") == "" and text(True) == "Ja"
    assert text(False) == "Nein" and text(["a", "<b>"]) == "a, &lt;b&gt;" and text([]) == "–"
    assert yes_no(True) == "Ja" and yes_no(False) == "Nein" and yes_no(None) == ""


def test_workbook_cells_are_plain_values() -> None:
    assert cell_value(NOW) == NOW.isoformat()
    naive = datetime(2026, 9, 25, 9, 30)
    assert cell_value(naive) is naive
    assert cell_value(date(2026, 9, 25)) == date(2026, 9, 25)
    assert cell_value(True) == "Ja" and cell_value(None) is None
    assert cell_value(("a", 1)) == "a, 1" and cell_value({"k": 1}) == "{'k': 1}"


def test_overview_tables_are_bounded() -> None:
    rows = [{"id": "x", "dsfa": None}]
    sheets = overview_tables(rows, "Mandant", NOW)
    assert [name for name, _, _ in sheets] == ["Folgenabschätzungen", "Stand"]
    assert sheets[0][2][0][6] == "noch nicht begonnen"
    with pytest.raises(ValueError, match="Zu viele Zeilen"):
        overview_tables([{}] * 100_001, "Mandant", NOW)
