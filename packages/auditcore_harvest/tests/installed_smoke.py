"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

import json
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_harvest import CONTRACT_VERSION, HarvestEngine, HarvestRequest, ReplayTransport
from auditcore_harvest.catalog import load_catalog, summary
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.reference import FeedAdapter, example_feed_source
from auditcore_harvest.testing import assert_adapter

FEED = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>A</title><guid>urn:a</guid></item><item><title>B</title><guid>urn:b</guid></item>
</channel></rss>"""


def main() -> None:
    """Catalogue, engine run and contract suite from the installed package."""
    package = distribution("auditcore_harvest")
    assert package.version == "0.1.0"
    assert not [r for r in package.requires or [] if "extra ==" not in r]
    assert find_spec("auditcore") is None
    assert CONTRACT_VERSION == "auditcore_harvest.contract/1"
    entries = load_catalog()
    assert len(entries) == 62
    assert summary(entries)["implementation"] == {"PLANNED": 53, "SUPPORTED": 7, "LEGACY_ONLY": 2}
    exchanges = [
        {
            "request": {"url": "https://feed.invalid/rss"},
            "response": {"status": 200, "body_text": FEED},
        }
    ]
    clock = FixedClock()
    engine = HarvestEngine(
        ReplayTransport(exchanges),
        StaticCredentials(),
        MemoryStateStore(),
        clock,
        ClockSleeper(clock),
    )
    sink = ListSink()
    result = engine.run(
        FeedAdapter(example_feed_source()),
        HarvestRequest("example.feed", "smoke"),
        sink,
        config={"url": "https://feed.invalid/rss"},
    )
    assert result.status.value == "complete" and result.records_delivered == 2
    assert_adapter(
        lambda: FeedAdapter(example_feed_source()),
        config={"url": "https://feed.invalid/rss"},
        transport_factory=lambda: ReplayTransport(exchanges),
        min_records=2,
    )
    print(json.dumps({"status": "PASS", "records": result.records_delivered}))


if __name__ == "__main__":
    main()
