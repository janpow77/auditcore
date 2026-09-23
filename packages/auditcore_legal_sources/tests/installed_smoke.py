"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from datetime import date
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_harvest import HarvestEngine, HarvestRequest, ReplayTransport, RunStatus
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)

from auditcore_legal_sources import available_profiles, dip, eurlex, legacy, load_profile
from auditcore_legal_sources.adapters import DipDrucksachenAdapter


def main() -> None:
    """Parse, normalize and harvest DIP pages through the installed engine."""
    package = distribution("auditcore_legal_sources")
    assert package.version == "0.1.0"
    runtime = [r for r in package.requires or [] if "extra ==" not in r]
    assert runtime == ["auditcore_harvest==0.1.0"], runtime
    assert find_spec("auditcore") is None
    assert available_profiles() == (
        ("audit_designer.vp_ai", "2026.09.1"),
        ("auditdatabase.esi", "2026.09.1"),
    )
    profile = load_profile("auditdatabase.esi", "2026.09.1")
    item = {
        "id": "1",
        "titel": "EFRE-Drucksache",
        "dokumentnummer": "20/1",
        "wahlperiode": 20,
        "datum": "2024-03-15",
        "fundstelle": {},
    }
    document = dip.normalize_drucksache(item, profile)
    assert document.publication_date == date(2024, 3, 15)
    assert legacy.legacy_parse_date("2024-03-15") is None  # LS-C01 of the source
    rows = eurlex.parse_results(
        {"results": {"bindings": [{"celex": {"type": "literal", "value": "32021R1060"}}]}}
    )
    assert eurlex.normalize_row({**rows[0], "title": "VO"}, profile).document_type == "Verordnung"
    url = dip.drucksache_url(profile)
    exchanges = [
        {
            "request": {
                "method": "GET",
                "url": url,
                "params": {"format": "json", "num": "30", "f.titel": "EFRE"},
            },
            "response": {"status": 200, "body_json": {"cursor": "c1", "documents": [item]}},
        },
        {
            "request": {
                "method": "GET",
                "url": url,
                "params": {"format": "json", "num": "30", "f.titel": "EFRE", "cursor": "c1"},
            },
            "response": {"status": 200, "body_json": {"cursor": "c1", "documents": []}},
        },
    ]
    clock = FixedClock()
    engine = HarvestEngine(
        transport=ReplayTransport(exchanges),
        credentials=StaticCredentials(
            {("legal.dip_bundestag", "api_key"): "nur-fuer-den-smoke-test"}
        ),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    )
    sink = ListSink()
    result = engine.run(
        DipDrucksachenAdapter(),
        HarvestRequest("legal.dip_bundestag", "lauf-1"),
        sink,
        config={"profile": {"id": profile.id, "version": profile.version}, "keywords": ["EFRE"]},
    )
    assert result.status is RunStatus.COMPLETE, result.errors
    assert list(sink.records) == [("legal.dip_bundestag", "dip_1")]
    assert "nur-fuer-den-smoke-test" not in repr(result.to_dict())
    print("PASS: installed auditcore_legal_sources parsers, legacy adapter and harvest run")


if __name__ == "__main__":
    main()
