"""Characterize the existing harvest base contracts by executing them.

Run with an interpreter that provides httpx, SQLAlchemy and BeautifulSoup
(for example the regulierung backend venv)::

    python -I tools/capture_legacy_harvest.py <repositories-dir> \
        tests/fixtures/legacy_harvest_observed.json

Sources are the clean, GitHub-verified checkouts. Every network request goes
to an in-process ``httpx.MockTransport``; no application database is used
(regulierung settings are redirected to in-memory SQLite before import).
Each source family is executed in its own subprocess so the three unrelated
``app`` packages do not collide.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import types
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PINNED = {
    "auditdatabase": (
        "bba911e918e102426d4ca2f88fd377fe8ca585e4",
        ["backend/app/harvester/base.py", "backend/app/harvester/dip.py"],
    ),
    "audit_designer": (
        "030a71e083ef0feddc14545b095a4945bc0bbd7a",
        [
            "backend/app/modules/vp_ai/harvester/base.py",
            "backend/app/modules/vp_ai/harvester/_funding_period.py",
            "backend/app/modules/vp_ai/harvester/scheduler.py",
        ],
    ),
    "regulierung": (
        "a5d48ea4b90a410210ec25e707781ef9e21ad743",
        [
            "backend/app/services/external_apis/base.py",
            "backend/app/services/external_apis/destatis_genesis.py",
            "backend/app/services/external_apis/overpass.py",
        ],
    ),
}


def blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return jsonable(asdict(value))
    if isinstance(value, datetime):
        return {"$datetime": "<wall-clock>"} if value.year > 2025 else value.isoformat()
    if isinstance(value, bytes):
        return {"$bytes_sha256": hashlib.sha256(value).hexdigest(), "length": len(value)}
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if hasattr(value, "name") and hasattr(value, "value") and type(value).__module__ != "builtins":
        return f"{type(value).__name__}.{value.name}"
    return value


def load(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def package(*names: str) -> None:
    for name in names:
        module = types.ModuleType(name)
        module.__path__ = []  # type: ignore[attr-defined]
        sys.modules[name] = module


class Recorder:
    """httpx.AsyncClient replacement routing to a scripted MockTransport."""

    def __init__(self, httpx: Any, script: Any) -> None:
        self.httpx = httpx
        self.script = script
        self.requests: list[dict[str, Any]] = []

    def install(self) -> None:
        httpx, recorder = self.httpx, self
        original = httpx.AsyncClient

        def handler(request: Any) -> Any:
            entry = {
                "method": request.method,
                "url": str(request.url.copy_with(query=None)),
                "params": {
                    k: v for k, v in request.url.params.items() if k not in {"apikey", "password"}
                },
                "secret_params_present": sorted(
                    k for k in request.url.params if k in {"apikey", "password"}
                ),
            }
            recorder.requests.append(entry)
            return recorder.script(request, sum(1 for r in recorder.requests if "url" in r))

        class Client(original):  # type: ignore[misc,valid-type]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                recorder.requests.append({"client_timeout": repr(kwargs.get("timeout"))})
                kwargs["transport"] = httpx.MockTransport(handler)
                super().__init__(*args, **kwargs)

        class SyncClient(httpx.Client):  # type: ignore[misc]
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                recorder.requests.append({"client_timeout": repr(kwargs.get("timeout"))})
                kwargs["transport"] = httpx.MockTransport(handler)
                super().__init__(*args, **kwargs)

        self.saved_sync = httpx.Client
        httpx.AsyncClient = Client
        httpx.Client = SyncClient

    def restore(self) -> None:
        """Undo :meth:`install` for the synchronous client (async is restored by callers)."""
        self.httpx.Client = self.saved_sync


def run_case(cases: list[dict[str, Any]], name: str, call: Any) -> None:
    try:
        output, error = jsonable(call()), None
    except Exception as exc:  # noqa: BLE001 - characterization records every error
        output, error = None, {"type": type(exc).__name__, "message": str(exc)}
    cases.append({"name": name, "output": output, "exception": error})


def capture_auditdatabase(root: Path) -> dict[str, Any]:
    import httpx

    package("app", "app.harvester")
    base = load("app.harvester.base", root / "backend/app/harvester/base.py")
    dip = load("app.harvester.dip", root / "backend/app/harvester/dip.py")
    cases: list[dict[str, Any]] = []
    doc = base.HarvestedDocument
    for label, kwargs in (
        ("content", {"content": "Inhalt", "abstract": "A", "title": "T"}),
        ("abstract-only", {"abstract": "A", "title": "T"}),
        ("title-only", {"title": "T"}),
        ("empty-content-falls-back", {"content": "", "abstract": "", "title": "T"}),
    ):
        run_case(cases, f"content-hash-{label}", lambda k=kwargs: doc("s", "e", **k).content_hash)
    harvester_cls = type(
        "H", (base.BaseHarvester,), {"harvest": lambda self: None, "RELEVANT_KEYWORDS": ["EFRE"]}
    )
    h = harvester_cls()
    for value in ("2024-05-17", "2024-05-17T10:00:00", "17.05.2024", "2024", "2024-5-7", None, 42):
        run_case(cases, f"parse-date-{value!r}", lambda v=value: h._parse_date(v))
    for text in ("VO 2021/1060", "1303/2013", "Dachverordnung", "", "keine"):
        run_case(cases, f"funding-period-{text!r}", lambda t=text: h._detect_funding_period(t))
    for text in ("EFRE", "ESF+", "ESF", "Kohäsion", "", "x"):
        run_case(cases, f"fund-{text!r}", lambda t=text: h._detect_fund(t))
    for text in ("Förderung aus dem EFRE", "nichts", ""):
        run_case(cases, f"relevant-{text!r}", lambda t=text: h.is_relevant(t))
    run_case(
        cases,
        "normalize-aliases",
        lambda: h.normalize_document(
            {
                "id": "7",
                "title": "T",
                "summary": "S",
                "date": "2024",
                "link": "https://x",
                "type": "t",
            }
        ),
    )

    scenarios: dict[str, Any] = {}

    def page(n: int, ids: list[str]) -> Any:
        return httpx.Response(
            200,
            json={
                "numFound": 99,
                "cursor": f"c{n}",
                "documents": [
                    {
                        "id": i,
                        "titel": f"EFRE {i}",
                        "dokumentnummer": "21/3426",
                        "wahlperiode": 21,
                        "datum": "2024-02-01",
                        "drucksachetyp": "Antrag",
                    }
                    for i in ids
                ],
            },
        )

    def script_ok(request: Any, n: int) -> Any:
        keyword = request.url.params.get("f.titel")
        return page(n, [f"{keyword}-1", "shared"])

    def script_partial(request: Any, n: int) -> Any:
        if request.url.params.get("f.titel") == "ESF":
            return httpx.Response(500, text="boom")
        if request.url.params.get("f.titel") == "EFRE":
            raise httpx.ConnectTimeout("simulated timeout", request=request)
        return page(n, [request.url.params.get("f.titel") + "-1"])

    def script_rate(request: Any, n: int) -> Any:
        return httpx.Response(429, headers={"Retry-After": "30"}, text="slow down")

    for label, script, limit in (
        ("ok", script_ok, 200),
        ("ok-limit-5", script_ok, 5),
        ("partial-failure", script_partial, 200),
        ("rate-limited", script_rate, 200),
    ):
        recorder = Recorder(httpx, script)
        saved = httpx.AsyncClient
        recorder.install()
        try:
            result = asyncio.run(dip.DIPHarvester(api_key="fixture-key").harvest(limit=limit))
        finally:
            httpx.AsyncClient = saved
            recorder.restore()
        scenarios[f"dip-{label}"] = {
            "result": {
                **jsonable(result),
                "documents": len(result.documents),
                "first_ids": [d["id"] for d in result.documents[:3]],
                "harvested_at": "<wall-clock>",
            },
            "requests": len([r for r in recorder.requests if "url" in r]),
            "client_timeouts": sorted(
                {r["client_timeout"] for r in recorder.requests if "client_timeout" in r}
            ),
            "cursor_requested": any("cursor" in r.get("params", {}) for r in recorder.requests),
            "sample_request": next(r for r in recorder.requests if "url" in r),
        }
    return {
        "cases": cases,
        "scenarios": scenarios,
        "static": {"keyword_count": len(dip.DIPHarvester.RELEVANT_KEYWORDS)},
    }


def capture_designer(root: Path) -> dict[str, Any]:
    import httpx

    package("app", "app.modules", "app.modules.vp_ai", "app.modules.vp_ai.harvester")
    load(
        "app.modules.vp_ai.harvester._funding_period",
        root / "backend/app/modules/vp_ai/harvester/_funding_period.py",
    )
    base = load(
        "app.modules.vp_ai.harvester.base", root / "backend/app/modules/vp_ai/harvester/base.py"
    )
    cases: list[dict[str, Any]] = []
    harvester_cls = type(
        "H", (base.BaseHarvester,), {"harvest": lambda self: None, "RELEVANT_KEYWORDS": ["Spezial"]}
    )
    h = harvester_cls()
    for kwargs in (
        {"content": "Inhalt", "title": "T"},
        {"title": "T"},
        {"content": "", "abstract": "", "title": "T"},
    ):
        run_case(
            cases,
            f"content-hash-{sorted(kwargs)}",
            lambda k=kwargs: base.HarvestedDocument("s", "e", **k).content_hash,
        )
    for value in ("2024-05-17", "17.05.2024", "2024", None):
        run_case(cases, f"parse-date-{value!r}", lambda v=value: h._parse_date(v))
    for text in ("am 3.4.2024 veröffentlicht", "2024-01-02 x", "04/05/2024", ""):
        run_case(cases, f"extract-date-{text!r}", lambda t=text: h._extract_date(t))
    for text, date in (
        ("Periode 2014-2020", None),
        ("", "2023-01-01"),
        ("", None),
        ("Dachverordnung", None),
    ):
        run_case(
            cases,
            f"funding-period-{text!r}-{date!r}",
            lambda t=text, d=date: h._detect_funding_period(t, d),
        )
    for text in ("Spezial", "EFRE Hessen", "nichts"):
        run_case(cases, f"relevant-{text!r}", lambda t=text: h.is_relevant(t))
    run_case(
        cases,
        "keywords-union-size-contains-global",
        lambda: ("EFRE" in h.get_keywords(), "Spezial" in h.get_keywords()),
    )
    run_case(cases, "supports-incremental-default", lambda: base.BaseHarvester.supports_incremental)

    scenarios: dict[str, Any] = {}
    for label, response in (
        (
            "html-200",
            lambda r, n: httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html><nav>N</nav><main><p>Haupttext</p></main></html>",
            ),
        ),
        ("html-404", lambda r, n: httpx.Response(404, text="nope")),
        (
            "pdf",
            lambda r, n: httpx.Response(
                200, headers={"content-type": "application/pdf"}, content=b"%PDF"
            ),
        ),
        ("timeout", lambda r, n: (_ for _ in ()).throw(httpx.ReadTimeout("t", request=r))),
    ):
        recorder = Recorder(httpx, response)
        saved = httpx.AsyncClient
        recorder.install()
        try:
            text = asyncio.run(h._fetch_page_content("https://example.invalid/seite"))
        finally:
            httpx.AsyncClient = saved
            recorder.restore()
        scenarios[f"fetch-{label}"] = {
            "text": text,
            "client_timeouts": sorted(
                {r["client_timeout"] for r in recorder.requests if "client_timeout" in r}
            ),
        }
    scheduler = (root / "backend/app/modules/vp_ai/harvester/scheduler.py").read_text(
        encoding="utf-8"
    )
    static = {
        "per_source_timeout_slow_seconds": 1800
        if "per_source_timeout = 1800 if is_slow else 600" in scheduler
        else None,
        "per_source_timeout_api_seconds": 600
        if "per_source_timeout = 1800 if is_slow else 600" in scheduler
        else None,
        "status_values_in_scheduler": sorted(
            v for v in ("success", "partial", "failed") if f'"{v}"' in scheduler
        ),
        "pause_between_sources_seconds": 1.0 if "await asyncio.sleep(1.0)" in scheduler else None,
        "note": "Scheduler-Ablauf gelesen (DB-/Redis-gebunden), nicht ausgeführt.",
    }
    return {"cases": cases, "scenarios": scenarios, "static": static}


def capture_regulierung(root: Path) -> dict[str, Any]:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["HARVEST_NULLPOOL"] = "true"
    sys.path.insert(0, str(root / "backend"))
    import app.database as database
    import httpx

    if not database.engine.url.drivername.startswith("sqlite"):
        raise SystemExit("Refusing to run: engine is not in-memory SQLite")
    from app.services.external_apis import base
    from app.services.external_apis.destatis_genesis import DestatisGenesisConnector

    class Session:
        def __init__(self) -> None:
            self.added: list[Any] = []
            self.commits = 0

        def add(self, obj: Any) -> None:
            self.added.append(obj)

        async def flush(self) -> None:
            return None

        async def commit(self) -> None:
            self.commits += 1

    def registry(**extra: Any) -> Any:
        return types.SimpleNamespace(
            id=1,
            basis_url="https://example.invalid/genesis",
            secret_env_var=None,
            auth_typ="token",
            konfiguration={"username": "u"},
            letzter_lauf=None,
            letzter_status=None,
            letzte_fehlermeldung=None,
            **extra,
        )

    scenarios: dict[str, Any] = {}
    for label, script, token in (
        ("all-ok", lambda r, n: httpx.Response(200, text="h;a\n1;2\n3;4\n"), "t"),
        (
            "one-table-500",
            lambda r, n: httpx.Response(500) if n == 1 else httpx.Response(200, text="h\n1\n"),
            "t",
        ),
        ("all-fail", lambda r, n: httpx.Response(503), "t"),
        ("rate-limit-429", lambda r, n: httpx.Response(429, headers={"Retry-After": "5"}), "t"),
        ("no-token", lambda r, n: httpx.Response(200, text="h\n1\n"), None),
    ):
        recorder = Recorder(httpx, script)
        saved = httpx.AsyncClient
        recorder.install()
        session = Session()
        try:
            connector = DestatisGenesisConnector(registry(), session)
            connector._api_key = token
            result = asyncio.run(connector.run())
        finally:
            httpx.AsyncClient = saved
            recorder.restore()
        scenarios[f"destatis-{label}"] = {
            "result": jsonable(result),
            "requests": len([r for r in recorder.requests if "url" in r]),
            "client_timeouts": sorted(
                {r["client_timeout"] for r in recorder.requests if "client_timeout" in r}
            ),
            "protocol_rows": len(session.added),
            "commits": session.commits,
        }
    no_credentials = registry()
    no_credentials.secret_env_var = "UNSET_FIXTURE_VAR"
    session = Session()
    connector = DestatisGenesisConnector(no_credentials, session)
    result = asyncio.run(connector.run())
    scenarios["run-missing-credentials"] = {
        "result": jsonable(result),
        "protocol_rows": len(session.added),
    }
    return {
        "cases": [],
        "scenarios": scenarios,
        "static": {
            "status_values": ["erfolg", "teilweise", "fehler"],
            "default_timeout": base.BaseConnector.DEFAULT_TIMEOUT,
            "retry_implemented": False,
            "note": "Docstring nennt Retry/Rate-Limit; im Code keine Wiederholung gefunden (grep).",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repositories", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--family", choices=sorted(PINNED))
    parser.add_argument("--root", type=Path, help="migrated consumer checkout (no blob pinning)")
    args = parser.parse_args()
    if args.family:
        root = args.root or args.repositories / f"janpow77__{args.family}"
        result = {
            "auditdatabase": capture_auditdatabase,
            "audit_designer": capture_designer,
            "regulierung": capture_regulierung,
        }[args.family](root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return
    report: dict[str, Any] = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION",
        "sources": {},
    }
    for family, (commit, paths) in PINNED.items():
        root = args.repositories / f"janpow77__{family}"
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if head != commit or dirty:
            raise SystemExit(f"{family}: checkout is not the clean pinned commit")
        files = [{"path": p, "git_blob": blob(root / p)} for p in paths]
        process = subprocess.run(
            [sys.executable, "-I", __file__, str(args.repositories), "-", "--family", family],
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp")},
        )
        if process.returncode:
            raise SystemExit(f"{family} capture failed:\n{process.stderr[-3000:]}")
        report["sources"][family] = {
            "repository": f"janpow77/{family}",
            "commit": commit,
            "files": files,
            **json.loads(process.stdout.strip().splitlines()[-1]),
        }
    args.output.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                f: {"cases": len(v["cases"]), "scenarios": len(v["scenarios"])}
                for f, v in report["sources"].items()
            }
        )
    )


if __name__ == "__main__":
    main()
