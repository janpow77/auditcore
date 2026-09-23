"""BaFin/CURIA/ECA feed and page behavior: exact legacy replay and the corrected contract."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from auditcore_legal_sources import feeds, legacy
from auditcore_legal_sources.errors import ConfigurationError, ParseError
from auditcore_legal_sources.profile import load_profile

DATA = json.loads((Path(__file__).parent / "fixtures" / "legacy_feeds_observed.json").read_text())
CASES = {c["name"]: c for c in DATA["cases"]}
ADB = load_profile("auditdatabase.esi", "2026.09.1")
DES = load_profile("audit_designer.vp_ai", "2026.09.1")
HASH_ID = re.compile(r"^(bafin|curia)_-?\d+$")


def _same_except_hash_id(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    if HASH_ID.match(expected["id"]) and not expected["source_url"]:
        assert HASH_ID.match(actual["id"])
        actual, expected = {**actual, "id": ""}, {**expected, "id": ""}
    assert actual == expected


@pytest.mark.parametrize(
    "case",
    [c for c in DATA["cases"] if c["operation"] in {"bafin_entry", "curia_entry"}],
    ids=lambda c: c["name"],
)
def test_legacy_entries_are_reproduced(case: dict[str, Any]) -> None:
    entry, feed = case["inputs"]["entry"], case["inputs"]["feed"]
    run = (
        legacy.legacy_bafin_entry
        if case["operation"] == "bafin_entry"
        else legacy.legacy_curia_entry
    )
    actual = run(entry, feed)
    assert actual is not None
    _same_except_hash_id(actual, case["output"])


def test_ls_c10_hash_identities_were_process_dependent() -> None:
    assert DATA["environment"]["PYTHONHASHSEED"] == "0"
    case = CASES["bafin-entry-aufsicht-1"]
    assert HASH_ID.match(case["output"]["id"])  # str(hash(title)) in the source
    with pytest.raises(ParseError):
        feeds.normalize_entry(case["inputs"]["entry"], ADB, "bafin", "aufsicht")
    linked = CASES["bafin-entry-aufsicht-0"]["inputs"]["entry"]
    ids = {feeds.normalize_entry(linked, ADB, "bafin", "aufsicht").external_id for _ in range(3)}
    assert len(ids) == 1 and not HASH_ID.match(ids.pop())


def test_entry_without_link_and_id_is_an_error() -> None:
    with pytest.raises(ParseError):
        feeds.normalize_entry({"title": "Nur Titel"}, ADB, "bafin", "aufsicht")
    with pytest.raises(ParseError):
        feeds.normalize_entry({"link": "https://example.invalid/x"}, ADB, "bafin", "aufsicht")
    with pytest.raises(ConfigurationError):
        feeds.normalize_entry({"title": "t", "link": "l"}, ADB, "bafin", "erfunden")
    with pytest.raises(ConfigurationError):
        feeds.feed_source(DES, "bafin")


def test_ls_c11_dates_keep_timezone_and_atom_updated_is_used() -> None:
    rss = feeds.normalize_entry(
        CASES["bafin-entry-aufsicht-0"]["inputs"]["entry"], ADB, "bafin", "aufsicht"
    )
    assert rss.publication_date == date(2024, 3, 15)
    assert rss.metadata["published_at"] == "2024-03-15T09:20:30+00:00"
    # Legacy wrote the UTC value without zone marker.
    assert CASES["bafin-entry-aufsicht-0"]["output"]["published_date"] == "2024-03-15T09:20:30"
    atom = feeds.normalize_entry(
        CASES["bafin-entry-atom-0"]["inputs"]["entry"], ADB, "bafin", "aufsicht"
    )
    assert atom.publication_date == date(2024, 2, 1)
    assert CASES["bafin-entry-atom-0"]["output"]["published_date"] == ""
    undated = {**CASES["bafin-entry-aufsicht-1"]["inputs"]["entry"], "id": "urn:x"}
    no_date = feeds.normalize_entry(undated, ADB, "bafin", "aufsicht")
    assert no_date.publication_date is None and no_date.raw_date == "kein Datum"


def test_ls_c12_curia_case_numbers_and_types() -> None:
    entry = CASES["curia-entry-gerichtshof-0"]["inputs"]["entry"]
    document = feeds.normalize_entry(entry, ADB, "curia", "gerichtshof")
    assert document.metadata["case_numbers"] == ["C-123/22"]
    assert document.document_type == "Rechtsprechung Gerichtshof"
    assert CASES["curia-entry-gerichtshof-0"]["output"]["document_type"] == "Pressemitteilung"
    general = feeds.normalize_entry({**entry, "title": "Urteil T-45/21"}, ADB, "curia", "gericht")
    assert general.metadata["case_numbers"] == ["T-45/21"]
    assert (
        legacy.legacy_curia_entry({**entry, "title": "Urteil T-45/21", "summary": ""}, "gericht")[
            "metadata"
        ]["case_number"]
        == ""
    )  # type: ignore[index]


def test_ls_c14_no_invented_classification() -> None:
    document = feeds.normalize_entry(
        CASES["bafin-entry-aufsicht-0"]["inputs"]["entry"], ADB, "bafin", "aufsicht"
    )
    assert document.classification == {}
    assert CASES["bafin-entry-aufsicht-0"]["output"]["fund"] == "EFRE"


def test_duplicates_share_identity_and_errors_are_indexed() -> None:
    entries = [
        c["inputs"]["entry"] for n, c in CASES.items() if n.startswith("bafin-entry-aufsicht")
    ]
    documents, errors = feeds.normalize_entries(entries + [{"title": ""}], ADB, "bafin", "aufsicht")
    assert documents[0].identity == documents[1].identity
    assert [e.location for e in errors] == ["entries[1].id", "entries[3].title"]


def test_ls_c15_relevance_filter_has_no_silent_fallback() -> None:
    entries = [
        c["inputs"]["entry"] for n, c in CASES.items() if n.startswith("curia-entry-gerichtshof")
    ]
    documents, _ = feeds.normalize_entries(entries, ADB, "curia", "gerichtshof")
    assert [d.title for d in feeds.select_relevant(documents, ADB.keywords_de)] == [
        "Urteil in der Rechtssache C-123/22 zur EFRE-Förderung"
    ]
    assert feeds.select_relevant(documents, ["nirgends"]) == []


def test_ls_c09_feed_cache_was_shared_between_sources() -> None:
    flow = CASES["rss-shared-feed-cache"]["output"]
    assert flow["cache_shared"] is True
    assert flow["curia_calls"] == [ADB.feeds["bafin"].feeds["aufsicht"]]
    assert flow["curia"]["documents"][0]["title"].startswith("Allgemeinverfügung")


def test_ls_c13_eca_links_without_placeholder_fallback() -> None:
    html = DATA["documents"]["eca_html"]
    documents = feeds.publication_links(html, ADB)
    scraped = CASES["eca-harvest"]["output"]["scraped"]["documents"]
    assert [d.source_url for d in documents] == [d["source_url"] for d in scraped]
    assert [d.title for d in documents] == [d["title"] for d in scraped]
    assert feeds.publication_links("<html></html>", ADB) == []
    fallback = CASES["eca-harvest"]["output"]["fallback"]
    assert fallback["success"] is True and len(fallback["documents"]) == 3
    assert [d["id"] for d in fallback["documents"]] == [
        d["id"] for d in legacy.legacy_eca_core_reports()
    ]
    assert CASES["eca-core-reports"]["output"] == legacy.legacy_eca_core_reports()


def test_profile_feed_urls_equal_the_source() -> None:
    recorded = DATA["profile"]
    assert dict(ADB.feeds["bafin"].feeds) == recorded["bafin_feeds"]
    assert dict(ADB.feeds["curia"].feeds) == recorded["curia_feeds"]
    assert list(ADB.feeds["eca"].publication_urls) == recorded["eca_publication_urls"]
