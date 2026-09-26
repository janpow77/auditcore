"""Adapters run through the real ``auditcore_harvest`` engine and its contract suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from auditcore_harvest import (
    AdapterRegistry,
    HarvestEngine,
    HarvestRequest,
    ReplayTransport,
    RunStatus,
)
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.testing import assert_adapter

from auditcore_legal_sources.adapters import (
    BaFinFeedAdapter,
    CuriaFeedAdapter,
    DipDrucksachenAdapter,
    EcaPublicationsAdapter,
    EurLexAdapter,
    register,
)

REPLAY = Path(__file__).parent / "fixtures" / "replay"
PROFILE = {"id": "auditdatabase.esi", "version": "2026.09.2"}
DIP_KEY = {("legal.dip_bundestag", "api_key"): "fixture-key-nicht-echt"}


def replay(name: str) -> ReplayTransport:
    return ReplayTransport.from_file(REPLAY / name)


def run(
    adapter: Any, fixture: str, config: dict[str, Any], **request: Any
) -> tuple[Any, ListSink, ReplayTransport]:
    transport = replay(fixture)
    clock = FixedClock()
    engine = HarvestEngine(
        transport=transport,
        credentials=StaticCredentials(DIP_KEY),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    )
    sink = ListSink()
    result = engine.run(
        adapter, HarvestRequest(adapter.source.source_id, "t", **request), sink, config=config
    )
    return result, sink, transport


@pytest.mark.parametrize(
    ("factory", "fixture", "config", "credentials", "minimum"),
    [
        (
            DipDrucksachenAdapter,
            "dip.json",
            {"profile": PROFILE, "keywords": ["EFRE", "Strukturfonds"]},
            DIP_KEY,
            4,
        ),
        (EurLexAdapter, "eurlex.json", {"profile": PROFILE}, None, 9),
        (BaFinFeedAdapter, "bafin.json", {"profile": PROFILE}, None, 3),
        (CuriaFeedAdapter, "curia.json", {"profile": PROFILE}, None, 3),
        (EcaPublicationsAdapter, "eca.json", {"profile": PROFILE}, None, 2),
    ],
    ids=["dip", "eurlex", "bafin", "curia", "eca"],
)
def test_contract_suite(
    factory: Any, fixture: str, config: dict[str, Any], credentials: Any, minimum: int
) -> None:
    report = assert_adapter(
        factory,
        config=config,
        transport_factory=lambda: replay(fixture),
        credentials=credentials,
        min_records=minimum,
    )
    assert all(v == "PASS" or v.startswith("SKIPPED") for v in report.cases.values())


def test_dip_pages_keywords_by_cursor_and_sends_key_only_as_header() -> None:
    result, sink, transport = run(
        DipDrucksachenAdapter(),
        "dip.json",
        {"profile": PROFILE, "keywords": ["EFRE", "Strukturfonds"]},
    )
    assert result.status is RunStatus.COMPLETE and result.source_exhausted
    assert sorted(k[1] for k in sink.records) == [
        "dip_270001",
        "dip_270002",
        "dip_270003",
        "dip_270004",
    ]
    assert result.pages == 5 and result.duplicates_in_run + result.duplicates_at_sink >= 1
    assert all("authorization" in c["header_names"] for c in transport.calls)
    assert all("apikey" not in c["params"] for c in transport.calls)
    assert "fixture-key-nicht-echt" not in repr(result.to_dict())
    record = sink.records[("legal.dip_bundestag", "dip_270003")]
    assert record.normalized["publication_date"] == "2019-06-01"
    assert record.normalized["classification"]["funding_period"] == "2014-2020"


def test_dip_defective_items_make_the_run_partial_not_silent() -> None:
    result, sink, _ = run(
        DipDrucksachenAdapter(), "dip_partial.json", {"profile": PROFILE, "keywords": ["EFRE"]}
    )
    assert result.status is RunStatus.PARTIAL
    assert [k[1] for k in sink.records] == ["dip_270001"]
    assert len(result.issues) == 2


def test_dip_config_is_validated_without_contacting_the_source() -> None:
    adapter = DipDrucksachenAdapter()
    for config in (
        {},
        {"profile": {"id": "x", "version": "1"}},
        {"profile": PROFILE, "keywords": ["erfunden"]},
        {"profile": PROFILE, "keywords": "EFRE"},
    ):
        with pytest.raises(Exception) as caught:
            adapter.validate_config(config)
        assert type(caught.value).__name__ == "ConfigError"


def test_eurlex_first_occurrence_wins_and_dates_are_parsed() -> None:
    result, sink, _ = run(EurLexAdapter(), "eurlex.json", {"profile": PROFILE})
    assert result.status is RunStatus.COMPLETE
    records = {k[1]: r for k, r in sink.records.items()}
    assert records["32021R1060"].normalized["title"] == "Dachverordnung 2021-2027"
    assert records["32022R0001"].normalized["title"] == "Delegierte VO zu 2021/1060 EFRE"
    assert records["32022R0001"].normalized["publication_date"] == "2022-05-04"
    assert records["52023DC0010"].normalized["date_precision"] == "month"
    assert len(records) == 7 + 3


def test_eurlex_incremental_run_uses_the_profile_update_query() -> None:
    result, sink, transport = run(
        EurLexAdapter(), "eurlex_update.json", {"profile": PROFILE}, since="2024-01-31"
    )
    assert result.status is RunStatus.COMPLETE
    assert [k[1] for k in sink.records] == ["32024R0500"]
    assert len(transport.calls) == 1


def test_curia_relevance_filter_is_explicit() -> None:
    _, everything, _ = run(CuriaFeedAdapter(), "curia.json", {"profile": PROFILE})
    _, relevant, _ = run(
        CuriaFeedAdapter(), "curia.json", {"profile": PROFILE, "relevant_only": True}
    )
    assert len(everything.records) == 3
    titles = sorted(r.normalized["title"] for r in relevant.records.values())
    assert titles == ["Urteil C-123/22 zur EFRE-Förderung", "Urteil T-45/21 Beihilfe"]


def test_eca_unavailable_page_fails_without_placeholders() -> None:
    result, sink, _ = run(EcaPublicationsAdapter(), "eca_unavailable.json", {"profile": PROFILE})
    assert result.status is RunStatus.FAILED
    assert sink.records == {}


def test_registry_lists_all_family_adapters() -> None:
    registry = register(AdapterRegistry())
    assert registry.sources() == (
        "legal.bafin",
        "legal.curia",
        "legal.dip_bundestag",
        "legal.eca",
        "legal.eurlex",
    )
    assert registry.create("legal.eurlex").source.family == "legal"


def test_catalog_entries_are_valid_and_match_the_adapters() -> None:
    import json
    from importlib import resources

    from auditcore_harvest.catalog import validate_catalog

    data = json.loads(
        resources.files("auditcore_legal_sources").joinpath("catalog.json").read_text("utf-8")
    )
    entries = {e.source_id: e for e in validate_catalog(data)}
    supported = {k for k, e in entries.items() if e.implementation == "SUPPORTED"}
    assert supported == set(register(AdapterRegistry()).sources())
    assert entries["legal.dip_bundestag"].live_test == "NOT_CONFIGURED"
    for entry in entries.values():
        for fixture in entry.data["fixtures"]:
            assert (Path(__file__).parents[1] / fixture).is_file(), fixture
    assert "fixture-key" not in json.dumps(data)
