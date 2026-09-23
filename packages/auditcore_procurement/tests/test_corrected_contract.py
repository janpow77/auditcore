"""Corrected contract next to the legacy result (behavior changes P-C01…P-C08)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tools_inputs import CLIENT_INPUTS

from auditcore_procurement import company_sources as cs
from auditcore_procurement import prechecks, records, ted

PROFILE = prechecks.load_profile("procurement.hvtg-legacy", "2026.09.1")
HVTG = prechecks.load_profile("procurement.hvtg", "2026.09.2")
SUPPLY = "Liefer-/Dienstleistungen"
AWARD = {
    "publication-number": "1-2024",
    "winner-name": "Beispiel GmbH",
    "result-value-notice": "1.234,56",
    "publication-date": "2024-01-15+01:00",
}


def statuses(report: dict) -> dict[str, str]:
    return {c["check_id"]: c["status"] for c in report["checks"]}


def test_p_c01_unknown_tier_is_not_checked_instead_of_pass() -> None:
    args = (Decimal("50000"), None, None, SUPPLY, "Irgendwas", "UNBEKANNT", [])
    legacy = prechecks.run_prechecks(PROFILE, *args)
    strict = prechecks.run_prechecks(PROFILE, *args, mode="strict")
    assert statuses(legacy)["precheck_procedure_threshold"] == "PASS"
    assert statuses(strict)["precheck_procedure_threshold"] == "NOT_CHECKED"
    assert statuses(strict)["precheck_min_bids"] == "NOT_CHECKED"


def test_p_c02_zero_values_are_values_not_missing() -> None:
    legacy = prechecks.run_prechecks(PROFILE, Decimal("0"), None, None, SUPPLY, None, None, [])
    strict = prechecks.run_prechecks(
        HVTG,
        Decimal("0"),
        Decimal("0"),
        Decimal("5"),
        SUPPLY,
        None,
        None,
        [],
        mode="strict",
        year=2026,
    )
    assert legacy["checks"][0]["message"] == "Kein geschaetzter Auftragswert angegeben."
    assert strict["checks"][0]["status"] == "PASS"
    assert strict["checks"][0]["calculated_tier"] == "BELOW_1K"
    assert statuses(strict)["precheck_value_deviation"] == "WARNING"  # contract value 0


def test_p_c03_exact_procedure_names_in_strict_mode() -> None:
    args = (
        Decimal("500"),
        None,
        None,
        SUPPLY,
        "Direktvergabe (Ausnahme)",
        "BELOW_1K",
        [{"procurement_doc_type": "VERGABEVERMERK"}],
    )
    assert (
        statuses(prechecks.run_prechecks(PROFILE, *args))["precheck_procedure_threshold"] == "PASS"
    )
    strict = prechecks.run_prechecks(PROFILE, *args, mode="strict")
    assert statuses(strict)["precheck_procedure_threshold"] == "FAIL"
    assert statuses(strict)["precheck_required_docs"] == "WARNING"


def test_p_c04_single_missing_value_is_reported() -> None:
    legacy = prechecks.run_prechecks(PROFILE, None, Decimal("100"), None, SUPPLY, None, None, [])
    strict = prechecks.run_prechecks(
        PROFILE, None, Decimal("100"), None, SUPPLY, None, None, [], mode="strict"
    )
    assert "precheck_value_deviation" not in statuses(legacy)
    assert statuses(strict)["precheck_value_deviation"] == "NOT_CHECKED"


def test_strict_report_names_profile_and_uses_injected_time() -> None:
    now = datetime(2026, 9, 22, tzinfo=UTC)
    report = prechecks.run_prechecks(
        PROFILE, None, None, None, SUPPLY, None, None, [], mode="strict", now=now
    )
    assert report["profile"] == PROFILE.reference and report["timestamp"] == now.isoformat()
    with pytest.raises(ValueError):
        prechecks.run_prechecks(PROFILE, None, None, None, SUPPLY, None, None, [], mode="x")


@pytest.mark.parametrize(
    ("contract", "invoice", "expected"),
    [
        ("100", "110", "PASS"),
        ("100", "110.01", "WARNING"),
        ("100", "120", "WARNING"),
        ("100", "120.01", "FAIL"),
        ("100", "79.99", "FAIL"),
    ],
)
def test_value_deviation_edges(contract: str, invoice: str, expected: str) -> None:
    result = prechecks.check_value_deviation(PROFILE, Decimal(contract), Decimal(invoice))
    assert result["status"] == expected


def test_p_c05_profile_validation_and_identity() -> None:
    assert (
        PROFILE.status == "SOURCE_CHARACTERIZED"
        and "HUMAN_DECISION_REQUIRED" in PROFILE.legal_status
    )
    assert len(PROFILE.fingerprint) == 64
    with pytest.raises(prechecks.ProfileError):
        prechecks.load_profile("procurement.hvtg-legacy", "0")
    with pytest.raises(prechecks.ProfileError):
        prechecks.load_profile("../x", "1")
    data = json.loads(
        (
            __import__("importlib.resources").resources.files("auditcore_procurement.profiles")
            / "procurement.hvtg-legacy-2026.09.1.json"
        ).read_text()
    )
    data["tiers"]["supply_service"].reverse()
    with pytest.raises(prechecks.ProfileError):
        prechecks.profile_from_dict(data)
    with pytest.raises(prechecks.ProfileError):
        prechecks.profile_from_dict({"schema": "x"})


def test_p_c06_ambiguous_german_amount_is_reported_not_silently_changed() -> None:
    record = ted.normalize_notice(AWARD)
    assert record is not None and record["contract_value"] == pytest.approx(1.23456)
    codes = [i.code for i in ted.inspect_notice(AWARD)]
    assert "ambiguous_amount" in codes
    assert [i.code for i in ted.inspect_notice({**AWARD, "result-value-notice": "1,234.56"})] == []
    assert "unparsed_amount" in [
        i.code for i in ted.inspect_notice({**AWARD, "result-value-notice": "n/a"})
    ]
    assert "correction_notice" in [
        i.code for i in ted.inspect_notice({**AWARD, "notice-type": "corr"})
    ]
    assert "no_contractor" in [i.code for i in ted.inspect_notice({"publication-number": "x"})]
    assert ted.inspect_notice(["x"])[0].code == "not_a_notice"
    assert "unparsed_date" in [
        i.code for i in ted.inspect_notice({**AWARD, "publication-date": "gestern"})
    ]


def test_p_c07_all_notice_types_on_request_and_coverage_labels() -> None:
    tender = {"publication-number": "2-2024", "notice-title": "Ausschreibung"}
    assert ted.normalize_notice(tender) is None
    assert ted.normalize_notice(tender, require_contractor=False) == {
        "notice_id": "2-2024",
        "document_number": "2-2024",
        "title": "Ausschreibung",
    }
    assert (
        ted.query_coverage(ted.build_ted_query(country="DEU"))
        == records.COVERAGE_AWARDS_WITH_WINNER
    )
    assert ted.query_coverage("buyer-country=DEU") == records.COVERAGE_ALL_NOTICES
    assert ted.query_coverage(None) == records.COVERAGE_AWARDS_WITH_WINNER


@pytest.mark.parametrize("variant", cs.VARIANTS)
@pytest.mark.parametrize("name", ["not-found", "server-error", "bad-json", "exception"])
def test_p_c08_ted_errors_are_explicit(variant: str, name: str) -> None:
    status, body = CLIENT_INPUTS[("ted", name)]
    assert cs.legacy_ted_company_parse(status, body, "DE", variant) == []
    result = cs.ted_company_result(status, body, "DE", variant)
    expected = "no_hit" if name == "not-found" else "failed"
    assert result.status == expected
    assert result.complete is (expected == "no_hit")


def test_p_c08_flowinvoice_parser_error_is_a_failure() -> None:
    status, body = CLIENT_INPUTS[("ted", "results-mnemonic")]
    assert cs.legacy_ted_company_parse(status, body, "DE", "flowinvoice") == []
    failed = cs.ted_company_result(status, body, "DE", "flowinvoice")
    assert failed.status == "failed" and "Parserfehler" in failed.error
    ok = cs.ted_company_result(status, body, "DE", "designer")
    assert ok.status == "ok" and ok.notices[0]["notice_title"] == "Titel"
    two = {"results": [{"ND": "1", "TI": "a"}, {"ND": "2", "TI": {"deu": "b"}}]}
    assert [
        n["publication_number"] for n in cs.legacy_ted_company_parse(200, two, "DE", "flowinvoice")
    ] == ["1"]
    assert cs.ted_company_result(200, [1], "DE", "designer").status == "failed"
    assert cs.ted_company_result(429, None, "DE", "designer").status == "rate_limited"
    assert cs.ted_company_result(200, {"notices": []}, "DE", "designer").status == "no_hit"


@pytest.mark.parametrize(
    ("name", "variant", "expected"),
    [
        ("forbidden", "flowinvoice", "rate_limited"),
        ("not-found", "designer", "no_hit"),
        ("not-found", "flowinvoice", "failed"),
        ("error", "designer", "failed"),
        ("exception", "designer", "failed"),
        ("none", "designer", "no_hit"),
        ("table", "flowinvoice", "ok"),
    ],
)
def test_p_c08_had_results_are_explicit(name: str, variant: str, expected: str) -> None:
    status, body = CLIENT_INPUTS[("had", name)]
    result = cs.had_result(status, body, variant)
    assert result.status == expected
    if name == "none":
        assert result.warnings


def test_unknown_variant_is_rejected() -> None:
    with pytest.raises(ValueError):
        cs.ted_company_request("x", "DE", "portal")


def test_file_import_and_online_records_share_the_contract() -> None:
    record = ted.normalize_notice({**AWARD, "result-value-notice": "150000.00"})
    assert record is not None and records.validate_record(record) == []
    back, columns, validation = ted.parse_ted_file(ted.dump_records([record]), "x.json")
    assert back == [record] and columns == list(records.NOTICE_FIELDS) and not validation["errors"]
    assert tuple(ted.FIELD_ALIASES) == records.NOTICE_FIELDS


def test_validate_record_findings() -> None:
    codes = [
        i.code
        for i in records.validate_record(
            {"x": 1, "contract_value": "7", "title": " ", "publication_date": "15.01.2024"}
        )
    ]
    assert codes == [
        "unknown_field",
        "not_numeric",
        "not_text",
        "not_iso_date",
        "missing_contractor",
    ]
    assert records.validate_record({"notice_id": "1"}, require_contractor=False) == []
    assert records.Issue("c", "m", True).to_dict()["blocking"] is True


def test_normalisation_does_not_mutate_input() -> None:
    notice = {**AWARD, "classification-cpv": ["1", "2"]}
    before = json.dumps(notice, sort_keys=True)
    ted.normalize_notice(notice)
    ted.inspect_notice(notice)
    assert json.dumps(notice, sort_keys=True) == before


def test_profile_from_consumer_ruleset_equals_packaged_rules() -> None:
    from conftest import LEGACY

    rules = LEGACY["ruleset"]
    built = prechecks.profile_from_ruleset(
        rules, profile_id="app.rules", version="1", source={"repository": "x"}
    )
    assert built.tiers == PROFILE.tiers and built.required_documents == PROFILE.required_documents
    assert built.status == "CONSUMER_RULESET"
    with pytest.raises(prechecks.ProfileError):
        prechecks.profile_from_ruleset({}, profile_id="a", version="1", source={})
