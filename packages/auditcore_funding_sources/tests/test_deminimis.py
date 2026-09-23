"""Corrected de-minimis register contract next to the recorded legacy behavior."""

from __future__ import annotations

import pytest

from auditcore_funding_sources import deminimis as dm


def test_fs_d01_unexpected_shape_is_an_error_legacy_returned_empty() -> None:
    assert dm.parse_award_list({"unerwartet": True}, strict=False) == []
    with pytest.raises(dm.RegisterResponseError):
        dm.parse_award_list({"unerwartet": True})
    assert dm.parse_award_list(None, status=404) == []
    assert dm.parse_award_list([{"referenceNumber": "x"}]) == [{"referenceNumber": "x"}]


def test_fs_d02_inventory_after_failed_run_is_not_complete() -> None:
    runs = [
        {"status": "ok", "content_hash": "h1", "started_at": "1", "finished_at": "f1"},
        {"status": "failed", "content_hash": "h2", "started_at": "2", "finished_at": "f2"},
    ]
    legacy = dm.inventory_state(runs, 500, 0, legacy=True)
    corrected = dm.inventory_state(runs, 500, 0)
    assert legacy["vollstaendig"] is True and legacy["inhaltshash"] == "h1"
    assert corrected["vollstaendig"] is False and corrected["letzter_status"] == "failed"
    assert corrected["letzter_vollstaendiger_lauf"] == "f1"


def test_vanished_only_after_complete_run() -> None:
    state = dm.Reconciliation()
    dm.reconcile_page(state, [{"referenceNumber": "A"}], 2, {})
    assert dm.mark_vanished(state, ["A", "B"]) == []
    state = dm.Reconciliation()
    dm.reconcile_page(state, [{"referenceNumber": "A"}], 1, {})
    assert state.complete and dm.mark_vanished(state, ["A", "B"]) == ["B"]


def test_request_construction_is_read_only_and_validated() -> None:
    criteria = dm.SearchCriteria(beneficiaryName="Beispiel", pageNumber=2, pageSize=500)
    assert dm.search_request(criteria).method == "POST"
    assert "pageNumber" not in (dm.count_request(criteria).json or {})
    assert dm.beneficiary_request("B-000123456").expected_empty_status == (404,)
    for bad in ("../x", "", "a b", "x" * 65):
        with pytest.raises(ValueError):
            dm.beneficiary_request(bad)
    assert dm.country_code("de") == "CountryDEU"


def test_authority_rules_keep_official_prefix_first() -> None:
    assert dm.authority_level("DE-RP-HWK Rheinhessen") == "Rheinland-Pfalz"
    assert dm.authority_level("Grenke Bank AG") == "unbestimmt"
