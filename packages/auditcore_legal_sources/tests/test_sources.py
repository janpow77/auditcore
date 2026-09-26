"""Corrected contract of the DIP and EUR-Lex parsers, each difference beside the legacy result."""

from __future__ import annotations

import ast
import json
from datetime import date, datetime
from pathlib import Path

import pytest
from capture_routes import drucksache

import auditcore_legal_sources
from auditcore_legal_sources import dip, eurlex, legacy
from auditcore_legal_sources.errors import ConfigurationError, ParseError, ProfileError
from auditcore_legal_sources.model import LegalDocument
from auditcore_legal_sources.normalize import (
    deduplicate,
    funding_period_auditdatabase,
    funding_period_designer,
    is_relevant,
    parse_publication_date,
)
from auditcore_legal_sources.profile import (
    available_profiles,
    fingerprint,
    load_profile,
    profile_from_dict,
)

ADB = load_profile("auditdatabase.esi", "2026.09.2")
DES = load_profile("audit_designer.vp_ai", "2026.09.2")
PROFILE_FILE = (
    Path(auditcore_legal_sources.__file__).parent / "profiles" / "auditdatabase.esi-2026.09.2.json"
)


# ------------------------------------------------------------------ dates


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2024-03-15", (date(2024, 3, 15), "day")),
        ("2024-03-15T10:20:30", (date(2024, 3, 15), "day")),
        ("2024-03-15T00:00:00+01:00", (date(2024, 3, 15), "day")),
        ("15.03.2024", (date(2024, 3, 15), "day")),
        ("1.3.2024", (date(2024, 3, 1), "day")),
        ("2024-03", (date(2024, 3, 1), "month")),
        ("2024", (date(2024, 1, 1), "year")),
        ("2024-13-45", (None, None)),
        ("20240315", (None, None)),
        ("kein Datum", (None, None)),
        ("", (None, None)),
        (None, (None, None)),
        (20240315, (None, None)),
        (datetime(2024, 3, 15, 8, 0), (date(2024, 3, 15), "day")),
    ],
)
def test_ls_c01_dates_are_parsed_unlike_legacy(
    value: object, expected: tuple[object, object]
) -> None:
    assert parse_publication_date(value) == expected
    if isinstance(value, str):
        # LS-C01: both source applications return None for every string.
        assert legacy.legacy_parse_date(value) is None


# -------------------------------------------------------------------- DIP


def test_dip_query_carries_no_credentials_and_supports_cursor_and_increment() -> None:
    params = dip.drucksache_query(ADB, "EFRE", cursor="c1", updated_since=date(2024, 1, 31))
    assert params == {
        "format": "json",
        "num": "30",
        "f.titel": "EFRE",
        "cursor": "c1",
        "f.aktualisiert.start": "2024-01-31",
    }
    # LS-C02: the source put the (hard-coded) key into the query string.
    assert "apikey" in legacy.legacy_dip_query("KEY", "EFRE")
    assert all("key" not in name.lower() for name in params)
    assert dip.drucksache_url(ADB) == "https://search.dip.bundestag.de/api/v1/drucksache"


@pytest.mark.parametrize("key", ["", "  ", "a\nb", "a\rb"])
def test_dip_auth_rejects_missing_or_injected_keys(key: str) -> None:
    with pytest.raises(ConfigurationError):
        dip.auth_header_value(key)
    assert dip.auth_header_value(" k ") == "ApiKey k"


def test_dip_query_needs_keyword() -> None:
    with pytest.raises(ConfigurationError):
        dip.drucksache_query(ADB, " ")


def test_dip_page_parsing_is_strict() -> None:
    page = dip.parse_page({"numFound": 2, "cursor": "c2", "documents": [drucksache(1)]})
    assert page.cursor == "c2" and page.num_found == 2 and len(page.items) == 1
    assert page.is_last("c2") and not page.is_last("c1")
    assert dip.parse_page({"documents": []}).is_last(None)
    for payload in (None, [], {"documents": None}, {"documents": [1]}, {"numFound": 1}):
        with pytest.raises(ParseError):
            dip.parse_page(payload)


