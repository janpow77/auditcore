"""Bounded live smoke test: at most one small request per configured source.

    EIA_API_KEY=… TANKERKOENIG_API_KEY=… python tools/live_smoke.py --output .auditcore/live.json

Sources without configuration are reported as ``NOT_CONFIGURED`` and not
contacted. Secrets are read from the environment, passed to the credential
provider and never written. The report contains status, counts, issues and
the unit/time-reference shape of one record — no source data values.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from auditcore_harvest import (
    HarvestEngine,
    HarvestRequest,
    Response,
    RetryPolicy,
    TransportError,
)
from auditcore_harvest.memory import ListSink, MemoryStateStore, StaticCredentials

import auditcore_price_sources as sources

USER_AGENT = "auditcore_price_sources live smoke (+https://github.com/janpow77/auditcore)"


class UrllibTransport:
    """Minimal standard-library transport (only https)."""

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        data: bytes | None = None,
        timeout: float,
    ) -> Response:
        if not url.startswith("https://"):
            raise TransportError("Nur https-Adressen.", retryable=False)
        full = url + ("?" + urllib.parse.urlencode(params) if params else "")
        request = urllib.request.Request(  # noqa: S310 - https enforced above
            full, data=data, method=method, headers={"User-Agent": USER_AGENT, **(headers or {})}
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as answer:  # noqa: S310
                return Response(answer.status, answer.read(), dict(answer.headers), url)
        except urllib.error.HTTPError as error:
            return Response(error.code, error.read(), dict(error.headers or {}), url)
        except (urllib.error.URLError, TimeoutError) as error:
            raise TransportError(f"Verbindung fehlgeschlagen: {type(error).__name__}") from error


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        import time

        return time.monotonic()


class Sleeper:
    def sleep(self, seconds: float) -> None:
        import time

        time.sleep(seconds)


def shape(record: Any) -> dict[str, Any]:
    data = record.normalized
    return {
        "record_id_form": record.record_id.split("@")[0][:40],
        "zeitbezug_art": (data.get("zeitbezug") or {}).get("art"),
        "einheit": (data.get("einheit") or {}).get("text"),
        "status": data.get("status"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only", action="append", help="nur diese Quellen abrufen")
    args = parser.parse_args()
    eia = os.environ.get("EIA_API_KEY")
    tk = os.environ.get("TANKERKOENIG_API_KEY")
    plan: list[tuple[str, dict[str, Any], dict[str, Any], dict[tuple[str, str], str] | None]] = [
        (
            "price.bundesbank",
            {"url": "https://api.statistiken.bundesbank.de/rest", "last_n_observations": 5},
            {},
            {},
        ),
        (
            "price.eia_brent",
            {"url": "https://api.eia.gov/v2", "window_days": 30},
            {},
            {("price.eia_brent", "api_key"): eia} if eia else None,
        ),
        (
            "price.tankerkoenig",
            {
                "url": "https://creativecommons.tankerkoenig.de/json",
                "lat": 50.5841,
                "lng": 8.6784,
                "rad": 2,
            },
            {},
            {("price.tankerkoenig", "api_key"): tk} if tk else None,
        ),
        (
            "price.eu_oil_bulletin",
            {"url": "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en"},
            {},
            {},
        ),
        (
            "price.overpass_fuel_stations",
            {"url": "https://overpass-api.de/api/interpreter"},
            {"area_iso": "DE-HB"},
            {},
        ),
        ("price.destatis_genesis", {}, {}, None),
    ]
    report: dict[str, Any] = {"executed_at": datetime.now(UTC).isoformat(), "sources": {}}
    previous = json.loads(args.output.read_text("utf-8")) if args.output.exists() else {}
    for source_id, config, filters, secrets in plan:
        if args.only and source_id not in args.only:
            if source_id in previous.get("sources", {}):
                report["sources"][source_id] = previous["sources"][source_id]
            continue
        if secrets is None:
            report["sources"][source_id] = {
                "status": "NOT_CONFIGURED",
                "reason": "Zugangsdaten/Kennung nicht in der Umgebung",
            }
            continue
        engine = HarvestEngine(
            transport=UrllibTransport(),
            credentials=StaticCredentials({k: v for k, v in secrets.items() if v}),
            state=MemoryStateStore(),
            clock=Clock(),
            sleeper=Sleeper(),
            retry=RetryPolicy(max_attempts=1),
            request_timeout=60.0,
        )
        sink = ListSink()
        result = engine.run(
            sources.FACTORIES[source_id](),
            HarvestRequest(source_id, run_id="live-smoke", filters=filters, max_pages=3),
            sink,
            config=config,
        )
        records = list(sink.records.values())
        report["sources"][source_id] = {
            "status": (
                ("PASS" if records else "EMPTY_REVIEW_REQUIRED")
                if result.status.value in ("complete", "partial")
                else "FAIL"
            ),
            "executed_at": datetime.now(UTC).isoformat(),
            "run_status": result.status.value,
            "legacy_status": sources.legacy_status(result),
            "pages": result.pages,
            "requests": result.attempts,
            "records": len(records),
            "missing_values": sum(1 for r in records if r.normalized.get("status") == "fehlwert"),
            "issues": [i.message[:120] for i in result.issues][:5],
            "errors": [e["code"] for e in result.errors],
            "shape": shape(records[0]) if records else None,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({k: v["status"] for k, v in report["sources"].items()}))


if __name__ == "__main__":
    main()
