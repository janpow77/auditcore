"""Every recorded audit_designer output (beneficiaries, state aid, de-minimis) is reproduced."""

from __future__ import annotations

import json
from typing import Any

import pytest
from conftest import encode, load, revive

from auditcore_funding_sources import cumulation as cu
from auditcore_funding_sources import deminimis as dm
from auditcore_funding_sources import designer as de

DATA = load("designer")
CONSTANTS = revive(DATA["constants"])
CLIENT_OPS = {"deminimis.client_search", "deminimis.client_count", "deminimis.client_beneficiary"}
CASES = [c for c in DATA["cases"] if c["operation"] not in CLIENT_OPS]


def run(case: dict[str, Any]) -> Any:
    op, i = case["operation"], revive(case["inputs"])
    simple = {
        "designer.parse_betrag": de.parse_amount,
        "designer.state_aid_parse_amount": de.state_aid_parse_amount,
        "designer.amount_is_range": de.amount_is_range,
        "designer.parse_satz": de.parse_rate,
        "designer.parse_datum": de.parse_date,
        "designer.state_aid_parse_date": de.state_aid_parse_date,
        "designer.detect_sa_reference": de.detect_sa_reference,
        "deminimis.country_code": dm.country_code,
        "deminimis.as_date": dm.as_date,
        "deminimis.harvest_date": dm.harvest_date,
        "deminimis.as_amount": dm.as_amount,
        "deminimis.harvest_amount": dm.harvest_amount,
        "deminimis.harvest_timestamp": dm.harvest_timestamp,
        "deminimis.harvest_normalize": dm.normalize_name,
        "deminimis.authority_level": dm.authority_level,
    }
    if op in simple:
        return simple[op](i["value"])
    if op == "designer.normalize_company_name":
        return de.normalize_company_name(i["value"], drop_filler=i["drop_filler"])
    if op == "designer.compute_record_hash":
        return de.compute_record_hash(i["row"], i["source_key"])
    if op == "deminimis.criteria_body":
        return dm.SearchCriteria(**i).body()
    if op == "deminimis.row":
        return dm.row(i["award"])
    if op == "deminimis.harvest_fields":
        return dm.harvest_fields(i["award"])
    if op == "deminimis.record_hash":
        return dm.record_hash(i["award"])
    if op == "deminimis.inventory_hash":
        return dm.inventory_hash(i["hashes"])
    if op == "deminimis.cumulation":
        return cu.legacy_cumulation(i["records"], reference_date=i["stichtag"])
    if op == "deminimis.cumulation_raw":
        values = cu.legacy_cumulation_values(i["records"], reference_date=i["stichtag"])
        return {"$dataclass": "Kumulierung", "fields": values}
    raise AssertionError(op)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_recorded_output(case: dict[str, Any]) -> None:
    if case["exception"]:
        # Source defect kept in the variant: ``parse_amount(True)`` raises (FS-G01).
        with pytest.raises(Exception) as caught:
            run(case)
        assert type(caught.value).__name__ == case["exception"]["type"]
        return
    expected = case["output"]
    got = run(case)
    if case["operation"] == "deminimis.cumulation_raw":
        assert {"$dataclass": "Kumulierung", "fields": encode(got["fields"])} == expected
    else:
        assert encode(got) == expected


AWARD = {
    "referenceNumber": "DM-2026-0001",
    "beneficiaryName": "Beispiel GmbH",
    "beneficiaryReferenceNumber": "B-000123456",
    "amountEur": 120000.5,
    "currency": "EUR",
    "amount": 120000.5,
    "grantingDate": "2026-02-01",
    "deMinimisType": "GENERAL",
    "grantingAuthorityName": "Hessisches Ministerium für Wirtschaft",
    "sector": "C",
    "instrument": "GRANT",
    "publishedDate": "2026-02-20 08:00:00",
    "country": "CountryDEU",
    "extra": "nicht in SPALTEN",
}


def mock(request: dm.Request) -> tuple[int, Any]:
    """The capture tool's in-process register, answering the library's request objects."""
    body = dict(request.json or {})
    if request.url.endswith("/de-minimis-aid-awards") and body.get("beneficiaryName") == "fehler":
        return 500, {"error": "x"}
    if request.url.endswith("/de-minimis-aid-awards") and body.get("beneficiaryName") == "kaputt":
        return 200, {"unerwartet": True}
    if request.url.endswith("/de-minimis-aid-awards"):
        page = body.get("pageNumber", 0)
        return 200, [{**AWARD, "referenceNumber": f"DM-{page}-{i}"} for i in range(2)]
    if request.url.endswith("/counters"):
        if body.get("beneficiaryName") == "liste":
            return 200, [{"count": 7}]
        if body.get("beneficiaryName") == "ohne":
            return 200, {"total": 1}
        return 200, {"count": 4}
    if "/beneficiary/B-404" in request.url:
        return 404, None
    if "/beneficiary/B-503" in request.url:
        return 503, None
    return 200, [AWARD]


