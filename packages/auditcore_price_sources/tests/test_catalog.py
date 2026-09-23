"""The shipped catalog lists exactly the implemented adapters with origin, units and status."""

from __future__ import annotations

import json
from importlib import resources

import auditcore_price_sources
from auditcore_price_sources import FACTORIES

CATALOG = json.loads(
    (resources.files("auditcore_price_sources") / "catalog.json").read_text(encoding="utf-8")
)


def test_catalog_matches_the_registered_adapters() -> None:
    entries = {e["source_id"]: e for e in CATALOG["sources"]}
    assert set(entries) == set(FACTORIES)
    for source_id, entry in entries.items():
        adapter = FACTORIES[source_id]()
        assert type(adapter).__name__ == entry["adapter"]
        assert adapter.source.snapshot_semantics.value == entry["snapshot_semantics"]
        assert adapter.source.profile_version == entry["profile_version"]
        assert entry["unit"] and entry["time_reference"]
        assert entry["licence_access"]["status"] == "REVIEW_REQUIRED"
        assert entry["implementation"]["status"] == "IMPLEMENTED"
        assert entry["live_test"]["status"] in {"PASS", "NOT_CONFIGURED", "NOT_EXECUTED"}
        assert all(
            o["commit"] == "853676d2b1ab792395d63c62c9f96d5edcca8c2d" for o in entry["origins"]
        )


def test_not_implemented_sources_carry_a_reason() -> None:
    reasons = {e["source_id"]: e for e in CATALOG["not_implemented"]}
    assert set(reasons) == {
        "price.mtsk",
        "price.vid_secondary",
        "registry.handelsregister",
        "geo.geoportal_hessen",
    }
    assert all(
        e["reason"] and e["status"] in {"NOT_APPLICABLE", "OUT_OF_SCOPE"} for e in reasons.values()
    )


def test_version_matches_package() -> None:
    assert CATALOG["version"] == auditcore_price_sources.__version__
