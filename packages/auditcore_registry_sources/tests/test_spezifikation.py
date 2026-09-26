"""Invariants of docs/spezifikation.md as Hypothesis properties (synthetic data, no network)."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

import pytest
from auditcore_harvest import Response, TransportError
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_registry_sources import (
    FormatError,
    ListEntry,
    ListSnapshot,
    QueryError,
    load_lists,
    load_profile,
    parse_targets_simple_csv,
)
from auditcore_registry_sources._company_vat import check_vat, parse_vies_response, split_vat_id
from auditcore_registry_sources.bulk_screening import local_screen
from auditcore_registry_sources.company import (
    names_match,
    normalize_company_name,
    score_indicators,
)
from auditcore_registry_sources.lists import find_list
from auditcore_registry_sources.model import LIST_FIELDS
from auditcore_registry_sources.opensanctions_csv import (
    SIMPLE_CSV_COLUMNS,
    entry_to_row,
    serialize_targets_simple_csv,
)
from auditcore_registry_sources.ownership import (
    OwnershipGraph,
    OwnershipNode,
    beneficial_owners,
    ownership_chain,
    sme_status,
)
from auditcore_registry_sources.screening import screen

EXAMPLES = settings(max_examples=100, deadline=None)
WORD = st.text(alphabet="abcdefghijklmnopqrstuvwxyzäöüß", min_size=1, max_size=8)
VALUE = st.text(alphabet='ABCDEFGHIJabcdefghij0123456789 -,.äöü"', max_size=12).map(str.strip)
LOCAL = load_profile("flowinvoice.sanctions_local", "2026.09.1")
DESIGNER = load_profile("audit_designer.sanctions_screening", "2026.09.2")
LISTS = load_lists("audit_designer.sanctions_lists", "2026.09.1")
COMPANY = load_profile("flowinvoice.company_verification", "2026.09.2")
UBO = load_profile("flowsearch.ubo", "2026.09.2")
SME = load_profile("flowsearch.kmu", "2026.09.2")


@st.composite
def entries(draw: st.DrawFn, max_size: int = 6) -> list[ListEntry]:
    count = draw(st.integers(min_value=1, max_value=max_size))
    result = []
    for index in range(count):
        fields = {f: draw(VALUE) for f in LIST_FIELDS}
        result.append(
            ListEntry(
                list_key="eu_fsf",
                entry_id=f"SYN-{index}",
                schema=draw(st.sampled_from(["Person", "Company", ""])),
                name=draw(WORD) + " " + draw(WORD),
                aliases=tuple(draw(st.lists(WORD, max_size=2))),
                **fields,
            )
        )
    return result


@EXAMPLES
@given(entries())
def test_i1_targets_csv_roundtrip(listed: list[ListEntry]) -> None:
    """I1: serialising entries and parsing them again gives the same entries."""
    data = serialize_targets_simple_csv(
        [entry_to_row(e) for e in listed], columns=SIMPLE_CSV_COLUMNS
    )
    parsed = parse_targets_simple_csv(data, list_key="eu_fsf")
    assert list(parsed.entries) == listed
    assert parsed.content_sha256 == hashlib.sha256(data).hexdigest()


ROW = st.fixed_dictionaries(
    {"id": st.one_of(st.just(""), WORD), "name": st.one_of(st.just(""), WORD)}
)


@EXAMPLES
@given(st.lists(ROW, max_size=8))
def test_i2_every_row_is_an_entry_or_an_issue(rows: list[dict[str, str]]) -> None:
    """I2: rows_seen = entries + issues; no usable row or no UTF-8 is a FormatError."""
    body = "id,name\n" + "".join(f"{r['id']},{r['name']}\n" for r in rows)
    usable = [r for r in rows if r["id"] and r["name"]]
    if not usable:
        with pytest.raises(FormatError):
            parse_targets_simple_csv(body.encode(), list_key="x")
        return
    parsed = parse_targets_simple_csv(body.encode(), list_key="x")
    assert parsed.rows_seen == len(rows) == len(parsed.entries) + len(parsed.issues)
    assert [(e.entry_id, e.name) for e in parsed.entries] == [(r["id"], r["name"]) for r in usable]
    with pytest.raises(FormatError):
        parse_targets_simple_csv(body.encode("utf-16"), list_key="x")


@EXAMPLES
@given(entries(), st.floats(min_value=0.0, max_value=1.0))
def test_i3_local_screen_hits_are_at_or_above_the_minimum(
    listed: list[ListEntry], minimum: float
) -> None:
    """I3: hits reach the minimum, exact names score 1.0, no inventory means NOT_SEARCHED."""
    query = listed[0].name
    result = local_screen(query, listed, LOCAL, min_score=minimum)
    assert result.status == ("HITS" if result.hits else "NO_HITS")
    assert result.entries_checked == len(listed)
    assert all(h.score >= round(minimum, 2) - 1e-9 for h in result.hits)
    exact = [h for h in result.hits if h.entry is listed[0]]
    assert exact and exact[0].score == 1.0 and exact[0].method == "exact"
    assert local_screen(query, [], LOCAL).status == "NOT_SEARCHED"


def _snapshot(key: str, listed: list[ListEntry]) -> ListSnapshot:
    return ListSnapshot(find_list(LISTS, key), tuple(listed), as_of="2026-09-01")


@EXAMPLES
@given(entries(), st.lists(st.booleans(), min_size=1, max_size=3), WORD)
def test_i4_screening_status_reflects_the_searched_lists(
    listed: list[ListEntry], filled: list[bool], extra: str
) -> None:
    """I4: one finding per list; HITS, NOT_SEARCHED, INCOMPLETE and NO_HITS as specified."""
    keys = [lst.key for lst in LISTS][: len(filled)]
    snapshots = [_snapshot(k, listed if f else []) for k, f in zip(keys, filled, strict=False)]
    query = "zzq " + extra + " qqz"
    result = screen(query, snapshots, DESIGNER)
    assert [f.list_key for f in result.findings] == keys[: len(snapshots)]
    assert [f.searched for f in result.findings] == [bool(f) for f in filled[: len(snapshots)]]
    if result.hits:
        assert result.status == "HITS"
    elif not any(filled[: len(snapshots)]):
        assert result.status == "NOT_SEARCHED"
    elif not all(filled[: len(snapshots)]):
        assert result.status == "INCOMPLETE"
    else:
        assert result.status == "NO_HITS"
    if result.status in ("NO_HITS", "INCOMPLETE"):
        assert any("Unbedenklichkeit" in text for text in result.limitations)


@EXAMPLES
@given(st.text(max_size=2), st.floats(allow_nan=False) | st.none())
def test_i5_queries_outside_the_profile_are_rejected(short: str, minimum: float | None) -> None:
    """I5: too short names and minimum scores outside the profile range are QueryErrors."""
    with pytest.raises(QueryError):
        screen(short, [], DESIGNER)
    if minimum is not None and not 50 <= minimum <= 100:
        with pytest.raises(QueryError):
            screen("Beispiel GmbH", [], DESIGNER, min_score=minimum)


FORMS = st.sampled_from(["GmbH", "AG", "GmbH & Co. KG", "e.V.", "UG"])


@EXAMPLES
@given(st.lists(WORD, min_size=1, max_size=4), st.one_of(st.none(), FORMS), WORD)
def test_i6_company_names_lose_only_whole_legal_forms(
    words: list[str], form: str | None, other: str
) -> None:
    """I6: legal forms are removed as whole words only; idempotent; matching is symmetric."""
    name = " ".join(words + ([form] if form else []))
    normalized = normalize_company_name(name, COMPANY)
    assert set(normalized.split()) <= set(name.lower().split())
    assert normalize_company_name(normalized, COMPANY) == normalized
    assert names_match(name, name, COMPANY)
    assert names_match(name, other, COMPANY) == names_match(other, name, COMPANY)
    assert normalize_company_name("Hagen Metall AG", COMPANY) == "hagen metall"


INDICATORS = st.lists(
    st.sampled_from(["INVALID_VAT_ID", "VIES_SERVICE_UNAVAILABLE", "NAME_MISMATCH", "OTHER_X"]),
    max_size=6,
)


@EXAMPLES
@given(INDICATORS, INDICATORS)
def test_i7_indicator_score_is_bounded_and_monotone(first: list[str], more: list[str]) -> None:
    """I7: score in [0, 1], never rises with more indicators; verified iff nothing critical."""
    verified, score = score_indicators(first, COMPANY)
    verified_more, score_more = score_indicators(first + more, COMPANY)
    assert 0.0 <= score_more <= score <= 1.0
    critical = COMPANY.setting("critical")
    assert verified is not any(i in critical for i in first)
    assert verified_more <= verified


@EXAMPLES
@given(
    st.dictionaries(st.sampled_from("abcdef"), st.sampled_from("abcdef"), max_size=6),
    st.sampled_from("abcdef"),
)
def test_i8_ownership_chain_terminates_and_reports_cycles(
    parents: Mapping[str, str], start: str
) -> None:
    """I8: the chain walk always ends; nodes are distinct; a repeated node is the cycle."""
    graph = OwnershipGraph()
    for node_id, parent in parents.items():
        graph.graph[node_id] = OwnershipNode(
            node_id, node_id, "company", 50.0, 50.0, parent_id=parent
        )
    chain = ownership_chain(graph, start)
    ids = [n.id for n in chain.nodes]
    assert len(ids) == len(set(ids))
    if chain.cycle is not None:
        assert chain.cycle in ids
    walked, seen, current = [], set(), start
    while current in graph.graph and current not in seen:
        seen.add(current)
        walked.append(current)
        current = graph.graph[current].parent_id or ""
    assert ids == list(reversed(walked))
    assert (chain.cycle is not None) == (current in seen)


NODES = st.lists(
    st.builds(
        OwnershipNode,
        id=WORD,
        name=WORD,
        type=st.sampled_from(["person", "company", "unknown"]),
        direct_share=st.floats(min_value=0, max_value=100),
        effective_share=st.floats(min_value=0, max_value=100),
        voting_rights=st.one_of(st.none(), st.floats(min_value=0, max_value=100)),
    ),
    max_size=8,
)


@EXAMPLES
@given(NODES)
def test_i9_beneficial_owners_are_persons_above_a_threshold(nodes: list[OwnershipNode]) -> None:
    """I9: only natural persons above 25 % capital or voting rights, by share descending."""
    owners = beneficial_owners(nodes, UBO)
    assert all(o.type == "person" for o in owners)
    assert all(o.effective_share > 25 or (o.voting_rights or 0) > 25 for o in owners)
    shares = [o.effective_share for o in owners]
    assert shares == sorted(shares, reverse=True)
    expected = [
        n
        for n in nodes
        if n.type == "person" and (n.effective_share > 25 or (n.voting_rights or 0) > 25)
    ]
    assert len(owners) == len(expected)


MONEY = st.one_of(st.none(), st.floats(min_value=0, max_value=1e9))


@EXAMPLES
@given(st.one_of(st.none(), st.integers(min_value=0, max_value=1000)), MONEY, MONEY)
def test_i10_sme_category_never_guesses(
    employees: int | None, turnover: float | None, balance: float | None
) -> None:
    """I10: AGVO class from headcount and turnover or balance sheet; gaps are „Nicht bestimmbar“."""
    company = {"employees": employees, "revenue": turnover, "balance_sheet_total": balance}
    result = sme_status(company, SME)
    sme_classes = {"Kleinstunternehmen", "Kleinunternehmen", "Mittleres Unternehmen"}
    assert result.category in sme_classes | {"Großunternehmen", "Nicht bestimmbar"}
    assert (result.is_sme is None) == (result.category == "Nicht bestimmbar")
    assert (result.is_sme is True) == (result.category in sme_classes)
    if employees is None or (turnover is None and balance is None):
        assert result.category == "Nicht bestimmbar"
    if employees is not None and employees >= 250 and turnover is not None and balance is not None:
        assert result.category == "Großunternehmen"


class _FailingTransport:
    def request(self, *args: object, **kwargs: object) -> Response:
        raise TransportError("synthetisch: keine Verbindung")


PREFIX = st.sampled_from(["", "ns2:", "tns:"])


@EXAMPLES
@given(st.from_regex(r"\A(DE|AT|FR) ?[0-9]{8,9}\Z"), PREFIX, st.booleans())
def test_i11_vies_unavailability_is_never_a_negative_answer(
    vat_id: str, prefix: str, valid: bool
) -> None:
    """I11: validity is read independent of prefixes; faults and outages are UNAVAILABLE."""
    compact, country, _ = split_vat_id(vat_id)
    assert split_vat_id(compact)[0] == compact and " " not in compact
    ns = f' xmlns:{prefix[:-1]}="urn:x"' if prefix else ""
    body = f"<{prefix}r{ns}><{prefix}valid>{str(valid).lower()}</{prefix}valid></{prefix}r>"
    assert parse_vies_response(vat_id, body.encode()).status == ("VALID" if valid else "INVALID")
    fault = b"<E><B><Fault><faultstring>MS_UNAVAILABLE</faultstring></Fault></B></E>"
    assert parse_vies_response(vat_id, fault).status == "UNAVAILABLE"
    assert check_vat(_FailingTransport(), vat_id).status == "UNAVAILABLE"
    assert check_vat(_FailingTransport(), vat_id).country_code == country
