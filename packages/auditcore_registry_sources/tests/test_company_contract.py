"""Company verification contract (REG-C07..REG-C11): VIES, register and indicators."""

from __future__ import annotations

import json
from typing import Any

import pytest
from auditcore_harvest import ParserError, Response, TransportError
from replay_support import FILES

from auditcore_registry_sources import (
    QueryError,
    RegisterLookup,
    check_vat,
    load_profile,
    lookup_register,
    parse_register_rows,
    parse_vies_response,
    verify_company,
)
from auditcore_registry_sources.company import (
    REGISTER_SQL,
    names_match,
    normalize_company_name,
    register_query,
    vies_request,
)

PROFILE = load_profile("flowinvoice.company_verification", "2026.09.1")


class Answer:
    def __init__(self, status: int, body: bytes = b"", fail: bool = False) -> None:
        self.status, self.body, self.fail = status, body, fail
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        self.calls.append({"method": method, "url": url, **kwargs})
        if self.fail:
            raise TransportError("Zeitüberschreitung")
        return Response(self.status, self.body, {}, url)


def test_reg_c07_vies_with_namespace_prefixes() -> None:
    valid = parse_vies_response("ATU00000000", (FILES / "vies_valid_ns2.xml").read_bytes())
    assert valid.status == "VALID" and valid.name == "Beispiel Handels GmbH"
    assert valid.request_date == "2026-09-23+02:00" and valid.name_disclosed
    live = parse_vies_response("DE000000000", (FILES / "vies_de_000000000_live.xml").read_bytes())
    assert live.status == "INVALID" and live.name is None and not live.name_disclosed
    hidden = parse_vies_response(
        "DE000000001", (FILES / "vies_valid_de_ohne_name.xml").read_bytes()
    )
    assert hidden.status == "VALID" and hidden.name is None
    plain = parse_vies_response("ATU00000000", (FILES / "vies_ohne_praefix.xml").read_bytes())
    assert plain.status == "VALID"


def test_reg_c08_fault_and_transport_errors_are_unavailable() -> None:
    fault = parse_vies_response("ATU00000000", (FILES / "vies_fault.xml").read_bytes())
    assert fault.status == "UNAVAILABLE" and fault.fault == "MS_UNAVAILABLE"
    server = check_vat(Answer(500, (FILES / "vies_fault.xml").read_bytes()), "ATU00000000")
    assert server.status == "UNAVAILABLE"
    timeout = check_vat(Answer(200, fail=True), "ATU00000000")
    assert timeout.status == "UNAVAILABLE" and "Zeitüberschreitung" in (timeout.fault or "")
    with pytest.raises(ParserError):
        parse_vies_response("ATU00000000", b"<x/>")
    with pytest.raises(QueryError):
        vies_request("123")


def test_vies_request_escapes_values() -> None:
    url, body, headers = vies_request("at u<0000")
    assert url.startswith("https://ec.europa.eu/") and b"U&lt;0000" in body
    assert headers["Content-Type"].startswith("text/xml")
    transport = Answer(200, (FILES / "vies_valid_ns2.xml").read_bytes())
    assert check_vat(transport, "ATU00000000").status == "VALID"
    assert transport.calls[0]["method"] == "POST"


def test_reg_c09_register_query_uses_bound_parameters() -> None:
    url, params = register_query("O'Beispiel; DROP TABLE companies")
    assert params["sql"] == REGISTER_SQL and ":pattern" in REGISTER_SQL
    assert params["pattern"] == "%O'Beispiel; DROP TABLE companies%"
    found = parse_register_rows((FILES / "offeneregister_datasette.json").read_bytes(), PROFILE)
    assert found.status == "FOUND" and found.company and found.company.status == "active"
    assert found.candidates == 2
    liquidation = parse_register_rows(
        (FILES / "offeneregister_liquidation.json").read_bytes(), PROFILE
    )
    assert liquidation.company and liquidation.company.status == "dissolved"
    empty = parse_register_rows((FILES / "offeneregister_leer.json").read_bytes(), PROFILE)
    assert empty.status == "NOT_FOUND"
    down = lookup_register(Answer(502, b"Bad Gateway"), "Beispiel GmbH", PROFILE)
    assert down.status == "UNAVAILABLE"
    with pytest.raises(ParserError):
        parse_register_rows(b"<html>", PROFILE)


def test_reg_c10_legal_forms_are_whole_words() -> None:
    assert normalize_company_name("Hagen Metall AG", PROFILE) == "hagen metall"
    assert normalize_company_name("Kagel GmbH & Co. KG", PROFILE) == "kagel"
    assert names_match("Hagen Metall AG", "Metallbau Hagen GmbH", PROFILE) is False
    assert names_match("Beispiel Handels GmbH", "BEISPIEL HANDELS GMBH", PROFILE)


def test_reg_c11_verification_separates_unavailable_from_negative() -> None:
    valid = parse_vies_response("ATU00000000", (FILES / "vies_valid_ns2.xml").read_bytes())
    ok = verify_company("Beispiel Handels GmbH", PROFILE, vat=valid, country="AT")
    assert ok.is_verified and ok.indicators == () and ok.score == 1.0 and ok.complete
    hidden = parse_vies_response(
        "DE000000001", (FILES / "vies_valid_de_ohne_name.xml").read_bytes()
    )
    registered = parse_register_rows(
        (FILES / "offeneregister_datasette.json").read_bytes(), PROFILE
    )
    de = verify_company("Beispiel Handels GmbH", PROFILE, vat=hidden, register=registered)
    assert de.is_verified and de.indicators == () and any("---" in n for n in de.notes)
    down = verify_company(
        "Beispiel Handels GmbH", PROFILE, register=RegisterLookup("UNAVAILABLE", error="502")
    )
    assert down.indicators == () and down.unavailable == ("register",) and not down.complete
    missing = verify_company("Beispiel Handels GmbH", PROFILE, register=RegisterLookup("NOT_FOUND"))
    assert missing.indicators == ("NOT_IN_REGISTER",) and missing.score == 0.9
    invalid = parse_vies_response(
        "DE000000000", (FILES / "vies_de_000000000_live.xml").read_bytes()
    )
    bad = verify_company("Beispiel Handels GmbH", PROFILE, vat=invalid, register=registered)
    assert not bad.is_verified and bad.indicators == ("INVALID_VAT_ID",) and bad.score == 0.7
    assert json.dumps(bad.to_dict(), ensure_ascii=False)
