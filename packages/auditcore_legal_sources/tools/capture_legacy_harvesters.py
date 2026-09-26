"""Capture actual DIP/EUR-Lex harvester behavior of two source applications.

Run with an interpreter that provides httpx, SPARQLWrapper and SQLAlchemy::

    python -I tools/capture_legacy_harvesters.py \
        --auditdatabase <checkout>/backend --designer <checkout>/backend \
        tests/fixtures/legacy_harvesters_observed.json

The tool never imports ``auditcore_legal_sources``. It verifies every executed
file against its pinned Git blob, loads the harvester modules without their
package ``__init__`` (no application settings, database or other harvesters),
replaces ``httpx.AsyncClient`` inside the modules with a recording fake and
stubs the SPARQL call. No network request is made; all responses are
synthetic, in the documented original response formats.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import types
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

SOURCES = {
    "auditdatabase": {
        "repository": "janpow77/auditdatabase",
        "commit": "bba911e918e102426d4ca2f88fd377fe8ca585e4",
        "package": "app.harvester",
        "directory": "app/harvester",
        "blobs": {
            "base.py": "fcefbe13ecdd3d8bb1fff83f04a53c56ad700c4b",
            "dip.py": "de4a26ed623989ef6b84dec92b3d7c1e7eb3af62",
            "eurlex.py": "3bad9865dc13fbc2c21e195741f77864ae3fd4f2",
        },
    },
    "designer": {
        "repository": "janpow77/audit_designer",
        "commit": "030a71e083ef0feddc14545b095a4945bc0bbd7a",
        "package": "app.modules.vp_ai.harvester",
        "directory": "app/modules/vp_ai/harvester",
        "blobs": {
            "_funding_period.py": "f67579071cfdb8c03ec249de231675e792c58966",
            "base.py": "7e5b9b652c9db72c8c661e38a8e5f7ce10d7f86e",
            "bundestag_dip.py": "6fa48fc0301f9bc8e92822d2ce1ab9ef515cb344",
            "eurlex.py": "c0cc8d9483f325cb1fd48707d2051fe747985fd3",
        },
    },
}


#: Set by ``--migrated``: a consumer after migration is loaded without the
#: pinned-blob/commit check; the actual blobs and the library origin are recorded.
MIGRATED = False


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, Enum):
        return {"$enum": value.name}
    if is_dataclass(value) and not isinstance(value, type):
        return jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, set):
        return sorted(jsonable(v) for v in value)
    return value


def error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def load(variant: str, backend: Path) -> dict[str, types.ModuleType]:
    spec = SOURCES[variant]
    directory = backend / str(spec["directory"])
    for name, blob in dict(spec["blobs"]).items():
        if git_blob(directory / name) != blob and not MIGRATED:
            raise SystemExit(f"{variant}/{name} does not match the pinned GitHub blob")
    head = subprocess.run(
        ["git", "-C", str(backend), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != spec["commit"] and not MIGRATED:
        raise SystemExit(f"{variant} checkout is not at the pinned commit")
    package = str(spec["package"])
    parts = package.split(".")
    for index in range(1, len(parts) + 1):
        name = ".".join(parts[:index])
        if name not in sys.modules:
            module = types.ModuleType(name)
            module.__path__ = []  # type: ignore[attr-defined]
            sys.modules[name] = module
    sys.modules[package].__path__ = [str(directory)]  # type: ignore[attr-defined]
    modules = {}
    for name in dict(spec["blobs"]):
        full = f"{package}.{name[:-3]}"
        module_spec = importlib.util.spec_from_file_location(full, directory / name)
        assert module_spec and module_spec.loader
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[full] = module
        module_spec.loader.exec_module(module)
        modules[name[:-3]] = module
    return modules


class FakeResponse:
    def __init__(self, status_code: int, payload: Any = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return copy.deepcopy(self._payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeClientFactory:
    """Replaces ``httpx.AsyncClient``; answers from a routing function and records calls."""

    def __init__(self, route: Any) -> None:
        self.route = route
        self.calls: list[dict[str, Any]] = []

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        factory = self
        init = {"timeout": kwargs.get("timeout"), "headers": kwargs.get("headers")}

        class Client:
            async def __aenter__(self) -> Client:
                return self

            async def __aexit__(self, *exc: Any) -> None:
                return None

            async def get(self, url: str, params: Any = None, headers: Any = None) -> Any:
                call = {
                    "url": url,
                    "params": copy.deepcopy(params),
                    "headers": headers,
                    "client": init,
                }
                factory.calls.append(call)
                return factory.route(call)

        return Client()


def drucksache(n: int, **extra: Any) -> dict[str, Any]:
    """Synthetic DIP ``drucksache`` item in the documented API response shape."""
    base = {
        "id": str(270000 + n),
        "titel": f"Synthetische Drucksache {n} zur EFRE-Förderung",
        "dokumentnummer": f"20/{1000 + n}",
        "wahlperiode": 20,
        "datum": "2024-03-15",
        "drucksachetyp": "Kleine Anfrage",
        "fundstelle": {"pdf_url": f"https://example.invalid/btd/20/{n}.pdf"},
        "urheber": [{"titel": "Fraktion X"}],
        "autoren_anzeige": [],
        "vorgangsbezug": [],
        "abstract": "",
    }
    base.update(extra)
    return base


NEUTRALIZED = (
    "Institutsnamen der Quelle durch neutrale Begriffe ersetzt "
    "(quality/institutsnamen-denylist.txt); sonst unverändert beobachtet."
)


def _neutral(text: str) -> str:
    """Institution names replaced as listed in the repository denylist."""
    script = Path(__file__).resolve().parents[3] / "scripts" / "check_institution_names.py"
    spec = importlib.util.spec_from_file_location("check_institution_names", script)
    assert spec is not None and spec.loader is not None
    module = sys.modules[spec.name] = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return str(module.neutralize(text))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auditdatabase", type=Path, required=True)
    parser.add_argument("--designer", type=Path, required=True)
    parser.add_argument("output", type=Path)
    parser.add_argument("--migrated", action="store_true")
    args = parser.parse_args()
    global MIGRATED
    MIGRATED = args.migrated
    cases: list[dict[str, Any]] = []

    def observe(variant: str, name: str, operation: str, inputs: Any, call: Any) -> None:
        before = copy.deepcopy(inputs)
        try:
            output = jsonable(call())
            exception = None
        except Exception as exc:  # noqa: BLE001 - every error is recorded
            output, exception = None, error(exc)
        if inputs != before:
            raise AssertionError(f"{name} mutated its input")
        cases.append(
            {
                "variant": variant,
                "name": name,
                "operation": operation,
                "inputs": jsonable(inputs),
                "output": output,
                "exception": exception,
            }
        )

    adb = load("auditdatabase", args.auditdatabase.resolve())
    base, dip, eurlex = adb["base"], adb["dip"], adb["eurlex"]

    class Probe(base.BaseHarvester):
        source_id = "probe"
        RELEVANT_KEYWORDS = ["EFRE", "Vergabe"]

        async def harvest(self) -> Any:
            raise NotImplementedError

    probe = Probe()
    date_inputs = [
        None,
        "2024-03-15",
        "2024-03-15T10:20:30",
        "15.03.2024",
        "2024",
        "1999",
        "9",
        "",
        "kein Datum",
        "2024-13-45",
        "20240315",
        20240315,
        datetime(2024, 3, 15, 8, 0),
    ]
    for value in date_inputs:
        observe(
            "auditdatabase",
            f"parse-date-{value!r}",
            "parse_date",
            {"value": value},
            lambda v=value: probe._parse_date(v),
        )
    texts = [
        "",
        None,
        "VO (EU) 2021/1060",
        "Förderperiode 2021-2027",
        "Dachverordnung",
        "VO 1303/2013",
        "2014-2020",
        "EFRE und ESF",
        "ERDF",
        "ESF+ Programm",
        "ESF plus",
        "ESF",
        "Kohäsionsfonds",
        "cohesion",
        "Sonstiges",
        "efre klein",
        "VO 1083/2006",
        "2007-2013",
        "1994-1999",
        "VO 2021/1058",
        "1260/1999",
        "ERDF Programm 2014-2020",
    ]
    for text in texts:
        observe(
            "auditdatabase",
            f"funding-period-{text!r}",
            "detect_funding_period",
            {"text": text},
            lambda t=text: probe._detect_funding_period(t),
        )
        observe(
            "auditdatabase",
            f"fund-{text!r}",
            "detect_fund",
            {"text": text},
            lambda t=text: probe._detect_fund(t),
        )
    for text in ["", None, "efre im Titel", "Vergabeverfahren", "ohne Bezug", "EfRe"]:
        observe(
            "auditdatabase",
            f"relevant-{text!r}",
            "is_relevant",
            {"text": text},
            lambda t=text: probe.is_relevant(t),
        )
    for raw in [
        {"id": "a", "title": "T", "content": "C", "date": "2024", "url": "https://x"},
        {"external_id": "b", "title": "T2", "summary": "S", "link": "https://y", "type": "R"},
        {},
    ]:
        observe(
            "auditdatabase",
            f"normalize-{sorted(raw)}",
            "normalize_document",
            raw,
            lambda r=raw: probe.normalize_document(r),
        )
    for content, abstract, title in [
        ("C", "A", "T"),
        (None, "A", "T"),
        (None, None, "T"),
        ("", "", "T"),
        (None, None, ""),
    ]:
        doc = base.HarvestedDocument(
            source_id="s", external_id="e", title=title, content=content, abstract=abstract
        )
        observe(
            "auditdatabase",
            f"hash-{content}-{abstract}-{title}",
            "content_hash",
            {"content": content, "abstract": abstract, "title": title},
            lambda d=doc: d.content_hash,
        )

    harvester = dip.DIPHarvester(api_key="TEST-KEY")
    for name, item in [
        ("full", drucksache(1)),
        ("no-fundstelle", drucksache(2, fundstelle=None)),
        ("fundstelle-string", drucksache(3, fundstelle="kaputt")),
        ("constructed-pdf", drucksache(4, fundstelle={})),
        ("old-period", drucksache(5, datum="2019-01-01", fundstelle={})),
        ("esf-title", drucksache(6, titel="ESF+ und Sozialfonds")),
        ("interreg-title", drucksache(7, titel="Interreg-Programme")),
        ("no-number", drucksache(8, dokumentnummer="", fundstelle={})),
        (
            "legacy-number-key",
            {**drucksache(9, fundstelle={}), "dokumentnummer": None, "drucksacheNummer": "19/77"},
        ),
        ("bad-number", drucksache(10, dokumentnummer="ohne-schraegstrich", fundstelle={})),
        ("bad-date", drucksache(11, datum="unbekannt")),
        ("abstract", drucksache(12, abstract="Kurzfassung")),
        ("empty", {}),
    ]:
        observe(
            "auditdatabase",
            f"dip-normalize-{name}",
            "dip_normalize",
            item,
            lambda i=item: harvester._normalize_drucksache(i),
        )

    def dip_route(call: dict[str, Any]) -> Any:
        keyword = (call["params"] or {}).get("f.titel")
        if keyword == "ESF":
            return FakeResponse(500, {"errors": "synthetic"})
        if keyword == "ESF+":
            raise RuntimeError("synthetic transport failure")
        if keyword == "EFRE":
            return FakeResponse(
                200,
                {
                    "numFound": 3,
                    "cursor": "c1",
                    "documents": [drucksache(1), drucksache(2), drucksache(1)],
                },
            )
        if keyword == "Strukturfonds":
            return FakeResponse(200, {"numFound": 2, "documents": [drucksache(2), drucksache(3)]})
        if keyword == "Kohäsionspolitik":
            return FakeResponse(200, ValueError("invalid json"))
        return FakeResponse(200, {"numFound": 0, "documents": []})

    for limit in (200, 2):
        factory = FakeClientFactory(dip_route)
        dip.httpx.AsyncClient = factory
        result = asyncio.run(harvester.harvest(limit=limit))
        cases.append(
            {
                "variant": "auditdatabase",
                "name": f"dip-harvest-limit-{limit}",
                "operation": "dip_harvest",
                "inputs": {"limit": limit},
                "output": {"result": jsonable(result), "calls": factory.calls},
                "exception": None,
            }
        )
    factory = FakeClientFactory(lambda call: FakeResponse(503, {}))
    dip.httpx.AsyncClient = factory
    result = asyncio.run(harvester.harvest())
    cases.append(
        {
            "variant": "auditdatabase",
            "name": "dip-harvest-all-failing",
            "operation": "dip_harvest",
            "inputs": {"limit": 200},
            "output": {"result": jsonable(result), "calls": len(factory.calls)},
            "exception": None,
        }
    )
    dip.httpx.AsyncClient = FakeClientFactory(lambda call: FakeResponse(200, {"id": "v"}))
    for name, coro in [
        ("dip-get-vorgang", lambda: harvester.get_vorgang("1")),
        ("dip-test-connection", lambda: harvester.test_connection()),
    ]:
        try:
            output, exception = jsonable(asyncio.run(coro())), None
        except Exception as exc:  # noqa: BLE001
            output, exception = None, error(exc)
        cases.append(
            {
                "variant": "auditdatabase",
                "name": name,
                "operation": "dip_misc",
                "inputs": {},
                "output": output,
                "exception": exception,
            }
        )
    cases.append(
        {
            "variant": "auditdatabase",
            "name": "dip-default-key-present",
            "operation": "dip_misc",
            "inputs": {},
            "output": {"has_default_key": bool(harvester.DEFAULT_API_KEY), "key_in_query": True},
            "exception": None,
        }
    )

    lex = eurlex.EURLexHarvester()
    for celex in [
        "",
        "32021R1060",
        "32019L0001",
        "32020D0002",
        "32021X0001",
        "52022DC0001",
        "62019CJ0001",
        "12012E",
        "R",
    ]:
        observe(
            "auditdatabase",
            f"celex-type-{celex}",
            "celex_type",
            {"celex": celex},
            lambda c=celex: lex._detect_document_type(c),
        )
    for name, raw in [
        (
            "core",
            {
                "celex": "32021R1060",
                "title": "Dachverordnung 2021-2027",
                "funding_period": "2021-2027",
                "source": "core_documents",
            },
        ),
        (
            "query",
            {
                "celex": "32022R0001",
                "title": "Delegierte Verordnung zu 2021/1060 EFRE",
                "date": "2022-05-04",
                "type": "REG_DEL",
                "source": "delegated_regulations",
            },
        ),
        ("no-date", {"celex": "52023DC0010", "title": "Mitteilung Kohäsion", "source": "x"}),
        ("empty", {}),
    ]:
        observe(
            "auditdatabase",
            f"eurlex-normalize-{name}",
            "eurlex_normalize",
            raw,
            lambda r=raw: lex._normalize_eurlex_doc(r),
        )

    class FakeSparql:
        def __init__(self, bindings: list[dict[str, Any]]) -> None:
            self.bindings = bindings
            self.queries: list[str] = []

        def setQuery(self, query: str) -> None:  # noqa: N802 - SPARQLWrapper API
            self.queries.append(query)

        def query(self) -> Any:
            outer = self

            class Result:
                def convert(self) -> Any:
                    return {
                        "head": {"vars": ["celex", "title", "date"]},
                        "results": {"bindings": copy.deepcopy(outer.bindings)},
                    }

            return Result()

    bindings = [
        {
            "celex": {"type": "literal", "value": "32022R0001"},
            "title": {"type": "literal", "xml:lang": "de", "value": "Delegierte VO EFRE"},
            "date": {"type": "typed-literal", "value": "2022-05-04"},
        },
        {
            "celex": {"type": "literal", "value": "32021R1060"},
            "title": {"type": "literal", "value": "Doppelt"},
        },
        {"title": {"type": "literal", "value": "Ohne CELEX"}},
    ]
    lex.sparql = FakeSparql(bindings)
    parsed = asyncio.run(lex._execute_sparql("SELECT"))
    cases.append(
        {
            "variant": "auditdatabase",
            "name": "eurlex-execute-sparql",
            "operation": "eurlex_sparql_parse",
            "inputs": {"bindings": bindings},
            "output": jsonable(parsed),
            "exception": None,
        }
    )

    async def fake_execute(query: str) -> list[dict[str, str]]:
        if "Delegierte" in query:
            raise RuntimeError("synthetic SPARQL timeout")
        if "Durchführung" in query:
            return [{"celex": "32023R0002", "title": "Durchführungs-VO ESF", "date": "2023-01-02"}]
        return [
            {"celex": "32021R1060", "title": "Dublette"},
            {"celex": "32022R0001", "title": "Kohäsion 2021/1060", "date": "2022-05-04"},
        ]

    lex._execute_sparql = fake_execute
    result = asyncio.run(lex.harvest())
    cases.append(
        {
            "variant": "auditdatabase",
            "name": "eurlex-harvest",
            "operation": "eurlex_harvest",
            "inputs": {},
            "output": jsonable(result),
            "exception": None,
        }
    )
    captured: list[str] = []

    async def capture(query: str) -> list[dict[str, str]]:
        captured.append(query)
        return []

    lex._execute_sparql = capture
    asyncio.run(lex.check_for_updates(datetime(2024, 1, 31)))
    cases.append(
        {
            "variant": "auditdatabase",
            "name": "eurlex-update-query",
            "operation": "eurlex_update_query",
            "inputs": {"since": "2024-01-31"},
            "output": captured[0],
            "exception": None,
        }
    )
    profile = {
        "global_keywords_de": list(base.GLOBAL_KEYWORDS_DE),
        "global_keywords_en": list(base.GLOBAL_KEYWORDS_EN),
        "dip_keywords": list(dip.DIPHarvester.RELEVANT_KEYWORDS),
        "dip_base_url": dip.DIPHarvester.BASE_URL,
        "eurlex_queries": dict(eurlex.EURLexHarvester.QUERIES),
        "eurlex_core_documents": list(eurlex.EURLexHarvester.CORE_DOCUMENTS),
        "eurlex_endpoint": eurlex.EURLexHarvester.SPARQL_ENDPOINT,
        "eurlex_base_url": eurlex.EURLexHarvester.EURLEX_BASE_URL,
    }

    # ------------------------------------------------------------ designer
    des = load("designer", args.designer.resolve())
    dbase, ddip, dlex = des["base"], des["bundestag_dip"], des["eurlex"]
    dharvester = ddip.BundestagDIPHarvester()
    for value in date_inputs:
        observe(
            "designer",
            f"parse-date-{value!r}",
            "parse_date",
            {"value": value},
            lambda v=value: dharvester._parse_date(v),
        )
    for text in texts:
        observe(
            "designer",
            f"funding-period-{text!r}",
            "detect_funding_period",
            {"text": text},
            lambda t=text: dharvester._detect_funding_period(t),
        )
        observe(
            "designer",
            f"fund-{text!r}",
            "detect_fund",
            {"text": text},
            lambda t=text: dharvester._detect_fund(t),
        )
    for text, date in [("", "2019-01-01"), (None, "2024"), ("x", "abc"), ("", None)]:
        observe(
            "designer",
            f"funding-period-date-{text!r}-{date!r}",
            "detect_funding_period",
            {"text": text, "publication_date": date},
            lambda t=text, d=date: dbase.detect_funding_period(t, d),
        )
    for name, item in [
        ("full", drucksache(1)),
        ("no-title", drucksache(2, titel="")),
        ("long-date", drucksache(3, datum="2024-03-15T00:00:00+01:00")),
        ("empty", {}),
    ]:
        observe(
            "designer",
            f"dip-parse-drucksache-{name}",
            "designer_dip_drucksache",
            {"item": item, "query": "EFRE"},
            lambda i=item: dharvester._parse_drucksache(i, "EFRE"),
        )
    vorgang = {
        "id": "9",
        "titel": "Vorgang EFRE",
        "aktualisiert": "2024-02-01T10:00:00",
        "vorgangstyp": "Gesetzgebung",
        "wahlperiode": 20,
    }
    for name, item in [("full", vorgang), ("no-title", {**vorgang, "titel": ""})]:
        observe(
            "designer",
            f"dip-parse-vorgang-{name}",
            "designer_dip_vorgang",
            {"item": item, "query": "EFRE"},
            lambda i=item: dharvester._parse_vorgang(i, "EFRE"),
        )
    dlexh = dlex.EURLexHarvester()
    for name, raw in [
        (
            "core",
            {
                "celex": "32021R1060",
                "title": "Dachverordnung 2021-2027 (VO 2021/1060)",
                "funding_period": "2021-2027",
                "source": "core_documents",
            },
        ),
        (
            "query",
            {
                "celex": "32022R0001",
                "title": "Delegierte Verordnung zu 2021/1060 EFRE",
                "date": "2022-05-04",
                "type": "REG_DEL",
                "source": "delegated_regulations",
            },
        ),
        ("empty", {}),
    ]:
        observe(
            "designer",
            f"eurlex-normalize-{name}",
            "eurlex_normalize",
            raw,
            lambda r=raw: dlexh._normalize_eurlex_doc(r),
        )
    profile["designer_dip_queries"] = list(ddip.BundestagDIPHarvester.SEARCH_QUERIES)
    profile["designer_eurlex_core_documents"] = list(dlex.EURLexHarvester.CORE_DOCUMENTS)
    profile["designer_eurlex_queries"] = dict(dlex.EURLexHarvester.QUERIES)
    profile["designer_dip_keywords"] = list(ddip.BundestagDIPHarvester.RELEVANT_KEYWORDS)
    profile["designer_global_keywords_de"] = list(dbase.GLOBAL_KEYWORDS_DE)
    profile["designer_dip_base_url"] = ddip.BundestagDIPHarvester.BASE_URL
    profile["designer_dip_api_url"] = ddip.BundestagDIPHarvester.API_URL

    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION_SYNTHETIC_RESPONSES_NO_NETWORK",
        "sources": {
            variant: {
                "repository": spec["repository"],
                "commit": spec["commit"],
                "files": [
                    {"path": f"backend/{spec['directory']}/{n}", "git_blob": b}
                    for n, b in dict(spec["blobs"]).items()
                ],
            }
            for variant, spec in SOURCES.items()
        },
        "environment": {
            "python": platform.python_version(),
            "httpx": sys.modules["httpx"].__version__,
            "network": "none (httpx.AsyncClient replaced, SPARQL stubbed)",
        },
        "profile": profile,
        "cases": cases,
    }
    report["neutralized"] = NEUTRALIZED
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_neutral(json.dumps(report, indent=1, ensure_ascii=False)) + "\n")
    print(
        json.dumps(
            {
                "status": "OBSERVED",
                "cases": len(cases),
                "exceptions": sum(c["exception"] is not None for c in cases),
            }
        )
    )


if __name__ == "__main__":
    main()
