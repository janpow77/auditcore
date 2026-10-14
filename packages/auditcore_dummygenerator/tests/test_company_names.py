"""Modular company names: size of the name space, determinism, no duplicates, legal forms."""

from __future__ import annotations

import random

import pytest

from auditcore_dummygenerator import (
    ENTITY_FORMS,
    TestDataGenerator,
    company_name_at,
    company_name_count,
    draw_company_name,
)
from auditcore_dummygenerator import company_names as names

LEGACY_COMPANIES = [
    "TechCorp GmbH", "Digital Solutions AG", "InnoTech KG", "DataServ GmbH",
    "CloudSys AG", "NetWorks GmbH", "SoftDev KG", "IT-Service GmbH",
    "WebTech AG", "AppFactory GmbH",
]  # fmt: skip


def test_name_space_exceeds_five_thousand_combinations() -> None:
    assert company_name_count("private") > 5000
    assert company_name_count() == sum(company_name_count(form) for form in ENTITY_FORMS)
    every_private = {names._compose(names._SCHEMES["private"], i) for i in range(25920)}
    assert len(every_private) == company_name_count("private") == 25920


def test_parts_are_separate_lists_without_duplicates() -> None:
    lists = (
        names.PREFIXES, names.COMMERCIAL_AREAS, names.CIVIC_AREAS, names.PUBLIC_AREAS,
        names.COMMERCIAL_SUFFIXES, names.PRIVATE_FORMS, names.NONPROFIT_FORMS, names.PUBLIC_FORMS,
    )  # fmt: skip
    for parts in lists:
        assert len(set(parts)) == len(parts)


@pytest.mark.parametrize(
    "form",
    ["GmbH", "AG", "Stiftung", "e. V.", "GmbH & Co. KG", "UG (haftungsbeschränkt)"],
)
def test_required_legal_forms_occur(form: str) -> None:
    patterns = names.PRIVATE_FORMS + names.NONPROFIT_FORMS
    assert any(pattern.replace("{}", "").strip() == form for pattern in patterns)


def test_legal_form_matches_entity_form() -> None:
    for position in range(300):
        private = company_name_at(position, seed=7, entity_form="private")
        public = company_name_at(position, seed=7, entity_form="public")
        nonprofit = company_name_at(position, seed=7, entity_form="nonprofit")
        assert private.endswith(("GmbH", "AG", "KG", "(haftungsbeschränkt)", "eG"))
        assert public.endswith("AöR") or public.startswith(("Zweckverband ", "Eigenbetrieb "))
        assert nonprofit.endswith(("e. V.", "gGmbH")) or nonprofit.startswith("Stiftung ")


def test_draw_is_reproducible_and_uses_one_rng_call() -> None:
    first = [draw_company_name(random.Random(42)) for _ in range(3)]
    assert len(set(first)) == 1
    rng, twin = random.Random(5), random.Random(5)
    draw_company_name(rng, "public")
    twin.randrange(company_name_count("public"))
    assert rng.getstate() == twin.getstate()


def test_positions_are_reproducible_across_calls() -> None:
    sequence = [company_name_at(i, seed=42) for i in range(50)]
    assert sequence == [company_name_at(i, seed=42) for i in range(50)]
    assert sequence != [company_name_at(i, seed=43) for i in range(50)]


@pytest.mark.parametrize("form", ENTITY_FORMS)
def test_no_duplicates_up_to_the_whole_name_space(form: str) -> None:
    count = company_name_count(form)
    drawn = [company_name_at(i, seed=2026, entity_form=form) for i in range(count)]
    assert len(set(drawn)) == count


def test_positions_outside_the_space_and_unknown_forms_raise() -> None:
    with pytest.raises(ValueError):
        company_name_at(-1, seed=1)
    with pytest.raises(ValueError):
        company_name_at(company_name_count("private"), seed=1)
    with pytest.raises(ValueError, match="Unknown entity form"):
        draw_company_name(random.Random(1), "cooperative")


def test_legacy_company_list_and_field_stay_unchanged() -> None:
    generator = TestDataGenerator(seed=42)
    assert generator.companies == LEGACY_COMPANIES
    assert generator.generate_company() in LEGACY_COMPANIES


def test_lists_avoid_the_legacy_brand_style_names() -> None:
    legacy_stems = {name.split()[0] for name in LEGACY_COMPANIES}
    assert not legacy_stems & set(names.PREFIXES)
