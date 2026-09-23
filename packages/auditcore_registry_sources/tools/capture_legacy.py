"""Capture the actual behavior of the register/sanctions/PEP sources before extraction.

Executes the pinned, blob-verified originals with synthetic inputs in the
original formats (``tests/fixtures/files``) and writes one observation file::

    python tools/capture_legacy.py <checkouts dir> tests/fixtures/legacy_observed.json

``<checkouts dir>`` contains clean checkouts named like the repositories
(``audit_designer``, ``flowworkshop``, ``audit-portal``, ``flowsearch``,
``osint``, ``riskanalysis``) at the pinned commits. The tool never imports
``auditcore_registry_sources``. The flowworkshop original imports
``auditcore_entity_matching`` itself; the environment must therefore contain
exactly version 0.1.0 of that library (checked). No database: the designer
service runs with its database methods replaced by recorded in-memory values.
No network: HTTP is answered by ``httpx.MockTransport``; the OSINT download
helper is replaced by a fixture lookup.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import copy
import csv
import hashlib
import importlib.util
import io
import json
import logging
import os
import platform
import re
import subprocess
import sys
import tempfile
import threading
import types
import unicodedata
from collections.abc import Iterable, Sequence
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, date, datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import rapidfuzz
from rapidfuzz import fuzz, process

FILES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "files"

DESIGNER = "backend/app/core/shared/research/register/sanctions.py"
WORKSHOP = "auditworkshop/backend/services/sanctions_service.py"
FI = "backend/app/services/fraud_detection/"
SOURCES: dict[str, dict[str, Any]] = {
    "audit_designer": {
        "repository": "janpow77/audit_designer",
        "commit": "1254591156d3bdf6ccdf4050dec7713a61ad4a20",
        "blobs": {DESIGNER: "5c064ddecb473b3f1a4341a0dc6513268d106295"},
    },
    "flowworkshop": {
        "repository": "janpow77/flowworkshop",
        "commit": "3d1cb40221645935c323392d70d84102d05ac7bb",
        "blobs": {WORKSHOP: "5b9de79484373428f45ddeb879a497b671a29e1c"},
    },
    "audit-portal": {
        "repository": "janpow77/audit-portal",
        "commit": "ac1ccc779db69492db0c2c154b6ec84fdd1794b1",
        "blobs": {
            "backend/audit_prep/sanctions_xml.py": "1412c58b200e720cc9ca4f3347a2a06300a10c28",
            "backend/audit_prep/sanctions.py": "835824a7123eac5249096cc47a4d8493709307e9",
            "backend/audit_prep/normalization.py": "c9f9c3dbb211cd6c215464293bccc5efebf0fc7d",
        },
    },
    "flowsearch": {
        "repository": "janpow77/flowsearch",
        "commit": "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4",
        "blobs": {
            "backend/app/services/api_client_base.py": "0344346638e1e24136eb58ea369bd252faa830dc",
            "backend/app/services/api_clients/sanctions.py": (
                "ddb377633153cfa0b936bec7d709d322e079fb2f"
            ),
            "backend/app/services/api_clients/pep_screening.py": (
                "2337f4ce14804c4102e9cbf46868e5413e9a4957"
            ),
            "backend/app/services/api_clients/openregister.py": (
                "e7b0c9e06868f09c678773a21f4efb4eaac6d03b"
            ),
            "backend/app/services/api_clients/handelsregister.py": (
                "54d892297846fcd158ebc5d1831af597cf3ff9bc"
            ),
            "backend/app/services/ubo_engine.py": "15de1235fe57088aac874e3b14c4b0f36d6cb431",
        },
    },
    "osint": {
        "repository": "janpow77/osint",
        "commit": "d361ddb9a502bb899065e799d50104f306cfdc89",
        "blobs": {"werkzeuge/traeger_quellen.py": "538c368e3a0de9b1d6db60edbf7007989c54a278"},
    },
    "flowinvoice": {
        "repository": "janpow77/flowinvoice",
        "commit": "fb2d18568d2eaf64574d131ceae51a936b9aac02",
        "blobs": {
            FI + "models.py": "e960f32633874444b9ddc0f323dd54f5b0242e59",
            FI + "rate_limiter.py": "c55f90f0ed29ea6e7fae0808ca72a5d16edd5134",
            FI + "cache.py": "77446c9735e1581627e4b48dfc86343021e3c21e",
            FI + "sanctions_checker.py": "f003318086914f9d8ea53a566f40289e8e278c39",
            FI + "sanctions_downloader.py": "54b2bf7352c6bf68ce12cc68e5df57df081ba2d5",
            FI + "pep_checker.py": "58d1849a626faa00509718287f7a5b793b0d7da1",
            FI + "company_verifier.py": "a34ee1a077afbb1173210ad08bcee91db55498a0",
            "backend/tests/test_pep_checker.py": "9dfb048831855efc80510a7ebf03103d764cb7e4",
        },
    },
    "riskanalysis": {
        "repository": "janpow77/riskanalysis",
        "commit": "b5c523bf7eaa326153778d9751f176f03d4d56ed",
        "blobs": {
            "backend/app/services/sanctions_screening.py": (
                "d21d5ec7b01b1bc9ee5a055cdb2d7621767b3056"
            )
        },
    },
}

#: Screening queries shared by both screening variants.
QUERIES: list[dict[str, Any]] = [
    {"name": "Iwan Musterow"},
    {"name": "Ivan Musterov", "birth_date": "1961", "country": "RU"},
    {"name": "Ivan Musterov", "birth_date": "1970-01-01", "country": "DE"},
    {"name": "Ivan Musterov", "birth_date": "unbekannt", "country": ""},
    {"name": "Müller-Lüdenscheidt Handels GmbH"},
    {"name": "Mueller Luedenscheidt"},
    {"name": "Muller Ludenscheidt"},
    {"name": "Müller-Lüdenscheidt"},
    {"name": "MLH"},
    {"name": "Beispielin"},
    {"name": "Vladimir Beispielin", "birth_date": "1952-10-07"},
    {"name": "Jorgen Odegard"},
    {"name": "Jørgen Ødegård"},
    {"name": "Lodz Beispiel"},
    {"name": "Anna Beispiel", "country": "AT"},
    {"name": "Anna Beispiel", "country": "de, at", "birth_date": "1981"},
    {"name": "Strasse und Soehne"},
    {"name": "Straße & Söhne"},
    {"name": "Beispiel Shipping", "schema": "Organization"},
    {"name": "Beispiel Shipping", "schema": "Person"},
    {"name": "Unbekannt Niemand"},
    {"name": "GmbH"},
    {"name": "   "},
    {"name": "Musterow", "min_score": 50.0},
    {"name": "Musterow", "limit": 1},
    {"name": "Иван Мустеров"},
    {"name": "Demo Trade"},
]

DOB_COUNTRY_CASES: list[dict[str, Any]] = [
    {"score": 80.0, "rec_dob": "1961-04-12;1962", "rec_c": "ru", "q_dob": "1961", "q_c": "RU"},
    {"score": 80.0, "rec_dob": "1961-04-12", "rec_c": "ru", "q_dob": "1970", "q_c": "DE"},
    {"score": 97.0, "rec_dob": "1961", "rec_c": "ru", "q_dob": "1961", "q_c": "ru"},
    {"score": 10.0, "rec_dob": "1961", "rec_c": "ru", "q_dob": "1999", "q_c": "de"},
    {"score": 80.0, "rec_dob": "", "rec_c": "", "q_dob": "1961", "q_c": "RU"},
    {"score": 80.0, "rec_dob": "ca. 1960", "rec_c": "de, at", "q_dob": "12.04.1961", "q_c": "AT"},
    {"score": 80.0, "rec_dob": "1961", "rec_c": "Österreich", "q_dob": None, "q_c": "Oesterreich"},
    {"score": 80.0, "rec_dob": "1961", "rec_c": "Österreich", "q_dob": None, "q_c": "Osterreich"},
    {"score": 75.5, "rec_dob": "19610412", "rec_c": "ru;by", "q_dob": "1961", "q_c": "BY"},
]

DATE_STRINGS = [
    None,
    "",
    "1961-04-12",
    "12/04/1961",
    "04/12/1961",
    "12.04.1961",
    "1961-04-12T00:00:00",
    "1961-04-12T00:00:00.123",
    "12 Apr 1961",
    "12 April 1961",
    "1961",
    "1961-13-45",
    "circa 1961",
    "unbekannt",
    " 1961-04-12 ",
]


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def jsonable(value: Any) -> Any:
    """Type-preserving JSON form so that replays compare types, not only text."""
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return {"$float": repr(value)}
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, bytes):
        return {"$bytes": value.decode("utf-8", errors="replace")}
    if is_dataclass(value) and not isinstance(value, type):
        return {"$dataclass": type(value).__name__, "fields": jsonable(asdict(value))}
    if isinstance(value, dict):
        return {"$dict": [[jsonable(k), jsonable(v)] for k, v in value.items()]}
    if isinstance(value, tuple):
        return {"$tuple": [jsonable(v) for v in value]}
    if isinstance(value, (list, set, frozenset)):
        items = list(value) if isinstance(value, list) else sorted(value, key=repr)
        return [jsonable(v) for v in items]
    return {"$repr": repr(value), "type": type(value).__name__}


class Recorder:
    def __init__(self) -> None:
        self.cases: list[dict[str, Any]] = []

    def observe(self, name: str, operation: str, inputs: Any, call: Any) -> Any:
        before = copy.deepcopy(inputs)
        result = None
        try:
            result = call()
            output, exception = jsonable(result), None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output = None
            exception = {"type": type(exc).__name__, "message": str(exc)}
            print(f"  Ausnahme in {name}: {exception}", file=sys.stderr)
        if inputs != before:
            raise AssertionError(f"{name}: legacy call mutated its input")
        self.cases.append(
            {
                "name": name,
                "operation": operation,
                "inputs": jsonable(inputs),
                "output": output,
                "exception": exception,
            }
        )
        return result


def verify(checkouts: Path) -> list[dict[str, Any]]:
    bound = []
    for key, source in SOURCES.items():
        checkout = checkouts / key
        head = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if head != source["commit"]:
            raise SystemExit(f"{key}: Checkout steht nicht auf {source['commit']}")
        for path, blob in source["blobs"].items():
            if git_blob((checkout / path).read_bytes()) != blob:
                raise SystemExit(f"{key}/{path}: Blob weicht ab")
            bound.append(
                {
                    "repository": source["repository"],
                    "commit": source["commit"],
                    "path": path,
                    "git_blob": blob,
                }
            )
    return bound


def ast_load(path: Path, names: Sequence[str], namespace: dict[str, Any]) -> dict[str, Any]:
    """Compile only the named top-level definitions of a pinned file."""
    tree = ast.parse(path.read_bytes().decode("utf-8"))
    wanted = []
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            wanted.append(node)
            found.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            hit = [t.id for t in targets if isinstance(t, ast.Name) and t.id in names]
            if hit:
                wanted.append(node)
                found.update(hit)
    missing = set(names) - found
    if missing:
        raise SystemExit(f"{path}: Definitionen fehlen: {sorted(missing)}")
    module = ast.Module(
        body=[ast.ImportFrom("__future__", [ast.alias("annotations")], 0), *wanted],
        type_ignores=[],
    )
    # Dataclasses look their module up in sys.modules; register a real module.
    holder = types.ModuleType(str(namespace["__name__"]))
    holder.__dict__.update(namespace)
    sys.modules[holder.__name__] = holder
    code = compile(ast.fix_missing_locations(module), str(path), "exec")
    exec(code, holder.__dict__)  # noqa: S102
    return holder.__dict__


def csv_rows(name: str) -> list[dict[str, str]]:
    with (FILES / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


# ---------------------------------------------------------------- audit_designer


class ResearchError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class Query:
    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def param(self, key: str) -> Any:
        return self.params.get(key)


def capture_designer(checkout: Path, rec: Recorder) -> dict[str, Any]:
    names = [
        "RECHTSFORMZUSAETZE",
        "_FALTUNG",
        "_NICHT_WORT",
        "falte_diakritika",
        "normalisiere_name",
        "STANDARD_MINDESTWERT",
        "_BONUS_GEBURTSJAHR",
        "_MALUS_GEBURTSJAHR",
        "_BONUS_LAND",
        "_MALUS_LAND",
        "_MEHRWERT_TRENNER",
        "klassifiziere",
        "_zerlege_mehrwert",
        "_geburtsjahre",
        "_laender",
        "_beruecksichtige_geburtsdatum_und_land",
        "Sanktionsliste",
        "SANKTIONSLISTEN",
        "_LISTE_JE_KEY",
        "_LISTE_JE_QUELLE",
        "liste",
        "liste_zu_quelle",
        "Sanktionseintrag",
        "Sanktionstreffer",
        "Listenbefund",
        "SPALTEN",
        "Listenindex",
        "SanktionslistenDienst",
        "_GRENZEN_ZUSATZ",
        "_HINWEIS_PRUEFHINWEIS",
        "methodenerlaeuterung",
        "SanctionsScreeningProvider",
    ]
    ns: dict[str, Any] = {
        "re": re,
        "unicodedata": unicodedata,
        "fuzz": fuzz,
        "process": process,
        "dataclass": dataclass,
        "field": field,
        "datetime": datetime,
        "Sequence": Sequence,
        "Iterable": Iterable,
        "ResearchError": ResearchError,
        "logger": logging.getLogger("designer"),
        "threading": threading,
        "csv": csv,
        "hashlib": hashlib,
        "Path": Path,
        "__name__": "designer_sanctions",
    }
    ns = ast_load(checkout / DESIGNER, names, ns)
    listen = {li.key: li for li in ns["SANKTIONSLISTEN"]}

    def entries(list_key: str, file_name: str) -> list[Any]:
        result = []
        for row in csv_rows(file_name):
            entry_id = str(row.get("id") or "").strip()
            name = str(row.get("name") or "").strip()
            if not entry_id or not name:
                continue
            satz = ns["SanktionslistenDienst"]._zu_datensatz(
                listen[list_key], row, entry_id, name, None
            )
            eintrag = ns["Sanktionseintrag"](
                entry_id=satz["entry_id"],
                entity_schema=satz["entity_schema"],
                name=satz["name"],
                aliases=list(satz["aliases"] or []),
                birth_date=satz["birth_date"] or "",
                countries=satz["countries"] or "",
                addresses=satz["addresses"] or "",
                identifiers=satz["identifiers"] or "",
                sanctions_program=satz["sanctions_program"] or "",
                program_ids=satz["program_ids"] or "",
                first_seen=satz["first_seen"] or "",
                last_seen=satz["last_seen"] or "",
                name_norm=ns["normalisiere_name"](satz["name"] or ""),
            )
            result.append(eintrag.normalisiere())
        return result

    for file_name, list_key in (
        ("eu_fsf_targets.simple.csv", "eu_fsf"),
        ("un_sc_targets.simple.csv", "un_sc"),
    ):
        for index, row in enumerate(csv_rows(file_name)):
            entry_id = str(row.get("id") or "").strip()
            name = str(row.get("name") or "").strip()
            rec.observe(
                f"designer-row-{list_key}-{index}",
                "designer_row",
                {"list_key": list_key, "row": row},
                lambda r=row, e=entry_id, n=name, k=list_key: (
                    None
                    if not e or not n
                    else ns["SanktionslistenDienst"]._zu_datensatz(listen[k], r, e, n, None)
                ),
            )

    index_eu = ns["Listenindex"](listen["eu_fsf"], entries("eu_fsf", "eu_fsf_targets.simple.csv"))
    for i, q in enumerate(QUERIES):
        rec.observe(
            f"designer-search-{i}",
            "designer_index_search",
            {"list_key": "eu_fsf", "query": q},
            lambda q=q: [
                t.to_dict()
                for t in index_eu.suche(
                    q["name"],
                    limit=q.get("limit", 15),
                    mindestwert=q.get("min_score", ns["STANDARD_MINDESTWERT"]),
                    entity_schema=q.get("schema"),
                    geburtsdatum=q.get("birth_date"),
                    land=q.get("country"),
                )
            ],
        )

    # Service level: per-list findings; the database methods are replaced by
    # recorded in-memory values (count, highest id, last change, list state).
    stand = datetime(2026, 9, 22, 18, 0, 0)
    bestand = {
        "eu_fsf": entries("eu_fsf", "eu_fsf_targets.simple.csv"),
        "un_sc": entries("un_sc", "un_sc_targets.simple.csv"),
        "us_ofac_sdn": [],
    }

    class Dienst(ns["SanktionslistenDienst"]):  # type: ignore[misc]
        def __init__(self) -> None:
            self.db = None

        def kennzahlen(self, list_key: str) -> tuple[int, int | None, datetime | None]:
            n = len(bestand.get(list_key, []))
            return n, (n or None), (stand if n else None)

        def stand(self, list_key: str) -> datetime | None:
            return stand if bestand.get(list_key) else None

        def index(self, sanktionsliste: Any) -> Any:
            daten = bestand.get(sanktionsliste.key, [])
            return ns["Listenindex"](sanktionsliste, daten) if daten else None

    dienst = Dienst()
    for i, q in enumerate(QUERIES[:6]):
        rec.observe(
            f"designer-service-{i}",
            "designer_service_search",
            {"lists": ["eu_fsf", "un_sc", "us_ofac_sdn"], "query": q},
            lambda q=q: [
                {
                    "list_key": b.liste.key,
                    "source_key": b.liste.quelle,
                    "durchsucht": b.durchsucht,
                    "bestand": b.bestand,
                    "stand": b.stand,
                    "hinweis": b.hinweis,
                    "treffer": [t.to_dict() for t in b.treffer],
                }
                for b in dienst.suche(
                    q["name"],
                    listen=[listen["eu_fsf"], listen["un_sc"], listen["us_ofac_sdn"]],
                    limit=q.get("limit", 15),
                    mindestwert=q.get("min_score", ns["STANDARD_MINDESTWERT"]),
                    entity_schema=q.get("schema"),
                    geburtsdatum=q.get("birth_date"),
                    land=q.get("country"),
                )
            ],
        )

    for i, c in enumerate(DOB_COUNTRY_CASES):
        rec.observe(
            f"designer-dob-country-{i}",
            "designer_dob_country",
            c,
            lambda c=c: ns["_beruecksichtige_geburtsdatum_und_land"](
                c["score"],
                geburtsdatum_eintrag=c["rec_dob"],
                laender_eintrag=c["rec_c"],
                geburtsdatum_anfrage=c["q_dob"],
                land_anfrage=c["q_c"],
            ),
        )

    provider = ns["SanctionsScreeningProvider"]
    for i, params in enumerate(
        [{}, {"name": "ab"}, {"q": "Musterow"}, {"name": "  Musterow  "}, {"name": "abc"}]
    ):
        rec.observe(
            f"designer-provider-name-{i}",
            "designer_provider_name",
            params,
            lambda p=params: provider._name(Query(p)),
        )
    for i, value in enumerate([None, "", "70", 49.9, 50, 100, 100.5, "x", "85.5"]):
        rec.observe(
            f"designer-provider-min-{i}",
            "designer_provider_min_score",
            {"min_score": value},
            lambda v=value: provider._mindestwert(Query({"min_score": v})),
        )
    for i, value in enumerate([None, "person", "Organization", "Vessel", "PERSON"]):
        rec.observe(
            f"designer-provider-schema-{i}",
            "designer_provider_schema",
            {"entity_schema": value},
            lambda v=value: provider._entity_schema(Query({"entity_schema": v})),
        )
    rec.observe("designer-method", "designer_method", {}, ns["methodenerlaeuterung"])
    return {
        "lists": [asdict(li) for li in ns["SANKTIONSLISTEN"]],
        "minimum_score": ns["STANDARD_MINDESTWERT"],
        "dob_bonus": ns["_BONUS_GEBURTSJAHR"],
        "dob_malus": ns["_MALUS_GEBURTSJAHR"],
        "country_bonus": ns["_BONUS_LAND"],
        "country_malus": ns["_MALUS_LAND"],
        "columns": list(ns["SPALTEN"]),
        "limitations_extra": ns["_GRENZEN_ZUSATZ"],
        "hint": ns["_HINWEIS_PRUEFHINWEIS"],
    }


# ------------------------------------------------------------------ flowworkshop


def capture_workshop(checkout: Path, rec: Recorder) -> dict[str, Any]:
    import auditcore_entity_matching
    from auditcore_entity_matching import legacy as library_010

    if auditcore_entity_matching.__version__ != "0.1.0":
        raise SystemExit("flowworkshop@3d1cb40 ruft auditcore_entity_matching 0.1.0 auf.")
    names = [
        "_LEGAL_SUFFIXES",
        "SanctionsSource",
        "FsfRecord",
        "SanctionsHit",
        "DEFAULT_SANCTIONS_SOURCES",
        "UMLAUT_UMSCHRIFT",
        "normalize_name",
        "_classify",
        "_MULTIVALUE_SPLIT_RE",
        "_DOB_MATCH_BONUS",
        "_DOB_CONFLICT_MALUS",
        "_COUNTRY_MATCH_BONUS",
        "_COUNTRY_CONFLICT_MALUS",
        "_split_multivalue",
        "_dob_year_tokens",
        "_country_tokens",
        "_adjust_score_for_dob_country",
        "_row_to_record",
        "_records_from_csv",
        "SanctionsListIndex",
        "MultiSanctionsService",
    ]
    ns: dict[str, Any] = {
        "re": re,
        "os": os,
        "csv": csv,
        "threading": threading,
        "datetime": datetime,
        "timezone": timezone,
        "dataclass": dataclass,
        "Iterable": Iterable,
        "fuzz": fuzz,
        "process": process,
        "log": logging.getLogger("workshop"),
        "_bibliothek": library_010,
        "__name__": "workshop_sanctions",
    }
    ns = ast_load(checkout / WORKSHOP, names, ns)
    source_cls = ns["SanctionsSource"]
    for file_name in ("eu_fsf_targets.simple.csv", "un_sc_targets.simple.csv"):
        for index, row in enumerate(csv_rows(file_name)):
            rec.observe(
                f"workshop-row-{file_name}-{index}",
                "workshop_row",
                {"row": row},
                lambda r=row: ns["_row_to_record"](r),
            )
    sources = [
        source_cls("eu_fsf", "EU", "EU", "-", str(FILES / "eu_fsf_targets.simple.csv"), "x"),
        source_cls("un_sc", "UN", "UN", "-", str(FILES / "un_sc_targets.simple.csv"), "x"),
        source_cls("us_ofac_sdn", "OFAC", "US", "-", str(FILES / "fehlt.csv"), "x"),
    ]
    index = ns["SanctionsListIndex"](sources[0])
    index.load()
    for i, q in enumerate(QUERIES):
        rec.observe(
            f"workshop-search-{i}",
            "workshop_index_search",
            {"list_key": "eu_fsf", "query": q},
            lambda q=q: index.search(
                q["name"],
                limit=q.get("limit", 15),
                min_score=q.get("min_score", 70.0),
                schema=q.get("schema"),
                birth_date=q.get("birth_date"),
                country=q.get("country"),
            ),
        )
    multi = ns["MultiSanctionsService"](sources, use_db=False)
    multi.load_all(use_db=False)
    for i, q in enumerate(QUERIES[:6]):
        rec.observe(
            f"workshop-multi-{i}",
            "workshop_multi_search",
            {"lists": ["eu_fsf", "un_sc", "us_ofac_sdn"], "query": q},
            lambda q=q: multi.search(
                q["name"],
                limit=q.get("limit", 15),
                min_score=q.get("min_score", 70.0),
                schema=q.get("schema"),
                birth_date=q.get("birth_date"),
                country=q.get("country"),
            ),
        )
    rec.observe(
        "workshop-multi-loaded",
        "workshop_multi_loaded",
        {},
        lambda: {k: idx.is_loaded() for k, idx in multi.indices.items()},
    )
    for i, c in enumerate(DOB_COUNTRY_CASES):
        rec.observe(
            f"workshop-dob-country-{i}",
            "workshop_dob_country",
            c,
            lambda c=c: ns["_adjust_score_for_dob_country"](
                c["score"],
                rec_birth_date=c["rec_dob"],
                rec_countries=c["rec_c"],
                query_birth_date=c["q_dob"],
                query_country=c["q_c"],
            ),
        )
    return {
        "lists": [
            {k: v for k, v in asdict(s).items() if k != "csv_path"}
            for s in ns["DEFAULT_SANCTIONS_SOURCES"]
        ],
        "service_default_min_score": 65.0,
        "router_default_min_score": 70.0,
        "dob_bonus": ns["_DOB_MATCH_BONUS"],
        "dob_malus": ns["_DOB_CONFLICT_MALUS"],
        "country_bonus": ns["_COUNTRY_MATCH_BONUS"],
        "country_malus": ns["_COUNTRY_CONFLICT_MALUS"],
    }


# ------------------------------------------------------------------ audit-portal


def capture_portal(checkout: Path, rec: Recorder) -> None:
    sys.path.insert(0, str(checkout / "backend"))
    from audit_prep import sanctions as portal_csv
    from audit_prep import sanctions_xml as portal_xml

    for name in (
        "eu_fsf_targets.simple.csv",
        "un_sc_targets.simple.csv",
        "leer_nur_kopf.csv",
        "falsches_format.csv",
        "latin1_minimal.csv",
    ):
        data = (FILES / name).read_bytes()
        rec.observe(
            f"portal-csv-{name}",
            "portal_parse_csv",
            {"file": name},
            lambda d=data: portal_csv.parse_sanctions_csv(d),
        )
    parsers = {
        "eu_fsf_export.xml": portal_xml._parse_eu_fsf,
        "ofac_sdn.xml": portal_xml._parse_ofac_sdn,
        "un_sc_consolidated.xml": portal_xml._parse_un_sc,
    }
    for name, parse in parsers.items():
        data = (FILES / name).read_bytes()
        parsed = rec.observe(
            f"portal-xml-{name}",
            "portal_parse_xml",
            {"file": name},
            lambda d=data, p=parse: p(d),
        )
        for i, item in enumerate(parsed or []):
            rec.observe(
                f"portal-row-{name}-{i}",
                "portal_simple_row",
                {"parsed": item},
                lambda it=item: portal_xml.parser_dict_to_simple_csv_row(it),
            )
        rec.observe(
            f"portal-serialize-{name}",
            "portal_serialize",
            {"file": name},
            lambda p=parsed: portal_xml.parser_dicts_to_simple_csv_bytes(p or []),
        )
    for name, parse in (("kaputt.xml", portal_xml._parse_eu_fsf),):
        broken = (FILES / name).read_bytes()
        rec.observe(
            f"portal-xml-{name}",
            "portal_parse_xml",
            {"file": name},
            lambda d=broken, p=parse: p(d),
        )
    for i, value in enumerate(DATE_STRINGS):
        rec.observe(
            f"portal-date-{i}",
            "portal_parse_date",
            {"value": value},
            lambda v=value: portal_xml._parse_date_safe(v),
        )


# -------------------------------------------------------------------- flowsearch


def load_module(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class MockHttp:
    """Answers flowsearch's own ``httpx.AsyncClient`` from recorded responses."""

    def __init__(self) -> None:
        self.handler: Any = None
        self.requests: list[dict[str, Any]] = []
        self._original = httpx.AsyncClient

    def install(self) -> None:
        original = self._original
        mock = self

        def factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
            def handle(request: httpx.Request) -> httpx.Response:
                try:
                    body: Any = json.loads(request.content) if request.content else None
                except ValueError:
                    body = {"text": request.content.decode("utf-8")}
                mock.requests.append(
                    {
                        "method": request.method,
                        "url": str(request.url),
                        "json": body,
                        "authorization": request.headers.get("authorization"),
                    }
                )
                return mock.handler(request)

            kwargs["transport"] = httpx.MockTransport(handle)
            return original(*args, **kwargs)

        httpx.AsyncClient = factory  # type: ignore[misc,assignment]


