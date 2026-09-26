"""Few, permitted live requests against the public sources (no credentials, no data kept).

Runs the real library functions/adapters with a standard-library transport
and records only statuses, counts and checksums — never list contents — in
``docs/live-smoke.json``. Sources that need a key (OpenSanctions matching
API) are ``NOT_CONFIGURED`` unless the key is present in the environment
variable ``OPENSANCTIONS_API_KEY``; its value is never written.

    python tools/live_smoke.py docs/live-smoke.json
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from auditcore_harvest import (
    ConfigError,
    HarvestEngine,
    HarvestRequest,
    Response,
    TransportError,
)
from auditcore_harvest.memory import ClockSleeper, ListSink, MemoryStateStore, StaticCredentials

from auditcore_registry_sources import adapters, check_vat, load_profile, lookup_register
from auditcore_registry_sources.chambers import IHK_URL, ZDH_URL, ZER_STATUS_URL, parse_zer_status

MAX = 60 * 1024 * 1024
AGENT = "auditcore-registry-sources/0.1.0 (Prüfabruf; Repository janpow77/auditcore)"


class UrllibTransport:
    """Standard-library transport (as ``auditcore_harvest/docs/examples``), redirects followed."""

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
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https"):
            raise ConfigError("Nur http(s)-Adressen.")
        if params:
            query = urllib.parse.urlencode(sorted(params.items()))
            url = f"{url}{'&' if parsed.query else '?'}{query}"
        request = urllib.request.Request(url, data=data, method=method)  # noqa: S310
        request.add_header("User-Agent", AGENT)
        for key, value in (headers or {}).items():
            request.add_header(key, value)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as reply:  # noqa: S310
                body = reply.read(MAX + 1)
                return Response(reply.status, body, dict(reply.headers.items()), reply.url)
        except urllib.error.HTTPError as error:
            return Response(error.code, error.read(MAX + 1), dict(error.headers.items()), url)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise TransportError(f"Verbindung fehlgeschlagen: {type(error).__name__}") from error


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        import time

        return time.monotonic()


def harvest(adapter: Any, config: dict[str, Any]) -> dict[str, Any]:
    clock = Clock()
    engine = HarvestEngine(
        transport=UrllibTransport(),
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),  # type: ignore[arg-type]
    )
    sink = ListSink()
    result = engine.run(
        adapter, HarvestRequest(adapter.source.source_id, run_id="live"), sink, config=config
    )
    as_of = {r.normalized.get("as_of") for r in sink.records.values()} - {None}
    return {
        "status": result.status.value,
        "records": result.records_delivered,
        "issues": len(result.issues),
        "snapshot_complete": result.snapshot_complete,
        "errors": [e.get("code") for e in result.errors],
        "as_of": sorted(as_of)[:1],
    }


def attempt(call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        outcome = call()
    except Exception as exc:  # noqa: BLE001 - every outcome is recorded
        return {"result": "FAIL", "error": f"{type(exc).__name__}: {exc}"[:300]}
    failed = outcome.get("status") in ("failed", "UNAVAILABLE") or outcome.get("errors")
    return {"result": "FAIL" if failed else "PASS", **outcome}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    designer = load_profile("audit_designer.sanctions_lists", "2026.09.1")
    lists = {i["key"]: i for i in designer.setting("lists")}
    official = {
        i["key"]: i for i in load_profile("official.sanctions_lists", "2026.09.1").setting("lists")
    }
    company = load_profile("flowinvoice.company_verification", "2026.09.1")
    transport = UrllibTransport()
    checks = {
        "registry.opensanctions_lists:eu_fsf": attempt(
            lambda: harvest(
                adapters.OpenSanctionsListAdapter(),
                {"list_key": "eu_fsf", "url": lists["eu_fsf"]["url"]},
            )
        ),
        "registry.official_sanctions_xml:un_sc": attempt(
            lambda: harvest(
                adapters.OfficialSanctionsXmlAdapter(),
                {"list_key": "un_sc", "url": official["un_sc"]["url"], "format": "un_sc_xml"},
            )
        ),
        "registry.ihk": attempt(lambda: harvest(adapters.IhkLocationsAdapter(), {"url": IHK_URL})),
        "registry.hwk": attempt(lambda: harvest(adapters.HwkPageAdapter(), {"url": ZDH_URL})),
        "registry.zer:status": attempt(
            lambda: {
                "total": parse_zer_status(
                    transport.request("GET", ZER_STATUS_URL, timeout=60).body
                ),
                "note": "Volldump (~300 MB) bewusst nicht abgerufen",
            }
        ),
        "registry.vies": attempt(lambda: {"status": check_vat(transport, "DE000000000").status}),
        "registry.offeneregister": attempt(
            lambda: lookup_register(transport, "Beispiel", company).to_dict()
        ),
    }
    if os.environ.get("OPENSANCTIONS_API_KEY"):
        checks["registry.opensanctions_match"] = {
            "result": "NOT_EXECUTED",
            "note": "Schlüssel vorhanden, Abruf nicht beauftragt",
        }
    else:
        checks["registry.opensanctions_match"] = {
            "result": "NOT_CONFIGURED",
            "note": "Kein OPENSANCTIONS_API_KEY; ein Abruf ohne Schlüssel beantwortet die API "
            "mit HTTP 401 (am 2026-09-23 einmal beobachtet).",
        }
    document = {
        "executed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "user_agent": AGENT,
        "checks": checks,
    }
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v["result"] for k, v in checks.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
