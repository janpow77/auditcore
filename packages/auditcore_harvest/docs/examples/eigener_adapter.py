"""Ausführbares Beispiel der Adapteranleitung: eigener Adapter, Registrierung, Lauf.

Aufruf ohne Netz: ``python docs/examples/eigener_adapter.py`` aus dem Paketordner.
Die Antworten stammen aus einer aufgezeichneten Fixture (ReplayTransport).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from auditcore_harvest import (
    AdapterRegistry,
    AuthKind,
    Capabilities,
    FetchContext,
    HarvestEngine,
    HarvestRecord,
    HarvestRequest,
    PageResult,
    ParserError,
    ReplayTransport,
    SnapshotSemantics,
    Source,
    raise_for_status,
    require,
)
from auditcore_harvest.memory import (
    ClockSleeper,
    FixedClock,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from auditcore_harvest.testing import assert_adapter

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "example_json_api.json"


class BeispielAdapter:
    """Schritt 1: Quelle, Versionen, Filter, Format und Fähigkeiten deklarieren."""

    source = Source(
        source_id="beispiel.register",
        title="Beispielregister (synthetisch)",
        family="beispiel",
        adapter_version="1.0.0",
        profile_version="2026.09.1",
        data_format="application/json",
        auth=AuthKind.API_KEY,
        capabilities=Capabilities(
            pagination=True, incremental=False, full_snapshot=True, deletions=True
        ),
        snapshot_semantics=SnapshotSemantics.FULL_SNAPSHOT_REPLACE,
        filters=("land",),
    )

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """Schritt 2a: Konfiguration prüfen, ohne die Quelle anzufragen."""
        require(config, "url", str)

    def fetch_page(self, context: FetchContext, cursor: Mapping[str, Any] | None) -> PageResult:
        """Schritt 2b/3/4: genau eine Seite abrufen, übersetzen, Fehler unterscheiden."""
        params = {"size": "2", "apikey": context.secret(self.source.source_id, "api_key")}
        if cursor:
            params["cursor"] = str(cursor["token"])
        response = raise_for_status(  # 429/401/5xx werden zu strukturierten Fehlern
            context.transport.request(
                "GET", str(context.config["url"]), params=params, timeout=context.timeout
            )
        )
        try:
            payload = json.loads(response.body)
            items = payload["items"]
        except (ValueError, KeyError) as exc:
            raise ParserError("Antwort hat nicht das erwartete Format.") from exc
        records = tuple(
            HarvestRecord(
                source_id=self.source.source_id,
                record_id=str(item["id"]),
                raw=item,
                normalized={"name": item["name"], "land": item["land"]},
                provenance=context.provenance(self.source, f"items/{item['id']}", item),
                deleted=item.get("deleted") is True,
            )
            for item in items
        )
        token = payload.get("next")
        return PageResult(
            records=records, next_cursor={"token": token} if token else None, complete=not token
        )


def main() -> None:
    """Schritt 5: registrieren, aus der Anwendung aufrufen, Senke und Checkpoint nutzen."""
    registry = AdapterRegistry()
    registry.register("beispiel.register", BeispielAdapter)
    clock = FixedClock()
    state = MemoryStateStore()
    sink = ListSink()
    engine = HarvestEngine(
        transport=ReplayTransport.from_file(FIXTURE),
        credentials=StaticCredentials({("beispiel.register", "api_key"): "nur-lokal"}),
        state=state,
        clock=clock,
        sleeper=ClockSleeper(clock),
    )
    config = {"url": "https://api.example.invalid/v1/items"}
    result = engine.run(
        registry.create("beispiel.register"),
        HarvestRequest("beispiel.register", run_id="lauf-1"),
        sink,
        config=config,
    )
    print(result.status.value, result.records_delivered, result.snapshot_complete)
    assert result.status.value == "complete" and result.snapshot_complete
    # Schritt 6: dieselbe Contract-Suite, die auch Adapterpakete ausführen.
    assert_adapter(
        BeispielAdapter,
        config=config,
        transport_factory=lambda: ReplayTransport.from_file(FIXTURE),
        credentials={("beispiel.register", "api_key"): "nur-lokal"},
    )
    print("Contract-Suite: PASS")


if __name__ == "__main__":
    main()
