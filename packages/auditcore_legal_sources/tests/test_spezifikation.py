"""Invariants of docs/spezifikation.md as Hypothesis properties (synthetic data, no network)."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_legal_sources import ConfigurationError, ParseError, SourceProfile, load_profile
from auditcore_legal_sources.dip import (
    DipPage,
    auth_header_value,
    drucksache_query,
    normalize_page,
)
from auditcore_legal_sources.eurlex import celex_document_type, merge_rows, update_query
from auditcore_legal_sources.feeds import normalize_entry
from auditcore_legal_sources.model import LegalDocument
from auditcore_legal_sources.normalize import (
    deduplicate,
    funding_period_auditdatabase,
    funding_period_designer,
    is_relevant,
    parse_publication_date,
)

ESI = load_profile("auditdatabase.esi", "2026.09.1")
DESIGNER = load_profile("audit_designer.vp_ai", "2026.09.1")
DATES = st.dates(min_value=date(1000, 1, 1), max_value=date(9999, 12, 31))
TEXT = st.text(max_size=40)
ASCII = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -/", max_size=30
)
PERIODS = {"2021-2027", "2014-2020", "2007-2013", "2000-2006", "1994-1999"}
EXAMPLES = settings(max_examples=150, deadline=None)


@EXAMPLES
@given(DATES)
def test_i1_publication_date_roundtrip(day: date) -> None:
    """I1: every supported spelling of a calendar date parses back with its precision."""
    assert parse_publication_date(day.isoformat()) == (day, "day")
    assert parse_publication_date(f"{day.isoformat()}T12:00:00Z") == (day, "day")
    assert parse_publication_date(f"{day.day}.{day.month}.{day.year:04d}") == (day, "day")
    month = f"{day.year:04d}-{day.month:02d}"
    assert parse_publication_date(month) == (day.replace(day=1), "month")
    assert parse_publication_date(f"{day.year:04d}") == (date(day.year, 1, 1), "year")


@EXAMPLES
@given(st.one_of(TEXT, st.none(), st.integers(), st.floats()))
def test_i2_publication_date_never_guesses(value: object) -> None:
    """I2: any other input is (None, None); invalid calendar dates are not repaired."""
    parsed, precision = parse_publication_date(value)
    assert (parsed is None) == (precision is None)
    assert precision in (None, "day", "month", "year")
    if parsed is not None:
        assert isinstance(value, str)
    assert parse_publication_date("2023-02-30") == (None, None)
    assert parse_publication_date("31.04.2024") == (None, None)


def _document(source: str, external: str, title: str, content: str | None) -> LegalDocument:
    return LegalDocument(source, external, title, None, None, None, None, content=content)


@EXAMPLES
@given(ASCII, ASCII, TEXT, st.one_of(st.none(), TEXT), st.one_of(st.none(), TEXT))
def test_i3_identity_and_content_hash(
    source: str, external: str, title: str, content: str | None, abstract: str | None
) -> None:
    """I3: identity is ``source_id:external_id``; hash over content, else abstract, else title."""
    document = LegalDocument(
        source, external, title, None, None, None, None, content=content, abstract=abstract
    )
    assert document.identity == f"{source}:{external}"
    expected = content or abstract or title
    assert document.content_hash == hashlib.sha256(expected.encode("utf-8")).hexdigest()
    assert json.loads(json.dumps(document.to_dict())) == document.to_dict()


@EXAMPLES
@given(st.lists(st.tuples(st.sampled_from("abc"), st.sampled_from("xyz"), TEXT), max_size=12))
def test_i4_deduplicate_first_occurrence_wins(rows: list[tuple[str, str, str]]) -> None:
    """I4: one document per identity, the first one, order kept; idempotent."""
    documents = [_document(s, e, t, None) for s, e, t in rows]
    kept, dropped = deduplicate(documents)
    identities = [d.identity for d in kept]
    assert len(identities) == len(set(identities))
    assert len(kept) + len(dropped) == len(documents)
    for document in kept:
        assert document is next(d for d in documents if d.identity == document.identity)
    assert deduplicate(kept) == (kept, [])


ITEM = st.fixed_dictionaries(
    {},
    optional={
        "id": st.one_of(st.integers(min_value=0), ASCII, st.none(), st.booleans()),
        "titel": st.one_of(TEXT, st.none(), st.integers()),
        "dokumentnummer": st.from_regex(r"\A\d{1,2}/\d{1,5}\Z"),
        "datum": st.one_of(DATES.map(date.isoformat), TEXT),
    },
)


@EXAMPLES
@given(st.lists(ITEM, max_size=8), st.sampled_from([ESI, DESIGNER]))
def test_i5_dip_items_are_documents_or_located_errors(
    items: list[dict[str, object]], profile: SourceProfile
) -> None:
    """I5: each DIP item becomes a document or a ParseError with its index; nothing is dropped."""
    documents, errors = normalize_page(DipPage(tuple(items), None, None), profile)
    assert len(documents) + len(errors) == len(items)
    for error in errors:
        assert error.location.startswith("documents[")
    for document in documents:
        assert document.title.strip()
        assert document.external_id.startswith("dip_") and len(document.external_id) > 4
        assert document.profile == profile.reference
        heuristic = document.classification.get("heuristic")
        assert heuristic is (True if profile.dip_classification == "auditdatabase.dip" else None)


@EXAMPLES
@given(TEXT, st.one_of(st.none(), ASCII), st.one_of(st.none(), DATES))
def test_i6_dip_credentials_never_in_the_query(
    key: str, cursor: str | None, since: date | None
) -> None:
    """I6: the API key only goes into the header; empty or multi-line keys are rejected."""
    if not key.strip() or "\r" in key or "\n" in key:
        with pytest.raises(ConfigurationError):
            auth_header_value(key)
    else:
        assert auth_header_value(key) == f"ApiKey {key.strip()}"
    params = drucksache_query(ESI, "EFRE", cursor=cursor, updated_since=since)
    assert set(params) <= {"format", "num", "f.titel", "cursor", "f.aktualisiert.start"}
    assert "apikey" not in {k.lower() for k in params}


@EXAMPLES
@given(ASCII.filter(str.strip), TEXT, TEXT, ASCII, ASCII)
def test_i7_feed_identity_depends_only_on_id_or_link(
    title: str, summary_a: str, summary_b: str, guid: str, link: str
) -> None:
    """I7: SHA-256 identity from ``id``, else ``link``; stable across content; none → ParseError."""
    if not (guid or link):
        guid = "urn:synthetic"
    a = normalize_entry(
        {"title": title, "id": guid, "link": link, "summary": summary_a}, ESI, "bafin", "presse"
    )
    b = normalize_entry(
        {"title": title + "x", "id": guid, "link": link, "summary": summary_b},
        ESI,
        "bafin",
        "presse",
    )
    assert a.identity == b.identity
    digest = hashlib.sha256((guid or link).encode("utf-8")).hexdigest()[:16]
    assert a.external_id == f"bafin_{digest}"


def test_i7_entry_without_id_and_link_is_rejected() -> None:
    """I7: without id and link there is no stable identity."""
    with pytest.raises(ParseError):
        normalize_entry({"title": "Meldung"}, ESI, "bafin", "presse")


@EXAMPLES
@given(st.one_of(st.none(), TEXT), st.integers(min_value=1994, max_value=2100))
def test_i8_funding_period_rules_are_closed(text: str | None, year: int) -> None:
    """I8: both period rules only return known periods; the designer year rule is monotone."""
    assert funding_period_auditdatabase(text) in {None, "2021-2027", "2014-2020"}
    assert funding_period_designer(text, str(year)) in PERIODS
    by_year = funding_period_designer(None, str(year))
    assert by_year is not None and int(by_year[:4]) <= year
    assert funding_period_designer(None, "1993") is None


CELEX = st.from_regex(r"\A[0-9][0-9]{4}[A-Z]{1,2}[0-9]{4}\Z")


@EXAMPLES
@given(st.lists(st.fixed_dictionaries({"celex": st.one_of(CELEX, st.just(""))}), max_size=10))
def test_i9_eurlex_core_documents_first_celex_unique(rows: list[dict[str, str]]) -> None:
    """I9: core documents come first, every CELEX appears once, rows without CELEX are skipped."""
    queries = {name: rows for name in ESI.eurlex_queries}
    merged = merge_rows(ESI, queries)
    core = [d.celex for d in ESI.eurlex_core_documents]
    assert [row["celex"] for row in merged[: len(core)]] == core
    celexes = [row["celex"] for row in merged]
    assert len(celexes) == len(set(celexes)) and "" not in celexes
    assert set(celexes) == set(core) | {r["celex"] for r in rows if r["celex"]}


@EXAMPLES
@given(DATES)
def test_i10_update_query_inserts_exactly_the_date(since: date) -> None:
    """I10: the incremental query contains the ISO date once, and nothing else is inserted."""
    query = update_query(ESI, since)
    assert query == ESI.eurlex_update_query_template.replace("{since}", since.isoformat())
    assert "{since}" not in query
    with pytest.raises(ConfigurationError):
        update_query(ESI, since.isoformat())  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError):
        update_query(DESIGNER, since)


@pytest.mark.xfail(strict=True, reason="Befund LS-S1: datetime wird als date angenommen")
def test_i10_update_query_rejects_datetimes() -> None:
    """I10 (Befund LS-S1): a datetime would insert a time into an xsd:date literal."""
    with pytest.raises(ConfigurationError):
        update_query(ESI, datetime(2024, 1, 2, 3, 4))


@EXAMPLES
@given(st.text(max_size=16))
def test_i11_celex_type_is_total(celex: str) -> None:
    """I11: every CELEX text maps to one of the documented document types."""
    assert celex_document_type(celex) in {
        "Unbekannt",
        "Verordnung",
        "Richtlinie",
        "Beschluss",
        "Guidance",
        "Rechtsprechung",
        "Sonstiges",
    }


@EXAMPLES
@given(ASCII, st.lists(ASCII.filter(str.strip), max_size=4))
def test_i12_relevance_is_case_insensitive_substring(text: str, keywords: list[str]) -> None:
    """I12: relevance is a case-insensitive substring match against explicit keywords only."""
    expected = any(k.lower() in text.lower() for k in keywords) if text else False
    assert is_relevant(text, keywords) is expected
    assert is_relevant(text.upper(), [k.lower() for k in keywords]) is expected
    assert is_relevant(text, []) is False
