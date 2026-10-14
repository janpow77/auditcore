"""Kataloge: Firmennamen und Orte des Feldgenerators, erfundene Straßen, Rollen statt Namen."""

from __future__ import annotations

from datetime import date
from random import Random

import pytest
from auditcore_dummygenerator import company_name_at, company_name_count

from auditcore_dummybundle import catalogs as cat
from auditcore_dummybundle.chain import build_operation
from auditcore_dummybundle.config import BundleConfig
from auditcore_dummybundle.receipts import build_suppliers


def test_company_names_come_from_the_modular_name_space_of_the_field_generator() -> None:
    assert [cat.company_name(42, i) for i in range(5)] == [
        company_name_at(i, seed=42) for i in range(5)
    ]
    assert cat.company_name(42, company_name_count("private")) == cat.company_name(42, 0)


def test_company_names_are_distinct_within_a_bundle_and_match_the_entity_form() -> None:
    config = BundleConfig(seed=42, base_date=date(2026, 6, 30), operations=200)
    operations = [build_operation(config, index) for index in range(1, 201)]
    names = [str(row["beneficiary_name"]) for row in operations]
    assert len(set(names)) == len(names)
    suppliers = {supplier.name for supplier in build_suppliers(config)}
    assert len(suppliers) == len(build_suppliers(config)) and not suppliers & set(names)
    for row, name in zip(operations, names, strict=True):
        public = row["entity_form"] == "öffentlich-rechtlich"
        assert public == (name.endswith("AöR") or name.startswith(("Zweckverband", "Eigenbetrieb")))


def test_package_data_carries_no_company_stems_of_its_own() -> None:
    raw = cat._raw()
    assert not {"company_cores", "company_sectors", "legal_forms"} & set(raw)


@pytest.mark.parametrize("country", cat.COUNTRIES)
def test_addresses_pair_city_and_postal_code_from_the_field_generator(country: str) -> None:
    pairs = set(cat.catalogs().cities[country])
    for seed in range(100):
        street, postal_code, city = cat.address(Random(seed), country)
        assert (city, postal_code) in pairs
        assert street.rsplit(" ", 1)[0] in cat.catalogs().streets
        assert city in cat.catalogs().nuts3


def test_default_person_is_a_role_not_a_name() -> None:
    names = set(cat.catalogs().first_names["DE"]) | set(cat.catalogs().last_names["DE"])
    for seed in range(100):
        role, number = cat.role_name(Random(seed)).rsplit(" ", 1)
        assert role in cat.catalogs().roles and number.isdigit()
        assert role not in names


def test_weighted_pick_respects_weights_and_rejects_empty_weights() -> None:
    rng = Random(1)
    drawn = [cat.weighted_pick(rng, (("a", 9), ("b", 1), ("c", 0))) for _ in range(2_000)]
    assert drawn.count("c") == 0 and drawn.count("a") > drawn.count("b") * 5
    with pytest.raises(ValueError):
        cat.weighted_pick(rng, (("a", 0),))
