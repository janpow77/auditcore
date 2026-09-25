"""Legacy profiles reproduce every recorded output of the original functions."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from auditcore_identifiers import CheckResult, Reason, Status
from auditcore_identifiers import legacy_flowinvoice as fi
from auditcore_identifiers import legacy_pipeline as lp

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = json.loads((FIXTURES / name).read_text("utf-8"))["cases"]
    return cases


def _validators(profile: str) -> dict[str, Callable[[dict[str, Any]], CheckResult]]:
    return {
        "validate_iban": lambda i: fi.validate_iban(i["value"], profile),
        "validate_bic": lambda i: fi.validate_bic(i["value"], profile),
        "validate_german_tax_id": lambda i: fi.validate_german_tax_id(i["value"], profile),
        "validate_german_vat_id": lambda i: fi.validate_german_vat_id(i["value"], profile),
        "validate_uk_vat_id": lambda i: fi.validate_uk_vat_id(i["value"], profile),
        "validate_eu_vat_id": lambda i: fi.validate_eu_vat_id(
            i["value"], i["country_code"], profile),
    }


def assert_validator(case: dict[str, Any], result: CheckResult) -> None:
    expected = case["output"]
    assert result.status.value == expected["status"]
    assert result.message == expected["message"]
    assert (dict(result.details) or None) == expected["details"]
    if result.status is Status.VALID:
        assert result.normalized == expected["value"]
    elif result.status is Status.MISSING:
        assert expected["value"] is None and result.normalized is None
    else:
        assert result.raw == expected["value"]


def assert_pipeline_iban(case: dict[str, Any], result: CheckResult) -> None:
    if case["exception"] == "AttributeError":  # original crashed on None
        assert case["inputs"]["value"] is None and result.reason is Reason.MISSING
        return
    ok, message = case["output"]
    assert result.valid is ok
    assert result.message == message


def assert_pipeline_vat(case: dict[str, Any], result: CheckResult) -> None:
    expected = case["output"]
    assert result.message == expected["message"]
    assert result.details["outcome"] == expected["outcome"]
    assert result.details["severity"] == expected["severity"]
    skipped = expected["message"].startswith("No VAT ID found")
    assert (result.status is Status.MISSING) is skipped
    assert result.valid is (expected["outcome"] == "PASS" and not skipped)


def _app_cases(name: str) -> list[dict[str, Any]]:
    return [c for c in _load(name) if c["function"] != "_normalize_vat_id"]


@pytest.mark.parametrize("fixture,profile,pipeline", [
    ("flowinvoice_observed.json", "flowinvoice.legacy", "flowinvoice.pipeline.legacy"),
    ("audit_portal_observed.json", "audit_portal.legacy", "audit_portal.pipeline.legacy"),
])
def test_application_originals_are_reproduced(fixture: str, profile: str, pipeline: str) -> None:
    validators = _validators(profile)
    checked = 0
    for case in _app_cases(fixture):
        function, inputs = case["function"], case["inputs"]
        if function in validators:
            assert case["exception"] is None
            assert_validator(case, validators[function](inputs))
        elif function == "_validate_iban":
            assert_pipeline_iban(case, lp.pipeline_validate_iban(inputs["value"], pipeline))
        else:
            assert function == "VatIdFormatRule.evaluate"
            assert_pipeline_vat(case, lp.pipeline_vat_id_format(inputs["value"], pipeline))
        checked += 1
    assert checked > 9000


@pytest.mark.parametrize("fixture", ["flowinvoice_observed.json", "audit_portal_observed.json"])
def test_normalize_vat_id_is_reproduced(fixture: str) -> None:
    for case in _load(fixture):
        if case["function"] == "_normalize_vat_id":
            if case["exception"]:
                assert case["inputs"]["value"] is None
            else:
                assert fi.normalize_vat_id(case["inputs"]["value"]) == case["output"]


def _internal_bool(case: dict[str, Any], result: CheckResult) -> None:
    if case["exception"] == "ValueError":  # original crashed on e.g. "ä"
        assert result.status is Status.INVALID
    elif case["exception"] == "AttributeError":
        assert result.reason is Reason.INVALID_TYPE
    else:
        assert result.valid is case["output"]


def _internal_message(case: dict[str, Any], result: CheckResult) -> None:
    # None crashed, "" is skipped by the Donut stage before the call: both MISSING here.
    if case["exception"] == "AttributeError" or case["inputs"]["value"] == "":
        assert result.status is Status.MISSING
    elif case["output"] is None:
        assert result.valid
    else:
        assert result.message == case["output"]


def test_internal_copies_are_reproduced() -> None:
    checks: dict[str, Callable[[dict[str, Any]], None]] = {
        "invoicesynth.iban_valid":
            lambda c: _internal_bool(c, lp.invoicesynth_iban_valid(c["inputs"]["value"])),
        "invoicesynth.vat_id_valid":
            lambda c: _internal_bool(c, lp.invoicesynth_vat_id_valid(c["inputs"]["value"])),
        "documents.validate_iban":
            lambda c: assert_pipeline_iban(c, lp.pipeline_validate_iban(c["inputs"]["value"])),
        "documents.donut_iban":
            lambda c: assert_pipeline_iban(c, lp.donut_validate_iban(c["inputs"]["value"])),
        "documents.donut_vat_id_check":
            lambda c: _internal_message(c, lp.donut_vat_id_check(c["inputs"]["value"])),
        "is_valid_lei": lambda c: _flowworkshop_lei(c),
        "extract_lei_from_text": lambda c: _flowworkshop_extract(c),
    }
    seen = set()
    for case in _load("internal_observed.json"):
        if case["function"] in checks:
            checks[case["function"]](case)
            seen.add(case["function"])
    assert seen == set(checks)


def _flowworkshop_lei(case: dict[str, Any]) -> None:
    assert lp.flowworkshop_is_valid_lei(case["inputs"]["value"]).valid is case["output"]


def _flowworkshop_extract(case: dict[str, Any]) -> None:
    assert lp.flowworkshop_extract_lei_from_text(case["inputs"]["value"]) == case["output"]