#: One shared interceptor: installing a second one would wrap the first.
HTTP = MockHttp()


def json_reply(name: str, status: int = 200) -> Any:
    body = (FILES / name).read_bytes()
    return lambda request: httpx.Response(
        status, content=body, headers={"content-type": "application/json"}
    )


def capture_flowsearch(checkout: Path, rec: Recorder) -> dict[str, Any]:
    base = checkout / "backend/app/services"
    mock = HTTP
    for pkg in ("app", "app.services", "app.services.api_clients"):
        module = types.ModuleType(pkg)
        module.__path__ = []  # type: ignore[attr-defined]
        sys.modules[pkg] = module
    load_module("app.services.api_client_base", base / "api_client_base.py")
    sanctions = load_module("app.services.api_clients.sanctions", base / "api_clients/sanctions.py")
    pep = load_module(
        "app.services.api_clients.pep_screening", base / "api_clients/pep_screening.py"
    )
    register = load_module(
        "app.services.api_clients.openregister", base / "api_clients/openregister.py"
    )
    handelsregister = load_module(
        "app.services.api_clients.handelsregister", base / "api_clients/handelsregister.py"
    )
    ubo = load_module("app.services.ubo_engine", base / "ubo_engine.py")

    def run(coro: Any) -> Any:
        return asyncio.run(coro)

    def with_http(handler: Any, call: Any) -> Any:
        mock.handler = handler
        mock.requests.clear()
        result = call()
        if isinstance(result, dict) and "checked_at" in result and result["checked_at"]:
            result = {**result, "checked_at": "<zeitabhängig>"}
        return {"result": result, "requests": list(mock.requests)}

    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("simulierte Zeitüberschreitung")

    unauthorized = lambda request: httpx.Response(  # noqa: E731
        401, json={"detail": "No API key provided."}
    )
    sanction_cases = {
        "api-shape": json_reply("opensanctions_match_sanctions.json"),
        "wrapped-shape": json_reply("opensanctions_match_sanctions_wrapped.json"),
        "unauthorized": unauthorized,
        "timeout": boom,
    }
    for label, handler in sanction_cases.items():
        rec.observe(
            f"flowsearch-sanctions-{label}",
            "flowsearch_check_sanctions",
            {"case": label, "name": "Müller-Lüdenscheidt Handels GmbH", "country": "DE"},
            lambda h=handler: with_http(
                h,
                lambda: run(
                    sanctions.SanctionsAPIClient().check_sanctions(
                        "Müller-Lüdenscheidt Handels GmbH", "DE"
                    )
                ),
            ),
        )
    pep_cases = {
        "api-shape": (json_reply("opensanctions_match_pep.json"), None, {}),
        "wrapped-shape": (json_reply("opensanctions_match_pep_wrapped.json"), None, {}),
        "wrapped-with-key": (
            json_reply("opensanctions_match_pep_wrapped.json"),
            "geheim-nicht-echt",
            {"date_of_birth": "1980-07-01", "nationality": "AT"},
        ),
        "unauthorized": (unauthorized, None, {}),
    }
    for label, (handler, key, extra) in pep_cases.items():
        rec.observe(
            f"flowsearch-pep-{label}",
            "flowsearch_check_person",
            {"case": label, "name": "Anna Beispiel", "api_key": bool(key), **extra},
            lambda h=handler, k=key, e=extra: with_http(
                h,
                lambda: run(
                    pep.PEPScreeningAPIClient(api_key=k).check_person("Anna Beispiel", **e)
                ),
            ),
        )
    client = pep.PEPScreeningAPIClient()
    risk_inputs = []
    for pep_type in ("PEP (aktiv)", "Former PEP", "RCA (Relative/Close Associate)", "Unknown"):
        for score in (0.95, 0.9, 0.86, 0.85, 0.8, 0.75, 0.7, 0.5):
            for title in (None, "Ministerin", "Direktor der Behörde", "Stadträtin"):
                risk_inputs.append((pep_type, score, title))
    for i, (pep_type, score, title) in enumerate(risk_inputs):
        positions = [] if title is None else [{"title": title, "is_current": True}]
        rec.observe(
            f"flowsearch-pep-risk-{i}",
            "flowsearch_assess_risk",
            {"pep_type": pep_type, "score": score, "positions": positions},
            lambda t=pep_type, s=score, p=positions: client._assess_risk(t, s, p),
        )
    for i, (topics, positions) in enumerate(
        [
            (["role.pep"], [{"is_current": True}]),
            (["role.pep"], [{"is_current": False}]),
            (["role.pep"], []),
            (["role.rca"], []),
            (["role.pep", "role.rca"], []),
            (["sanction"], []),
            ([], []),
        ]
    ):
        rec.observe(
            f"flowsearch-pep-type-{i}",
            "flowsearch_pep_type",
            {"topics": topics, "positions": positions},
            lambda t=topics, p=positions: client._determine_pep_type(t, p),
        )
    for i, types_ in enumerate(
        [
            ["PEP (aktiv)", "RCA"],
            ["Former PEP"],
            ["RCA (Relative/Close Associate)"],
            ["Unknown"],
            [],
        ]
    ):
        matches = [{"pep_type": t} for t in types_]
        rec.observe(
            f"flowsearch-pep-category-{i}",
            "flowsearch_pep_category",
            {"matches": matches},
            lambda m=matches: client._categorize_pep(m),
        )

    not_found = lambda request: httpx.Response(  # noqa: E731
        404, text="<!DOCTYPE html><html><body>Not Found</body></html>"
    )
    rec.observe(
        "flowsearch-openregister-search-404",
        "flowsearch_openregister_search",
        {"case": "live-beobachtet-404", "name": "Beispiel GmbH"},
        lambda: with_http(
            not_found, lambda: run(register.OpenRegisterAPIClient().search_company("Beispiel GmbH"))
        ),
    )
    rec.observe(
        "flowsearch-handelsregister-search",
        "flowsearch_handelsregister_search",
        {"name": "Beispiel GmbH", "location": "Kassel"},
        lambda: run(
            handelsregister.HandelsregisterAPIClient().search_company("Beispiel GmbH", "Kassel")
        ),
    )
    oreg = register.OpenRegisterAPIClient()
    for i, name in enumerate(
        ["Beispiel GmbH", "Max Mustermann", "Agnes Beispiel", "Kagel Holding", "ACME Ltd", ""]
    ):
        rec.observe(
            f"flowsearch-entity-type-{i}",
            "flowsearch_entity_type",
            {"name": name},
            lambda n=name: oreg._determine_entity_type(n),
        )
    for i, officer in enumerate(
        [
            {"shares": "25.5"},
            {"shares": 40},
            {"position": "Gesellschafter mit 25% Anteil"},
            {"position": "Gesellschafter mit 12.5 % Anteil"},
            {"position": "Gesellschafter"},
            {},
        ]
    ):
        rec.observe(
            f"flowsearch-share-{i}",
            "flowsearch_share",
            {"officer": officer},
            lambda o=officer: oreg._extract_share_percentage(o),
        )

    structures = {
        "einfach": {
            "id": "root",
            "name": "Ziel GmbH",
            "shareholders": [
                {"name": "Person A", "type": "person", "share": 30.0},
                {"name": "Person B", "type": "person", "share": 25.0},
                {"name": "Person C", "type": "person", "share": 10.0, "voting_rights": 51.0},
                {
                    "id": "hold",
                    "name": "Holding GmbH",
                    "type": "company",
                    "share": 35.0,
                    "has_details": True,
                    "shareholders": [
                        {"name": "Person D", "type": "person", "share": 80.0},
                        {"name": "Person E", "type": "person", "share": 20.0},
                    ],
                },
            ],
        },
        "zyklus": {
            "id": "x",
            "name": "X",
            "shareholders": [
                {
                    "id": "x",
                    "name": "X",
                    "type": "company",
                    "share": 50.0,
                    "has_details": True,
                    "shareholders": [{"name": "P", "type": "person", "share": 100.0}],
                },
                {"name": "Q", "type": "person", "share": 26.0, "voting_rights": 26.0},
            ],
        },
        "ohne_details": {
            "id": "y",
            "name": "Y",
            "shareholders": [
                {"name": "Firma Z", "type": "company", "share": 100.0},
                {"name": "Person ohne Typ", "share": 25.01},
            ],
        },
    }
    for label, data in structures.items():

        def ubo_run(d: dict[str, Any] = data) -> dict[str, Any]:
            engine = ubo.UBOEngine()
            nodes = engine.traverse_ownership(d)
            loops = [n.id for n in engine.ownership_graph.values() if n.parent_id == n.id]
            return {
                "nodes": nodes,
                "ubos": engine.identify_ubos(nodes),
                # build_ownership_chain does not terminate on a self-referencing
                # node (observed: unbounded memory growth); it is only called
                # for acyclic graphs and the loop is recorded instead.
                "chain": None if loops else [engine.build_ownership_chain(n.id) for n in nodes],
                "self_loops": loops,
                "graph": engine.generate_network_graph_data(),
            }

        rec.observe(f"flowsearch-ubo-{label}", "flowsearch_ubo", {"structure": data}, ubo_run)
    kmu_inputs = [
        {},
        {"employees": 9, "revenue": 2_000_000, "balance_sheet_total": 1_000_000},
        {"employees": 9, "revenue": 3_000_000, "balance_sheet_total": 1_500_000},
        {"employees": 49, "revenue": 10_000_000, "balance_sheet_total": 5_000_000},
        {"employees": 49, "revenue": 12_000_000, "balance_sheet_total": 9_000_000},
        {"employees": 249, "revenue": 60_000_000, "balance_sheet_total": 43_000_000},
        {"employees": 249, "revenue": 60_000_000, "balance_sheet_total": 44_000_000},
        {"employees": 250, "revenue": 1_000_000, "balance_sheet_total": 1_000_000},
    ]
    for i, data in enumerate(kmu_inputs):
        rec.observe(
            f"flowsearch-kmu-{i}",
            "flowsearch_kmu",
            {"company": data},
            lambda d=data: ubo.UBOEngine().calculate_kmu_status(d),
        )
    return {
        "ubo_threshold": ubo.UBOEngine.UBO_THRESHOLD,
        "max_depth": ubo.UBOEngine.MAX_DEPTH,
        "opensanctions_api": pep.PEPScreeningAPIClient.OPENSANCTIONS_API,
    }


