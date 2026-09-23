"""Every adapter passes the reusable auditcore_harvest contract suite."""

from __future__ import annotations

import pytest
from auditcore_harvest import AdapterRegistry
from auditcore_harvest.testing import assert_adapter
from support import CASES, SECRETS, transport

import auditcore_price_sources
from auditcore_price_sources import FACTORIES, register


@pytest.mark.parametrize("source_id", sorted(FACTORIES))
def test_adapter_contract(source_id: str) -> None:
    report = assert_adapter(
        FACTORIES[source_id],
        config=CASES[source_id]["config"],
        transport_factory=lambda: transport(source_id),
        credentials={k: v for k, v in SECRETS.items() if k[0] == source_id},
    )
    assert report.passed
    expected_skip = source_id in {
        "price.bundesbank",
        "price.overpass_fuel_stations",
        "price.eu_oil_bulletin",
    }
    assert report.cases["missing_credentials"].startswith("SKIPPED") is expected_skip
    assert all(v == "PASS" or v.startswith("SKIPPED") for v in report.cases.values())


def test_registry_registers_every_adapter_once() -> None:
    registry = AdapterRegistry()
    register(registry)
    assert registry.sources() == tuple(sorted(FACTORIES))
    for source_id in registry.sources():
        adapter = registry.create(source_id)
        assert adapter.source.family == "price"
        assert adapter.source.profile_version == "2026.09.1"
    assert auditcore_price_sources.CONTRACT_VERSION == "auditcore_price_sources.contract/1"
