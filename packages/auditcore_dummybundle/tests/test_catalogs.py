"""Kataloge: Firmennamen und Orte des Feldgenerators, erfundene Straßen, Rollen statt Namen."""

from __future__ import annotations

from random import Random

import pytest
from auditcore_dummygenerator import TestDataGenerator

from auditcore_dummybundle import catalogs as cat


def test_company_names_are_the_list_of_the_field_generator() -> None:
    legacy = tuple(TestDataGenerator(seed=0).companies)
    assert cat.catalogs().companies == legacy and len(legacy) == 10
    drawn = {cat.company_name(Random(seed)) for seed in range(300)}
    assert drawn == set(legacy)


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
