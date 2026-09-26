"""Tariff selection: legacy equivalence on released records plus explicit exclusions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from replay import decode, load_fixture

from auditcore_price_analysis import (
    ReleaseStatus,
    Tariff,
    comparison_profile_from_dict,
    legacy,
    load_comparison_profile,
    select_tariff,
)

CP = load_comparison_profile("regulierung.hpp.vergleich", "2026.09.1")
CASES = [c for c in load_fixture()["cases"] if c["group"] in ("auswahl", "wasser-auswahl")]
#: PA-L17: legacy float |4.01 - 4.0| = 0.00999… lies inside the 0.01 tolerance, exactly it does not
Q3_DIVERGES = {"wasser-auswahl-005": ("q10-neu", "nicht_verfuegbar_fuer_q3", False)}


def as_tariff(row: Any, preferred: set[int]) -> Tariff:
    q3 = getattr(row, "zaehlergroesse_q3", None)
    return Tariff(
        kind="wasser",
        components={},
        valid_from=row.stichtag,
        release=ReleaseStatus.FREIGEGEBEN,
        q3=None if q3 is None else Decimal(repr(q3)),
        variant_id=getattr(row, "variant_id", None),
        row_id=getattr(row, "id", None),
        standard_variant=getattr(row, "variant_id", None) in preferred,
        source_ref=row.ref,
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_same_choice_as_legacy_for_released_records(case: dict[str, Any]) -> None:
    args = decode(case["args"])
    rows = args[0]
    if case["function"] == "waehle_preis_deterministisch":
        preferred = args[1] if len(args) > 1 and args[1] else set()
        chosen, ambiguous = case["ok"]["$tuple"]
        status = "ok"
        q3 = None
    else:
        preferred = args[2] if len(args) > 2 and args[2] else set()
        chosen, status, ambiguous = case["ok"]["$tuple"]
        q3 = args[1]
    if case["id"] in Q3_DIVERGES:
        chosen, status, ambiguous = Q3_DIVERGES[case["id"]]
        chosen = {"$ref": chosen}
    tariffs = [as_tariff(r, preferred) for r in rows]
    selection = select_tariff(tariffs, stichtag=date(2030, 1, 1), profile=CP, q3=q3)
    if chosen is None:
        assert selection.tariff is None and selection.datenstatus == "kein_tarif"
        return
    assert selection.tariff is not None and selection.tariff.source_ref == chosen["$ref"]
    assert selection.datenstatus == status and selection.ambiguous == ambiguous


def tariff(ref: str, day: str, **kwargs: Any) -> Tariff:
    return Tariff(
        kind="nahwaerme",
        components={},
        valid_from=date.fromisoformat(day),
        source_ref=ref,
        **kwargs,
    )


def test_release_and_date_exclusions_are_listed() -> None:
    rows = [
        tariff("offen", "2025-01-01", release=ReleaseStatus.AUSSTEHEND),
        tariff("abgelehnt", "2025-02-01", release=ReleaseStatus.ABGELEHNT),
        tariff("zukunft", "2026-01-01", release=ReleaseStatus.FREIGEGEBEN),
        tariff("gueltig", "2024-01-01", release=ReleaseStatus.FREIGEGEBEN),
        Tariff(kind="nahwaerme", components={}, release=ReleaseStatus.FREIGEGEBEN),
    ]
    selection = select_tariff(rows, stichtag="2025-06-01", profile=CP)
    assert selection.tariff is rows[3]
    assert selection.excluded == (
        (0, "freigabe:ausstehend"),
        (1, "freigabe:abgelehnt"),
        (2, "gueltig_erst_spaeter"),
        (4, "ohne_gueltigkeitsbeginn"),
    )
    assert selection.to_dict()["profile"]["profile_id"] == "regulierung.hpp.vergleich"


def test_no_released_tariff_means_none_not_a_pending_one() -> None:
    rows = [tariff("offen", "2025-01-01", release=ReleaseStatus.AUSSTEHEND)]
    selection = select_tariff(rows, stichtag="2025-06-01", profile=CP)
    assert selection.tariff is None and selection.datenstatus == "kein_tarif"
    assert rows[0].release is ReleaseStatus.AUSSTEHEND


def test_pa_h04_valid_to_only_with_profile_rule() -> None:
    rows = [
        tariff(
            "abgelaufen",
            "2025-01-01",
            release=ReleaseStatus.FREIGEGEBEN,
            valid_to=date(2025, 3, 31),
        ),
        tariff("aelter", "2024-01-01", release=ReleaseStatus.FREIGEGEBEN),
    ]
    assert select_tariff(rows, stichtag="2025-06-01", profile=CP).tariff is rows[0]
    raw = {**CP.raw, "selection": {**CP.raw["selection"], "respect_valid_to": True}}
    strict = comparison_profile_from_dict(raw)
    selection = select_tariff(rows, stichtag="2025-06-01", profile=strict)
    assert selection.tariff is rows[1] and selection.excluded == ((0, "abgelaufen"),)


def test_q3_tolerance_is_exact_decimal() -> None:
    rows = [
        Tariff(
            kind="wasser",
            components={},
            valid_from=date(2025, 1, 1),
            release=ReleaseStatus.FREIGEGEBEN,
            q3=Decimal("4.0"),
            source_ref="q4",
        ),
    ]
    assert select_tariff(rows, stichtag="2025-06-01", profile=CP, q3="4.0099").datenstatus == "ok"
    fallback = select_tariff(rows, stichtag="2025-06-01", profile=CP, q3="4.01")
    assert fallback.datenstatus == "nicht_verfuegbar_fuer_q3" and fallback.tariff is rows[0]


def test_legacy_selection_is_reexported_unchanged() -> None:
    assert legacy.DATENSTATUS_KEIN_Q3_TARIF == "nicht_verfuegbar_fuer_q3"
