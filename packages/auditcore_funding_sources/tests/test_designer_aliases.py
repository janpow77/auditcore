"""Deprecated source names of the designer profile (renamed in 0.1.2)."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Any

import pytest

from auditcore_funding_sources import designer

ALIASES = {
    "parse_betrag": ("parse_amount", ["1.234.567", "weniger als 5.000 EUR", "–", 12.5, None]),
    "parse_satz": ("parse_rate", ["80 %", "0,5", "150", "", None]),
    "parse_datum": ("parse_date", ["31.12.24", "2024-03-15T10:00:00", "kein Datum", None]),
}


@pytest.mark.parametrize("old", sorted(ALIASES))
def test_old_name_is_the_new_function_and_warns(old: str) -> None:
    new, samples = ALIASES[old]
    with pytest.warns(DeprecationWarning, match=f"designer.{old} ist veraltet; stattdessen {new}"):
        alias: Callable[[Any], Any] = getattr(designer, old)
    assert alias is getattr(designer, new)
    for value in samples:
        assert alias(value) == getattr(designer, new)(value)


def test_from_import_of_old_name_warns() -> None:
    with pytest.warns(DeprecationWarning):
        from auditcore_funding_sources.designer import parse_betrag
    assert parse_betrag is designer.parse_amount


def test_new_names_do_not_warn_and_unknown_names_fail() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert designer.parse_rate("80 %") == designer.parse_rate("80")
    with pytest.raises(AttributeError):
        designer.parse_unbekannt  # noqa: B018
