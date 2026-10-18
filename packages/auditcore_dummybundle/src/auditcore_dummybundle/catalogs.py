"""Catalogues: lists of the field generator plus neutral labels of this package.

Cities, postal codes, first and last names, purpose phrases and company names
come from ``auditcore_dummygenerator``; company names from its modular name
space (prefix, business area, name suffix, legal form). They are generic
sample names; any resemblance to existing companies is coincidental and not
intended. Street names and neutral labels come from
``data/catalogs.json``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from importlib.resources import files
from random import Random
from typing import cast

from auditcore_dummygenerator import TestDataGenerator, company_name_at, company_name_count

COUNTRIES = ("DE", "AT")


@dataclass(frozen=True)
class CostCategory:
    """Neutral cost category; ``staff`` marks personnel costs."""

    name: str
    weight: int
    staff: bool


@dataclass(frozen=True)
class Catalogs:
    """All catalogue data, loaded once."""

    companies: tuple[str, ...]
    streets: tuple[str, ...]
    roles: tuple[str, ...]
    cost_categories: tuple[CostCategory, ...]
    ineligible_cost_category: str
    programme_groups: tuple[tuple[str, str], ...]
    operation_titles: tuple[str, ...]
    nuts3: dict[str, str]
    country_names: dict[str, str]
    vat_rates: dict[str, Decimal]
    award_types: tuple[str, ...]
    placeholders: dict[str, str]
    cities: dict[str, tuple[tuple[str, str], ...]]
    first_names: dict[str, tuple[str, ...]]
    last_names: dict[str, tuple[str, ...]]
    purposes: tuple[str, ...]


def _raw() -> dict[str, object]:
    path = files("auditcore_dummybundle").joinpath("data/catalogs.json")
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def _texts(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in cast(list[object], value))


def _text_map(value: object) -> dict[str, str]:
    return {str(key): str(item) for key, item in cast(dict[str, object], value).items()}


@cache
def catalogs() -> Catalogs:
    """Catalogue data of this package plus the DE/AT lists of the field generator."""
    raw = _raw()
    legacy = TestDataGenerator(seed=0)
    categories = cast(list[dict[str, object]], raw["cost_categories"])
    return Catalogs(
        companies=tuple(legacy.companies),
        streets=_texts(raw["streets"]),
        roles=_texts(raw["roles"]),
        cost_categories=tuple(
            CostCategory(str(c["name"]), int(str(c["weight"])), bool(c["staff"]))
            for c in categories
        ),
        ineligible_cost_category=str(raw["ineligible_cost_category"]),
        programme_groups=tuple(
            (str(code), str(name))
            for code, name in cast(list[list[object]], raw["programme_groups"])
        ),
        operation_titles=_texts(raw["operation_titles"]),
        nuts3=_text_map(raw["nuts3"]),
        country_names=_text_map(raw["country_names"]),
        vat_rates={k: Decimal(v) for k, v in _text_map(raw["vat_rates"]).items()},
        award_types=_texts(raw["award_types"]),
        placeholders=_text_map(raw["placeholders"]),
        cities={"DE": tuple(legacy.cities_de), "AT": tuple(legacy.cities_at)},
        first_names={"DE": tuple(legacy.first_names_de), "AT": tuple(legacy.first_names_at)},
        last_names={"DE": tuple(legacy.last_names_de), "AT": tuple(legacy.last_names_at)},
        purposes=tuple(legacy.purposes),
    )


def weighted_pick(rng: Random, items: tuple[tuple[str, int], ...]) -> str:
    """Draw one name from ``(name, weight)`` pairs with integer weights."""
    total = sum(weight for _, weight in items)
    if total <= 0:
        raise ValueError("weights must have a positive sum")
    position = rng.randrange(total)
    for name, weight in items:
        position -= weight
        if position < 0:
            return name
    return items[-1][0]


def country_of(rng: Random, countries: str) -> str:
    """``DE`` or ``AT``; ``DE+AT`` draws one of both."""
    return COUNTRIES[rng.randrange(2)] if countries == "DE+AT" else countries


def company_name(seed: int, position: int, entity_form: str = "private") -> str:
    """Company name number ``position`` of the seeded name sequence of the field generator.

    Different positions give different names until the name space of the
    entity form (``private``, ``nonprofit``, ``public``) is used up; beyond
    that the sequence starts again. The legal form matches the entity form.
    """
    count = company_name_count(entity_form)
    return company_name_at(position % count, seed=seed, entity_form=entity_form)


def address(rng: Random, country: str) -> tuple[str, str, str]:
    """Invented street with house number plus a matching postal code and city."""
    data = catalogs()
    street = data.streets[rng.randrange(len(data.streets))]
    city, postal_code = data.cities[country][rng.randrange(len(data.cities[country]))]
    return f"{street} {rng.randrange(1, 150)}", postal_code, city


def role_name(rng: Random) -> str:
    """Role label instead of a personal name, e.g. ``Sachbearbeitung 3``."""
    data = catalogs()
    return f"{data.roles[rng.randrange(len(data.roles))]} {rng.randrange(1, 10)}"


def person_name(rng: Random, country: str) -> str:
    """First and last name from the DE/AT catalogues of the field generator."""
    data = catalogs()
    first = data.first_names[country]
    last = data.last_names[country]
    return f"{first[rng.randrange(len(first))]} {last[rng.randrange(len(last))]}"


def purpose_text(rng: Random, low: int = 1, high: int = 2) -> str:
    """One or more purpose phrases of the field generator, joined by commas."""
    data = catalogs()
    count = rng.randrange(low, high + 1)
    return ", ".join(data.purposes[rng.randrange(len(data.purposes))] for _ in range(count))