def test_ls_c03_defective_items_are_errors_not_empty_documents() -> None:
    page = dip.parse_page({"documents": [drucksache(1), {}, drucksache(2, titel="")]})
    documents, errors = dip.normalize_page(page, ADB)
    assert [d.external_id for d in documents] == ["dip_270001"]
    assert [e.location for e in errors] == ["documents[1].id", "documents[2].titel"]
    # Legacy: the empty item became a document with id "dip_" and title "Ohne Titel".
    assert legacy.legacy_dip_normalize({})["title"] == "Ohne Titel"  # type: ignore[index]


def test_dip_normalization_matches_legacy_fields_and_parses_dates() -> None:
    item = drucksache(4, fundstelle={}, abstract="Kurz")
    document = dip.normalize_drucksache(item, ADB)
    old = legacy.legacy_dip_normalize(item)
    assert old is not None
    assert document.external_id == old["id"]
    assert document.source_url == old["source_url"]
    assert document.document_url == old["pdf_url"]
    assert document.classification["funding_period"] == old["funding_period"]
    assert document.classification["fund"] == old["fund"]
    assert document.classification["heuristic"] is True
    assert document.content == old["content"] == "Kurz"
    # LS-C04: legacy stored the date under "published_date" as text; ingestion read
    # "publication_date" and "external_id" and therefore stored neither.
    assert "publication_date" not in old and "external_id" not in old
    assert document.publication_date == date(2024, 3, 15)
    assert document.profile == ADB.reference


def test_dip_pdf_url_construction_and_designer_profile_without_classification() -> None:
    assert dip.normalize_drucksache(drucksache(5, fundstelle={}), ADB).document_url == (
        "https://dserver.bundestag.de/btd/20/010/2001005.pdf"
    )
    odd = dip.normalize_drucksache(drucksache(6, fundstelle={}, dokumentnummer="x"), ADB)
    assert odd.document_url is None
    assert dip.normalize_drucksache(drucksache(7), DES).classification == {}


def test_dip_keyword_selection() -> None:
    assert dip.keywords(ADB) == ADB.dip_keywords
    assert dip.keywords(ADB, ["EFRE"]) == ("EFRE",)
    with pytest.raises(ConfigurationError):
        dip.keywords(ADB, ["erfunden"])


# ---------------------------------------------------------------- EUR-Lex


def test_sparql_form_and_update_query() -> None:
    assert eurlex.sparql_form("SELECT") == {
        "query": "SELECT",
        "format": "application/sparql-results+json",
    }
    with pytest.raises(ConfigurationError):
        eurlex.sparql_form("")
    query = eurlex.update_query(ADB, date(2024, 1, 31))
    assert query == legacy.legacy_update_query(ADB, datetime(2024, 1, 31))
    with pytest.raises(ConfigurationError):
        eurlex.update_query(ADB, '2024-01-01"^^xsd:date) } #')  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError):
        eurlex.update_query(DES, date(2024, 1, 31))


def test_ls_c05_sparql_parsing_is_strict() -> None:
    payload = {"results": {"bindings": [{"celex": {"type": "literal", "value": "32021R1060"}}]}}
    assert eurlex.parse_results(payload) == [{"celex": "32021R1060"}]
    for bad in (
        {},
        {"results": {}},
        {"results": {"bindings": [1]}},
        {"results": {"bindings": [{"celex": {"type": "uri"}}]}},
    ):
        with pytest.raises(ParseError):
            eurlex.parse_results(bad)
        # Legacy turned structural defects into an empty or partial result.
        if bad in ({}, {"results": {}}):
            assert legacy.legacy_sparql_rows(bad) == []


def test_merge_keeps_core_documents_first_and_deduplicates() -> None:
    rows = eurlex.merge_rows(
        ADB,
        {
            "cohesion_regulations": [
                {"celex": "32021R1060", "title": "Dublette"},
                {"celex": "32022R0001", "title": "Neu", "date": "2022-05-04"},
                {"title": "ohne CELEX"},
            ],
            "unknown_query": [{"celex": "39999R9999", "title": "nicht im Profil"}],
        },
    )
    assert [r["celex"] for r in rows][:7] == [d.celex for d in ADB.eurlex_core_documents]
    assert [r["celex"] for r in rows][7:] == ["32022R0001"]


