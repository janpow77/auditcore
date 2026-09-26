"""Invariants of docs/spezifikation.md as Hypothesis properties (synthetic data, no network)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_property_sources import bienici, zvg, zvg_lifecycle
from auditcore_property_sources._zvg_text import parse_money_amount
from auditcore_property_sources.robots import RobotsRules, is_allowed, parse_robots
from auditcore_property_sources.zvg_lifecycle import CaseState

EXAMPLES = settings(max_examples=150, deadline=None)
AMOUNTS = st.decimals(min_value=0, max_value=Decimal("999999999.99"), places=2)
NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
MOMENTS = st.integers(min_value=-20 * 24, max_value=20 * 24).map(lambda h: NOW + timedelta(hours=h))
FILES = st.sampled_from(["1 K 1/26", "1 K 2/26", "2 K 7/25", "3 K 4/24", ""])


def _german(value: Decimal, *, grouped: bool, decimals: int) -> str:
    text = f"{value:,.{decimals}f}" if grouped else f"{value:.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


@EXAMPLES
@given(AMOUNTS, st.booleans(), st.sampled_from([0, 1, 2]), st.sampled_from(["", " €", " EUR"]))
def test_i1_german_number_roundtrip(
    value: Decimal, grouped: bool, decimals: int, unit: str
) -> None:
    """I1: a German number (thousands points, decimal comma, ≤ 2 decimals) parses exactly.

    Exception (I2): an integer with exactly one thousands group (``12.345``) is
    ambiguous and gives ``None``.
    """
    rounded = round(value, decimals)
    text = _german(rounded, grouped=grouped, decimals=decimals) + unit
    one_group = grouped and decimals == 0 and 1000 <= rounded < 1_000_000
    assert zvg.parse_de_number(text) == (None if one_group else float(rounded))


@EXAMPLES
@given(st.integers(min_value=1, max_value=999), st.integers(min_value=0, max_value=999))
def test_i2_ambiguous_or_embedded_numbers_give_none(head: int, tail: int) -> None:
    """I2: ambiguous separators and text around the number are not guessed (PS-C10)."""
    assert zvg.parse_de_number(f"{head}.{tail:03d}") is None
    assert zvg.parse_de_number(f"{head},{tail:03d}") is None
    assert zvg.parse_de_number(f"ca. {head},5 m²") is None
    assert zvg.parse_de_number(f"Wohnfläche {head}") is None


@EXAMPLES
@given(AMOUNTS)
def test_i3_money_amounts_roundtrip(value: Decimal) -> None:
    """I3: portal amounts with thousands points, ``,-`` and currency parse to the amount."""
    exact = _german(value, grouped=True, decimals=2)
    assert parse_money_amount(exact + " €") == float(value)
    whole = _german(Decimal(int(value)), grouped=True, decimals=0)
    assert parse_money_amount(whole + ",-") == float(int(value))


CASES = st.lists(
    st.builds(
        CaseState,
        file_number=FILES,
        status=st.sampled_from(sorted(zvg_lifecycle.STATUSES)),
        last_seen_at=st.one_of(st.none(), MOMENTS),
        closed_at=st.none(),
        deleted=st.booleans(),
        dates=st.lists(MOMENTS, max_size=3).map(tuple),
    ),
    max_size=8,
)


@EXAMPLES
@given(CASES, st.lists(FILES, max_size=4))
def test_i4_mark_seen_only_touches_listed_cases(cases: list[CaseState], listed: list[str]) -> None:
    """I4: listed cases get ``last_seen_at = now``, everything else stays identical."""
    out = zvg_lifecycle.mark_seen(cases, listed, NOW)
    wanted = {n for n in listed if n}
    assert len(out) == len(cases)
    for before, after in zip(cases, out, strict=True):
        if before.file_number in wanted:
            assert after.last_seen_at == NOW
            assert (after.status, after.dates, after.deleted) == (
                before.status,
                before.dates,
                before.deleted,
            )
        else:
            assert after is before
    assert zvg_lifecycle.mark_seen(cases, [], NOW) == cases


@EXAMPLES
@given(CASES, st.integers(min_value=0, max_value=10))
def test_i5_close_vanished_closes_exactly_the_stale_open_cases(
    cases: list[CaseState], grace: int
) -> None:
    """I5: open, not deleted cases seen strictly before the grace limit close; idempotent."""
    out, closed = zvg_lifecycle.close_vanished(cases, NOW, grace)
    limit = NOW - timedelta(days=grace)
    changed = 0
    for before, after in zip(cases, out, strict=True):
        stale = (
            not before.deleted
            and before.status in zvg_lifecycle.OPEN
            and before.last_seen_at is not None
            and before.last_seen_at < limit
        )
        if stale:
            changed += 1
            assert after.status == zvg_lifecycle.closing_status(before, NOW)
            assert after.status in zvg_lifecycle.CLOSED and after.closed_at == NOW
        else:
            assert after is before
    assert closed == changed
    assert zvg_lifecycle.close_vanished(out, NOW, grace)[1] == 0


@EXAMPLES
@given(CASES, st.one_of(st.none(), MOMENTS))
def test_i6_reappear_reopens(cases: list[CaseState], termin: datetime | None) -> None:
    """I6: a listed case is open again: ``terminiert`` iff its date is now or later."""
    for case in cases:
        after = zvg_lifecycle.reappear(case, termin, NOW)
        assert after.status in zvg_lifecycle.OPEN and after.closed_at is None
        assert after.last_seen_at == NOW
        assert (after.status == "terminiert") == (termin is not None and termin >= NOW)
        assert after.dates == (() if termin is None else (termin,))


@EXAMPLES
@given(st.text(max_size=12), st.datetimes(max_value=datetime(2100, 1, 1)))
def test_i7_case_state_rejects_unknown_status_and_naive_times(status: str, naive: datetime) -> None:
    """I7: unknown statuses and naive datetimes are rejected, never interpreted."""
    if status not in zvg_lifecycle.STATUSES:
        with pytest.raises(ValueError):
            CaseState("1 K 1/26", status, None)
    with pytest.raises((ValueError, TypeError)):
        CaseState("1 K 1/26", "erfasst", naive)
    with pytest.raises(ValueError):
        zvg_lifecycle.close_vanished([], NOW, -1)


SEGMENT = st.text(alphabet="abcdefgh", min_size=1, max_size=4)
PATHS = st.lists(SEGMENT, min_size=1, max_size=3).map(lambda parts: "/" + "/".join(parts))


@EXAMPLES
@given(PATHS, PATHS, st.booleans())
def test_i8_robots_prefix_rules(disallowed: str, target: str, allow_sub: bool) -> None:
    """I8: plain rules are prefixes; the longest match wins, ``Allow`` wins ties; no rule allows."""
    text = f"User-agent: *\nDisallow: {disallowed}\n"
    rules = parse_robots(text)
    assert is_allowed(rules, "https://example.org" + target) is (not target.startswith(disallowed))
    assert is_allowed(parse_robots("User-agent: *\nDisallow:\n"), target) is True
    assert is_allowed(parse_robots(""), target) is True
    tie = parse_robots(f"User-agent: *\nDisallow: {disallowed}\nAllow: {disallowed}\n")
    assert is_allowed(tie, disallowed) is True
    if allow_sub:
        longer = parse_robots(f"User-agent: *\nDisallow: /\nAllow: {disallowed}\n")
        assert is_allowed(longer, disallowed) is True
    assert RobotsRules.from_list(rules.to_list()) == rules


NAMES = st.text(alphabet="ABCDEFGHIJKLMNOPabcdefghijklmnop ", max_size=20)
RENTS = st.one_of(st.none(), st.integers(min_value=0, max_value=5000))


@EXAMPLES
@given(NAMES, st.sampled_from(["individual", "agency"]), RENTS, RENTS)
def test_i9_bienici_private_names_and_rents(
    name: str, account: str, warm: int | None, charges: int | None
) -> None:
    """I9: ``minimal`` hides private offerers; cold rent = warm − charges if absent."""
    ad = {
        "id": "syn1",
        "accountType": account,
        "accountDisplayName": name,
        "price": warm,
        "charges": charges,
    }
    minimal = bienici.normalise(ad, advertiser_names="minimal")
    legacy = bienici.normalise(ad, advertiser_names="legacy")
    if account == "individual":
        assert minimal["gesellschaft"] == "Privatangebot"
        assert legacy["gesellschaft"] == (name.strip() or "Privatangebot")
    else:
        assert minimal["gesellschaft"] == legacy["gesellschaft"] == name.strip()
    if warm is not None and charges is not None:
        assert legacy["kaltmiete"] == round(float(warm) - float(charges), 2)
    assert bienici.normalise(ad) == legacy


@EXAMPLES
@given(st.dates(min_value=date(1971, 1, 1), max_value=date(9999, 12, 31)))
def test_i10_bienici_dates(day: date) -> None:
    """I10: ISO timestamps become ``TT.MM.JJJJ``; 1970-01-01 and non-text mean unknown."""
    assert bienici.date(f"{day.isoformat()}T11:54:43.211Z") == day.strftime("%d.%m.%Y")
    assert bienici.date("1970-01-01T00:00:00Z") is None
    assert bienici.date(None) is None


@EXAMPLES
@given(st.lists(st.sampled_from(sorted(zvg.COURT_NAMES)), max_size=5))
def test_i11_court_selection(courts: list[str]) -> None:
    """I11: court selections are explicit: named groups or a comma list, kept in order."""
    assert zvg.resolve_courts(", ".join(courts)) == courts
    assert set(zvg.resolve_courts("kern")) <= set(zvg.resolve_courts("all"))
    assert zvg.resolve_courts("all") == list(zvg.COURT_NAMES)
