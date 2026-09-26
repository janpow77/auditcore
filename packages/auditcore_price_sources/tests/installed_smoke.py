"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

import json
from importlib import resources
from importlib.metadata import distribution
from importlib.util import find_spec


def main() -> None:
    """Run every adapter once through the harvest engine with a synthetic replay."""
    package = distribution("auditcore_price_sources")
    assert package.version == "0.1.3"
    runtime = [r for r in package.requires or [] if "extra ==" not in r]
    assert runtime == ["auditcore_common==0.2.0", "auditcore_harvest==0.1.3"], runtime
    assert find_spec("auditcore") is None
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

    import auditcore_price_sources as ps

    registry = AdapterRegistry()
    ps.register(registry)
    assert len(registry.sources()) == 6
    catalog = json.loads((resources.files(ps) / "catalog.json").read_text("utf-8"))
    assert {e["source_id"] for e in catalog["sources"]} == set(registry.sources())
    sdmx = {
        "data": {
            "structure": {
                "dimensions": {
                    "series": [
                        {"id": "BBK_STD_CURRENCY", "values": [{"id": "USD"}]},
                        {"id": "BBK_ERX_PARTNER_CURRENCY", "values": [{"id": "EUR"}]},
                    ],
                    "observation": [{"values": [{"id": "2026-09-01"}, {"id": "2026-09-02"}]}],
                }
            },
            "dataSets": [{"series": {"0:0": {"observations": {"0": ["1.1050"], "1": [None]}}}}],
        }
    }
    url = "https://example.invalid/rest/data/BBEX3/D.USD.EUR.BB.AC.000"
    transport = ReplayTransport(
        (
            {
                "request": {"url": url, "params": {"format": "json", "lastNObservations": "30"}},
                "response": {"status": 200, "body_json": sdmx},
            },
        )
    )
    clock = FixedClock()
    sink = ListSink()
    result = HarvestEngine(
        transport=transport,
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
    ).run(
        registry.create("price.bundesbank"),
        HarvestRequest("price.bundesbank", run_id="smoke"),
        sink,
        config={"url": "https://example.invalid/rest"},
    )
    assert result.status is RunStatus.COMPLETE and ps.legacy_status(result) == "erfolg"
    values = {r.normalized["zeitbezug"]["wert"]: r.normalized for r in sink.records.values()}
    assert values["2026-09-01"]["wert"] == "1.1050"
    assert values["2026-09-02"]["status"] == "fehlwert"
    assert values["2026-09-01"]["einheit"]["text"] == "USD je 1 EUR"
    rows = ps.legacy_exchange_rate_rows(list(sink.records.values()))
    assert [str(r["kurs"]) for r in rows] == ["1.1050"]
    table = ps.parse_ffcsv("time;value;value_unit\n2026;118,4;2020=100\n2026;...;2020=100\n")
    assert table.summary()["fehlwerte"] == 1
    assert ps.check_list_response(200, b'{"ok": false, "message": "x"}') == (False, "x")
    print("PASS: installed auditcore_price_sources adapters, engine run, parsers, legacy bridges")


if __name__ == "__main__":
    main()
