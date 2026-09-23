"""audit_designer and flowworkshop screening originals are reproduced exactly."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from replay_support import BY_NAME, cases, csv_rows, plain, same

from auditcore_registry_sources import legacy

EU = "eu_fsf_targets.simple.csv"
UN = "un_sc_targets.simple.csv"


def query(case: dict[str, Any]) -> dict[str, Any]:
    return dict(plain(case["inputs"])["query"])


@pytest.mark.parametrize("case", cases("designer_row"), ids=lambda c: c["name"])
def test_designer_rows(case: dict[str, Any]) -> None:
    inputs = plain(case["inputs"])
    assert same(legacy.designer_row(inputs["row"], inputs["list_key"]), case["output"])


@pytest.mark.parametrize("case", cases("designer_index_search"), ids=lambda c: c["name"])
def test_designer_index_search(case: dict[str, Any]) -> None:
    q = query(case)
    records = legacy.designer_records(csv_rows(EU), "eu_fsf")
    found = legacy.designer_index_search(
        records,
        "eu_fsf",
        q["name"],
        limit=q.get("limit", 15),
        min_score=q.get("min_score", 70.0),
        schema=q.get("schema"),
        birth_date=q.get("birth_date"),
        country=q.get("country"),
    )
    assert same(found, case["output"])


@pytest.mark.parametrize("case", cases("designer_service_search"), ids=lambda c: c["name"])
def test_designer_service_search(case: dict[str, Any]) -> None:
    q = query(case)
    inventory = {
        "eu_fsf": legacy.designer_records(csv_rows(EU), "eu_fsf"),
        "un_sc": legacy.designer_records(csv_rows(UN), "un_sc"),
        "us_ofac_sdn": [],
    }
    found = legacy.designer_service_search(
        inventory,
        ["eu_fsf", "un_sc", "us_ofac_sdn"],
        q["name"],
        as_of=datetime(2026, 9, 22, 18, 0, 0),
        limit=q.get("limit", 15),
        min_score=q.get("min_score", 70.0),
        schema=q.get("schema"),
        birth_date=q.get("birth_date"),
        country=q.get("country"),
    )
    assert same(found, case["output"])


@pytest.mark.parametrize(
    "case",
    cases("designer_dob_country") + cases("workshop_dob_country"),
    ids=lambda c: c["name"],
)
def test_date_of_birth_and_country(case: dict[str, Any]) -> None:
    c = plain(case["inputs"])
    function = (
        legacy.designer_dob_country
        if case["operation"].startswith("designer")
        else legacy.workshop_dob_country
    )
    result = function(
        c["score"],
        entry_birth_date=c["rec_dob"],
        entry_countries=c["rec_c"],
        birth_date=c["q_dob"],
        country=c["q_c"],
    )
    assert same(result, case["output"])


PROVIDER = {
    "designer_provider_name": lambda i: legacy.designer_provider_name(i),
    "designer_provider_min_score": lambda i: legacy.designer_provider_min_score(i["min_score"]),
    "designer_provider_schema": lambda i: legacy.designer_provider_schema(i["entity_schema"]),
}


@pytest.mark.parametrize(
    "case",
    [c for op in PROVIDER for c in cases(op)],
    ids=lambda c: c["name"],
)
def test_designer_provider_input_rules(case: dict[str, Any]) -> None:
    function = PROVIDER[case["operation"]]
    if case["exception"]:
        with pytest.raises(legacy.QueryError) as error:
            function(plain(case["inputs"]))
        assert str(error.value) == case["exception"]["message"]
    else:
        assert same(function(plain(case["inputs"])), case["output"])


def test_designer_method_constants_match_the_profiles() -> None:
    method = plain(BY_NAME["designer-method"]["output"])
    profile = legacy._profile("audit_designer.sanctions_screening")
    assert method["mindestwert"] == profile.setting("default_min_score")
    assert method["grenzen"][1] == profile.setting("limitations")[0]
    assert [x["list_key"] for x in method["listen"]] == [
        x["key"] for x in legacy._profile("audit_designer.sanctions_lists").setting("lists")
    ]
    assert "phonetisch" not in " ".join(profile.setting("limitations")).replace(
        "Ein phonetisches Verfahren ist nicht im Einsatz", ""
    )


@pytest.mark.parametrize("case", cases("workshop_row"), ids=lambda c: c["name"])
def test_workshop_rows(case: dict[str, Any]) -> None:
    assert same(legacy.workshop_record(plain(case["inputs"])["row"]), case["output"])


@pytest.mark.parametrize("case", cases("workshop_index_search"), ids=lambda c: c["name"])
def test_workshop_index_search(case: dict[str, Any]) -> None:
    q = query(case)
    found = legacy.workshop_index_search(
        legacy.workshop_records(csv_rows(EU)),
        "eu_fsf",
        "EU",
        q["name"],
        limit=q.get("limit", 15),
        min_score=q.get("min_score", 70.0),
        schema=q.get("schema"),
        birth_date=q.get("birth_date"),
        country=q.get("country"),
    )
    assert same(found, case["output"])


@pytest.mark.parametrize("case", cases("workshop_multi_search"), ids=lambda c: c["name"])
def test_workshop_multi_search(case: dict[str, Any]) -> None:
    q = query(case)
    found = legacy.workshop_multi_search(
        [
            ("eu_fsf", "EU", legacy.workshop_records(csv_rows(EU))),
            ("un_sc", "UN", legacy.workshop_records(csv_rows(UN))),
            ("us_ofac_sdn", "OFAC", []),
        ],
        q["name"],
        limit=q.get("limit", 15),
        min_score=q.get("min_score", 70.0),
        schema=q.get("schema"),
        birth_date=q.get("birth_date"),
        country=q.get("country"),
    )
    assert same(found, case["output"])


def test_workshop_skips_lists_without_inventory_silently() -> None:
    assert plain(BY_NAME["workshop-multi-loaded"]["output"]) == {
        "eu_fsf": True,
        "un_sc": True,
        "us_ofac_sdn": False,
    }
