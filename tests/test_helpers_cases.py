"""The shared contract cases: schema, decisions, integrity."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from helper_contracts_support import CASES

from auditcore.tools.helpers.cases import (
    NON_CONTRACT_FILES,
    find_cases_dir,
    load_cases,
    resolve,
)
from auditcore.tools.helpers.model import HelperToolError

CASE_FILES = sorted(p for p in CASES.glob("*.json") if p.name not in NON_CONTRACT_FILES)
EXPECTED_CONTRACTS = {
    "parse-number",
    "format-money",
    "format-date",
    "format-datetime",
    "format-filesize",
    "iban-valid",
    "lei-valid",
    "csv-cell",
    "csv-document",
    "api-error-message",
    "empty-value",
}


@pytest.mark.parametrize("path", CASE_FILES, ids=lambda p: p.name)
def test_case_files_follow_the_schema(path: Path) -> None:
    schema = json.loads((CASES / "schema.json").read_text(encoding="utf-8"))
    document = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(document, schema)
    assert document["contract"] == path.stem


def test_all_contracts_load_with_resolved_decisions() -> None:
    library = load_cases(CASES)
    assert set(library.contracts) == EXPECTED_CONTRACTS
    empty = library.decisions["empty_value"]
    assert empty == "—"
    money = library.contract("format-money")
    assert next(c for c in money.cases if c.id == "leer-null").expect == {"value": empty}
    assert library.probe_timezone == "America/New_York"


def test_every_decision_is_documented_as_provisional() -> None:
    text = (CASES / "DECISIONS.md").read_text(encoding="utf-8")
    decisions = json.loads((CASES / "decisions.json").read_text(encoding="utf-8"))
    assert decisions["status"] == "vorläufig" and "vorläufig" in text
    for key in decisions["decisions"]:
        assert f"`{key}`" in text, key


def test_probe_cases_exist_for_probe_rules() -> None:
    library = load_cases(CASES)
    parse = [c for c in library.contract("parse-number").cases if "probe" in c.tags]
    assert {c.input["mode"] for c in parse} == {"de"} and len(parse) >= 5
    assert [c.id for c in library.contract("format-date").cases if "probe" in c.tags] == [
        "reines-datum",
        "utc-abend-winter",
    ]


def test_unknown_decision_is_an_error() -> None:
    with pytest.raises(HelperToolError):
        resolve({"$decision": "gibt_es_nicht"}, {})


def test_cases_dir_is_found_from_the_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUDITCORE_HELPER_CASES", raising=False)
    assert find_cases_dir().resolve() == CASES.resolve()
