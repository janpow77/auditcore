"""Characterize regulierung's price/market connectors by executing the original code.

Run with the regulierung backend interpreter against a clean, GitHub-verified
checkout of the pinned commit; ``auditcore_harvest`` 0.1.0 must be importable
(the Destatis connector of that commit already uses it)::

    PYTHONPATH=<auditcore>/packages/auditcore_harvest/src \
    python -I tools/capture_regulierung_connectors.py <regulierung-checkout> \
        tests/fixtures/regulierung_connectors_observed.json

Every HTTP request goes to an in-process ``httpx.MockTransport`` that answers
with the synthetic payloads in ``tests/fixtures/payloads``; no network, no
application database (settings point to in-memory SQLite, the session is a
recording stub). Recorded per scenario: requests (method, URL, parameters,
body, whether a secret parameter was present — never its value), client
timeout, the returned ``HarvestResult``, the ORM rows the connector added,
commits and rollbacks.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import types
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

COMMIT = "853676d2b1ab792395d63c62c9f96d5edcca8c2d"
FILES = {
    "backend/app/services/external_apis/__init__.py": None,
    "backend/app/services/external_apis/base.py": None,
    "backend/app/services/external_apis/harvest_kern.py": None,
    "backend/app/services/external_apis/bundesbank.py": None,
    "backend/app/services/external_apis/destatis_genesis.py": None,
    "backend/app/services/external_apis/eia_brent.py": None,
    "backend/app/services/external_apis/eu_oil_bulletin.py": None,
    "backend/app/services/external_apis/mtsk.py": None,
    "backend/app/services/external_apis/overpass.py": None,
    "backend/app/services/external_apis/tankerkoenig.py": None,
    "backend/app/api/admin/external_apis.py": None,
}
SECRETS = {"apikey", "api_key", "password", "token"}
PAYLOADS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "payloads"


def blob(path: Path) -> str:
    raw = path.read_bytes()
    header = b"blob " + str(len(raw)).encode() + b"\0"
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return jsonable(asdict(value))
    if isinstance(value, datetime):
        return {"$datetime": "<wall-clock>"}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, bytes):
        return {"$bytes_sha256": hashlib.sha256(value).hexdigest(), "length": len(value)}
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def payload(name: str) -> bytes:
    return (PAYLOADS / name).read_bytes()


class Result:
    def __init__(self, existing: bool, rows: list[tuple[Any, ...]]) -> None:
        self._existing = existing
        self._rows = rows

    def scalar_one_or_none(self) -> Any:
        return object() if self._existing else None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self._rows


class Session:
    """Records ORM rows; ``existing_days`` simulates stored rows for dedupe queries."""

    def __init__(self, existing_days: set[date] | None = None, osm_keys: list[str] | None = None):
        self.added: list[Any] = []
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0
        self.existing_days = existing_days or set()
        self.osm_keys = osm_keys or []

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flushes += 1

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def execute(self, statement: Any) -> Result:
        params = statement.compile().params
        existing = any(v in self.existing_days for v in params.values() if isinstance(v, date))
        return Result(existing, [(k,) for k in self.osm_keys])

    def rows(self) -> list[dict[str, Any]]:
        out = []
        for obj in self.added:
            table = getattr(obj, "__table__", None)
            if table is None:
                out.append({"$type": type(obj).__name__})
                continue
            row = {"$type": type(obj).__name__}
            for column in table.columns:
                value = getattr(obj, column.key, None)
                if column.key in {"stamm_id", "gueltig_von"} and value is not None:
                    value = f"<{column.key}>"
                row[column.key] = jsonable(value)
            out.append(row)
        return out


class Recorder:
    """Routes httpx clients to a scripted MockTransport and records the requests."""

    def __init__(self, httpx: Any, script: Any) -> None:
        self.httpx = httpx
        self.script = script
        self.requests: list[dict[str, Any]] = []
        self.timeouts: list[str] = []

    def install(self) -> None:
        httpx, recorder = self.httpx, self
        self.saved = (httpx.AsyncClient, httpx.Client)

        def handler(request: Any) -> Any:
            params = dict(request.url.params.multi_items())
            body = request.content.decode("utf-8", "replace") if request.content else None
            recorder.requests.append(
                {
                    "method": request.method,
                    "url": str(request.url.copy_with(query=None)),
                    "params": {k: v for k, v in params.items() if k not in SECRETS},
                    "secret_params_present": sorted(k for k in params if k in SECRETS),
                    "body": body,
                    "accept": request.headers.get("accept"),
                    "user_agent": request.headers.get("user-agent"),
                }
            )
            return recorder.script(request, len(recorder.requests))

        original_async, original_sync = self.saved

        class AsyncClient(original_async):  # type: ignore[misc,valid-type]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                recorder.timeouts.append(repr(kwargs.get("timeout")))
                kwargs["transport"] = httpx.MockTransport(handler)
                super().__init__(*args, **kwargs)

        class Client(original_sync):  # type: ignore[misc,valid-type]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                recorder.timeouts.append(repr(kwargs.get("timeout")))
                kwargs["transport"] = httpx.MockTransport(handler)
                super().__init__(*args, **kwargs)

        httpx.AsyncClient = AsyncClient
        httpx.Client = Client

    def restore(self) -> None:
        self.httpx.AsyncClient, self.httpx.Client = self.saved


def registry(**extra: Any) -> Any:
    values = {
        "id": 1,
        "basis_url": "https://example.invalid/api",
        "secret_env_var": None,
        "auth_typ": "none",
        "konfiguration": {},
        "letzter_lauf": None,
        "letzter_status": None,
        "letzte_fehlermeldung": None,
    }
    values.update(extra)
    return types.SimpleNamespace(**values)


def capture(root: Path) -> dict[str, Any]:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["HARVEST_NULLPOOL"] = "true"
    sys.path.insert(0, str(root / "backend"))
    import app.database as database  # noqa: PLC0415
    import httpx  # noqa: PLC0415

    if not database.engine.url.drivername.startswith("sqlite"):
        raise SystemExit("Refusing to run: engine is not in-memory SQLite")
    from app.services import external_apis  # noqa: PLC0415
    from app.services.external_apis import (  # noqa: PLC0415
        bundesbank,
        destatis_genesis,
        eia_brent,
        eu_oil_bulletin,
        mtsk,
        overpass,
        tankerkoenig,
    )

    class FixedDate(date):
        @classmethod
        def today(cls) -> FixedDate:
            return cls(2026, 9, 2)

    eia_brent.date = FixedDate  # deterministic 30-day window

    def run(
        name: str,
        cls: Any,
        script: Any,
        *,
        method: str = "run",
        key: str | None = None,
        session: Session | None = None,
        **reg: Any,
    ) -> dict[str, Any]:
        recorder = Recorder(httpx, script)
        recorder.install()
        session = session or Session()
        try:
            connector = cls(registry(**reg), session)
            if key is not None:
                connector._api_key = key
            outcome = asyncio.run(getattr(connector, method)())
        except Exception as exc:  # noqa: BLE001 - observed behavior
            outcome = {"$raised": type(exc).__name__, "message": str(exc)}
        finally:
            recorder.restore()
        return {
            "scenario": name,
            "connector": cls.__name__,
            "method": method,
            "result": jsonable(outcome),
            "requests": recorder.requests,
            "client_timeouts": recorder.timeouts,
            "rows": session.rows(),
            "commits": session.commits,
            "rollbacks": session.rollbacks,
            "registry_after": {
                "letzter_status": connector.registry.letzter_status
                if "connector" in locals()
                else None,
                "letzte_fehlermeldung": connector.registry.letzte_fehlermeldung
                if "connector" in locals()
                else None,
            },
        }

    def ok(body: bytes, ctype: str = "application/json") -> Any:
        return lambda request, n: httpx.Response(200, content=body, headers={"content-type": ctype})

    def status(
        code: int, body: bytes = b"Fehlerseite", headers: dict[str, str] | None = None
    ) -> Any:
        return lambda request, n: httpx.Response(code, content=body, headers=headers or {})

    scenarios = [
        run("bundesbank-ok", bundesbank.BundesbankConnector, ok(payload("bundesbank_fx.json"))),
        run(
            "bundesbank-ok-existing-day",
            bundesbank.BundesbankConnector,
            ok(payload("bundesbank_fx.json")),
            session=Session(existing_days={date(2026, 9, 1)}),
        ),
        run(
            "bundesbank-empty", bundesbank.BundesbankConnector, ok(payload("bundesbank_empty.json"))
        ),
        run("bundesbank-http-500", bundesbank.BundesbankConnector, status(500)),
        run("bundesbank-not-json", bundesbank.BundesbankConnector, ok(b"<html>kein json</html>")),
        run(
            "bundesbank-health-head-200",
            bundesbank.BundesbankConnector,
            ok(b""),
            method="health_check",
        ),
        run(
            "eia-ok",
            eia_brent.EiaBrentConnector,
            ok(payload("eia_brent.json")),
            key="fixture-key",
            auth_typ="api_key",
        ),
        run(
            "eia-no-key",
            eia_brent.EiaBrentConnector,
            ok(payload("eia_brent.json")),
            auth_typ="api_key",
            secret_env_var="UNSET_FIXTURE_VAR",
        ),
        run("eia-no-key-harvest", eia_brent.EiaBrentConnector, ok(b"{}"), method="harvest"),
        run(
            "eia-http-403",
            eia_brent.EiaBrentConnector,
            status(403),
            key="fixture-key",
            auth_typ="api_key",
        ),
        run(
            "eu-oil-ok",
            eu_oil_bulletin.EuOilBulletinConnector,
            ok(payload("eu_oil_bulletin.html"), "text/html"),
        ),
        run("eu-oil-404", eu_oil_bulletin.EuOilBulletinConnector, status(404)),
        run(
            "tankerkoenig-health-ok",
            tankerkoenig.TankerkoenigConnector,
            ok(payload("tankerkoenig_list.json")),
            method="health_check",
            key="fixture-key",
            auth_typ="api_key",
        ),
        run(
            "tankerkoenig-health-api-error",
            tankerkoenig.TankerkoenigConnector,
            ok(payload("tankerkoenig_error.json")),
            method="health_check",
            key="fixture-key",
            auth_typ="api_key",
        ),
        run(
            "tankerkoenig-health-http-500",
            tankerkoenig.TankerkoenigConnector,
            status(500),
            method="health_check",
            key="fixture-key",
            auth_typ="api_key",
        ),
        run(
            "tankerkoenig-health-no-key",
            tankerkoenig.TankerkoenigConnector,
            ok(b"{}"),
            method="health_check",
            auth_typ="api_key",
        ),
        run(
            "tankerkoenig-run",
            tankerkoenig.TankerkoenigConnector,
            ok(payload("tankerkoenig_list.json")),
            key="fixture-key",
            auth_typ="api_key",
        ),
        run("overpass-ok", overpass.OverpassConnector, ok(payload("overpass_fuel.json"))),
        run(
            "overpass-ok-existing",
            overpass.OverpassConnector,
            ok(payload("overpass_fuel.json")),
            session=Session(osm_keys=["osm-node-1001"]),
        ),
        run("overpass-remark", overpass.OverpassConnector, ok(payload("overpass_remark.json"))),
        run("overpass-429", overpass.OverpassConnector, status(429, headers={"Retry-After": "30"})),
        run("overpass-504", overpass.OverpassConnector, status(504)),
        run("overpass-not-json", overpass.OverpassConnector, ok(b"<html>busy</html>", "text/html")),
        run("mtsk-run", mtsk.MtskConnector, status(500)),
        run("mtsk-health-unconfigured", mtsk.MtskConnector, status(500), method="health_check"),
        run(
            "mtsk-health-configured",
            mtsk.MtskConnector,
            status(500),
            method="health_check",
            konfiguration={"sftp_host": "sftp.example.invalid"},
        ),
    ]

    def destatis(request: Any, n: int) -> Any:
        name = request.url.params["name"]
        return httpx.Response(200, content=payload(f"destatis_{name}.csv"))

    for label, script, key in (
        ("destatis-ok", destatis, "fixture-token"),
        (
            "destatis-one-table-500",
            lambda r, n: httpx.Response(500) if n == 1 else destatis(r, n),
            "fixture-token",
        ),
        ("destatis-binary", lambda r, n: httpx.Response(200, content=b"PK\x03\x04\x00\x00"), "t"),
        ("destatis-no-token", destatis, None),
    ):
        scenarios.append(
            run(
                label,
                destatis_genesis.DestatisGenesisConnector,
                script,
                key=key,
                auth_typ="token",
                konfiguration={"username": "fixture-user"},
            )
        )
    static = {
        "connectors": sorted(external_apis.CONNECTORS),
        "default_timeout": external_apis.BaseConnector.DEFAULT_TIMEOUT,
        "user_agent": external_apis.BaseConnector.USER_AGENT,
        "bundesbank": {
            "flow_ref": bundesbank.BundesbankConnector.FLOW_REF,
            "series_key": bundesbank.BundesbankConnector.SERIES_KEY,
        },
        "eia_product": eia_brent.EiaBrentConnector.PRODUCT_BRENT,
        "overpass_query": overpass.HESSEN_TANKSTELLEN_QUERY,
        "tankerkoenig_probe": tankerkoenig.HESSEN_BBOX,
        "destatis_tables": destatis_genesis.KRAFTSTOFF_TABELLEN,
        "destatis_source": destatis_genesis.QUELLE.to_dict(),
    }
    return {"scenarios": scenarios, "static": static}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--migrated",
        action="store_true",
        help="migrierten Consumer-Stand erfassen (ohne Commit-/Blob-Bindung)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if not args.migrated:
        if head != COMMIT:
            raise SystemExit(f"Checkout ist {head}, erwartet {COMMIT}")
        dirty = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--", *FILES],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if dirty:
            raise SystemExit("Quelldateien sind lokal verändert")
    files = [{"path": p, "git_blob": blob(root / p)} for p in FILES]
    payloads = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PAYLOADS.iterdir())
    }
    report = {
        "status": "OBSERVED",
        "scope": "MIGRATED_CONSUMER" if args.migrated else "LOCAL_LEGACY_CHARACTERIZATION",
        "repository": "janpow77/regulierung",
        "commit": head if args.migrated else COMMIT,
        "files": files,
        "payload_sha256": payloads,
        "python": sys.version.split()[0],
        **capture(root),
    }
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{len(report['scenarios'])} Szenarien beobachtet")


if __name__ == "__main__":
    main()