def test_eurlex_normalization_parses_dates_and_keeps_rules_apart() -> None:
    row = {
        "celex": "32013R1083",
        "title": "VO 1083/2006 Durchführung",
        "date": "2013-12-17",
        "source": "x",
    }
    adb_doc = eurlex.normalize_row(row, ADB)
    des_doc = eurlex.normalize_row(row, DES)
    assert adb_doc.publication_date == date(2013, 12, 17)
    assert legacy.legacy_eurlex_normalize(row)["publication_date"] is None
    assert adb_doc.classification["funding_period"] is None
    assert des_doc.classification["funding_period"] == "2007-2013"
    assert adb_doc.document_type == "Verordnung"
    with pytest.raises(ParseError):
        eurlex.normalize_row({"title": "x"}, ADB)


def test_funding_period_variants_are_not_harmonised() -> None:
    assert funding_period_auditdatabase("VO 2021/1058") is None
    assert funding_period_designer("VO 2021/1058") == "2021-2027"
    assert funding_period_designer("", "2016-01-01") == "2014-2020"
    assert funding_period_designer("", "unbekannt") is None


# ------------------------------------------------------------- model, rules


def test_content_hash_identity_and_dedup_are_source_compatible() -> None:
    first = dip.normalize_drucksache(drucksache(1), ADB)
    again = dip.normalize_drucksache(drucksache(1), ADB)
    other = dip.normalize_drucksache(drucksache(2), ADB)
    assert first.content_hash == legacy.legacy_content_hash(
        first.content, first.abstract, first.title
    )
    kept, dropped = deduplicate([first, other, again])
    assert kept == [first, other] and dropped == ["dip_bundestag:dip_270001"]
    assert json.loads(json.dumps(first.to_dict()))["identity"] == "dip_bundestag:dip_270001"


def test_relevance_uses_explicit_keywords() -> None:
    assert is_relevant("EFRE-Förderung", ADB.keywords_de)
    assert not is_relevant("", ADB.keywords_de)
    assert not is_relevant("Nichts", ["EFRE"])


def test_profiles_are_explicit_versioned_and_tamper_evident() -> None:
    assert available_profiles() == (
        ("audit_designer.vp_ai", "2026.09.2"),
        ("auditdatabase.esi", "2026.09.2"),
    )
    data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    assert fingerprint(data) == ADB.fingerprint
    data["dip"]["page_size"] = 31
    assert profile_from_dict(data).fingerprint != ADB.fingerprint
    for mutate in (
        lambda d: d.update(schema="x"),
        lambda d: d["dip"].update(page_size=0),
        lambda d: d["dip"].update(classification="neu"),
        lambda d: d["eurlex"].update(queries={}),
        lambda d: d["eurlex"].update(update_query_template="ohne"),
        lambda d: d.pop("keywords"),
    ):
        broken = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        mutate(broken)
        with pytest.raises(ProfileError):
            profile_from_dict(broken)
    for name in ("unknown", "../auditdatabase.esi"):
        with pytest.raises(ProfileError):
            load_profile(name, "2026.09.2")


def test_profile_content_equals_executed_sources(legacy: dict[str, object]) -> None:
    recorded = legacy["profile"]  # type: ignore[index]
    assert list(ADB.dip_keywords) == recorded["dip_keywords"]  # type: ignore[index]
    assert dict(ADB.eurlex_queries) == recorded["eurlex_queries"]  # type: ignore[index]
    assert dict(DES.eurlex_queries) == recorded["designer_eurlex_queries"]  # type: ignore[index]
    assert list(ADB.keywords_de) == recorded["global_keywords_de"]  # type: ignore[index]
    assert list(DES.dip_keywords) == recorded["designer_dip_queries"]  # type: ignore[index]


def test_document_is_immutable() -> None:
    document = LegalDocument("s", "e", "t", None, None, None, None)
    with pytest.raises(AttributeError):
        document.title = "x"  # type: ignore[misc]


def test_runtime_modules_use_only_stdlib_and_no_network_or_io() -> None:
    package = Path(auditcore_legal_sources.__file__).parent
    forbidden = {
        "socket",
        "urllib.request",
        "http",
        "httpx",
        "requests",
        "subprocess",
        "logging",
        "sqlalchemy",
        "SPARQLWrapper",
    }
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            roots = {n.split(".")[0] for n in names} | set(names)
            assert not roots & forbidden, path.name
            assert all(not n.startswith("urllib.request") for n in names), path.name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "print", "__import__"}
