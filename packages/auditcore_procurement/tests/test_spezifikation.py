"""Invariants of docs/spezifikation.md as Hypothesis properties (I1–I12)."""

from __future__ import annotations

import copy
from datetime import UTC, date, datetime
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_procurement import (
    NOTICE_FIELDS,
    inspect_notice,
    load_profile,
    normalize_notice,
    run_prechecks,
    validate_record,
)
from auditcore_procurement.prechecks import (
    FAIL,
    PASS,
    REVIEW_REQUIRED,
    WARNING,
    check_minimum_bids,
    check_required_documents,
    check_threshold,
    check_value_deviation,
    eu_period,
    eu_threshold,
)
from auditcore_procurement.ted import FIELD_ALIASES
from auditcore_procurement.ted_values import extract_amount

CURRENT = load_profile("procurement.hvtg", "2026.09.3")
LEGACY = load_profile("procurement.hvtg-legacy", "2026.09.1")
PROFILES = st.sampled_from([CURRENT, LEGACY, load_profile("procurement.hvtg", "2026.09.2")])
EXAMPLES = settings(max_examples=150, deadline=None)
RANK = {PASS: 0, WARNING: 1, REVIEW_REQUIRED: 2, FAIL: 3}
NOW = datetime(2026, 9, 26, 12, tzinfo=UTC)

TEXT = st.text(max_size=12)
SCALAR = (
    st.none() | TEXT | st.integers(-(10**9), 10**9) | st.floats(allow_nan=False) | st.booleans()
)
VALUE = st.recursive(
    SCALAR,
    lambda inner: (
        st.lists(inner, max_size=3)
        | st.dictionaries(
            st.sampled_from(["amount", "value", "currency", "deu", "eng", "x"]), inner, max_size=3
        )
    ),
    max_leaves=6,
)
KEYS = sorted({alias for aliases in FIELD_ALIASES.values() for alias in aliases})
NOTICES = st.dictionaries(st.sampled_from(KEYS), VALUE, max_size=8)
AMOUNTS = st.decimals(min_value=0, max_value=20_000_000, places=2, allow_nan=False)
DOC_TYPES = [
    "VERGABEVERMERK",
    "ANGEBOT",
    "ZUSCHLAG",
    "AUSSCHREIBUNG",
    "SUBMISSIONSPROTOKOLL",
    "VERTRAG",
]
DOCUMENTS = st.lists(
    st.sampled_from(DOC_TYPES).map(lambda t: {"procurement_doc_type": t}), max_size=10
)


@EXAMPLES
@given(NOTICES | VALUE, st.booleans())
def test_i1_normalized_records_use_only_contract_fields(notice: object, require: bool) -> None:
    """I1: records are None for non-objects, deterministic and use only NOTICE_FIELDS."""
    record = normalize_notice(notice, require_contractor=require)
    assert record == normalize_notice(notice, require_contractor=require)
    if not isinstance(notice, dict):
        assert record is None
    if record is not None:
        assert set(record) <= set(NOTICE_FIELDS)
        if require:
            assert record.get("contractor_name")


@EXAMPLES
@given(NOTICES)
def test_i2_contractor_filter_only_drops_records(notice: dict) -> None:
    """I2: require_contractor=True returns the same record or None, never a different one."""
    strict = normalize_notice(notice, require_contractor=True)
    loose = normalize_notice(notice, require_contractor=False)
    assert loose is not None
    assert strict is None or strict == loose


@EXAMPLES
@given(NOTICES)
def test_i3_normalized_records_pass_the_record_check_on_types_and_dates(notice: dict) -> None:
    """I3: numbers are numbers, dates are ISO dates, keys are known."""
    record = normalize_notice(notice, require_contractor=False)
    assert record is not None
    codes = {issue.code for issue in validate_record(record, require_contractor=False)}
    assert not codes & {"unknown_field", "not_numeric", "not_iso_date"}


