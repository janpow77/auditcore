"""Capture actual behavior of the TED/HAD clients and procurement prechecks before extraction.

Run with the interpreter of audit-portal (provides httpx, requests, lxml)::

    <audit-portal>/backend/.venv/bin/python tools/capture_procurement_legacy.py \
        --repositories <.auditcore/repositories> tests/fixtures/procurement_legacy_observed.json

Every executed source file is checked against its pinned Git blob. Modules
are loaded from their file path (no application package side effects where
avoidable); the application database URL is redirected to an unreachable
address, network calls go to in-process fakes only. Inputs are synthetic in
the original response formats. ``--migrated PORTAL_BACKEND`` re-runs the
portal part against a migrated consumer checkout without the blob check.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.util
import json
import os
import platform
import sys
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

PORTAL = ("janpow77/audit-portal", "d8eefa426826bdecb67036774f3128ae05e7d0d0")
FLOWINVOICE = ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02")
DESIGNER = ("janpow77/audit_designer", "030a71e083ef0feddc14545b095a4945bc0bbd7a")
BLOBS = {
    (
        PORTAL,
        "backend/app/services/ted_harvester_service.py",
    ): "1f8b43677a794b8b2fdb6787c8e533c08a78a2cb",
    (PORTAL, "backend/audit_prep/ted_normalize.py"): "600c9dd9909b147c253ef72d5d8e27e80af0d002",
    (
        PORTAL,
        "backend/app/services/procurement_analyzer.py",
    ): "e76961b1bdab273f8c2441a4bfe2108a2c71f9eb",
    (
        PORTAL,
        "backend/app/seeds/procurement_ruleset.py",
    ): "fde338f32489a7f7ebd334d53d96568aed76fdb1",
    (FLOWINVOICE, "company_records.py"): "b19d308f2e0cf3d9e99e91f8f325f89183ee4f84",
    (
        FLOWINVOICE,
        "backend/app/services/procurement_analyzer.py",
    ): "a3fa3be4d0c486f2cf0d161a94b3795e6f46455b",
    (
        FLOWINVOICE,
        "backend/app/seeds/procurement_ruleset.py",
    ): "fde338f32489a7f7ebd334d53d96568aed76fdb1",
    (
        DESIGNER,
        "backend/app/modules/vp_ai/services/company/company_records.py",
    ): "874901d0414976bbc3f9f9314894c7cf913c043a",
}


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return plain(asdict(value))
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if hasattr(value, "value") and type(value).__module__.endswith("enums"):
        return value.value
    return value


def error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


# ----------------------------------------------------------------- inputs

AWARD = {
    "publication-number": "324184-2024",
    "notice-title": {"deu": "Rahmenvertrag IT-Dienstleistungen", "eng": "Framework IT"},
    "publication-date": "2024-01-15+01:00",
    "classification-cpv": ["72000000", "72200000"],
    "buyer-name": {"deu": ["Bundesamt für Beispiele"]},
    "buyer-country": ["DEU"],
    "winner-name": {"deu": ["Beispiel GmbH"]},
    "winner-country": ["DEU"],
    "winner-identifier": ["DE123456789"],
    "winner-decision-date": ["2024-02-01+01:00"],
    "result-value-notice": "150000.0000",
    "result-value-cur-notice": "EUR",
    "procedure-type": "open",
    "contract-nature": ["services", "services"],
}
NO_WINNER = {
    "publication-number": "324999-2024",
    "notice-title": {"deu": "Ausschreibung ohne Zuschlag"},
    "publication-date": "2024-03-01+01:00",
}
NOTICES: dict[str, Any] = {
    "award": AWARD,
    "no-winner": NO_WINNER,
    "english-only": {
        **AWARD,
        "notice-title": {"eng": "Only English"},
        "winner-name": {"eng": "X Ltd"},
    },
    "french-first-value": {**AWARD, "notice-title": {"fra": "Titre", "ita": "Titolo"}},
    "legacy-mnemonics": {
        "ND": "100-2019",
        "TI": "Alt",
        "AA_NAME": "Amt",
        "CY": "DE",
        "WIN_NAME": "Firma",
        "PD": "20190301",
        "DT_AWARD": "01/02/2019",
        "CPV": "45000000",
        "RC": ["DE7"],
        "PR_PROC": "1",
    },
    "amount-object": {**AWARD, "result-value-notice": {"amount": "99.5", "currency": "USD"}},
    "amount-list-max": {
        **AWARD,
        "result-value-notice": [
            {"amount": 10, "currency": "EUR"},
            {"amount": 20, "currency": "CHF"},
        ],
    },
    "amount-german": {**AWARD, "result-value-notice": "1.234,56"},
    "amount-thousands": {**AWARD, "result-value-notice": "1,234.56"},
    "amount-garbage": {**AWARD, "result-value-notice": "n/a"},
    "amount-int": {**AWARD, "result-value-notice": 5},
    "estimated-only": {**AWARD, "result-value-notice": None, "estimated-value-proc": "70000"},
    "currency-separate": {**AWARD, "result-value-notice": "7", "result-value-cur-notice": "PLN"},
    "empty-values": {**AWARD, "buyer-name": "", "classification-cpv": [], "notice-title": {}},
    "cpv-objects": {**AWARD, "classification-cpv": [{"code": "1"}, {"value": "2"}, {"id": "1"}]},
    "nuts": {**AWARD, "place-performance-nuts": ["DE71", "DE71", "DE72"]},
    "dates-variants": {
        **AWARD,
        "publication-date": "15.01.2024",
        "contract-start-date": "2024/02/01",
        "contract-end-date": "garbage",
        "winner-decision-date": "20240201",
    },
    "datetime-string": {**AWARD, "publication-date": "2024-01-15T10:00:00Z"},
    "winner-list": {**AWARD, "winner-name": ["", "Zweite GmbH"]},
    "numeric-title": {**AWARD, "notice-title": 12345},
    "correction-fields": {**AWARD, "notice-type": "corr", "change-notice-version-identifier": "2"},
    "not-a-dict": ["x"],
}
FILES: dict[str, bytes] = {
    "raw-array": json.dumps([AWARD, NO_WINNER]).encode(),
    "raw-object-notices": json.dumps({"notices": [AWARD]}).encode(),
    "raw-object-results": json.dumps({"results": [AWARD]}).encode(),
    "normalized": json.dumps(
        [{"contractor_name": "A", "notice_id": "1"}, {"notice_id": "2"}]
    ).encode(),
    "empty-array": b"[]",
    "invalid-json": b"{not json",
    "latin1": json.dumps([{**AWARD, "winner-name": "Müller"}], ensure_ascii=False).encode(
        "latin-1"
    ),
    "utf8-bom": b"\xef\xbb\xbf" + json.dumps([AWARD]).encode(),
    "scalar": b"42",
    "only-no-winner": json.dumps([NO_WINNER]).encode(),
}


class FakeResponse:
    def __init__(self, status: int, payload: Any = None, content: bytes = b"") -> None:
        self.status_code = status
        self._payload = payload
        self.content = content

    def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    """requests.Session stand-in; records calls, returns prepared responses."""

    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def _next(self, method: str, url: str, **kwargs: Any) -> Any:
        self.calls.append({"method": method, "url": url, **plain(kwargs)})
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def get(self, url: str, **kwargs: Any) -> Any:
        return self._next("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        return self._next("POST", url, **kwargs)


HAD_TABLE = b"""<html><body><table class="result-list">
<tr><td>Neubau Kita</td><td>Stadt Kassel</td><td>Offenes Verfahren</td><td>Bauleistung</td>
<td>Kassel</td><td><a href="details.html?id=4711">mehr</a></td><td>01.03.2024</td></tr>
<tr><td>Nur Titel</td></tr>
<tr><td>Reinigung</td><td>Land Hessen</td><td><a href="https://www.had.de/x.html?id=99">x</a></td></tr>
</table></body></html>"""
HAD_DIVS = (
    b'<html><body><div class="search-result"><span>Schulbau</span><span>Kreis Fulda</span>\n'
    b'<a href="a.html">ohne id</a></div><div class="search-result"><span>Leer</span></div>'
    b"</body></html>"
)
HAD_NONE = b"<html><body><p>Keine Treffer</p></body></html>"


async def fetch_capture(ted: ModuleType, httpx: Any) -> list[dict[str, Any]]:
    """Run the real async fetch loop against an httpx.MockTransport."""
    rows: list[dict[str, Any]] = []
    original = httpx.AsyncClient

    def scenario(name: str, pages: list[Any], **kwargs: Any) -> Any:
        requests_seen: list[dict[str, Any]] = []

        def handler(request: Any) -> Any:
            body = json.loads(request.content)
            requests_seen.append(
                {
                    "body": body,
                    "headers": {
                        k: v
                        for k, v in request.headers.items()
                        if k.lower() in {"authorization", "x-api-key"}
                    },
                }
            )
            item = pages.pop(0) if pages else {"notices": []}
            if isinstance(item, Exception):
                raise item
            status, payload = item if isinstance(item, tuple) else (200, item)
            if isinstance(payload, (bytes, str)):
                return httpx.Response(status, content=payload)
            return httpx.Response(status, json=payload)

        class Client(original):  # type: ignore[misc, valid-type]
            def __init__(self, *args: Any, **options: Any) -> None:
                options["transport"] = httpx.MockTransport(handler)
                super().__init__(*args, **options)

        return name, Client, requests_seen, kwargs

    def notices(prefix: str, count: int) -> list[dict[str, Any]]:
        return [{**AWARD, "publication-number": f"{prefix}-{i}"} for i in range(count)]

    cases = [
        scenario(
            "single-page-total",
            [{"notices": notices("a", 3), "totalNoticeCount": 3}],
            page_size=10,
            max_notices=100,
        ),
        scenario(
            "two-pages-then-empty",
            [{"notices": notices("b", 2)}, {"notices": notices("c", 2)}, {"notices": []}],
            page_size=2,
            max_notices=100,
        ),
        scenario(
            "max-notices-not-multiple",
            [{"notices": notices("d", 4)}, {"notices": notices("e", 4)}],
            page_size=4,
            max_notices=6,
        ),
        scenario(
            "results-key", [{"results": notices("f", 1), "total": 1}], page_size=5, max_notices=5
        ),
        scenario("data-key", [{"data": notices("g", 1)}, {"data": []}], page_size=5, max_notices=5),
        scenario("non-list", [{"notices": {"x": 1}}], page_size=5, max_notices=5),
        scenario("http-500", [(500, {"error": "x"})], page_size=5, max_notices=5),
        scenario("http-400", [(400, {"error": "bad field"})], page_size=5, max_notices=5),
        scenario("bad-json", [(200, b"not json")], page_size=5, max_notices=5),
        scenario("network-error", [httpx.ConnectError("boom")], page_size=5, max_notices=5),
        scenario(
            "second-page-fails",
            [{"notices": notices("h", 2)}, (503, {})],
            page_size=2,
            max_notices=10,
        ),
        scenario(
            "page-cap",
            [{"notices": notices(f"p{i}", 1)} for i in range(10)],
            page_size=1,
            max_notices=3,
        ),
        scenario(
            "auth-and-fields",
            [{"notices": notices("i", 1), "totalNoticeCount": 1}],
            page_size=1,
            max_notices=1,
            auth_headers={"Authorization": "Bearer X"},
            fields=["a", "b"],
        ),
    ]
    for name, client, seen, kwargs in cases:
        ted.httpx.AsyncClient = client
        try:
            result = await ted.fetch_ted_notices(
                "q", api_url="http://ted.invalid/search", timeout=5, **kwargs
            )
            rows.append(
                {
                    "name": name,
                    "kwargs": kwargs,
                    "requests": seen,
                    "output": [n.get("publication-number") for n in result],
                    "exception": None,
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "name": name,
                    "kwargs": kwargs,
                    "requests": seen,
                    "output": None,
                    "exception": error(exc),
                }
            )
        finally:
            ted.httpx.AsyncClient = original
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repositories", type=Path, required=True)
    parser.add_argument("--migrated-portal", type=Path, default=None)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    roots = {
        PORTAL: args.repositories / "janpow77__audit-portal",
        FLOWINVOICE: args.repositories / "janpow77__flowinvoice",
        DESIGNER: args.repositories / "janpow77__audit_designer",
    }
    files = []
    for (repo, path), blob in BLOBS.items():
        root = (
            args.migrated_portal.parent
            if (args.migrated_portal and repo == PORTAL)
            else roots[repo]
        )
        observed = git_blob(root / path)
        if observed != blob and not (args.migrated_portal and repo == PORTAL):
            raise SystemExit(f"{repo[0]}:{path} does not match the pinned blob")
        files.append({"repository": repo[0], "commit": repo[1], "path": path, "git_blob": observed})

    os.environ["DATABASE_URL"] = "postgresql+asyncpg://nobody:none@127.0.0.1:9/none"
    portal_backend = args.migrated_portal or roots[PORTAL] / "backend"
    sys.path.insert(0, str(portal_backend))
    import httpx

    ted_normalize = load("audit_prep.ted_normalize", portal_backend / "audit_prep/ted_normalize.py")
    ted = load("legacy_ted_harvester", portal_backend / "app/services/ted_harvester_service.py")
    analyzer = load(
        "legacy_procurement_analyzer", portal_backend / "app/services/procurement_analyzer.py"
    )
    from app.seeds.procurement_ruleset import get_procurement_ruleset

    cases: list[dict[str, Any]] = []

    def observe(name: str, operation: str, inputs: Any, call: Any) -> None:
        before = copy.deepcopy(inputs)
        try:
            output, exception = plain(call()), None
        except Exception as exc:  # noqa: BLE001
            output, exception = None, error(exc)
        if inputs != before:
            raise AssertionError(f"{name}: input mutated")
        cases.append(
            {
                "name": name,
                "operation": operation,
                "inputs": plain(inputs),
                "output": output,
                "exception": exception,
            }
        )

    for name, notice in NOTICES.items():
        observe(
            f"normalize-{name}",
            "normalize_notice",
            notice,
            lambda n=notice: ted_normalize.normalize_notice(n),
        )
    observe(
        "normalize-list",
        "normalize_notices",
        list(NOTICES.values())[:6],
        lambda: ted_normalize.normalize_notices(list(NOTICES.values())[:6]),
    )
    for name, raw in FILES.items():
        observe(
            f"file-{name}",
            "parse_ted_file",
            {"bytes_hex": raw.hex(), "file_name": f"{name}.json"},
            lambda r=raw, n=name: ted_normalize.parse_ted_file(r, f"{n}.json"),
        )
    for value in (
        "2024-01-15",
        "2024-01-15+01:00",
        "20240115",
        "15/01/2024",
        "15.01.2024",
        "15-01-2024",
        "2024/01/15",
        "Jan 15",
        None,
        "",
        ["2024-03-01"],
        {"deu": "2024-04-01"},
        5,
    ):
        observe(
            f"iso-date-{value!r}",
            "to_iso_date",
            {"value": value},
            lambda v=value: ted_normalize._to_iso_date(v),
        )
    for name, kwargs in (
        ("empty", {}),
        ("explicit-query", {"query": "  FT=x  ", "country": "DEU"}),
        ("blank-query", {"query": "  ", "country": "DEU"}),
        ("cpv", {"cpv_codes": ["72000000", " ", " 45000000 "]}),
        ("cpv-empty", {"cpv_codes": [" "]}),
        (
            "all",
            {
                "cpv_codes": ["1"],
                "country": " DEU ",
                "contractor_name": " X GmbH ",
                "date_from": "2024-01-01",
                "date_to": "2024-12-31+01:00",
            },
        ),
        ("unparseable-date", {"date_from": "gestern"}),
        ("quote-in-name", {"contractor_name": 'A "B" C'}),
    ):
        observe(
            f"query-{name}", "build_ted_query", kwargs, lambda k=kwargs: ted.build_ted_query(**k)
        )
    observe(
        "query-date-object",
        "build_ted_query",
        {"date_from": "date(2024,1,2)"},
        lambda: ted.build_ted_query(date_from=__import__("datetime").date(2024, 1, 2)),
    )
    cases.append(
        {
            "name": "default-fields",
            "operation": "constant",
            "inputs": None,
            "output": list(ted._DEFAULT_FIELDS),
            "exception": None,
        }
    )
    cases.append(
        {
            "name": "field-aliases",
            "operation": "constant",
            "inputs": None,
            "output": ted_normalize._FIELD_ALIASES,
            "exception": None,
        }
    )
    fetch = asyncio.run(fetch_capture(ted, httpx))

    # ---------------------------------------------------------------- prechecks
    ruleset = get_procurement_ruleset()
    checker = analyzer.ProcurementPreChecker(ruleset)
    d = Decimal

    def docs(*types: str) -> list[dict[str, str]]:
        return [{"procurement_doc_type": t} for t in types]

    full_eu = docs(
        "VERGABEVERMERK",
        "AUSSCHREIBUNG",
        *["ANGEBOT"] * 5,
        "SUBMISSIONSPROTOKOLL",
        "ZUSCHLAG",
        "VERTRAG",
        "COI",
        "TARIFTREUEERKLAERUNG",
    )
    precheck_inputs = {
        "all-missing": (None, None, None, "Liefer-/Dienstleistungen", None, None, []),
        "zero-estimated": (d("0"), None, None, "Liefer-/Dienstleistungen", None, None, []),
        "below-1k-direct": (
            d("800"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Direktvergabe",
            "BELOW_1K",
            docs("VERGABEVERMERK"),
        ),
        "edge-1000": (d("1000"), None, None, "Liefer-/Dienstleistungen", None, "BELOW_1K", []),
        "edge-1000.01": (
            d("1000.01"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            None,
            "BELOW_1K",
            [],
        ),
        "edge-25000": (
            d("25000"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Verhandlungsvergabe",
            "BELOW_25K",
            docs("VERGABEVERMERK", "ANGEBOT", "ZUSCHLAG"),
        ),
        "edge-221000": (
            d("221000"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Oeffentliche Ausschreibung",
            "BELOW_EU",
            docs(
                "VERGABEVERMERK",
                "AUSSCHREIBUNG",
                "ANGEBOT",
                "ANGEBOT",
                "ANGEBOT",
                "SUBMISSIONSPROTOKOLL",
                "ZUSCHLAG",
            ),
        ),
        "above-eu-supply": (
            d("221000.01"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "EU-Verfahren",
            "ABOVE_EU",
            full_eu,
        ),
        "construction-below-eu": (
            d("5538000"),
            None,
            None,
            "Bauleistungen",
            "Oeffentliche Ausschreibung",
            "BELOW_EU",
            [],
        ),
        "construction-above-eu": (
            d("5538000.01"),
            None,
            None,
            "Bauleistungen",
            "EU-Verfahren",
            "ABOVE_EU",
            full_eu,
        ),
        "construction-freihaendig": (
            d("20000"),
            None,
            None,
            "Bauleistungen",
            "Freihaendige Vergabe",
            "BELOW_25K",
            docs("VERGABEVERMERK", "ANGEBOT"),
        ),
        "bau-substring": (d("20000"), None, None, "Hochbau", None, None, []),
        "wrong-tier": (
            d("50000"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Direktvergabe",
            "BELOW_1K",
            [],
        ),
        "procedure-mismatch": (
            d("50000"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Direktvergabe",
            "BELOW_EU",
            [],
        ),
        "unknown-tier-matches-all": (
            d("50000"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Irgendwas",
            "UNBEKANNT",
            [],
        ),
        "unknown-procedure": (
            d("50000"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Sonderverfahren",
            "BELOW_EU",
            [],
        ),
        "substring-procedure": (
            d("500"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Direktvergabe (Ausnahme)",
            "BELOW_1K",
            docs("VERGABEVERMERK"),
        ),
        "no-bids": (
            d("50000"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Oeffentliche Ausschreibung",
            "BELOW_EU",
            docs("VERGABEVERMERK"),
        ),
        "one-bid": (
            d("50000"),
            None,
            None,
            "Liefer-/Dienstleistungen",
            "Oeffentliche Ausschreibung",
            "BELOW_EU",
            docs("ANGEBOT"),
        ),
        "deviation-0": (None, d("100"), d("100"), "Liefer-/Dienstleistungen", None, None, []),
        "deviation-10": (None, d("100"), d("110"), "Liefer-/Dienstleistungen", None, None, []),
        "deviation-10.01": (
            None,
            d("100"),
            d("110.01"),
            "Liefer-/Dienstleistungen",
            None,
            None,
            [],
        ),
        "deviation-20": (None, d("100"), d("80"), "Liefer-/Dienstleistungen", None, None, []),
        "deviation-20.01": (
            None,
            d("100"),
            d("120.01"),
            "Liefer-/Dienstleistungen",
            None,
            None,
            [],
        ),
        "deviation-zero-contract": (
            None,
            d("0"),
            d("100"),
            "Liefer-/Dienstleistungen",
            None,
            None,
            [],
        ),
        "deviation-zero-invoice": (
            None,
            d("100"),
            d("0"),
            "Liefer-/Dienstleistungen",
            None,
            None,
            [],
        ),
        "deviation-negative": (
            None,
            d("100"),
            d("-50"),
            "Liefer-/Dienstleistungen",
            None,
            None,
            [],
        ),
    }
    prechecks = []
    for name, call_args in precheck_inputs.items():
        try:
            result = checker.run_prechecks(*call_args)
            result = {**result, "timestamp": "<wall-clock>"}
            prechecks.append(
                {
                    "name": name,
                    "args": plain(list(call_args)),
                    "output": plain(result),
                    "exception": None,
                }
            )
        except Exception as exc:  # noqa: BLE001
            prechecks.append(
                {
                    "name": name,
                    "args": plain(list(call_args)),
                    "output": None,
                    "exception": error(exc),
                }
            )

    # ------------------------------------------------ company-records clients
    clients: list[dict[str, Any]] = []
    if not args.migrated_portal:
        variants = {
            "flowinvoice": load(
                "legacy_company_records_flowinvoice", roots[FLOWINVOICE] / "company_records.py"
            ),
            "designer": load(
                "legacy_company_records_designer",
                roots[DESIGNER] / "backend/app/modules/vp_ai/services/company/company_records.py",
            ),
        }
        mnemonic = {
            "ND": "12-2020",
            "PD": "2020-01-02",
            "TI": {"deu": "Titel", "eng": "Title"},
            "OL": "Amt",
            "NC": "services",
            "PR": "open",
            "TV": 100,
            "TD": "7",
        }
        ted_payloads = {
            "results-mnemonic": (200, {"results": [mnemonic]}),
            "notices-mnemonic": (200, {"notices": [{**mnemonic, "TI": "Plain"}]}),
            "long-names": (200, {"notices": [{"noticeNumber": "N", "title": "T" * 300}]}),
            "empty": (200, {"notices": []}),
            "not-found": (404, None),
            "server-error": (500, None),
            "bad-json": (200, ValueError("no json")),
            "exception": ConnectionError("down"),
        }
        had_pages = {
            "table": (200, HAD_TABLE),
            "divs": (200, HAD_DIVS),
            "none": (200, HAD_NONE),
            "forbidden": (403, b""),
            "not-found": (404, b""),
            "error": (500, b""),
            "exception": ConnectionError("down"),
        }
        for variant, module in variants.items():
            for name, item in ted_payloads.items():
                response = item if isinstance(item, Exception) else FakeResponse(item[0], item[1])
                session = FakeSession([response])
                client = module._TEDClient(session)
                try:
                    out = [asdict(n) for n in client.search('Beispiel "GmbH"', "DE")]
                    exc = None
                except Exception as e:  # noqa: BLE001
                    out, exc = None, error(e)
                clients.append(
                    {
                        "variant": variant,
                        "source": "ted",
                        "name": name,
                        "calls": session.calls,
                        "output": plain(out),
                        "exception": exc,
                    }
                )
            for name, item in had_pages.items():
                response = (
                    item if isinstance(item, Exception) else FakeResponse(item[0], None, item[1])
                )
                session = FakeSession([response])
                client = module._HADClient(session)
                try:
                    out = [
                        asdict(n) for n in client.search("Kita", include_archived=name != "none")
                    ]
                    exc = None
                except Exception as e:  # noqa: BLE001
                    out, exc = None, error(e)
                clients.append(
                    {
                        "variant": variant,
                        "source": "had",
                        "name": name,
                        "calls": session.calls,
                        "output": plain(out),
                        "exception": exc,
                    }
                )

    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION_NOT_LEGAL_VALIDATION",
        "source": {"files": files, "migrated_portal": str(args.migrated_portal or "")},
        "library": _library_origin(),
        "environment": {
            "python": platform.python_version(),
            "httpx": httpx.__version__,
            "network": "in-process fakes only",
            "database": "unreachable URL, never connected",
        },
        "ruleset": {
            "threshold_rules": ruleset["threshold_rules"],
            "required_documents_by_procedure": ruleset["required_documents_by_procedure"],
            "keys": sorted(ruleset),
        },
        "cases": cases,
        "fetch": fetch,
        "prechecks": prechecks,
        "clients": clients,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "cases": len(cases),
                "fetch": len(fetch),
                "prechecks": len(prechecks),
                "clients": len(clients),
            }
        )
    )


def _library_origin() -> str | None:
    module = sys.modules.get("auditcore_procurement")
    return getattr(module, "__file__", None)


if __name__ == "__main__":
    main()
