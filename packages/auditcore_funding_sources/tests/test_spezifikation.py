"""Invariants of docs/spezifikation.md as Hypothesis properties (synthetic data, no network)."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_funding_sources import designer, flowsearch, workshop
from auditcore_funding_sources.cumulation import calculate, window_start
from auditcore_funding_sources.deminimis import authority_level
from auditcore_funding_sources.snapshot import plan_snapshot
from auditcore_funding_sources.workshop import SnapshotContext, compute_record_hash

EXAMPLES = settings(max_examples=120, deadline=None)
DAYS = st.dates(min_value=date(2015, 1, 1), max_value=date(2030, 12, 31))
REFERENCES = st.sampled_from(["B-1", "B-2", "B-3"])
AMOUNT = st.one_of(
    st.decimals(min_value=-1000, max_value=400_000, places=2).map(str),
    st.none(),
    st.just("kein Betrag"),
)
AWARD = st.fixed_dictionaries(
    {
        "referenceNumber": st.text(alphabet="AZ09", min_size=1, max_size=4),
        "beneficiaryReferenceNumber": REFERENCES,
        "grantingDate": st.one_of(DAYS.map(date.isoformat), st.none(), st.just("unbekannt")),
        "amountEur": AMOUNT,
        "deMinimisType": st.sampled_from(["GENERAL", "GENERAL", "AGRI"]),
    }
)
STATUSES = {"considered", "excluded", "unclear"}


@EXAMPLES
@given(st.lists(AWARD, max_size=8), DAYS, st.one_of(st.none(), st.lists(REFERENCES, max_size=2)))
def test_i1_every_award_is_classified_and_summed_once(
    awards: list[dict[str, Any]], day: date, group: list[str] | None
) -> None:
    """I1: one classification per award; the sum is exactly the considered amounts; no verdict."""
    result = calculate(awards, reference_date=day, undertaking_references=group)
    assert len(result.awards) == len(awards)
    assert {a.status for a in result.awards} <= STATUSES
    considered = [a.amount_eur for a in result.awards if a.status == "considered"]
    assert result.sum_considered_eur == sum(considered, Decimal("0"))
    assert result.sum_considered_eur == sum(result.sum_per_type_eur.values(), Decimal("0"))
    assert result.decision is None and result.to_dict()["decision"] is None
    assert result.complete == all(a.status != "unclear" for a in result.awards)


@EXAMPLES
@given(st.lists(AWARD, max_size=8), DAYS)
def test_i2_ceiling_comparison_only_when_clear(awards: list[dict[str, Any]], day: date) -> None:
    """I2: the ceiling is compared only for clear, purely general awards in the window."""
    result = calculate(awards, reference_date=day)
    if result.reasons_without_comparison:
        assert result.ceiling_eur is None and result.exceeds_ceiling is None
        assert result.arithmetic_difference_eur is None
    else:
        assert result.ceiling_eur == Decimal("300000")
        assert set(result.sum_per_type_eur) == {"GENERAL"} and result.complete
        assert result.exceeds_ceiling == (result.sum_considered_eur > result.ceiling_eur)
        assert result.arithmetic_difference_eur == result.ceiling_eur - result.sum_considered_eur


@EXAMPLES
@given(DAYS)
def test_i3_window_is_three_calendar_years_with_both_edges(day: date) -> None:
    """I3: the window runs from the same day three years back to the reference date inclusive."""
    start = window_start(day, 3)
    assert start.year == day.year - 3
    assert (start.month, start.day) == (
        (2, 28) if (day.month, day.day) == (2, 29) else (day.month, day.day)
    )
    edge = [
        {
            "referenceNumber": "E1",
            "beneficiaryReferenceNumber": "B-1",
            "grantingDate": start.isoformat(),
            "amountEur": "1",
            "deMinimisType": "GENERAL",
        },
        {
            "referenceNumber": "E2",
            "beneficiaryReferenceNumber": "B-1",
            "grantingDate": day.isoformat(),
            "amountEur": "1",
            "deMinimisType": "GENERAL",
        },
        {
            "referenceNumber": "E3",
            "beneficiaryReferenceNumber": "B-1",
            "grantingDate": (start - timedelta(days=1)).isoformat(),
            "amountEur": "1",
            "deMinimisType": "GENERAL",
        },
    ]
    statuses = [a.status for a in calculate(edge, reference_date=day).awards]
    assert statuses == ["considered", "considered", "excluded"]


@EXAMPLES
@given(
    st.lists(AWARD, max_size=8),
    DAYS,
    st.lists(REFERENCES, min_size=1, max_size=3),
    st.randoms(use_true_random=False),
)
def test_i4_undertaking_and_order_do_not_change_the_sum(
    awards: list[dict[str, Any]], day: date, group: list[str], rnd: Any
) -> None:
    """I4: other references are excluded; order of records and references is irrelevant."""
    result = calculate(awards, reference_date=day, undertaking_references=group)
    for award in result.awards:
        if award.beneficiary_reference not in group:
            assert award.status == "excluded"
    shuffled, references = list(awards), list(group)
    rnd.shuffle(shuffled)
    rnd.shuffle(references)
    again = calculate(shuffled, reference_date=day, undertaking_references=references)
    assert again.sum_considered_eur == result.sum_considered_eur
    assert (
        again.undertaking_references == result.undertaking_references == tuple(sorted(set(group)))
    )


@EXAMPLES
@given(DAYS, st.sampled_from([None, "", "unlesbar", "-5.00"]), st.booleans())
def test_i5_unclear_awards_are_never_guessed(day: date, amount: str | None, no_date: bool) -> None:
    """I5: missing date, unreadable or negative amount: unclear award, incomplete result."""
    award = {
        "referenceNumber": "U1",
        "beneficiaryReferenceNumber": "B-1",
        "grantingDate": None if no_date else day.isoformat(),
        "amountEur": amount,
        "deMinimisType": "GENERAL",
    }
    result = calculate([award], reference_date=day)
    assert result.awards[0].status == "unclear"
    assert not result.complete and result.exceeds_ceiling is None
    with pytest.raises(TypeError):
        calculate([award], reference_date=day.isoformat())  # type: ignore[arg-type]


TEXT = st.text(max_size=20)
ROW = st.fixed_dictionaries({f: TEXT for f in workshop.profile()["hash_fields"]})


@EXAMPLES
@given(ROW, st.text(min_size=1, max_size=8), TEXT)
def test_i6_record_identity_is_normalised_and_stable(
    row: dict[str, str], source: str, extra: str
) -> None:
    """I6: 32-hex identity over the hash fields; case, NFKC and spacing do not matter."""
    identity = compute_record_hash(row, source)
    assert len(identity) == 32 and int(identity, 16) >= 0
    variant = {k: f"  {v.upper()}  " for k, v in row.items()}
    if all(v.upper().casefold() == v.casefold() for v in row.values()):
        assert compute_record_hash(variant, source) == identity
    assert compute_record_hash({**row, "unrelated": extra}, source) == identity


NAMED = st.lists(
    st.fixed_dictionaries(
        {
            "beneficiary_name": st.sampled_from(["Alpha", "Beta", "Gamma", "Delta"]),
            "project_name": st.sampled_from(["P1", "P2"]),
        }
    ),
    min_size=1,
    max_size=6,
)
CONTEXT = SnapshotContext(
    "syn.source", bundesland="XX", fonds="EFRE", periode="2021-2027", country_code="DE"
)


@EXAMPLES
@given(NAMED, st.sampled_from(workshop.MODES), st.lists(st.sampled_from(["s1", "s2"]), max_size=2))
def test_i7_snapshot_plan_modes(rows: list[dict[str, str]], mode: str, stored: list[str]) -> None:
    """I7: force/snapshot replace the inventory, smart/full-refresh keep it; identities unique."""
    plan = plan_snapshot(rows, CONTEXT, mode=mode, stored_identities=stored)
    inserted = [identity for identity, _ in plan.inserts]
    assert len(inserted) == len(set(inserted))
    result = plan.resulting_identities(stored)
    if mode in ("force", "snapshot"):
        assert plan.delete_all_first and plan.deleted_count == len(set(stored))
        assert result == sorted(set(inserted))
    else:
        assert set(stored) <= set(result) and plan.deleted_count == 0
    assert plan.records_seen == len(rows)
    assert plan.status == "ok"


def test_i7_snapshot_without_context_is_rejected() -> None:
    """I7: a snapshot without fund, period or country must not replace an inventory."""
    from auditcore_funding_sources.errors import SnapshotRejected

    with pytest.raises(SnapshotRejected):
        plan_snapshot(
            [{"beneficiary_name": "Alpha"}],
            SnapshotContext("syn"),
            mode="snapshot",
            stored_identities=["s1"],
        )


AMOUNTS = st.decimals(min_value=0, max_value=Decimal("99999999.99"), places=2)


def _german(value: Decimal) -> str:
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


@EXAMPLES
@given(AMOUNTS)
def test_i8_amount_variants_stay_separate(value: Decimal) -> None:
    """I8: all three variants read German amounts; they differ exactly as documented."""
    text = _german(value) + " €"
    assert workshop.parse_amount(text) == value
    assert designer.parse_amount(text) == value
    assert flowsearch.parse_amount(text) == float(value)
    whole = f"{int(value):,}".replace(",", ".")
    if whole.count(".") >= 2:
        assert workshop.parse_amount(whole) is None  # FS-W05
        assert designer.parse_amount(whole) == Decimal(int(value))


@EXAMPLES
@given(st.one_of(st.none(), st.just(""), st.text(alphabet="xyz", min_size=1, max_size=5)))
def test_i9_flowsearch_defaults_and_md5_identity(value: str | None) -> None:
    """I9: flowsearch reads missing or unreadable amounts as 0.0; its identity is 16-hex MD5."""
    assert flowsearch.parse_amount(value) == 0.0
    identity = flowsearch.project_id("k", "Name", "Titel", date(2024, 1, 1))
    assert identity == flowsearch.project_id("k", "Name", "Titel", date(2024, 1, 1))
    assert len(identity) == 16 and int(identity, 16) >= 0
    if value:
        assert designer.parse_amount(value) is None  # a 0 would be a claim


LEVELS = {
    "Bund",
    "unbestimmt",
    "Baden-Württemberg",
    "Bayern",
    "Berlin",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Hessen",
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Nordrhein-Westfalen",
    "Rheinland-Pfalz",
    "Saarland",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Thüringen",
}


@EXAMPLES
@given(st.one_of(st.none(), st.text(max_size=40)))
def test_i10_authority_level_is_closed(name: str | None) -> None:
    """I10: an authority maps to the federal level, a federal state or „unbestimmt“."""
    assert authority_level(name) in LEVELS
