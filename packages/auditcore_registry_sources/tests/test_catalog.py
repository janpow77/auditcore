"""The source catalogue is valid, distinguishes supported/planned and records live checks."""

from __future__ import annotations

import json
from pathlib import Path

from auditcore_harvest.catalog import summary, validate_catalog

ROOT = Path(__file__).parents[1]
CATALOG = json.loads((ROOT / "docs" / "source-catalog.json").read_text(encoding="utf-8"))


def test_catalog_is_valid_and_fixtures_exist() -> None:
    entries = validate_catalog(CATALOG)
    for entry in entries:
        for fixture in entry.data["fixtures"]:
            assert (ROOT.parent / fixture).is_file(), fixture
    counts = summary(entries)
    assert counts["implementation"] == {"SUPPORTED": 8, "LEGACY_ONLY": 2, "PLANNED": 3}


def test_every_supported_source_states_data_licence_and_live_status() -> None:
    for entry in CATALOG["sources"]:
        assert entry["licence_access"]["note"], entry["source_id"]
        if entry["implementation"]["status"] == "SUPPORTED":
            assert entry["live_test"]["status"] in {
                "PASS",
                "FAIL",
                "NOT_CONFIGURED",
                "NOT_EXECUTED",
            }
    by_id = {e["source_id"]: e for e in CATALOG["sources"]}
    assert "CC BY-NC 4.0" in by_id["registry.opensanctions_lists"]["licence_access"]["note"]
    assert by_id["registry.opensanctions_match"]["live_test"]["status"] == "NOT_CONFIGURED"
    assert by_id["registry.offeneregister"]["live_test"]["status"] == "FAIL"
