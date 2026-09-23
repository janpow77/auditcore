"""Minimal live smoke: at most one result page per portal.

Manual tool, not part of the test suite. Since the user decision of
2026-09-23 (PS-D01) the adapters run with the default
``robots_policy="ignore"``, so the Kleinanzeigen search (``/*/preis:*``) and one
ZVG detail page (``showZvg``) are requested as well, exactly once each. Terms
of use are **not** reviewed (REVIEW_REQUIRED), so the result documents
technical reachability and parser fit only. Only aggregates are written — no
ad texts, names or addresses::

    python tools/live_smoke.py <output.json>
"""

from __future__ import annotations

import http.cookiejar
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from auditcore_harvest import (
    ConfigError,
    HarvestEngine,
    HarvestRequest,
    Response,
    RetryPolicy,
    TransportError,
)
from auditcore_harvest.memory import ListSink, MemoryStateStore, StaticCredentials

from auditcore_property_sources.adapters import (
    BieniciAdapter,
    CityaAdapter,
    ImmobilienDeAdapter,
    InBerlinWohnenAdapter,
    KleinanzeigenAdapter,
    ParuvenduAdapter,
    ZvgDetailAdapter,
    ZvgListingAdapter,
)

AGENT = "auditcore-property-sources-smoke/0.1 (einmalige Strukturpruefung, janpow77/auditcore)"
FIELDS = ("plz", "flaeche_qm", "kaltmiete", "gesamtmiete", "preisart", "file_number", "court_id")


class CookieTransport:
    """Standard-library HTTP(S) transport with a session cookie jar."""

    def __init__(self) -> None:
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.calls: list[str] = []

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
        if parsed.scheme != "https":
            raise ConfigError("Nur https-Adressen.")
        if params:
            url = f"{url}{'&' if parsed.query else '?'}{urllib.parse.urlencode(params)}"
        self.calls.append(f"{method} {urllib.parse.urlsplit(url).netloc}")
        request = urllib.request.Request(url, data=data, method=method)  # noqa: S310
        request.add_header("User-Agent", AGENT)
        for key, value in (headers or {}).items():
            request.add_header(key, value)
        try:
            with self.opener.open(request, timeout=timeout) as reply:
                return Response(reply.status, reply.read(8_000_000), dict(reply.headers), url)
        except urllib.error.HTTPError as error:
            return Response(error.code, error.read(100_000), dict(error.headers), url)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise TransportError(f"Verbindung fehlgeschlagen: {type(error).__name__}") from error


def smoke(
    name: str, adapter: Any, config: dict[str, Any], first: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    transport = CookieTransport()
    sink = ListSink()
    result = HarvestEngine(
        transport=transport,
        credentials=StaticCredentials({}),
        state=MemoryStateStore(),
        clock=_Clock(),
        sleeper=_Sleeper(),
        retry=RetryPolicy(max_attempts=1),
    ).run(
        adapter,
        HarvestRequest(adapter.source.source_id, run_id=f"smoke-{name}", max_pages=1),
        sink,
        config=config,
    )
    records = [dict(r.normalized) for r in sink.records.values()]
    if first is not None and records:
        first.append(records[0])
    return {
        "source_id": adapter.source.source_id,
        "requests": transport.calls,
        "status": result.status.value,
        "pages": result.pages,
        "records": len(records),
        "issues": len(result.issues),
        "errors": [e["code"] for e in result.errors],
        "field_presence": {
            f: sum(1 for r in records if r.get(f) not in (None, ""))
            for f in FIELDS
            if any(f in r for r in records)
        },
        "total_hint_seen": result.to_dict().get("records_received"),
    }


class _Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        import time

        return time.monotonic()


class _Sleeper:
    def sleep(self, seconds: float) -> None:
        import time

        time.sleep(seconds)


def main() -> int:
    runs = {
        "immobilien_de": (ImmobilienDeAdapter({}), {"max_price": 700, "pages": 1}),
        "inberlinwohnen": (InBerlinWohnenAdapter(), {}),
        "bienici": (BieniciAdapter(), {"zones": ["-7415"], "page_size": 24, "max_pages": 1}),
        "citya": (CityaAdapter(), {"departements": ["bas-rhin-67"], "max_pages": 1}),
        "paruvendu": (
            ParuvenduAdapter(),
            {"departements": ["bas-rhin-67"], "kinds": ["appartement"], "max_pages": 1},
        ),
        "kleinanzeigen": (KleinanzeigenAdapter({}), {"max_price": 700, "pages": 1}),
    }
    results = {name: smoke(name, adapter, config) for name, (adapter, config) in runs.items()}
    notices: list[dict[str, Any]] = []
    results["zvg_liste"] = smoke("zvg_liste", ZvgListingAdapter(), {"courts": ["M1201"]}, notices)
    if notices:
        notice = {k: notices[0][k] for k in ("zvg_id", "court_id", "file_number")}
        results["zvg_detail"] = smoke("zvg_detail", ZvgDetailAdapter(), {"notices": [notice]})
    report = {
        "executed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "user_agent": AGENT,
        "terms_of_use": "REVIEW_REQUIRED",
        "robots_policy": "ignore (Nutzerentscheidung 2026-09-23, PS-D01)",
        "results": results,
    }
    with open(sys.argv[1], "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1)
    print(
        json.dumps(
            {k: (v["status"], v["records"], v["errors"]) for k, v in report["results"].items()},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
