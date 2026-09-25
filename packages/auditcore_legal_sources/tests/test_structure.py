"""Structure of the 0.1.1 refactoring: split legacy package and table-driven period rules."""

from __future__ import annotations

import importlib

import pytest

from auditcore_legal_sources import legacy, normalize
from auditcore_legal_sources.legacy import dip as legacy_dip


def test_legacy_names_stay_importable_from_the_package() -> None:
    for name in legacy.__all__:
        assert getattr(legacy, name) is not None
    for module in ("common", "dip", "eurlex", "feeds"):
        assert importlib.import_module(f"auditcore_legal_sources.legacy.{module}")


@pytest.mark.parametrize(
    ("text", "published", "expected"),
    [
        ("VO 2081/93 und 1303/2013", None, "2000-2006"),
        ("Programm 1994-1999 nach 2021/1060", None, "1994-1999"),
        ("Dachverordnung", "1999", "2021-2027"),
        ("ohne Treffer", "1999-05-01", "1994-1999"),
        ("ohne Treffer", "1993", None),
        (None, "kein Jahr", None),
        ("", "2014", "2014-2020"),
        (None, None, None),
    ],
)
def test_designer_period_tables_keep_the_rule_order(
    text: str | None, published: str | None, expected: str | None
) -> None:
    assert normalize.funding_period_designer(text, published) == expected


def test_legacy_dip_helpers_swallow_like_the_source() -> None:
    assert legacy_dip._legacy_funding_period(12345) == "2021-2027"
    assert legacy_dip._legacy_funding_period("1999-01-01") == "2014-2020"
    assert legacy_dip._legacy_pdf_url({}, "kein-schrägstrich", "20") is None
    assert legacy_dip._legacy_fund("Sozialfonds") == "ESF+"