CLIENT_CASES = [c for c in DATA["cases"] if c["operation"] in CLIENT_OPS]


@pytest.mark.parametrize("case", CLIENT_CASES, ids=[c["name"] for c in CLIENT_CASES])
def test_client_semantics(case: dict[str, Any]) -> None:
    """Request construction and response interpretation match the source client."""
    op, i = case["operation"], revive(case["inputs"])
    if i.get("network") == "down":
        assert case["exception"]["message"] == dm.legacy_error_message(None)
        return
    if op == "deminimis.client_beneficiary":
        request = dm.beneficiary_request(i["reference"])
    elif op == "deminimis.client_count":
        request = dm.count_request(dm.SearchCriteria(**i))
    else:
        request = dm.search_request(dm.SearchCriteria(**i))
    status, payload = mock(request)
    if status >= 400 and status not in request.expected_empty_status:
        assert case["exception"]["message"] == dm.legacy_error_message(status)
        return
    if op == "deminimis.client_count":
        got: Any = dm.parse_count(payload)
    else:
        got = dm.parse_award_list(payload, status=status, strict=False)
    assert encode(got) == case["output"]


def test_request_log_matches_source_requests() -> None:
    """Methods, paths and bodies of the recorded requests are the ones the library builds."""
    for call in CONSTANTS["requests"]:
        assert call["path"].startswith("/eair/public/api/de-minimis-aid-awards")
    counters = [c for c in CONSTANTS["requests"] if c["path"].endswith("/counters")]
    assert all("pageNumber" not in (c["body"] or {}) for c in counters)
    body = dm.count_request(dm.SearchCriteria(beneficiaryName="liste")).json
    assert json.loads(json.dumps(body)) in [c["body"] for c in counters]


def test_harvest_scenarios_reproduce_source_runs() -> None:
    """Page-by-page reconciliation equals the counters of the executed ``ernte`` runs."""
    award = AWARD

    def rows(prefix: str, n: int, amount: float = 1000.0) -> list[dict[str, Any]]:
        return [
            {**award, "referenceNumber": f"{prefix}-{i}", "amountEur": amount} for i in range(n)
        ]

    scenarios: dict[str, tuple[list[list[dict[str, Any]]], int | None, int | None]] = {
        "complete": ([rows("A", 3)], 3, None),
        "changed-and-vanished": ([rows("A", 2, 2000.0)], 2, None),
        "partial-reported-more": ([rows("A", 1)], 5, None),
        "error-on-second-page": ([rows("A", 500), rows("B", 1)], 501, 1),
        "reappear": ([rows("A", 3)], 3, None),
        "unknown-total": ([rows("A", 3)], None, None),
        "missing-reference": ([[{"beneficiaryName": "ohne Nummer"}] + rows("A", 3)], 3, None),
    }
    stored: dict[str, str] = {}
    vanished: set[str] = set()
    runs: list[dict[str, Any]] = []
    for number, observed in enumerate(CONSTANTS["harvest"]):
        pages, reported, fail_at = scenarios[observed["name"]]
        state = dm.Reconciliation()
        index = 0
        while True:
            if fail_at is not None and index == fail_at:
                state.error = "RuntimeError: Seite nicht abrufbar"
                break
            page = pages[index] if index < len(pages) else []
            more = dm.reconcile_page(state, page, reported, stored)
            for reference, digest in state.seen.items():
                stored[reference] = digest
                vanished.discard(reference)
            if not more:
                break
            index += 1
        vanished.update(dm.mark_vanished(state, [r for r in stored if r not in vanished]))
        expected = observed["run"]
        assert state.status == expected["status"]
        assert state.reported == expected["records_reported"]
        assert len(state.seen) == expected["records_seen"]
        assert len(state.inserted) == expected["records_inserted"]
        assert len(state.updated) == expected["records_updated"]
        assert len(state.unchanged) == expected["records_unchanged"]
        assert len(state.vanished) == expected["records_vanished"]
        assert state.requests == expected["requests"]
        assert state.content_hash == expected["content_hash"]
        runs.append(
            {
                "status": state.status,
                "content_hash": state.content_hash,
                "started_at": f"{number:03d}",
                "finished_at": f"{number:03d}",
            }
        )
        legacy_state = dm.inventory_state(
            runs, len(stored) - len(vanished), len(vanished), legacy=True
        )
        inventory = observed["inventory"]
        assert legacy_state["saetze"] == inventory["saetze"]
        assert legacy_state["verschwunden"] == inventory["verschwunden"]
        # ``inhaltshash``/``stand_am`` of the source depend on ``started_at`` ordering; in the
        # capture all runs started within one second (SQLite CURRENT_TIMESTAMP), so the source
        # returned an arbitrary tied run (FS-D03). They are therefore not compared here.
        assert legacy_state["vollstaendig"] == inventory["vollstaendig"]


def test_fixture_is_complete() -> None:
    assert len(DATA["cases"]) == 384
    assert DATA["source"]["checkout_clean"] is True
