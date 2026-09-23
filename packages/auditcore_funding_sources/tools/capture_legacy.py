"""Capture actual behavior of the funding/state-aid/de-minimis source code before extraction.

One run per source application, each with that application's interpreter::

    python tools/capture_legacy.py flowworkshop <checkout>/auditworkshop/backend tests/fixtures
    python tools/capture_legacy.py flowsearch   <checkout>/backend               tests/fixtures
    python tools/capture_legacy.py designer     <checkout>/backend               tests/fixtures

The tool never imports ``auditcore_funding_sources``. It verifies every executed
source file against the pinned GitHub blob, requires a clean checkout at the
pinned commit (unless ``--migrated``), and refuses to run unless the
application database URL points to an unreachable or scratch target. Only
synthetic inputs in original formats are used; no network access (HTTP is
answered by an in-process mock transport).
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

_REGISTER = "app/core/shared/research/register/"
SOURCES: dict[str, dict[str, Any]] = {
    "flowworkshop": {
        "repository": "janpow77/flowworkshop",
        "commit": "a05bb2143bd96d5e981f9462f05b965e1658be36",
        "root": "auditworkshop/backend",
        "blobs": {
            "services/beneficiary_harvester.py": "45c82fd8e7e27a5d9422052266009a6d516e0f92",
            "services/state_aid_service.py": "e41be2700affb91c2a6436a7e3ce488696b07116",
            "services/dataframe_service.py": "da75ef92f2ea749f0d184e0e647288ef67f08acf",
            "services/geocoding_service.py": "3c6ac686be9bc222749fc06b7271ef94c44c2cc3",
        },
        "database_env": {"DATABASE_URL": "postgresql://nobody:nobody@127.0.0.1:1/never"},
    },
    "flowsearch": {
        "repository": "janpow77/flowsearch",
        "commit": "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4",
        "root": "backend",
        "blobs": {
            "app/services/eu_beneficiary_harvester_v2.py": (
                "4cbc58a2057e896808a079808d8f6fa968c2f79f"
            ),
            "app/services/harvest_source_manager.py": "9768fc66299f933e643349579d351050c789d101",
        },
        "database_env": {"DATABASE_URL": "postgresql+asyncpg://nobody:nobody@127.0.0.1:1/never"},
    },
    "designer": {
        "repository": "janpow77/audit_designer",
        "commit": "030a71e083ef0feddc14545b095a4945bc0bbd7a",
        "root": "backend",
        "blobs": {
            _REGISTER + "beneficiaries.py": "88f8d649c6a43607daaabab93a16cb6fdf82a8b2",
            _REGISTER + "state_aid.py": "79fb0ab5aa2082a3c080867bec9e8e14d3245b06",
            _REGISTER + "de_minimis.py": "e0a660aa902933d5c7f6a550b908e8b0b1b0be16",
            _REGISTER + "de_minimis_ernte.py": "9ad78b1bf491d546caea4e161d8a140d8853e161",
            _REGISTER + "de_minimis_models.py": "b73451505740935ff201968295ce5b2e2c12b582",
            _REGISTER + "de_minimis_zuordnung.py": "56e1f5053ba1aa356be64a505b6c62d8a3489d52",
        },
        "database_env": {"DATABASE_URL": "postgresql://nobody:nobody@127.0.0.1:1/never"},
    },
}


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def jsonable(value: Any) -> Any:
    """Type-preserving JSON form so that replays compare types, not only text."""
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        if value != value:
            return {"$float": "nan"}
        return {"$float": repr(value)}
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, bytes):
        return {"$bytes_sha256": hashlib.sha256(value).hexdigest(), "length": len(value)}
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

    def observe(self, name: str, operation: str, inputs: Any, call: Any) -> None:
        before = copy.deepcopy(inputs)
        try:
            output = jsonable(call())
            exception = None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output = None
            exception = {"type": type(exc).__name__, "message": str(exc)}
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


AMOUNTS: list[Any] = [
    None,
    "",
    " ",
    "-",
    "—",
    "–",
    "0",
    "1234",
    "1.234",
    "1.234.567",
    "1.234,56",
    "1,234.56",
    "1,234,567",
    "1,5",
    "1,50",
    "1,500",
    "12,3456",
    "1.2.3",
    "1.000.000,00 €",
    "€ 1.200",
    "EUR 1.200,00",
    "1.200,00 EUR",
    "usd 10",
    "150.000,00 €",
    "500,001 to 1,000,000",
    "500.001 bis 1.000.000",
    "less than 100,000",
    "weniger als 100.000",
    "< 50000",
    "more than 30,000,000",
    "mehr als 5",
    "> 10",
    "1\xa0234,56",
    "1 234 567",
    "-1.500,00",
    "abc",
    "12e3",
    "0,5",
    "1.5",
    "100.",
    ".5",
    "1,2,3",
    1234,
    1234.5,
    0,
    -3,
    float("nan"),
    Decimal("12.50"),
    True,
]
DATES: list[Any] = [
    None,
    "",
    "2024-03-15",
    "15.03.2024",
    "15/03/2024",
    "2024/03/15",
    "15.03.24",
    "2024-03-15T00:00:00",
    "2024-03-15 10:00",
    "31.02.2024",
    "3/4/2024",
    " 2024-01-01 ",
    "01.01.1900",
    "20240315",
    datetime(2024, 3, 15, 12, 30),
    date(2024, 3, 15),
    45000,
    "Q1 2024",
]
NAMES: list[Any] = [
    None,
    "",
    "Beispiel GmbH",
    "  BEISPIEL   gmbh  ",
    "Müller & Söhne KG",
    "Fraunhofer-Gesellschaft e.V.",
    "ÄÖÜ Straße ß GmbH & Co. KG",
    "Holding Group Deutschland AG",
    "ACME Ltd.",
    "Société Générale S.A.",
    "Łódź Sp. z o.o.",
    "Dvořák s.r.o.",
    "gGmbH Stiftung",
    "Co. KG",
    "Gruppe International",
    "123 GmbH",
    "Her************",
    "o’Brien & Co",
    "Peter\tMeier\nGmbH",
]
SA_TEXTS: list[Any] = [
    None,
    "",
    "SA.12345",
    "sa 12345",
    "SA-12345/2021",
    "SA.123456",
    "SA.1234",
    "SA.123",
    "Beihilfe SA_54321.2020",
    "XSA.12345",
    "SA12345/20",
    "Verweis auf SA.98765 und SA.11111",
    "N 123/2010",
]


def capture_flowworkshop(root: Path, fixtures: Path, rec: Recorder) -> dict[str, Any]:
    import openpyxl
    from services import beneficiary_harvester as bh
    from services import dataframe_service as dfs
    from services import state_aid_service as sa
    from services.geocoding_service import COLUMN_PATTERNS

    for i, v in enumerate(AMOUNTS):
        rec.observe(
            f"parse_amount-{i}",
            "workshop.parse_amount",
            {"value": v},
            lambda v=v: sa.parse_amount(v),
        )
    for i, v in enumerate(DATES):
        rec.observe(
            f"parse_date-{i}", "workshop.parse_date", {"value": v}, lambda v=v: sa.parse_date(v)
        )
    for i, v in enumerate(NAMES):
        for filler in (False, True):
            rec.observe(
                f"normalize_company_name-{i}-{filler}",
                "workshop.normalize_company_name",
                {"value": v, "drop_filler": filler},
                lambda v=v, f=filler: sa.normalize_company_name(v, drop_filler=f),
            )
        rec.observe(
            f"strip_accents-{i}",
            "workshop.strip_accents",
            {"value": v},
            lambda v=v: sa._strip_accents(v),
        )
        rec.observe(
            f"normalize_for_hash-{i}",
            "workshop.normalize_for_hash",
            {"value": v},
            lambda v=v: bh._normalize_for_hash(v),
        )
        rec.observe(
            f"normalize_name_simple-{i}",
            "workshop.normalize_company_name_simple",
            {"value": v},
            lambda v=v: bh._normalize_company_name_simple(v),
        )
    for i, v in enumerate(SA_TEXTS):
        rec.observe(
            f"detect_sa-{i}",
            "workshop.detect_sa_reference",
            {"value": v},
            lambda v=v: sa.detect_sa_reference(v),
        )
    for i, v in enumerate(
        [None, float("nan"), "", " x ", 12345.0, 1234.0, 12345.5, "01067", 1067, 0, "  "]
    ):
        rec.observe(
            f"stringify-{i}", "workshop.stringify", {"value": v}, lambda v=v: bh._stringify(v)
        )
        rec.observe(
            f"stringify_plz-{i}",
            "workshop.stringify_plz",
            {"value": v},
            lambda v=v: bh._stringify_plz(v),
        )
    for i, v in enumerate([None, "", "50,1", "50.1", " 8,25 ", "x", 7, 7.5, float("nan"), True]):
        rec.observe(
            f"coerce_float-{i}",
            "workshop.coerce_float",
            {"value": v},
            lambda v=v: bh._coerce_float(v),
        )
    base_row = {
        "beneficiary_name": "Beispiel GmbH",
        "project_name": "Energieeffizienz 2030",
        "project_aktenzeichen": "AZ-12345",
        "bundesland": "Hessen",
        "periode": "2021-2027",
        "fonds": "EFRE",
        "funded_at_raw": "2024-03-15",
        "cost_total_raw": "150.000,00 €",
    }
    hash_rows = {
        "full": base_row,
        "whitespace": {**base_row, "beneficiary_name": "  Beispiel   GmbH "},
        "case": {**base_row, "beneficiary_name": "BEISPIEL GMBH"},
        "legal-form": {**base_row, "beneficiary_name": "Beispiel KG"},
        "without-context": {
            k: v for k, v in base_row.items() if k not in ("bundesland", "periode", "fonds")
        },
        "nan": {**base_row, "cost_total_raw": float("nan")},
        "float-cost": {**base_row, "cost_total_raw": "150000.0"},
        "int-cost": {**base_row, "cost_total_raw": "150000"},
        "nfkc": {**base_row, "beneficiary_name": "Beispiel GmbH"},
        "empty": {},
        "extra-field": {**base_row, "plz": "12345"},
    }
    for name, row in hash_rows.items():
        for key in ("hessen_efre_2021_2027", "src1", ""):
            rec.observe(
                f"hash-{name}-{key}",
                "workshop.compute_record_hash",
                {"row": row, "source_key": key},
                lambda r=row, k=key: bh.compute_record_hash(r, k),
            )
    headers_sets = {
        "german": [
            "Name des Begünstigten",
            "Bezeichnung des Vorhabens",
            "Gesamtkosten",
            "Unionsbeteiligung",
            "PLZ",
            "Ort",
            "Datum des Beginns",
            "Datum des Endes",
            "Aktenzeichen",
        ],
        "english": [
            "beneficiary_name",
            "operation_name",
            "total_eligible_cost",
            "eu_funding",
            "postcode",
            "city",
            "start_date",
            "end_date",
            "operation_id",
        ],
        "ambiguous": [
            "Name",
            "Firmenname",
            "Projekt",
            "Projektkosten",
            "Betrag",
            "Standort PLZ",
            "Standort Ort",
        ],
        "empty": [],
        "no-name": ["Projekt", "Kosten"],
    }
    mappings: list[Any] = [
        None,
        {},
        {"name": "Firmenname"},
        {"name": "fehlt"},
        {"unbekannt": "Projekt"},
        {"kosten": "Betrag", "plz": "Standort PLZ"},
    ]
    for hname, headers in headers_sets.items():
        for mi, mapping in enumerate(mappings):
            rec.observe(
                f"columns-{hname}-{mi}",
                "workshop.detect_canonical_columns",
                {"headers": headers, "mapping": mapping},
                lambda h=headers, m=mapping: bh._detect_canonical_columns(h, m),
            )

    files = fixtures / "files"
    files.mkdir(parents=True, exist_ok=True)
    generated = _workshop_files(files, openpyxl)
    runs = [(n, s) for n, s in generated.items()]
    runs.append(("ohne_namensspalte.csv", {"field_mapping": {"name": "Projekt"}}))
    runs.append(("semikolon_titelzeilen.csv", {"field_mapping": {"name": "Ort", "unbekannt": "x"}}))
    for index, (file_name, spec) in enumerate(runs):
        content = (files / file_name).read_bytes()
        rec.observe(
            f"parse_file-{index}-{file_name}",
            "workshop.parse_xlsx_or_csv",
            {"file": file_name, "sha256": hashlib.sha256(content).hexdigest(), **spec},
            lambda c=content, n=file_name, s=spec: list(
                bh.parse_xlsx_or_csv(
                    c,
                    file_name=n,
                    header_row=s.get("header_row", 0),
                    field_mapping=s.get("field_mapping"),
                    sheet=s.get("sheet"),
                )
            ),
        )
        if "field_mapping" not in spec:
            rec.observe(
                f"read-{file_name}",
                "workshop.read_table",
                {"file": file_name, **spec},
                lambda c=content, n=file_name: _frame(dfs, c, n),
            )

    rows_named = [
        {"_row_number": i + 1, "beneficiary_name": f"N{i}", "raw_row": {"Fonds": f}}
        for i, f in enumerate(["EFRE", "JTF", "EFRE", "ESF+", "efre "])
    ]
    for fonds in (None, "", "EFRE", "JTF", "ESF", "ESF+", "KOHÄSION"):
        rec.observe(
            f"fund-filter-{fonds}",
            "workshop.filter_by_fund",
            {"rows": rows_named, "fonds": fonds},
            lambda f=fonds: bh.filtere_nach_fonds(copy.deepcopy(rows_named), f),
        )
    single = [
        {"_row_number": 1, "raw_row": {"Fonds": "EFRE"}},
        {"_row_number": 2, "raw_row": {"Fonds": "EFRE"}},
    ]
    rec.observe(
        "fund-filter-uniform",
        "workshop.filter_by_fund",
        {"rows": single, "fonds": "JTF"},
        lambda: bh.filtere_nach_fonds(copy.deepcopy(single), "JTF"),
    )
    headerish = [
        {"_row_number": 1, "raw_row": {"Fund concerned": "Fund concerned"}},
        {"_row_number": 2, "raw_row": {"Fund concerned": "ERDF"}},
    ]
    rec.observe(
        "fund-filter-header-remnant",
        "workshop.filter_by_fund",
        {"rows": headerish, "fonds": "ERDF"},
        lambda: bh.filtere_nach_fonds(copy.deepcopy(headerish), "ERDF"),
    )

    def rows(total: int, nameless: int, **extra: Any) -> list[dict[str, Any]]:
        out = [
            {"_row_number": i + 1, "beneficiary_name": f"B{i}", **extra}
            for i in range(total - nameless)
        ]
        out += [
            {"_row_number": total - nameless + i + 1, "_skip_reason": "no_name"}
            for i in range(nameless)
        ]
        return out

    params_ok = {"source_key": "s", "fonds": "EFRE", "periode": "2021-2027", "country_code": "DE"}
    validation_cases = {
        "ok": (rows(10, 0), params_ok),
        "missing-context": (rows(3, 0), {"source_key": "s"}),
        "nameless-20pct-50": (rows(250, 50), params_ok),
        "nameless-20pct-51": (rows(255, 51), params_ok),
        "nameless-21pct-60": (rows(280, 60), params_ok),
        "nameless-50pct": (rows(20, 10), params_ok),
        "nameless-55pct": (rows(20, 11), params_ok),
        "negative": (
            [{"_row_number": 1, "cost_total_raw": "-5", "cost_eu_funding_raw": "-1"}],
            params_ok,
        ),
        "eu-over-total": (
            [{"_row_number": 1, "cost_total_raw": "100", "cost_eu_funding_raw": "150"}],
            params_ok,
        ),
        "dates": (
            [
                {
                    "_row_number": 1,
                    "project_start_raw": "2025-01-01",
                    "project_end_raw": "2024-01-01",
                }
            ],
            params_ok,
        ),
        "coords": ([{"_row_number": 1, "latitude": 91.0, "longitude": -181.0}], params_ok),
        "unparsable": (
            [{"_row_number": 1, "cost_total_raw": "abc", "project_start_raw": "x"}],
            params_ok,
        ),
    }
    for name, (rws, prm) in validation_cases.items():
        rec.observe(
            f"validate-{name}",
            "workshop.validate_rows",
            {"rows": rws, "params": prm},
            lambda r=rws, p=prm: bh.validate_beneficiary_rows(r, bh.BeneficiaryHarvestParams(**p)),
        )
    return {
        "column_patterns": COLUMN_PATTERNS,
        "canonical_aliases": list(bh._CANONICAL_ALIASES),
        "hash_fields": list(bh._HASH_FIELDS),
        "nameless": {
            "max_share": bh.NAMENLOS_MAX_ANTEIL,
            "tolerance": bh.NAMENLOS_TOLERANZ,
            "hard_limit": bh.NAMENLOS_HARTE_GRENZE,
        },
        "fund_columns": list(bh._FONDS_SPALTEN),
        "default_mode": bh.BeneficiaryHarvestParams(source_key="x").mode,
        "modes": ["smart", "full-refresh", "force", "snapshot"],
        "legal_suffixes": sorted(sa._LEGAL_SUFFIXES),
        "transliteration": {
            chr(k): v
            for k, v in str.maketrans(
                {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"}
            ).items()
        },
        "filler_words": sorted(sa._FILLER_WORDS),
        "files": {
            n: {"sha256": hashlib.sha256((files / n).read_bytes()).hexdigest(), **s}
            for n, s in generated.items()
        },
    }


def capture_workshop_modes(database_url: str, files: Path) -> list[dict[str, Any]]:
    """Run the original ``run_beneficiary_harvest`` against a disposable PostgreSQL."""
    from models.beneficiary_records import BeneficiaryHarvestRun, BeneficiaryRecord
    from services import beneficiary_harvester as bh
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine(database_url)
    BeneficiaryRecord.__table__.drop(engine, checkfirst=True)
    BeneficiaryHarvestRun.__table__.drop(engine, checkfirst=True)
    BeneficiaryHarvestRun.__table__.create(engine)
    BeneficiaryRecord.__table__.create(engine)
    base = (files / "semikolon_ohne_titel.csv").read_bytes()
    changed = base.replace(b"150000;75000", b"160000;80000").replace(
        b"Ohne Kosten e.V.;Beratung;;;", b"Neu GmbH;Beratung;;;"
    )
    duplicate = (
        base
        + b"Beispiel GmbH;Energie 2030;1.234.567,89;617.283,95;01067;Dresden;01.02.2024;"
        + b"31.12.2026;AZ-1;EFRE\n"
    )
    rejected = b"Name des Begr\xc3\xbcnstigten;Gesamtkosten\nA;-5\n"
    context = {
        "source_key": "hessen_efre",
        "bundesland": "Hessen",
        "fonds": "EFRE",
        "periode": "2021-2027",
        "country_code": "DE",
        "file_name": "liste.csv",
    }
    steps = [
        ("snapshot-initial", "snapshot", base),
        ("smart-same", "smart", base),
        ("smart-changed", "smart", changed),
        ("full-refresh-changed", "full-refresh", changed),
        ("force-base", "force", base),
        ("snapshot-changed", "snapshot", changed),
        ("snapshot-duplicate-row", "snapshot", duplicate),
        ("smart-rejected", "smart", rejected),
        ("snapshot-rejected", "snapshot", rejected),
        ("invalid-mode", "unbekannt", base),
        ("no-context", "snapshot", base),
    ]
    out = []
    with Session(engine) as session:
        for name, mode, content in steps:
            params = {**context, "mode": mode, "file_content": content}
            if name == "no-context":
                params = {
                    "source_key": "hessen_efre",
                    "mode": mode,
                    "file_content": content,
                    "file_name": "liste.csv",
                }
            try:
                result = bh.run_beneficiary_harvest(session, bh.BeneficiaryHarvestParams(**params))
                result = {k: v for k, v in result.items() if k != "run_id"}
                exception = None
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                result, exception = None, {"type": type(exc).__name__, "message": str(exc)}
            records = (
                session.query(BeneficiaryRecord).order_by(BeneficiaryRecord.source_record_id).all()
            )
            out.append(
                {
                    "name": name,
                    "mode": mode,
                    "result": jsonable(result),
                    "exception": exception,
                    "inventory": [
                        [
                            r.source_record_id,
                            r.beneficiary_name,
                            r.cost_total_raw,
                            str(r.cost_total) if r.cost_total is not None else None,
                            r.plz,
                        ]
                        for r in records
                    ],
                }
            )
    BeneficiaryRecord.__table__.drop(engine)
    BeneficiaryHarvestRun.__table__.drop(engine)
    engine.dispose()
    return out


def _frame(dfs: Any, content: bytes, name: str) -> dict[str, Any]:
    import math

    ext = name.rsplit(".", 1)[-1].lower()
    df = dfs._read_csv_smart(content) if ext == "csv" else dfs._read_excel_smart(content, ext, 0)
    rows = []
    for _, row in df.iterrows():
        values = []
        for v in row.tolist():
            if isinstance(v, float) and math.isnan(v):
                values.append(None)
            elif hasattr(v, "item") and not isinstance(v, (str, bytes)):
                values.append(v.item())
            else:
                values.append(v)
        rows.append(values)
    return {"headers": [str(c) for c in df.columns], "rows": rows}


def _workshop_files(files: Path, openpyxl: Any) -> dict[str, dict[str, Any]]:
    """Write deterministic source files once; later runs reuse the exact bytes."""
    specs: dict[str, dict[str, Any]] = {}

    def write(name: str, data: bytes) -> None:
        path = files / name
        if not path.exists():
            path.write_bytes(data)

    write(
        "semikolon_titelzeilen.csv",
        (
            "Liste der Vorhaben EFRE Hessen\n"
            "Stand: 01.09.2026\n"
            "\n"
            "Name des Begünstigten;Bezeichnung des Vorhabens;Gesamtkosten;"
            "Unionsbeteiligung;PLZ;Ort;"
            "Datum des Beginns;Datum des Endes;Aktenzeichen;Fonds\n"
            "Beispiel GmbH;Energie 2030;1.234.567,89;617.283,95;01067;Dresden;"
            "01.02.2024;31.12.2026;AZ-1;EFRE\n"
            "Müller & Söhne KG;Digitalisierung;150000;75000;34117;Kassel;"
            "2024-03-15;2025-03-15;2;EFRE\n"
            ";Summe;1.384.567,89;;;;;;;\n"
            "Ohne Kosten e.V.;Beratung;;;60311;Frankfurt am Main;15/03/2024;;AZ-3;EFRE\n"
        ).encode(),
    )
    specs["semikolon_titelzeilen.csv"] = {}
    body = (
        "Name des Begünstigten;Bezeichnung des Vorhabens;Gesamtkosten;"
        "Unionsbeteiligung;PLZ;Ort;"
        "Datum des Beginns;Datum des Endes;Aktenzeichen;Fonds\n"
        "Beispiel GmbH;Energie 2030;1.234.567,89;617.283,95;01067;Dresden;"
        "01.02.2024;31.12.2026;AZ-1;EFRE\n"
        "Müller & Söhne KG;Digitalisierung;150000;75000;34117;Kassel;"
        "2024-03-15;2025-03-15;2;EFRE\n"
        ";Summe;1.384.567,89;;;;;;;\n"
        "Ohne Kosten e.V.;Beratung;;;60311;Frankfurt am Main;15/03/2024;;AZ-3;EFRE\n"
    )
    write("semikolon_ohne_titel.csv", body.encode("utf-8"))
    specs["semikolon_ohne_titel.csv"] = {}
    write(
        "semikolon_titel_gepolstert.csv",
        ("Liste der Vorhaben;;;;;;;;;\nStand 2026;;;;;;;;;\n;;;;;;;;;\n" + body).encode("utf-8"),
    )
    specs["semikolon_titel_gepolstert.csv"] = {}
    write(
        "zahlen_spalte.csv",
        (
            "Name des Begünstigten;Gesamtkosten;PLZ\nA GmbH;150000;01067\n"
            "B GmbH;;34117\nC GmbH;2500;\n"
        ).encode(),
    )
    specs["zahlen_spalte.csv"] = {}
    write(
        "erste_zeile_numerisch.csv",
        "Name des Begünstigten;Vorhaben;Gesamtkosten;Unionsbeteiligung;PLZ\n"
        "A GmbH;P1;150000;75000;34117\nB GmbH;P2;2500;1000;60311\n".encode(),
    )
    specs["erste_zeile_numerisch.csv"] = {}
    write(
        "komma_doppelkopf.csv",
        (
            "Name des Begünstigten,Vorhaben,Gesamtkosten,PLZ,Beginn\n"
            "beneficiary_name,operation_name,total_cost,postcode,start_date\n"
            '"ACME Ltd.","Wind, Solar","1,200,000.50",12345,2024-01-01\n'
            "Solo Firma,Projekt B,500,,2024-02-01\n"
        ).encode(),
    )
    specs["komma_doppelkopf.csv"] = {}
    write(
        "tab_cp1252.csv",
        (
            "Zuwendungsempfänger\tMaßnahme\tFördersumme\tStandort\n"
            "Straßenbau Süd GmbH\tBrücke\t1.000,00\t80331 München\n"
            "Öko Ölmühle\tPresse\t2.500\t\n"
        ).encode("cp1252"),
    )
    specs["tab_cp1252.csv"] = {}
    write(
        "fonds_gemischt.csv",
        (
            "Name des Begünstigten;Vorhaben;Gesamtkosten;Betroffener Fonds\n"
            "A GmbH;P1;100;EFRE\nB GmbH;P2;200;JTF\nC GmbH;P3;300;EFRE\n"
        ).encode(),
    )
    specs["fonds_gemischt.csv"] = {}
    write("ohne_namensspalte.csv", b"Projekt;Kosten;Ort\nP1;10;X\nP2;20;Y\n")
    specs["ohne_namensspalte.csv"] = {}

    if not (files / "titelzeilen.xlsx").exists():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Vorhaben"
        ws.append(["Liste der Vorhaben ESF+"])
        ws.append([])
        ws.append(
            [
                "Name des Begünstigten",
                "Bezeichnung des Vorhabens",
                "Gesamtkosten",
                "PLZ",
                "Ort",
                "Datum des Beginns",
                "Breitengrad",
                "Längengrad",
            ]
        )
        ws.append(
            [
                "Beispiel GmbH",
                "Qualifizierung",
                125000.5,
                1067,
                "Dresden",
                datetime(2024, 2, 1),
                51.05,
                13.74,
            ]
        )
        ws.append(
            ["Zweite AG", "Beratung", 80000, 34117, "Kassel", datetime(2024, 3, 15), None, None]
        )
        ws.append([None, "Summe", 205000.5, None, None, None, None, None])
        ws.append(
            ["Dritte eG", 12345, "1.000,00", "60311", "Frankfurt", "15.03.2024", "50,1", "8,7"]
        )
        buffer = io.BytesIO()
        wb.properties.created = datetime(2026, 9, 1)
        wb.properties.modified = datetime(2026, 9, 1)
        wb.save(buffer)
        (files / "titelzeilen.xlsx").write_bytes(buffer.getvalue())
    specs["titelzeilen.xlsx"] = {}
    if not (files / "kopfzeile_explizit.xlsx").exists():
        (files / "kopfzeile_explizit.xlsx").write_bytes((files / "titelzeilen.xlsx").read_bytes())
    specs["kopfzeile_explizit.xlsx"] = {"header_row": 2}
    return specs


class _FakeResult:
    def scalar_one_or_none(self) -> None:
        return None


class _FakeAsyncSession:
    """Answers the single existence query of ``_import_record`` with 'not found'."""

    def __init__(self) -> None:
        self.added: list[Any] = []

    async def execute(self, *_: Any, **__: Any) -> _FakeResult:
        return _FakeResult()

    def add(self, obj: Any) -> None:
        self.added.append(obj)


def capture_flowsearch(root: Path, fixtures: Path, rec: Recorder) -> dict[str, Any]:
    import openpyxl
    from app.services.eu_beneficiary_harvester_v2 import EUBeneficiaryHarvesterV2

    # Tracked data file; the inventory checkout may be sparse, so read it from the pinned commit.
    mappings_text = subprocess.run(
        ["git", "-C", str(root), "show", "HEAD:backend/app/data/bundesland_mappings.json"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    mappings = json.loads(mappings_text)["mappings"]
    harvester = object.__new__(EUBeneficiaryHarvesterV2)
    harvester.mappings = mappings
    for i, v in enumerate(AMOUNTS):
        rec.observe(
            f"parse_amount-{i}",
            "flowsearch.parse_amount",
            {"value": v},
            lambda v=v: harvester._parse_amount(v),
        )
    for i, v in enumerate(DATES):
        rec.observe(
            f"parse_date-{i}",
            "flowsearch.parse_date",
            {"value": v},
            lambda v=v: harvester._parse_date(v),
        )
    for i, v in enumerate(NAMES):
        if isinstance(v, str):
            rec.observe(
                f"normalize_name-{i}",
                "flowsearch.normalize_name",
                {"value": v},
                lambda v=v: harvester._normalize_name(v),
            )
    for i, v in enumerate(
        [
            None,
            "",
            "70173 Stuttgart",
            "Stuttgart, 70173",
            "70173",
            "Stuttgart",
            "1234 Wien",
            " 01067  Dresden ",
            "Berlin,12345",
            "D-12345 Berlin",
        ]
    ):
        rec.observe(
            f"parse_location-{i}",
            "flowsearch.parse_location",
            {"value": v},
            lambda v=v: harvester._parse_location(v),
        )
    for i, (v, n) in enumerate([(None, 5), ("abc", 5), ("abcdef", 5), ("äöüß" * 3, 5)]):
        rec.observe(
            f"truncate-{i}",
            "flowsearch.truncate",
            {"value": v, "max": n},
            lambda v=v, n=n: harvester._truncate(v, n),
        )
    record = {"Name": "Beispiel GmbH", "Begünstigter Name": "Fuzzy AG", "Kosten": "", "Leer": None}
    columns = {"beneficiary_name": "Name", "total_cost": "Kosten", "location": "Fehlt"}
    for field_name in ("beneficiary_name", "total_cost", "location", "project_name"):
        rec.observe(
            f"extract-{field_name}",
            "flowsearch.extract_mapped_field",
            {"record": record, "columns": columns, "field": field_name},
            lambda f=field_name: harvester._extract_mapped_field(record, columns, f),
        )

    files = fixtures / "files"
    files.mkdir(parents=True, exist_ok=True)
    csv_name = "flowsearch_quelle.csv"
    if not (files / csv_name).exists():
        (files / csv_name).write_bytes(
            (
                "Titelzeile\n"
                "Begünstigter;Vorhaben;Gesamtkosten;EU-Beitrag;Ort;Beginn\n"
                "Beispiel GmbH;Energie;1.234,56;600,00;70173 Stuttgart;01.02.2024\n"
                ";Summe;1.234,56;;;\n"
                "Zweite AG;Digital;;;Stuttgart;2024-03-15\n"
            ).encode()
        )
    xlsx_name = "flowsearch_quelle.xlsx"
    if not (files / xlsx_name).exists():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Titel"])
        ws.append(
            ["Begünstigter", "Vorhaben\nName", "Gesamtkosten", "EU-Beitrag", "Ort", "Beginn", None]
        )
        ws.append(
            ["Beispiel GmbH", "Energie", 1234.56, 600, "70173 Stuttgart", datetime(2024, 2, 1), "x"]
        )
        ws.append([None, None, None, None, None, None, None])
        ws.append(["Zweite AG", "Digital", None, None, "Stuttgart", "15.03.2024", None])
        wb.properties.created = datetime(2026, 9, 1)
        wb.properties.modified = datetime(2026, 9, 1)
        buffer = io.BytesIO()
        wb.save(buffer)
        (files / xlsx_name).write_bytes(buffer.getvalue())
    zip_name = "flowsearch_quelle.zip"
    if not (files / zip_name).exists():
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zi = zipfile.ZipInfo("readme.txt", date_time=(2026, 9, 1, 0, 0, 0))
            zf.writestr(zi, "nur Text")
            zi = zipfile.ZipInfo("daten/liste.csv", date_time=(2026, 9, 1, 0, 0, 0))
            zf.writestr(zi, (files / csv_name).read_bytes())
        (files / zip_name).write_bytes(buffer.getvalue())
    empty_zip = io.BytesIO()
    with zipfile.ZipFile(empty_zip, "w") as zf:
        zf.writestr(zipfile.ZipInfo("a.txt", date_time=(2026, 9, 1, 0, 0, 0)), "x")

    source = {
        "source_key": "test_quelle",
        "bundesland": "Hessen",
        "fonds": "EFRE",
        "url": "https://example.invalid/liste.csv",
        "portal": "https://example.invalid/",
        "periode": "2021-2027",
    }
    mapping = {
        "delimiter": ";",
        "skip_rows": 1,
        "header_row": 2,
        "columns": {
            "beneficiary_name": "Begünstigter",
            "project_name": "Vorhaben",
            "total_cost": "Gesamtkosten",
            "eu_contribution": "EU-Beitrag",
            "location": "Ort",
            "start_date": "Beginn",
        },
    }
    harvester.mappings = {**mappings, "test_quelle": mapping}
    csv_bytes = (files / csv_name).read_bytes()
    rec.observe(
        "parse_csv",
        "flowsearch.parse_csv",
        {"file": csv_name, "mapping": mapping},
        lambda: asyncio.run(harvester._parse_csv(csv_bytes, source)),
    )
    xlsx_mapping = {**mapping, "columns": {**mapping["columns"], "project_name": "Vorhaben Name"}}
    harvester.mappings = {**mappings, "test_quelle": xlsx_mapping}
    xlsx_bytes = (files / xlsx_name).read_bytes()
    rec.observe(
        "parse_excel",
        "flowsearch.parse_excel",
        {"file": xlsx_name, "mapping": xlsx_mapping},
        lambda: asyncio.run(harvester._parse_excel(xlsx_bytes, source)),
    )
    rec.observe(
        "extract_zip",
        "flowsearch.extract_from_zip",
        {"file": zip_name},
        lambda: harvester._extract_from_zip((files / zip_name).read_bytes()),
    )
    rec.observe(
        "extract_zip_empty",
        "flowsearch.extract_from_zip",
        {"file": "(no table)"},
        lambda: harvester._extract_from_zip(empty_zip.getvalue()),
    )

    harvester.mappings = {**mappings, "test_quelle": mapping}
    records = asyncio.run(harvester._parse_csv(csv_bytes, source))
    for i, rec_row in enumerate([*records, {"Begünstigter": "  "}, {"Unbekannt": "x"}]):

        def imported(row: dict[str, Any] = rec_row) -> Any:
            db = _FakeAsyncSession()
            harvester.db = db
            result = asyncio.run(harvester._import_record(row, source))
            if result is None:
                return None
            fields = (
                "project_id",
                "beneficiary_name",
                "beneficiary_name_normalized",
                "fund_type",
                "nuts0",
                "nuts1",
                "eu_cofinancing",
                "national_cofinancing",
                "total_amount",
                "total_eligible_expenditure",
                "project_title",
                "project_summary",
                "start_date",
                "end_date",
                "city",
                "postal_code",
                "data_source",
                "data_source_url",
                "programming_period",
            )
            return {f: getattr(result, f) for f in fields}

        rec.observe(
            f"import_record-{i}",
            "flowsearch.import_record",
            {"record": rec_row, "source": source},
            imported,
        )
    return {
        "nuts1": EUBeneficiaryHarvesterV2.NUTS1_MAPPING,
        "fallback_mapping": mappings.get("_fallback"),
        "mapping_keys": sorted(mappings),
    }


def capture_designer(root: Path, fixtures: Path, rec: Recorder) -> dict[str, Any]:
    import httpx
    from app.core.shared.research.register import beneficiaries as bn
    from app.core.shared.research.register import de_minimis as dm
    from app.core.shared.research.register import de_minimis_ernte as de
    from app.core.shared.research.register import de_minimis_models as dmm
    from app.core.shared.research.register import de_minimis_zuordnung as dz
    from app.core.shared.research.register import state_aid as sa
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    for i, v in enumerate(AMOUNTS):
        rec.observe(
            f"parse_betrag-{i}",
            "designer.parse_betrag",
            {"value": v},
            lambda v=v: bn.parse_betrag(v),
        )
        rec.observe(
            f"sa_parse_amount-{i}",
            "designer.state_aid_parse_amount",
            {"value": v},
            lambda v=v: sa.parse_amount(v),
        )
        rec.observe(
            f"betrag_ist_spanne-{i}",
            "designer.amount_is_range",
            {"value": v},
            lambda v=v: sa.betrag_ist_spanne(v),
        )
    for i, v in enumerate(
        [
            None,
            "",
            "42 %",
            "29,07\xa0%",
            "50.00 %",
            60,
            44.0978,
            0.49204867971092,
            "0,5",
            "1",
            "1 %",
            "150",
            "4400",
            "-5",
            "85 Prozent",
            "x",
        ]
    ):
        rec.observe(
            f"parse_satz-{i}", "designer.parse_satz", {"value": v}, lambda v=v: bn.parse_satz(v)
        )
    for i, v in enumerate(DATES):
        rec.observe(
            f"parse_datum-{i}", "designer.parse_datum", {"value": v}, lambda v=v: bn.parse_datum(v)
        )
        rec.observe(
            f"sa_parse_date-{i}",
            "designer.state_aid_parse_date",
            {"value": v},
            lambda v=v: sa.parse_date(v),
        )
    for i, v in enumerate(NAMES):
        for filler in (False, True):
            rec.observe(
                f"sa_normalize-{i}-{filler}",
                "designer.normalize_company_name",
                {"value": v, "drop_filler": filler},
                lambda v=v, f=filler: sa.normalize_company_name(v, drop_filler=f),
            )
    for i, v in enumerate(SA_TEXTS):
        rec.observe(
            f"sa_detect-{i}",
            "designer.detect_sa_reference",
            {"value": v},
            lambda v=v: sa.detect_sa_reference(v),
        )
    base_row = {
        "beneficiary_name": "Beispiel GmbH",
        "project_name": "Energieeffizienz 2030",
        "project_aktenzeichen": "AZ-12345",
        "bundesland": "Hessen",
        "periode": "2021-2027",
        "fonds": "EFRE",
        "funded_at_raw": "2024-03-15",
        "cost_total_raw": "150.000,00 €",
    }
    for name, row in {
        "full": base_row,
        "whitespace": {**base_row, "beneficiary_name": "  Beispiel   GmbH "},
        "without-context": {
            k: v for k, v in base_row.items() if k not in ("bundesland", "periode", "fonds")
        },
        "nan": {**base_row, "cost_total_raw": float("nan")},
        "empty": {},
    }.items():
        rec.observe(
            f"hash-{name}",
            "designer.compute_record_hash",
            {"row": row, "source_key": "src1"},
            lambda r=row: bn.compute_record_hash(r, "src1"),
        )

    # --- de-minimis: pure parts
    for i, v in enumerate(
        [None, "", "DE", "de", "DEU", "CountryDEU", "countrydeu", "AT", "EL", "GR", "XX", "USA"]
    ):
        rec.observe(
            f"landeskennung-{i}",
            "deminimis.country_code",
            {"value": v},
            lambda v=v: dm.landeskennung(v),
        )
    for i, kw in enumerate(
        [
            {},
            {"beneficiaryName": "Beispiel", "deMinimisTypes": [], "amountFrom": 0.0},
            {"country": None, "referenceNumber": "", "pageNumber": 3, "pageSize": 500},
        ]
    ):
        rec.observe(
            f"criteria-{i}",
            "deminimis.criteria_body",
            kw,
            lambda kw=kw: dm.Suchkriterien(**kw).als_koerper(),
        )
    for i, v in enumerate(
        [None, "", "2024-03-15", "2024-03-15T10:00:00Z", "15.03.2024", date(2024, 1, 1), "x"]
    ):
        rec.observe(f"as_date-{i}", "deminimis.as_date", {"value": v}, lambda v=v: dm._als_datum(v))
        rec.observe(
            f"harvest_date-{i}", "deminimis.harvest_date", {"value": v}, lambda v=v: de._datum(v)
        )
    for i, v in enumerate(
        [None, "", "1000", "1000.50", 1000, 1000.5, "1.000,50", "NaN", "Infinity", True, "x"]
    ):
        rec.observe(
            f"as_amount-{i}", "deminimis.as_amount", {"value": v}, lambda v=v: dm._als_betrag(v)
        )
        rec.observe(
            f"harvest_amount-{i}",
            "deminimis.harvest_amount",
            {"value": v},
            lambda v=v: de._betrag(v),
        )
    for i, v in enumerate([None, "", "2026-01-15 10:00:00", "2026-01-15T10:00:00", "x"]):
        rec.observe(
            f"harvest_timestamp-{i}",
            "deminimis.harvest_timestamp",
            {"value": v},
            lambda v=v: de._zeitpunkt(v),
        )
    for i, v in enumerate([None, "", "  Beispiel   GmbH ", "Her************"]):
        rec.observe(
            f"harvest_normalize-{i}",
            "deminimis.harvest_normalize",
            {"value": v},
            lambda v=v: de._normalisiere(v),
        )
    award = {
        "referenceNumber": "DM-2026-0001",
        "beneficiaryName": "Beispiel GmbH",
        "beneficiaryReferenceNumber": "B-000123456",
        "amountEur": 120000.5,
        "currency": "EUR",
        "amount": 120000.5,
        "grantingDate": "2026-02-01",
        "deMinimisType": "GENERAL",
        "grantingAuthorityName": "Hessisches Ministerium für Wirtschaft",
        "sector": "C",
        "instrument": "GRANT",
        "publishedDate": "2026-02-20 08:00:00",
        "country": "CountryDEU",
        "extra": "nicht in SPALTEN",
    }
    for i, v in enumerate(
        [
            None,
            "",
            "DE-RP-HWK Rheinhessen",
            "Hessisches Ministerium für Wirtschaft",
            "Bundesamt für Wirtschaft und Ausfuhrkontrolle (BAFA)",
            "KfW Bankengruppe",
            "Grenke Bank AG",
            "Landratsamt Görlitz",
            "Stadt Leipzig",
            "Sachsen-Anhalt Invest",
            "IB.SH Kiel",
            "Regierungspräsidium Kassel",
            "NRW.BANK",
            "bafa",
            "Rheinhessen",
        ]
    ):
        rec.observe(
            f"authority_level-{i}",
            "deminimis.authority_level",
            {"value": v},
            lambda v=v: dz.ebene(v),
        )
    rec.observe("row", "deminimis.row", {"award": award}, lambda: dm._zeile(award))
    masked = {
        **award,
        "beneficiaryName": "Her************",
        "grantingAuthorityName": "Bundesamt für X",
    }
    for i, a in enumerate(
        [award, masked, {}, {"country": None, "grantingAuthorityName": "Landratsamt Y"}]
    ):
        rec.observe(
            f"fields-{i}", "deminimis.harvest_fields", {"award": a}, lambda a=a: de._felder(a)
        )
        rec.observe(
            f"satz_hash-{i}", "deminimis.record_hash", {"award": a}, lambda a=a: dmm.satz_hash(a)
        )
    rec.observe(
        "bestand_hash",
        "deminimis.inventory_hash",
        {"hashes": ["b", "a", "c"]},
        lambda: dmm.bestand_hash(["b", "a", "c"]),
    )
    rec.observe(
        "bestand_hash-empty",
        "deminimis.inventory_hash",
        {"hashes": []},
        lambda: dmm.bestand_hash([]),
    )

    def aw(day: str | None, amount: Any, kind: str | None = "GENERAL") -> dict[str, Any]:
        return {"grantingDate": day, "amountEur": amount, "deMinimisType": kind}

    cumulation_cases = {
        "empty": ([], date(2026, 9, 1)),
        "inside": ([aw("2024-01-01", 100000), aw("2026-08-31", 150000.25)], date(2026, 9, 1)),
        "boundary-start": ([aw("2023-09-01", 1000)], date(2026, 9, 1)),
        "before-start": ([aw("2023-08-31", 1000)], date(2026, 9, 1)),
        "boundary-end": ([aw("2026-09-01", 1000)], date(2026, 9, 1)),
        "after-end": ([aw("2026-09-02", 1000)], date(2026, 9, 1)),
        "leap-day": ([aw("2021-02-28", 1), aw("2021-03-01", 2)], date(2024, 2, 29)),
        "over-ceiling": ([aw("2025-01-01", 200000), aw("2026-01-01", 150000)], date(2026, 9, 1)),
        "exact-ceiling": ([aw("2025-01-01", 300000)], date(2026, 9, 1)),
        "agri": ([aw("2025-01-01", 1000, "AGRI"), aw("2025-02-01", 1000)], date(2026, 9, 1)),
        "unknown-type": ([aw("2025-01-01", 1000, None)], date(2026, 9, 1)),
        "no-date": ([aw(None, 1000), aw("2025-01-01", 500)], date(2026, 9, 1)),
        "no-amount": ([aw("2025-01-01", None), aw("2025-01-02", "x")], date(2026, 9, 1)),
        "string-amounts": (
            [aw("2025-01-01", "1000.10"), aw("2025-01-02", "0.20")],
            date(2026, 9, 1),
        ),
        "float-precision": ([aw("2025-01-01", 0.1), aw("2025-01-02", 0.2)], date(2026, 9, 1)),
        "negative": ([aw("2025-01-01", -500)], date(2026, 9, 1)),
    }
    for name, (records, day) in cumulation_cases.items():
        rec.observe(
            f"cumulation-{name}",
            "deminimis.cumulation",
            {"records": records, "stichtag": day},
            lambda r=records, d=day: dm.berechne_kumulierung(r, stichtag=d).to_dict(),
        )
        rec.observe(
            f"cumulation-raw-{name}",
            "deminimis.cumulation_raw",
            {"records": records, "stichtag": day},
            lambda r=records, d=day: dm.berechne_kumulierung(r, stichtag=d),
        )

    # --- de-minimis: client against an in-process mock transport
    calls: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content or b"null") if request.content else None
        calls.append({"method": request.method, "path": request.url.path, "body": body})
        path = request.url.path
        if (
            path.endswith("/de-minimis-aid-awards")
            and body
            and body.get("beneficiaryName") == "fehler"
        ):
            return httpx.Response(500, json={"error": "x"})
        if (
            path.endswith("/de-minimis-aid-awards")
            and body
            and body.get("beneficiaryName") == "kaputt"
        ):
            return httpx.Response(200, json={"unerwartet": True})
        if path.endswith("/de-minimis-aid-awards"):
            page = body.get("pageNumber", 0)
            return httpx.Response(
                200, json=[{**award, "referenceNumber": f"DM-{page}-{i}"} for i in range(2)]
            )
        if path.endswith("/counters"):
            if body and body.get("beneficiaryName") == "liste":
                return httpx.Response(200, json=[{"count": 7}])
            if body and body.get("beneficiaryName") == "ohne":
                return httpx.Response(200, json={"total": 1})
            return httpx.Response(200, json={"count": 4})
        if "/beneficiary/B-404" in path:
            return httpx.Response(404)
        if "/beneficiary/B-503" in path:
            return httpx.Response(503)
        if "/beneficiary/" in path:
            return httpx.Response(200, json=[award])
        return httpx.Response(418)

    def netfail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("keine Verbindung", request=request)

    def client(fn: Any = handler) -> Any:
        return dm.EAidRegisterClient(httpx.Client(transport=httpx.MockTransport(fn)))

    for i, kw in enumerate(
        [
            {},
            {"beneficiaryName": "fehler"},
            {"beneficiaryName": "kaputt"},
            {"pageNumber": 2, "pageSize": 2},
        ]
    ):
        rec.observe(
            f"client-search-{i}",
            "deminimis.client_search",
            kw,
            lambda kw=kw: client().suche(dm.Suchkriterien(**kw)),
        )
    for i, kw in enumerate([{}, {"beneficiaryName": "liste"}, {"beneficiaryName": "ohne"}]):
        rec.observe(
            f"client-count-{i}",
            "deminimis.client_count",
            kw,
            lambda kw=kw: client().anzahl(dm.Suchkriterien(**kw)),
        )
    for ref in ("B-000123456", "B-404", "B-503"):
        rec.observe(
            f"client-beneficiary-{ref}",
            "deminimis.client_beneficiary",
            {"reference": ref},
            lambda r=ref: client().je_beguenstigtem(r),
        )
    rec.observe(
        "client-network",
        "deminimis.client_search",
        {"network": "down"},
        lambda: client(netfail).suche(dm.Suchkriterien()),
    )
    request_log = list(calls)

    # --- de-minimis: harvest against an isolated in-memory SQLite database
    engine = create_engine("sqlite://")
    dmm.ResearchDeMinimisHarvestRun.__table__.create(engine)
    dmm.ResearchDeMinimisAward.__table__.create(engine)
    harvest_steps: list[dict[str, Any]] = []

    def pages(
        pages_data: list[list[dict[str, Any]]], reported: int | None, fail_at: int | None = None
    ) -> Any:
        def fetch(offset: int, limit: int) -> tuple[list[dict[str, Any]], int | None]:
            index = offset // limit
            if fail_at is not None and index == fail_at:
                raise RuntimeError("Seite nicht abrufbar")
            return (pages_data[index] if index < len(pages_data) else []), reported

        return fetch

    def rows(prefix: str, n: int, amount: float = 1000.0) -> list[dict[str, Any]]:
        return [
            {**award, "referenceNumber": f"{prefix}-{i}", "amountEur": amount} for i in range(n)
        ]

    scenarios = [
        ("complete", pages([rows("A", 3)], 3)),
        ("changed-and-vanished", pages([rows("A", 2, 2000.0)], 2)),
        ("partial-reported-more", pages([rows("A", 1)], 5)),
        ("error-on-second-page", pages([rows("A", 500), rows("B", 1)], 501, fail_at=1)),
        ("reappear", pages([rows("A", 3)], 3)),
        ("unknown-total", pages([rows("A", 3)], None)),
        ("missing-reference", pages([[{"beneficiaryName": "ohne Nummer"}] + rows("A", 3)], 3)),
    ]
    with Session(engine) as session:
        for name, fetch in scenarios:
            run = de.ernte(session, land="DE", ausgeloest_von="capture", seiten_abrufer=fetch)
            state = de.bestandsstand(session, "DE")
            awards = (
                session.query(dmm.ResearchDeMinimisAward)
                .order_by(dmm.ResearchDeMinimisAward.reference_number)
                .all()
            )
            harvest_steps.append(
                {
                    "name": name,
                    "run": {
                        k: jsonable(getattr(run, k))
                        for k in (
                            "status",
                            "records_reported",
                            "records_seen",
                            "records_inserted",
                            "records_updated",
                            "records_unchanged",
                            "records_vanished",
                            "requests",
                            "content_hash",
                            "error_message",
                            "country",
                            "source_url",
                        )
                    },
                    "inventory": {
                        k: jsonable(v)
                        for k, v in state.items()
                        if k not in ("stand_am", "letzter_lauf")
                    },
                    "award_count": len(awards),
                    "vanished_count": sum(a.verschwunden_seit is not None for a in awards),
                    "awards_digest": hashlib.sha256(
                        json.dumps(
                            [
                                [
                                    a.reference_number,
                                    str(a.amount_eur),
                                    a.verschwunden_seit is not None,
                                    a.aenderungen,
                                    a.content_hash,
                                ]
                                for a in awards
                            ]
                        ).encode()
                    ).hexdigest(),
                    "awards": [
                        {
                            "reference": a.reference_number,
                            "amount": jsonable(a.amount_eur),
                            "vanished": a.verschwunden_seit is not None,
                            "changes": a.aenderungen,
                            "hash": a.content_hash,
                        }
                        for a in awards
                        if not a.reference_number.startswith("A-")
                        or int(a.reference_number[2:]) < 5
                    ],
                }
            )
    return {
        "ceiling_general": str(dm.HOECHSTBETRAG_GENERAL),
        "method_version": dm.METHOD_VERSION,
        "types_without_ceiling": sorted(dm.ARTEN_OHNE_GRENZWERT),
        "columns": dm.SPALTEN,
        "hash_fields": list(dmm.HASHFELDER),
        "page_size": de.SEITENGROESSE,
        "masked_marker": de.MASKIERT,
        "api_base": dm.EAIR_BASIS,
        "timeout": dm.ZEITGRENZE,
        "notices": {
            "company": dm.VORBEHALT_UNTERNEHMEN,
            "period": dm.VORBEHALT_ZEITRAUM,
            "deadline": dm.VORBEHALT_FRIST,
            "name": dm.VORBEHALT_NAME,
        },
        "iso2_to_iso3": dm._ISO2_ZU_ISO3,
        "hash_fields_beneficiaries": list(bn._HASH_FELDER),
        "authority_rules": [[target, list(patterns)] for target, patterns in dz.REGELN],
        "sa_legal_suffixes": sorted(sa._RECHTSFORMEN),
        "sa_filler_words": sorted(sa._FUELLWOERTER),
        "sa_transliteration": {chr(k): v for k, v in sa._UMSCHRIFT.items()},
        "authority_levels": list(dz.EBENEN),
        "requests": request_log,
        "harvest": harvest_steps,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variant", choices=sorted(SOURCES))
    parser.add_argument("root", type=Path, help="application directory containing the modules")
    parser.add_argument("fixtures", type=Path)
    parser.add_argument("--migrated", action="store_true")
    parser.add_argument(
        "--modes-database",
        help="flowworkshop only: URL of a disposable PostgreSQL on 127.0.0.1 whose database "
        "name contains 'capture'; used to execute the original harvest modes",
    )
    args = parser.parse_args()
    spec = SOURCES[args.variant]
    root = args.root.resolve()
    files = []
    for relative, expected in spec["blobs"].items():
        observed = git_blob(root / relative)
        if observed != expected and not args.migrated:
            raise SystemExit(f"{relative} does not match the pinned GitHub blob")
        files.append(
            {"path": f"{spec['root']}/{relative}", "git_blob": observed, "pinned_blob": expected}
        )
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--", "."],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if not args.migrated and (head != spec["commit"] or dirty):
        raise SystemExit("Checkout is not the clean pinned source commit")
    for key, value in spec["database_env"].items():
        os.environ[key] = value
    os.environ.pop("PYTHONPATH", None)
    sys.path.insert(0, str(root))
    rec = Recorder()
    capture = {
        "flowworkshop": capture_flowworkshop,
        "flowsearch": capture_flowsearch,
        "designer": capture_designer,
    }[args.variant]
    constants = capture(root, args.fixtures, rec)
    if args.modes_database:
        from urllib.parse import urlparse

        target = urlparse(args.modes_database)
        if (
            args.variant != "flowworkshop"
            or target.hostname != "127.0.0.1"
            or "capture" not in (target.path or "")
        ):
            raise SystemExit("Refusing: modes database must be a disposable local capture database")
        constants["modes_run"] = capture_workshop_modes(
            args.modes_database, args.fixtures / "files"
        )
    library = None
    if args.migrated:
        import auditcore_funding_sources

        library = auditcore_funding_sources.__file__
    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION",
        "variant": args.variant,
        "source": {
            "repository": spec["repository"],
            "commit": spec["commit"],
            "head": head,
            "files": files,
            "checkout_clean": not dirty,
            "migrated": args.migrated,
            "library": library,
        },
        "environment": {
            "python": sys.version.split()[0],
            "database": "unreachable/scratch URL; only in-memory SQLite for de-minimis harvest",
        },
        "constants": jsonable(constants),
        "cases": rec.cases,
    }
    args.fixtures.mkdir(parents=True, exist_ok=True)
    out = args.fixtures / f"{args.variant}_observed.json"
    if args.migrated:
        out = args.fixtures / f"{args.variant}_observed_migrated.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "variant": args.variant,
                "cases": len(rec.cases),
                "exceptions": sum(c["exception"] is not None for c in rec.cases),
            }
        )
    )


if __name__ == "__main__":
    main()
