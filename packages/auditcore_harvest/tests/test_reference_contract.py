"""The two reference adapters pass the reusable contract suite through the real engine."""

from __future__ import annotations

from pathlib import Path

from auditcore_harvest.reference import (
    FeedAdapter,
    JsonApiAdapter,
    example_feed_source,
    example_json_source,
)
from auditcore_harvest.testing import assert_adapter
from auditcore_harvest.transport import ReplayTransport

FIXTURES = Path(__file__).parent / "fixtures"


def json_adapter() -> JsonApiAdapter:
    return JsonApiAdapter(example_json_source(), api_key_param="apikey")


def test_json_api_reference_adapter_passes_contract() -> None:
    report = assert_adapter(
        json_adapter,
        config={"url": "https://api.example.invalid/v1/items", "page_size": 2},
        transport_factory=lambda: ReplayTransport.from_file(FIXTURES / "example_json_api.json"),
        credentials={("example.json_api", "api_key"): "geheimer-fixture-schluessel"},
        min_records=5,
    )
    assert report.cases["missing_credentials"] == "PASS"


def test_feed_reference_adapter_passes_contract() -> None:
    report = assert_adapter(
        lambda: FeedAdapter(example_feed_source()),
        config={"url": "https://feed.example.invalid/rss"},
        transport_factory=lambda: ReplayTransport.from_file(FIXTURES / "example_feed.json"),
        min_records=2,
    )
    assert report.cases["missing_credentials"].startswith("SKIPPED")
