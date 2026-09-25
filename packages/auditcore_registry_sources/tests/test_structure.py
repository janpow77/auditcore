"""Module structure of 0.1.1: facades keep every public import path, helpers are covered."""

from __future__ import annotations

import json

import pytest

from auditcore_registry_sources import (
    _company_register,
    _company_vat,
    _opensanctions_assessment,
    _opensanctions_match,
    _opensanctions_query,
    _screening_index,
    _screening_rules,
    company,
    legacy,
    load_profile,
    opensanctions_api,
    sanctions_xml,
    screening,
)
from auditcore_registry_sources.company import RegisterCompany, RegisterLookup, VatCheck
from auditcore_registry_sources.screening import ListFinding, _status


@pytest.mark.parametrize(
    ("facade", "modules"),
    [
        (screening, (_screening_index, _screening_rules)),
        (company, (_company_vat, _company_register)),
        (
            opensanctions_api,
            (_opensanctions_query, _opensanctions_match, _opensanctions_assessment),
        ),
    ],
)
def test_facades_re_export_the_same_objects(facade: object, modules: tuple[object, ...]) -> None:
    for name in facade.__all__:  # type: ignore[attr-defined]
        value = getattr(facade, name)
        for module in modules:
            if hasattr(module, name):
                assert getattr(module, name) is value, name


def test_legacy_facade_exports_every_replay() -> None:
    assert "designer_row" in legacy.__all__ and "flowinvoice_verify_company" in legacy.__all__
    for name in legacy.__all__:
        assert getattr(legacy, name) is not None
    assert legacy._profile("flowsearch.ubo").id == "flowsearch.ubo"
    assert legacy.VERSION == "2026.09.1"


def test_extra_key_constant_is_kept_but_not_leaked() -> None:
    assert sanctions_xml.EXTRA == "__extra"
    assert set(sanctions_xml.FORMATS) == {"eu_fsf_xml", "ofac_sdn_xml", "un_sc_xml"}


def test_simple_row_accepts_plain_mappings() -> None:
    row = sanctions_xml.to_simple_row(
        {"list_id": " 7 ", "entity_type": "entity", "name": "X", "aliases": ["a", " "]}
    )
    assert row["id"] == "7" and row["schema"] == "Organization" and row["aliases"] == "a"


def _finding(searched: bool) -> ListFinding:
    return ListFinding("k", "K", None, searched, 1, None, None, 0)


def test_status_table() -> None:
    assert _status([], [_finding(False)]) == "NOT_SEARCHED"
    assert _status([], [_finding(True), _finding(False)]) == "INCOMPLETE"
    assert _status([], [_finding(True)]) == "NO_HITS"


def _company(status: str) -> RegisterLookup:
    return RegisterLookup(
        "FOUND", RegisterCompany("A GmbH", status, None, None, None, None, status)
    )


def test_register_findings_cover_every_state() -> None:
    profile = load_profile("flowinvoice.company_verification", "2026.09.2")
    verify = company.verify_company
    assert verify("A GmbH", profile, register=_company("inactive")).indicators == (
        "COMPANY_INACTIVE",
    )
    assert verify("A GmbH", profile, register=_company("active")).indicators == ()
    assert verify("A GmbH", profile, register=RegisterLookup("FOUND")).indicators == ()
    missing = verify("A GmbH", profile)
    assert missing.unavailable == ("register",) and missing.notes


def test_vat_findings_order_before_register() -> None:
    profile = load_profile("flowinvoice.company_verification", "2026.09.2")
    result = company.verify_company(
        "A GmbH",
        profile,
        vat=VatCheck("UNAVAILABLE", "DE1", "DE"),
        register=RegisterLookup("NOT_FOUND"),
    )
    assert result.indicators == ("VIES_SERVICE_UNAVAILABLE", "NOT_IN_REGISTER")
    assert result.unavailable == ("vies",)


def test_views_are_json_serialisable() -> None:
    candidate = _opensanctions_match.Candidate(
        "id", "c", "Person", 0.9, None, ("ds",), ("role.pep",), {}, None, None, None
    )
    match = _opensanctions_assessment.PepMatch(
        candidate,
        "PEP",
        "low",
        tuple(_opensanctions_assessment.positions({"position": ["Minister"]})),
    )
    view = match.to_dict()
    assert json.loads(json.dumps(view))["positions"][0]["title"] == "Minister"
    assert view["positions"][0] is not match.positions[0]
