"""Begrenzter Live-Abruf gegen den öffentlichen Nominatim-Dienst (höchstens zwei Anfragen).

Nur mit ausdrücklichem ``--ausfuehren``; sonst Status NOT_EXECUTED. Aufgezeichnet
werden Status, Trefferzahl und Hashes – keine OSM-Inhalte (ODbL) und keine Kontaktdaten.

    python tools/live_smoke.py --ausfuehren --transport <harvest>/docs/examples/urllib_transport.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from auditcore_harvest import HarvestEngine
from auditcore_harvest.memory import ListSink, MemoryStateStore, StaticCredentials

from auditcore_geo import __version__
from auditcore_geo.nominatim import NominatimAdapter, empfohlene_laufparameter

ANFRAGEN = [
    {"id": "bkg", "q": "Richard-Strauss-Allee 11, 60598 Frankfurt am Main"},
    {"id": "wiesbaden", "q": "Kaiser-Friedrich-Ring 75, 65185 Wiesbaden"},
]


class _Uhr:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        import time

        return time.monotonic()


class _Schlaf:
    def sleep(self, seconds: float) -> None:
        import time

        time.sleep(seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ausfuehren", action="store_true")
    parser.add_argument("--transport", type=Path, required=True)
    args = parser.parse_args()
    if not args.ausfuehren:
        print(json.dumps({"status": "NOT_EXECUTED"}))
        return 0
    spec = importlib.util.spec_from_file_location("urllib_transport", args.transport)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    kennung = f"auditcore_geo/{__version__} (+https://github.com/janpow77/auditcore)"
    konfig: dict[str, Any] = {
        "anfragen": ANFRAGEN,
        "user_agent": kennung,
        "budget": len(ANFRAGEN),
        "laufart": "einmalig",
        "countrycodes": "de",
        "limit": 1,
    }
    rate, request = empfohlene_laufparameter(konfig, "live-smoke", heute_bereits_gesendet=0)
    engine = HarvestEngine(
        modul.UrllibTransport(kennung),
        StaticCredentials({}),
        MemoryStateStore(),
        _Uhr(),
        _Schlaf(),
        rate_limit=rate,
        request_timeout=20.0,
    )
    sink = ListSink()
    result = engine.run(NominatimAdapter(), request, sink, config=konfig)
    zusammenfassung = {
        "status": "PASS" if result.status.value == "complete" else "FAIL",
        "run_status": result.status.value,
        "zeit": datetime.now(UTC).isoformat(timespec="seconds"),
        "rate_limit_s": rate.min_interval_seconds,
        "anfragen": len(ANFRAGEN),
        "datensaetze": {
            r.record_id: {
                "status": r.normalized["status"],
                "anzahl": r.normalized["anzahl"],
                "raw_sha256": r.provenance.raw_sha256,
                "lizenz_osm": "OpenStreetMap" in str(r.normalized["lizenz"]),
            }
            for r in sink.records.values()
        },
    }
    print(json.dumps(zusammenfassung, ensure_ascii=False))
    return 0 if zusammenfassung["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
