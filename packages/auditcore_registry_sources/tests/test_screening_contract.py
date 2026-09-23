"""Library screening contract and its deliberate corrections (REG-C01..REG-C05)."""

from __future__ import annotations

import pytest
from replay_support import FILES

from auditcore_registry_sources import (
    ListSnapshot,
    QueryError,
    load_lists,
    load_profile,
    parse_targets_simple_csv,
    screen,
)
from auditcore_registry_sources.lists import find_list

V = "2026.09.1"
DESIGNER = load_profile("audit_designer.sanctions_screening", V)
WORKSHOP = load_profile("flowworkshop.sanctions_screening", V)
LISTS = load_lists("audit_designer.sanctions_lists", V)


def snapshots() -> list[ListSnapshot]:
    eu = parse_targets_simple_csv(
        (FILES / "eu_fsf_targets.simple.csv").read_bytes(), list_key="eu_fsf"
    )
    un = parse_targets_simple_csv(
        (FILES / "un_sc_targets.simple.csv").read_bytes(), list_key="un_sc"
    )
    return [
        ListSnapshot(find_list(LISTS, "eu_fsf"), eu.entries, as_of="2026-09-22T18:00:00Z"),
        ListSnapshot(find_list(LISTS, "un_sc"), un.entries, as_of="2026-09-22T18:00:00Z"),
        ListSnapshot(find_list(LISTS, "us_ofac_sdn"), ()),
    ]


def test_every_list_has_a_finding_and_a_state() -> None:
    result = screen("Iwan Musterow", snapshots(), DESIGNER)
    assert result.status == "HITS"
    assert [(f.list_key, f.searched) for f in result.findings] == [
        ("eu_fsf", True),
        ("un_sc", True),
        ("us_ofac_sdn", False),
    ]
    assert result.findings[0].as_of == "2026-09-22T18:00:00Z"
    assert result.findings[2].note and "nicht abgefragt" in result.findings[2].note
    assert not result.coverage_complete
    assert result.profile["id"] == "audit_designer.sanctions_screening"
    assert result.normalization["id"] == "audit_designer.sanctions"
    assert result.normalization["version"] == "2026.09.2"
    assert "Prüfhinweis" in result.notice
    assert any("phonetisches Verfahren" in text for text in result.limitations)


def test_reg_c01_no_hit_with_unsearched_list_is_incomplete() -> None:
    result = screen("Unbekannt Niemand", snapshots(), DESIGNER)
    assert result.status == "INCOMPLETE" and not result.hits
    assert any("belegt keine Unbedenklichkeit" in text for text in result.limitations)
    result = screen("Unbekannt Niemand", snapshots()[:2], DESIGNER)
    assert result.status == "NO_HITS"
    result = screen("Unbekannt Niemand", snapshots()[2:], DESIGNER)
    assert result.status == "NOT_SEARCHED"


def test_reg_c01_flowworkshop_profile_also_reports_empty_lists() -> None:
    result = screen("Iwan Musterow", snapshots(), WORKSHOP)
    assert [f.searched for f in result.findings] == [True, True, False]


def test_uncertainty_indicators_are_visible() -> None:
    result = screen("Ivan Musterov", snapshots(), DESIGNER, birth_date="1970", country="DE")
    hit = result.hits[0]
    assert hit.raw_score == 100.0 and hit.score == 72.0
    assert hit.dob_conflict and hit.country_conflict
    assert [a.kind for a in hit.adjustments] == ["date_of_birth", "country"]
    assert "alias_match" in hit.indicators
    subset = screen("Iwan Musterow", snapshots()[:1], DESIGNER).hits[0]
    assert subset.confidence == "high" and "token_subset" in subset.indicators
    assert "date_of_birth_not_compared" in subset.indicators


def test_reg_c02_hit_below_minimum_after_malus_is_flagged() -> None:
    result = screen("Anna Beispiel", snapshots()[:1], DESIGNER, country="de, at", birth_date="1981")
    low = [h for h in result.hits if h.score < result.min_score]
    assert low and all(h.below_min_score for h in low)
    assert all("below_min_score_after_adjustment" in h.indicators for h in low)


def test_transliteration_decision_mueller() -> None:
    for spelling in ("Mueller Luedenscheidt", "Müller-Lüdenscheidt", "Müller-Lüdenscheidt"):
        hit = screen(spelling, snapshots()[:1], DESIGNER).hits[0]
        assert hit.entry.entry_id == "eu-fsf-demo-0002" and hit.raw_score == 100.0
    assert screen("Muller Ludenscheidt", snapshots()[:1], DESIGNER).hits[0].raw_score < 80


def test_query_rules_of_the_profiles() -> None:
    with pytest.raises(QueryError):
        screen("ab", snapshots(), DESIGNER)
    assert screen("MLH", snapshots(), DESIGNER).hits
    with pytest.raises(QueryError):
        screen("Musterow", snapshots(), DESIGNER, min_score=45)
    assert screen("Musterow", snapshots(), WORKSHOP, min_score=45).min_score == 45
    with pytest.raises(QueryError):
        screen("Musterow", snapshots(), DESIGNER, schema="Vessel")
    assert screen("Beispiel Shipping", snapshots(), DESIGNER, schema="organization").hits
    with pytest.raises(QueryError):
        screen("Musterow", snapshots(), DESIGNER, limit=0)


def test_limit_and_truncation() -> None:
    result = screen("Beispiel", snapshots(), DESIGNER, min_score=50, limit=2)
    assert len(result.hits) == 2 and result.truncated
    assert result.findings[0].hit_count == 2  # the list itself had more candidates
    as_dict = result.to_dict()
    assert as_dict["contract"] == "auditcore_registry_sources.screening/1"
    assert as_dict["coverage_complete"] is False
