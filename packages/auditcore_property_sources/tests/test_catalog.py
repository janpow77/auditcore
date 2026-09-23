"""Catalog: origin bound to the characterized blobs, planned consumers, honest access status."""

from __future__ import annotations

from support import observed

from auditcore_property_sources import catalog, source_entry


def test_every_source_is_bound_to_a_characterized_blob() -> None:
    sources = observed()["sources"]
    blobs = {**sources["wohnungsmonitor"]["files"], **sources["versteigerung"]["files"]}
    commits = {sources["wohnungsmonitor"]["commit"], sources["versteigerung"]["commit"]}
    data = catalog()
    assert data["schema"] == "auditcore_property_sources.catalog/1"
    assert len(data["sources"]) == 7
    for entry in data["sources"]:
        origin = entry["origin"]
        assert origin["commit"] in commits and blobs[origin["path"]] == origin["git_blob"]
        assert entry["consumer_status"]["status"] == "GEPLANT"
        assert "der mehrfache Nutzen kommt noch" in entry["consumer_status"]["decision"]
        assert origin["consumer"]["repository"] == origin["repository"]
        assert entry["access"]["terms_of_use"]["status"] == "REVIEW_REQUIRED"
        assert entry["live_test"]["status"] in {"PASS", "FAIL", "NOT_EXECUTED", "NOT_CONFIGURED"}
        assert set(entry["semantics"]) == {"price", "area", "address"}


def test_price_semantics_stay_separate() -> None:
    assert "Verkehrswert" in source_entry("property.zvg")["semantics"]["price"]
    assert "unklar" in source_entry("property.kleinanzeigen")["semantics"]["price"]
    assert "warm" in source_entry("property.bienici")["semantics"]["price"]
    try:
        source_entry("property.unbekannt")
    except KeyError:
        pass
    else:  # pragma: no cover
        raise AssertionError("unbekannte Quelle")


def test_not_extracted_parts_are_named() -> None:
    names = {(e["repository"], e["path"]) for e in catalog()["not_extracted"]}
    assert ("janpow77/wohnungsmonitor", "details.py") in names
    assert ("janpow77/versteigerung", "backend/app/ingest/gutachten_ingest.py") in names