@EXAMPLES
@given(
    st.integers(1, 999),
    st.integers(0, 999),
    st.integers(0, 99),
    st.sampled_from(["result-value-notice", "estimated-value-proc"]),
)
def test_i4_german_amounts_are_reported_not_altered(
    head: int, group: int, cents: int, key: str
) -> None:
    """I4: „1.234,56“ is a blocking ambiguous_amount; inspect_notice never changes the notice."""
    notice = {key: f"{head}.{group:03d},{cents:02d}", "winner-name": "Muster GmbH"}
    before = copy.deepcopy(notice)
    issues = inspect_notice(notice)
    assert notice == before
    assert any(i.code == "ambiguous_amount" and i.blocking for i in issues)


@EXAMPLES
@given(
    st.lists(
        st.integers(-(10**6), 10**6) | st.floats(-1e6, 1e6, allow_nan=False), min_size=1, max_size=5
    )
)
def test_i5_amount_lists_yield_the_largest_amount(values: list) -> None:
    """I5: of several amounts the largest is taken (source rule)."""
    amount, _ = extract_amount([{"amount": v, "currency": "EUR"} for v in values])
    assert amount == max(float(v) for v in values)


@EXAMPLES
@given(
    AMOUNTS,
    st.sampled_from(["Lieferung", "Dienstleistung", "Bauleistung"]),
    st.sampled_from(["central", "sub_central"]),
    st.integers(2014, 2027),
)
def test_i6_eu_threshold_applies_when_reached(
    value: Decimal, service: str, authority: str, year: int
) -> None:
    """I6: strict mode: value ≥ EU threshold of the period → above-EU tier, below → never."""
    day = date(year, 7, 1)
    category = "construction" if "Bau" in service else "supply_service"
    period = eu_period(CURRENT, day)
    threshold = eu_threshold(CURRENT, category, period, authority)
    row = check_threshold(
        CURRENT, value, service, None, "strict", reference_date=day, authority_type=authority
    )
    assert row["status"] == PASS
    if value >= Decimal(str(threshold.value)):
        assert row["calculated_tier"] == CURRENT.fallback_tier
    else:
        assert row["calculated_tier"] != CURRENT.fallback_tier


@EXAMPLES
@given(
    AMOUNTS,
    st.dates(min_value=date(1990, 1, 1), max_value=date(2013, 12, 31))
    | st.dates(min_value=date(2028, 1, 1), max_value=date(2100, 1, 1)),
)
def test_i7_no_period_means_review_not_fallback(value: Decimal, day: date) -> None:
    """I7: without a documented period (or without a date) strict mode asks for review."""
    for kwargs in ({"reference_date": day}, {}):
        row = check_threshold(
            CURRENT, value, "Lieferung", None, "strict", authority_type="central", **kwargs
        )
        assert row["status"] == REVIEW_REQUIRED


@EXAMPLES
@given(
    PROFILES,
    st.none() | AMOUNTS,
    st.none() | AMOUNTS,
    st.none() | AMOUNTS,
    st.sampled_from(["Lieferung", "Bauleistung"]),
    st.none()
    | st.sampled_from(["Direktvergabe", "Verhandlungsvergabe", "EU-Verfahren", "Sonstiges"]),
    st.none() | st.sampled_from(["BELOW_1K", "BELOW_25K", "BELOW_EU", "ABOVE_EU", "X"]),
    DOCUMENTS,
    st.sampled_from(["legacy", "strict"]),
    st.none() | st.dates(min_value=date(2014, 1, 1), max_value=date(2027, 12, 31)),
)
def test_i8_overall_status_is_the_worst_and_runs_are_reproducible(
    profile, estimated, contract, invoice, service, procedure, tier, docs, mode, day
) -> None:
    """I8: overall = worst check (FAIL > REVIEW_REQUIRED > WARNING > PASS); reproducible."""
    kwargs = {"mode": mode, "now": NOW, "reference_date": day, "authority_type": "sub_central"}
    report = run_prechecks(
        profile, estimated, contract, invoice, service, procedure, tier, docs, **kwargs
    )
    again = run_prechecks(
        profile, estimated, contract, invoice, service, procedure, tier, docs, **kwargs
    )
    assert report == again
    statuses = [row["status"] for row in report["checks"]]
    worst = max(statuses, key=lambda s: RANK.get(s, 0))
    expected = worst if RANK.get(worst, 0) else PASS
    assert report["overall_status"] == expected
    assert report["timestamp"] == NOW.isoformat()
    if mode == "strict":
        assert report["profile"] == profile.reference
    else:
        assert REVIEW_REQUIRED not in statuses