# ------------------------------------------------------------------------- osint


def capture_osint(checkout: Path, rec: Recorder) -> None:
    module = load_module("osint_traeger_quellen", checkout / "werkzeuge/traeger_quellen.py")
    replies: dict[str, bytes] = {}

    def abrufen(url: str, sekunden: int = 300) -> bytes:
        if url not in replies:
            raise OSError(f"keine Aufzeichnung für {url}")
        return replies[url]

    module._abrufen = abrufen
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        module.DATEN = root
        module.ZER_DATEI = root / "zer.json"
        module.KAMMERN_DATEI = root / "kammern.json"

        def run_writer(call: Any, target: Path) -> dict[str, Any]:
            out, err = io.StringIO(), io.StringIO()
            if target.exists():
                target.unlink()
            with redirect_stdout(out), redirect_stderr(err):
                count = call()
            return {
                "return": count,
                "file": json.loads(target.read_text(encoding="utf-8")),
                "stdout": out.getvalue(),
                "stderr": err.getvalue(),
            }

        for label, status in (
            ("gleich", "zer_status.json"),
            ("abweichend", "zer_status_abweichend.json"),
        ):
            replies.clear()
            replies[module.ZER_STATUS] = (FILES / status).read_bytes()
            replies[module.ZER_ABRUF] = (FILES / "zer_register.json").read_bytes()
            rec.observe(
                f"osint-zer-{label}",
                "osint_zer",
                {"status": status, "register": "zer_register.json"},
                lambda: run_writer(module.zer_holen, module.ZER_DATEI),
            )
        for label, file_name in (
            ("liste", "ihk_locations.json"),
            ("objekt", "ihk_locations_wrapped.json"),
        ):
            replies.clear()
            replies[module.IHK_ABRUF] = (FILES / file_name).read_bytes()
            rec.observe(f"osint-ihk-{label}", "osint_ihk", {"file": file_name}, module.ihk_holen)
        replies.clear()
        replies[module.ZDH_SEITE] = (FILES / "zdh_handwerkskammern.html").read_bytes()
        rec.observe(
            "osint-hwk", "osint_hwk", {"file": "zdh_handwerkskammern.html"}, module.hwk_holen
        )
        replies[module.IHK_ABRUF] = (FILES / "ihk_locations.json").read_bytes()
        rec.observe(
            "osint-kammern",
            "osint_kammern",
            {"ihk": "ihk_locations.json", "hwk": "zdh_handwerkskammern.html"},
            lambda: run_writer(module.kammern_holen, module.KAMMERN_DATEI),
        )
        replies.clear()
        rec.observe("osint-ihk-fehler", "osint_ihk", {"file": None}, module.ihk_holen)