@EXAMPLES
@given(st.sampled_from(sorted(CURRENT.required_documents)), DOCUMENTS)
def test_i9_required_documents_count_multiplicity(procedure: str, docs: list) -> None:
    """I9: PASS exactly when every required type is present at least as often as required."""
    row = check_required_documents(CURRENT, procedure, docs, "strict")
    required = CURRENT.required_documents[procedure]
    present = [d["procurement_doc_type"] for d in docs]
    complete = all(present.count(t) >= required.count(t) for t in required)
    assert (row["status"] == PASS) == complete
    assert row["status"] in (PASS, FAIL)


@EXAMPLES
@given(
    st.sampled_from(["BELOW_1K", "BELOW_25K", "BELOW_EU", "ABOVE_EU"]),
    st.integers(0, 8),
    st.sampled_from(["Lieferung", "Bauleistung"]),
)
def test_i10_minimum_bids(tier: str, bids: int, service: str) -> None:
    """I10: PASS if enough bids, FAIL with none, WARNING with some but too few."""
    docs = [{"procurement_doc_type": "ANGEBOT"}] * bids
    row = check_minimum_bids(CURRENT, tier, service, docs, "strict")
    minimum = row["min_required"]
    expected = PASS if bids >= minimum else (FAIL if bids == 0 else WARNING)
    assert row["status"] == expected


@EXAMPLES
@given(AMOUNTS.filter(lambda v: v > 0), AMOUNTS, AMOUNTS)
def test_i11_value_deviation_is_monotone(contract: Decimal, a: Decimal, b: Decimal) -> None:
    """I11: a larger deviation from the contract value never yields a milder status."""
    near, far = sorted((a, b), key=lambda v: abs(v - contract))
    first = check_value_deviation(CURRENT, contract, near)["status"]
    second = check_value_deviation(CURRENT, contract, far)["status"]
    assert RANK[first] <= RANK[second]
    assert check_value_deviation(CURRENT, Decimal(0), a)["status"] == WARNING


@EXAMPLES
@given(st.sampled_from(["BELOW_1K", "BELOW_25K", "BELOW_EU", "ABOVE_EU", "UNBEKANNT"]), DOCUMENTS)
def test_i12_unknown_tier_is_not_checked_in_strict_mode(tier: str, docs: list) -> None:
    """I12: strict never passes a procedure for a tier the profile does not define (P-C01)."""
    report = run_prechecks(
        CURRENT, None, None, None, "Lieferung", "EU-Verfahren", tier, docs, mode="strict", now=NOW
    )
    procedure = next(r for r in report["checks"] if r["check_id"] == "precheck_procedure_threshold")
    if tier == "UNBEKANNT":
        assert procedure["status"] == "NOT_CHECKED"
    legacy = run_prechecks(
        LEGACY,
        None,
        None,
        None,
        "Lieferung",
        "EU-Verfahren",
        "UNBEKANNT",
        docs,
        mode="legacy",
        now=NOW,
    )
    legacy_row = next(
        r for r in legacy["checks"] if r["check_id"] == "precheck_procedure_threshold"
    )
    assert legacy_row["status"] == PASS