# ------------------------------------------------------------------- flowinvoice


class MemoryCache:
    """Stand-in for the file cache: records keys, never hits."""

    def __init__(self) -> None:
        self.keys: list[str] = []

    async def get(self, name: str, country: str | None = None) -> None:
        self.keys.append(f"get:{name}:{country}")
        return None

    async def set(self, name: str, result: Any, country: str | None = None) -> bool:
        self.keys.append(f"set:{name}:{country}")
        return True


def capture_flowinvoice(checkout: Path, rec: Recorder) -> dict[str, Any]:
    base = checkout / FI
    mock = HTTP
    # Package stub: the real __init__ imports the whole application (database,
    # ORM); the audited modules only use relative imports among themselves.
    for pkg, path in (
        ("app", None),
        ("app.services", None),
        ("app.services.fraud_detection", base),
    ):
        module = types.ModuleType(pkg)
        module.__path__ = [str(path)] if path else []  # type: ignore[attr-defined]
        sys.modules[pkg] = module
    models = load_module("app.services.fraud_detection.models", base / "models.py")
    load_module("app.services.fraud_detection.rate_limiter", base / "rate_limiter.py")
    cache = load_module("app.services.fraud_detection.cache", base / "cache.py")
    checker_mod = load_module(
        "app.services.fraud_detection.sanctions_checker", base / "sanctions_checker.py"
    )
    pep_mod = load_module("app.services.fraud_detection.pep_checker", base / "pep_checker.py")
    company_mod = load_module(
        "app.services.fraud_detection.company_verifier", base / "company_verifier.py"
    )
    import xml.etree.ElementTree as ET  # the original parser; inputs are local fixtures

    downloader_ns = ast_load(
        base / "sanctions_downloader.py",
        ["SanctionsDownloader"],
        {
            "ET": ET,
            "re": re,
            "date": date,
            "datetime": datetime,
            "UTC": UTC,
            "Path": Path,
            "Any": Any,
            "httpx": httpx,
            "logger": logging.getLogger("flowinvoice.downloader"),
            "__name__": "flowinvoice_sanctions_downloader",
        },
    )

    def run(coro: Any) -> Any:
        return asyncio.run(coro)

    def with_http(handler: Any, call: Any) -> Any:
        mock.handler = handler
        mock.requests.clear()
        result = call()
        return {"result": result, "requests": list(mock.requests)}

    with tempfile.TemporaryDirectory() as tmp:
        downloader = downloader_ns["SanctionsDownloader"](download_dir=tmp)
        parsed: dict[str, list[dict[str, Any]]] = {}
        for name, method in (
            ("eu_fsf_export.xml", downloader._parse_eu_fsf),
            ("ofac_sdn.xml", downloader._parse_ofac_sdn),
            ("un_sc_consolidated.xml", downloader._parse_un_sc),
            ("kaputt.xml", downloader._parse_eu_fsf),
        ):
            content = (FILES / name).read_bytes()
            parsed[name] = (
                rec.observe(
                    f"flowinvoice-xml-{name}",
                    "flowinvoice_parse_xml",
                    {"file": name},
                    lambda d=content, m=method: m(d),
                )
                or []
            )
        for i, value in enumerate(DATE_STRINGS):
            rec.observe(
                f"flowinvoice-date-{i}",
                "flowinvoice_parse_date",
                {"value": value},
                lambda v=value: downloader._parse_date_safe(v),
            )
        for i, value in enumerate([None, [], ["a", "", " b "], "x, y ,,z", "", 5]):
            rec.observe(
                f"flowinvoice-to-list-{i}",
                "flowinvoice_to_list",
                {"value": value},
                lambda v=value: downloader._to_list(v),
            )

        # Local screening against parsed list entries (difflib variant).
        entities = []
        for list_type, name in (
            ("EU_FSF", "eu_fsf_export.xml"),
            ("OFAC_SDN", "ofac_sdn.xml"),
            ("UN_SC", "un_sc_consolidated.xml"),
        ):
            for item in parsed[name]:
                entities.append(
                    types.SimpleNamespace(
                        name=item["name"],
                        aliases=item.get("aliases") or [],
                        list_type=list_type,
                        entity_type=item.get("entity_type"),
                        sanction_programs=item.get("sanction_programs") or [],
                        vat_ids=item.get("vat_ids") or [],
                    )
                )
        checker = checker_mod.SanctionsChecker()
        checker.cache = MemoryCache()
        for i, (query, min_score) in enumerate(
            [
                ("Iwan Petrowitsch Musterow", 0.75),
                ("iwan musterow", 0.75),
                ("Ivan Musterov", 0.75),
                ("Müller-Lüdenscheidt Handels GmbH", 0.75),
                ("Mueller-Luedenscheidt Handels GmbH", 0.75),
                ("Demo Trade Holding", 0.75),
                ("Demo Trade Holding", 0.95),
                ("Jorgen Odegard", 0.75),
                ("Unbekannte Firma", 0.75),
            ]
        ):
            rec.observe(
                f"flowinvoice-local-{i}",
                "flowinvoice_local_screen",
                {"name": query, "min_score": min_score},
                lambda q=query, m=min_score: run(
                    checker.check_entity_local(None, q, entities=entities, min_score=m)
                ),
            )

        def search_reply(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=(FILES / "sanctions_network_search.json").read_bytes()
            )

        def dns_failure(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("[Errno -2] Name or service not known")

        def server_error(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="Fehler")

        for label, handler in (
            ("antwort", search_reply),
            ("dns", dns_failure),
            ("http500", server_error),
        ):
            rec.observe(
                f"flowinvoice-network-{label}",
                "flowinvoice_sanctions_network",
                {"case": label, "name": "Iwan Musterow", "country": "RU"},
                lambda h=handler: with_http(
                    h,
                    lambda: run(checker._check_sanctions_network("Iwan Musterow", "RU", 0.8)),
                ),
            )
            rec.observe(
                f"flowinvoice-check-entity-{label}",
                "flowinvoice_check_entity",
                {"case": label, "name": "Iwan Musterow", "country": "RU"},
                lambda h=handler: with_http(
                    h, lambda: run(checker.check_entity("Iwan Musterow", country="RU"))
                ),
            )

        # PEP bulk list: the original download/parse path against a synthetic
        # peps CSV, then the matching with the parsed entries.
        pep_checker = pep_mod.PEPChecker(cache_dir=str(Path(tmp) / "pep"), min_score=0.8)

        def peps_reply(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=(FILES / "peps_targets.simple.csv").read_bytes())

        pep_entries = (
            rec.observe(
                "flowinvoice-pep-parse",
                "flowinvoice_pep_parse",
                {"file": "peps_targets.simple.csv"},
                lambda: with_http(peps_reply, lambda: run(pep_checker._download_and_parse())),
            )
            or {"result": []}
        )["result"]

        async def loaded() -> list[dict[str, Any]]:
            return pep_entries  # type: ignore[no-any-return]

        pep_checker._load_pep_data = loaded
        pep_checker._dataset_size = len(pep_entries)
        pep_checker._last_update = "<Ladezeitpunkt>"
        for i, (query, country, min_score) in enumerate(
            [
                ("Erika Musterfrau", "DE", None),
                ("Erika Beispiel", None, None),
                ("Beispiel", "AT", None),
                ("Anna Beispiel", "AT", 0.5),
                ("Jorgen Strassburger", "DE", None),
                ("Jørgen Straßburger", "NO", None),
                ("Max Mustermann", "DE", None),
                ("Max Mustermann", "FR", 0.6),
                ("Эрика Беиспиел", None, None),
                ("", None, None),
                ("   ", None, None),
            ]
        ):
            rec.observe(
                f"flowinvoice-pep-{i}",
                "flowinvoice_pep_check",
                {"name": query, "country": country, "min_score": min_score},
                lambda q=query, c=country, m=min_score: run(
                    pep_checker.check_entity(q, country=c, min_score=m)
                ),
            )
        failing = pep_mod.PEPChecker(cache_dir=str(Path(tmp) / "pep2"))

        async def load_fails() -> list[dict[str, Any]]:
            raise httpx.ConnectError("Datenquelle nicht erreichbar")

        failing._load_pep_data = load_fails
        rec.observe(
            "flowinvoice-pep-load-error",
            "flowinvoice_pep_check",
            {"name": "Erika Beispiel", "country": None, "min_score": None, "load": "error"},
            lambda: run(failing.check_entity("Erika Beispiel")),
        )
        for i, name in enumerate(
            ["Müller GmbH", "Straße", "Jørgen Ødegård", "Łódź", "Иван", "  A--B  ", "ÉCOLE"]
        ):
            rec.observe(
                f"flowinvoice-pep-normalize-{i}",
                "flowinvoice_pep_normalize",
                {"name": name},
                lambda n=name: pep_mod.PEPChecker._normalize_name(n),
            )
        for i, (q, n, c, countries) in enumerate(
            [
                ("anna beispiel", "anna beispiel", None, ""),
                ("anna beispiel", "anna maria beispiel", None, ""),
                ("anna beispiel", "anna maria beispiel", "AT", "at"),
                ("beispiel", "anna beispiel", None, ""),
                ("anna", "berta", None, ""),
                ("anna beispiel", "anna beispiel mueller", "de", "at;de"),
                ("anna beispiel", "beispiel anna", "q", "iq"),
            ]
        ):
            rec.observe(
                f"flowinvoice-pep-score-{i}",
                "flowinvoice_pep_score",
                {"query": q, "pep_name": n, "country": c, "countries": countries},
                lambda q=q, n=n, c=c, k=countries: pep_checker._match_name(
                    q, n, c, {"countries": k}
                ),
            )
        rec.observe(
            "flowinvoice-pep-position",
            "flowinvoice_pep_position",
            {"values": ["", '{"position": ["A", "B"]}', '{"role": "R"}', "kein json"]},
            lambda: [
                pep_mod.PEPChecker._extract_position(v)
                for v in ["", '{"position": ["A", "B"]}', '{"role": "R"}', "kein json"]
            ],
        )

        # Original regression tests of flowinvoice (backend/tests/test_pep_checker.py).
        tests = load_module(
            "flowinvoice_test_pep_checker", checkout / "backend/tests/test_pep_checker.py"
        )
        outcomes = {}
        for name in sorted(n for n in dir(tests) if n.startswith("test_")):

            class Patch:
                def setattr(self, target: Any, attr: str, value: Any) -> None:
                    setattr(target, attr, value)

            with tempfile.TemporaryDirectory() as test_tmp:
                try:
                    run(getattr(tests, name)(Path(test_tmp), Patch()))
                    outcomes[name] = "PASS"
                except AssertionError as exc:
                    outcomes[name] = f"FAIL: {exc}"
        rec.observe(
            "flowinvoice-original-tests", "flowinvoice_original_tests", {}, lambda: outcomes
        )

    # Company verification: VIES and OffeneRegister (datasette).
    verifier = company_mod.CompanyVerifier()

    def xml_reply(name: str) -> Any:
        return lambda request: httpx.Response(
            200, content=(FILES / name).read_bytes(), headers={"content-type": "text/xml"}
        )

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("simulierte Zeitüberschreitung")

    vies_cases = {
        "live-de-ungueltig": ("DE000000000", xml_reply("vies_de_000000000_live.xml")),
        "gueltig-ns2": ("ATU00000000", xml_reply("vies_valid_ns2.xml")),
        "gueltig-de-ohne-name": ("DE 000 000 001", xml_reply("vies_valid_de_ohne_name.xml")),
        "ohne-praefix": ("ATU00000000", xml_reply("vies_ohne_praefix.xml")),
        "fault": ("ATU00000000", xml_reply("vies_fault.xml")),
        "timeout": ("ATU00000000", timeout),
        "formatfehler": ("123", xml_reply("vies_valid_ns2.xml")),
        "kleinbuchstaben": ("atu00000000", xml_reply("vies_valid_ns2.xml")),
    }
    for label, (vat_id, handler) in vies_cases.items():
        rec.observe(
            f"flowinvoice-vies-{label}",
            "flowinvoice_vies",
            {"case": label, "vat_id": vat_id},
            lambda v=vat_id, h=handler: with_http(h, lambda: run(verifier.validate_vat_id(v))),
        )

    def json_file(name: str, status: int = 200) -> Any:
        return lambda request: httpx.Response(status, content=(FILES / name).read_bytes())

    register_cases = {
        "registriert": ("Beispiel Handels GmbH", json_file("offeneregister_datasette.json")),
        "liquidation": ("Beispiel Handels GmbH", json_file("offeneregister_liquidation.json")),
        "dissolved": ("Beispiel Handels GmbH", json_file("offeneregister_dissolved.json")),
        "removed": ("Beispiel Handels GmbH", json_file("offeneregister_removed.json")),
        "leer": ("Beispiel Handels GmbH", json_file("offeneregister_leer.json")),
        "http502": ("Beispiel Handels GmbH", json_file("offeneregister_leer.json", 502)),
        "apostroph": ("O'Beispiel GmbH", json_file("offeneregister_datasette.json")),
        "umlaut": ("Müller & Söhne GmbH", json_file("offeneregister_datasette.json")),
        "sonderzeichen": ("Beispiel/Handels GmbH", json_file("offeneregister_datasette.json")),
        "zu-lang": ("B" * 101, json_file("offeneregister_datasette.json")),
    }
    for label, (name, handler) in register_cases.items():
        rec.observe(
            f"flowinvoice-offeneregister-{label}",
            "flowinvoice_offeneregister",
            {"case": label, "name": name},
            lambda n=name, h=handler: with_http(h, lambda: run(verifier.search_offene_register(n))),
        )
    pairs = [
        ("Beispiel Handels GmbH", "BEISPIEL HANDELS GMBH"),
        ("Beispiel Handels GmbH", "Beispiel Handels"),
        ("Hagen Metall AG", "Hagen Metall"),
        ("Hagen Metall AG", "Metallbau Hagen GmbH"),
        ("Kagel & Co. KG", "Kagel GmbH & Co. KG"),
        ("Alpha Beta Gamma GmbH", "Alpha Beta Delta GmbH"),
        ("Alpha Beta Gamma GmbH", "Alpha Zeta Eta GmbH"),
        ("Beispiel Handels GmbH", "---"),
        ("Müller GmbH", "Mueller GmbH"),
        ("", ""),
    ]
    for i, (a, b) in enumerate(pairs):
        rec.observe(
            f"flowinvoice-names-{i}",
            "flowinvoice_names_match",
            {"a": a, "b": b},
            lambda a=a, b=b: {
                "match": verifier._names_match(a, b),
                "a": verifier._normalize_company_name(a),
                "b": verifier._normalize_company_name(b),
            },
        )
    verify_cases = {
        "gueltig-name-gleich-at": (
            "Beispiel Handels GmbH",
            "ATU00000000",
            "AT",
            {"vies": "vies_valid_ns2.xml"},
        ),
        "de-live-ungueltig-registriert": (
            "Beispiel Handels GmbH",
            "DE000000000",
            "DE",
            {"vies": "vies_de_000000000_live.xml", "register": "offeneregister_datasette.json"},
        ),
        "de-ohne-ustid-liquidation": (
            "Beispiel Handels GmbH",
            None,
            "DE",
            {"register": "offeneregister_liquidation.json"},
        ),
        "de-ohne-ustid-nicht-gefunden": (
            "Beispiel Handels GmbH",
            None,
            "DE",
            {"register": "offeneregister_leer.json"},
        ),
        "de-gueltig-ohne-name-registriert": (
            "Beispiel Handels GmbH",
            "DE000000001",
            "DE",
            {"vies": "vies_valid_de_ohne_name.xml", "register": "offeneregister_datasette.json"},
        ),
        "vies-fault-de": (
            "Beispiel Handels GmbH",
            "DE000000001",
            "DE",
            {"vies": "vies_fault.xml", "register": "offeneregister_removed.json"},
        ),
    }
    for label, (name, vat_id, country, files) in verify_cases.items():

        def route(request: httpx.Request, f: dict[str, str] = files) -> httpx.Response:
            if "vies" in str(request.url):
                if f.get("vies") == "vies_fault.xml":
                    return httpx.Response(500, content=(FILES / "vies_fault.xml").read_bytes())
                return httpx.Response(200, content=(FILES / f["vies"]).read_bytes())
            return httpx.Response(200, content=(FILES / f["register"]).read_bytes())

        rec.observe(
            f"flowinvoice-verify-{label}",
            "flowinvoice_verify_company",
            {"case": label, "name": name, "vat_id": vat_id, "country": country, "files": files},
            lambda n=name, v=vat_id, c=country, r=route: with_http(
                r, lambda: run(verifier.verify_company(n, vat_id=v, country=c))
            ),
        )
    rate = sys.modules["app.services.fraud_detection.rate_limiter"]
    return {
        "rate_limits": {
            "vies": list(rate.VIES_RATE_LIMIT),
            "sanctions_network": list(rate.SANCTIONS_RATE_LIMIT),
            "offeneregister": list(rate.OFFENEREGISTER_RATE_LIMIT),
        },
        "cache_key_example": cache.FileCache(cache_dir=tempfile.gettempdir())
        ._get_cache_path("sanctions:müller & söhne:DE")
        .name,
        "urls": {
            "sanctions_network": checker_mod.SanctionsChecker.SANCTIONS_NETWORK_URL,
            "pep_csv": pep_mod.PEPChecker.PEP_CSV_URL,
            "vies": company_mod.CompanyVerifier.VIES_URL,
            "offeneregister": company_mod.CompanyVerifier.OFFENE_REGISTER_URL,
            "eu_fsf": downloader_ns["SanctionsDownloader"].EU_FSF_URL,
            "ofac_sdn": downloader_ns["SanctionsDownloader"].OFAC_SDN_URL,
            "un_sc": downloader_ns["SanctionsDownloader"].UN_SC_URL,
        },
        "models": sorted(n for n in dir(models) if not n.startswith("_"))[:0],
    }


# ------------------------------------------------------------------ riskanalysis


def capture_riskanalysis(checkout: Path, rec: Recorder) -> dict[str, Any]:
    module = load_module(
        "riskanalysis_sanctions", checkout / "backend/app/services/sanctions_screening.py"
    )
    for i, name in enumerate(
        [
            "Fiktiver Auftragnehmer 007",
            "Fiktiv Auftragnehmer 7",
            "Demo Trade Holdings",
            "Demo Trade Holdings Ltd",
            "Müller GmbH",
            "Unbekannt",
        ]
    ):
        rec.observe(
            f"riskanalysis-screen-{i}",
            "riskanalysis_screen",
            {"name": name},
            lambda n=name: module.screen_name(n),
        )
    return {"threshold_default": 82.0, "sources": module.SOURCES}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkouts", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    bound = verify(args.checkouts)
    HTTP.install()
    rec = Recorder()
    constants = {
        "audit_designer": capture_designer(args.checkouts / "audit_designer", rec),
        "flowworkshop": capture_workshop(args.checkouts / "flowworkshop", rec),
        "flowsearch": capture_flowsearch(args.checkouts / "flowsearch", rec),
        "riskanalysis": capture_riskanalysis(args.checkouts / "riskanalysis", rec),
        "flowinvoice": capture_flowinvoice(args.checkouts / "flowinvoice", rec),
    }
    capture_portal(args.checkouts / "audit-portal", rec)
    capture_osint(args.checkouts / "osint", rec)
    import auditcore_entity_matching

    document = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION",
        "captured_at": datetime.now(UTC).date().isoformat(),
        "sources": bound,
        "fixture_files": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(FILES.iterdir())
        },
        "environment": {
            "python": platform.python_version(),
            "rapidfuzz": rapidfuzz.__version__,
            "httpx": httpx.__version__,
            "unicode": unicodedata.unidata_version,
            "auditcore_entity_matching_called_by_workshop": auditcore_entity_matching.__version__,
        },
        "constants": jsonable(constants),
        "cases": rec.cases,
    }
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"{len(rec.cases)} Fälle → {args.output}")


if __name__ == "__main__":
    main()
