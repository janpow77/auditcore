"""Capture the original normalisation, LEI and scoring behavior before extraction.

The application modules import databases, HTTP clients and ORM models. This
tool therefore compiles only the pinned, unchanged top-level definitions it
needs (constants and functions, verified by Git blob) from the source files
and executes them with the standard library and rapidfuzz. It never imports
``auditcore_entity_matching`` and never touches a database or network.

    python tools/capture_legacy.py <repositories dir> tests/fixtures/legacy_observed.json
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import platform
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

import rapidfuzz
from rapidfuzz import fuzz, process

SOURCES = {
    "flowworkshop": {
        "repository": "janpow77/flowworkshop",
        "commit": "a05bb2143bd96d5e981f9462f05b965e1658be36",
        "files": {
            "entity_resolution": (
                "auditworkshop/backend/services/entity_resolution.py",
                "d7a799b65e0444e8be8e606b35bd2cc1ecbdfac0",
                [
                    "_LEI_RE",
                    "CONFIDENCE_FUZZY_THRESHOLD",
                    "is_valid_lei",
                    "extract_lei_from_text",
                    "_find_by_name_fuzzy",
                ],
            ),
            "state_aid": (
                "auditworkshop/backend/services/state_aid_service.py",
                "e41be2700affb91c2a6436a7e3ce488696b07116",
                [
                    "_LEGAL_SUFFIXES",
                    "_FILLER_WORDS",
                    "_WS_RE",
                    "_PUNCT_RE",
                    "_strip_accents",
                    "normalize_company_name",
                ],
            ),
            "sanctions": (
                "auditworkshop/backend/services/sanctions_service.py",
                "3e7ad8bd826eed4da15f9860af267f9fe8a9076b",
                [
                    "_LEGAL_SUFFIXES",
                    "_DIACRITIC_FOLD_MAP",
                    "_fold_diacritics",
                    "normalize_name",
                    "_classify",
                ],
            ),
        },
    },
    "audit_designer": {
        "repository": "janpow77/audit_designer",
        "commit": "030a71e083ef0feddc14545b095a4945bc0bbd7a",
        "files": {
            "designer_sanctions": (
                "backend/app/core/shared/research/register/sanctions.py",
                "3d48504d92207d6c5a03c038d22fcdf09be63235",
                [
                    "RECHTSFORMZUSAETZE",
                    "_FALTUNG",
                    "_NICHT_WORT",
                    "falte_diakritika",
                    "normalisiere_name",
                    "klassifiziere",
                    "STANDARD_MINDESTWERT",
                ],
            ),
        },
    },
}


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load(path: Path, blob: str, names: list[str]) -> dict[str, Any]:
    raw = path.read_bytes()
    if git_blob(raw) != blob:
        raise SystemExit(f"{path} does not match the pinned blob")
    tree = ast.parse(raw.decode("utf-8"))
    wanted = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            wanted.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id in names for t in targets):
                wanted.append(node)
    found = {getattr(n, "name", None) for n in wanted} | {
        t.id
        for n in wanted
        if isinstance(n, (ast.Assign, ast.AnnAssign))
        for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
        if isinstance(t, ast.Name)
    }
    missing = set(names) - found
    if missing:
        raise SystemExit(f"{path}: missing definitions {sorted(missing)}")
    module = ast.Module(
        body=[ast.ImportFrom("__future__", [ast.alias("annotations")], 0), *wanted], type_ignores=[]
    )
    namespace: dict[str, Any] = {
        "re": re,
        "unicodedata": unicodedata,
        "fuzz": fuzz,
        "process": process,
        "__name__": "legacy",
    }
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)  # noqa: S102
    return namespace


NAMES = [
    None,
    "",
    "   ",
    "Müller GmbH",
    "MÜLLER GMBH",
    "Muller GmbH",
    "Straße & Söhne KG",
    "STRASSE & SÖHNE KG",
    "Fraunhofer-Gesellschaft e.V.",
    "Fraunhofer Gesellschaft",
    "Société Générale S.A.",
    "SOCIÉTÉ GÉNÉRALE SA",
    "José Strauß",
    "Søren Ørsted A/S",
    "Łódź Sp. z o.o.",
    "Brüder Weiß GmbH & Co. KG",
    "Siemens AG",
    "SIEMENS Aktiengesellschaft",
    "Deutsche Bank AG Holding Group",
    "ACME Holding GmbH Deutschland",
    "Æther Œuvre Ltd.",
    "Þór Ðað plc",
    "ẞtraße GmbH",
    "Café Crème SARL",
    "  Doppelte   Leerzeichen  GmbH  ",
    "gGmbH Stiftung",
    "Firma co.kg",
    "Alpha CO. KG",
    "Omega Inc., LLC",
    "O'Reilly Media, Inc.",
    "Name_mit_Unterstrich GmbH",
    "Zahl 123 AG",
    "ПАО Газпром",
    "北京公司",
    "Ōsaka Kōgyō K.K.",
    "Kraków S.A.",
    "Čapek s.r.o.",
    "Đorđević d.o.o.",
    "Ñandú S.L.",
    "Ÿves Ëmile",
    "İstanbul A.Ş.",
    "GmbH",
    "AG & Co",
    "UG (haftungsbeschränkt)",
    "ﬁnance ﬂow GmbH",
    "Ⅷ Holding",
    "①②③",
    "tab\tname\nline",
    "Emoji 😀 GmbH",
    "Vladimir Vladimirovich Putin",
    "putin",
]

LEIS = [
    None,
    "",
    "HWUPKR0MPOU8FGXBT394",
    "hwupkr0mpou8fgxbt394",
    " 529900T8BM49AURSDO55 ",
    "5493001KJTIIGC8Y1R12",
    "7LTWFZYICNSX8D621K86",
    "7LTWFZYICNSX8D621K87",
    "HWUPKR0MPOU8FGXBT39",
    "HWUPKR0MPOU8FGXBT3945",
    "HWUPKR0MPOU8FGXBT39A",
    "HWUPKR0MPOU8FGXB-394",
    "ÄWUPKR0MPOU8FGXBT394",
    "00000000000000000000",
    "LEI: 529900T8BM49AURSDO55",
    "ID 529900T8BM49AURSDO55; HRB 123",
    "prefix529900T8BM49AURSDO55suffix",
    "HRB 12345",
    12345,
]

PAIRS = [
    ("putin", "vladimir vladimirovich putin"),
    ("vladimir putin", "putin vladimir"),
    ("mueller", "muller"),
    ("siemens", "siemens"),
    ("deutsche bank", "deutsche bank holding"),
    ("alpha beta", "alpha gamma"),
    ("", ""),
    ("acme", "acne"),
]


class _Column:
    """Stand-in for an ORM column; the SQL prefilter is recorded, not executed."""

    def ilike(self, pattern: str) -> tuple[str, str]:
        return ("ilike", pattern)

    def is_(self, value: object) -> tuple[str, object]:
        return ("is", value)

    def __eq__(self, other: object) -> tuple[str, object]:  # type: ignore[override]
        return ("eq", other)

    __hash__ = object.__hash__


class _CompanyEntity:
    id = _Column()
    canonical_name = _Column()
    canonical_name_normalized = _Column()
    country_code = _Column()


class _Func:
    @staticmethod
    def similarity(*args: object) -> _Order:
        return _Order()


class _Order:
    def desc(self) -> _Order:
        return self


class _Row:
    def __init__(self, id: int, normalized: str) -> None:
        self.id = id
        self.canonical_name = normalized
        self.canonical_name_normalized = normalized


class _Query:
    def __init__(self, rows: list[_Row], log: list[object]) -> None:
        self.rows, self.log = rows, log

    def filter(self, *conditions: object) -> _Query:
        self.log.append(("filter", [str(c) for c in conditions]))
        return self

    def order_by(self, *args: object) -> _Query:
        return self

    def limit(self, n: int) -> _Query:
        self.log.append(("limit", n))
        return self

    def all(self) -> list[_Row]:
        return self.rows


class _Session:
    """Returns the candidate rows in the given order (the database ordering)."""

    def __init__(self, rows: list[_Row]) -> None:
        self.rows, self.log = rows, []

    def query(self, *columns: object) -> _Query:
        return _Query(self.rows, self.log)

    def get(self, model: object, key: int) -> dict[str, int]:
        return {"id": key}


CANDIDATE_SETS = [
    ("siemens", [(1, "siemens"), (2, "siemens energy"), (3, "simens")]),
    ("fraunhofer gesellschaft", [(1, "fraunhofer gesellschaft zur foerderung"), (2, "fraunhofer")]),
    ("deutsche bank", [(7, "deutsche bahn"), (8, "deutsche bank"), (9, "bank deutsche")]),
    ("acme", [(1, "acne"), (2, "acme corp")]),
    ("ab", [(1, "ab")]),
    ("", [(1, "x")]),
    ("mueller bau", [(5, "mueller bau"), (4, "mueller bau")]),
    ("alpha beta gamma", [(1, "delta epsilon"), (2, "zeta")]),
    ("muller logistik", [(1, "mueller logistik"), (2, "muller logistic")]),
]
SCORES = [100.0, 97.0, 96.99, 90.0, 89.99, 80.0, 79.99, 0.0, -1.0, 101.0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repositories", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    loaded: dict[str, dict[str, Any]] = {}
    sources = []
    for key, repo in SOURCES.items():
        checkout = args.repositories / f"janpow77__{key}"
        head = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if head != repo["commit"]:
            raise SystemExit(f"{key}: checkout is not at the pinned commit")
        for name, (path, blob, names) in repo["files"].items():
            loaded[name] = load(checkout / path, blob, names)
            sources.append(
                {
                    "repository": repo["repository"],
                    "commit": repo["commit"],
                    "path": path,
                    "git_blob": blob,
                    "symbols": names,
                }
            )

    cases: list[dict[str, Any]] = []

    def observe(name: str, operation: str, inputs: Any, call: Any) -> None:
        before = copy.deepcopy(inputs)
        try:
            output, exception = call(), None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output, exception = None, {"type": type(exc).__name__, "message": str(exc)}
        assert inputs == before
        cases.append(
            {
                "name": name,
                "operation": operation,
                "inputs": inputs,
                "output": output,
                "exception": exception,
            }
        )

    er, sa, sn, ds = (
        loaded[k] for k in ("entity_resolution", "state_aid", "sanctions", "designer_sanctions")
    )
    for i, value in enumerate(NAMES):
        observe(
            f"state-aid-{i}",
            "state_aid_normalize",
            {"text": value},
            lambda v=value: sa["normalize_company_name"](v),
        )
        observe(
            f"state-aid-filler-{i}",
            "state_aid_normalize_filler",
            {"text": value},
            lambda v=value: sa["normalize_company_name"](v, drop_filler=True),
        )
        observe(
            f"sanctions-{i}",
            "sanctions_normalize",
            {"text": value},
            lambda v=value: sn["normalize_name"](v),
        )
        observe(
            f"designer-{i}",
            "designer_normalize",
            {"text": value},
            lambda v=value: ds["normalisiere_name"](v),
        )
    for i, value in enumerate(LEIS):
        observe(
            f"lei-valid-{i}",
            "is_valid_lei",
            {"value": value},
            lambda v=value: er["is_valid_lei"](v),
        )
        observe(
            f"lei-extract-{i}",
            "extract_lei",
            {"value": value},
            lambda v=value: er["extract_lei_from_text"](v),
        )
    for score in SCORES:
        observe(
            f"classify-{score}",
            "sanctions_classify",
            {"score": score},
            lambda s=score: sn["_classify"](s),
        )
        observe(
            f"klassifiziere-{score}",
            "designer_classify",
            {"score": score},
            lambda s=score: ds["klassifiziere"](s),
        )
        for q, m in PAIRS:
            observe(
                f"classify-{score}-{q}-{m}",
                "sanctions_classify",
                {"score": score, "q_norm": q, "matched_norm": m},
                lambda s=score, q=q, m=m: sn["_classify"](s, q, m),
            )
            observe(
                f"klassifiziere-{score}-{q}-{m}",
                "designer_classify",
                {"score": score, "q_norm": q, "matched_norm": m},
                lambda s=score, q=q, m=m: ds["klassifiziere"](s, q, m),
            )
    fuzzy = er["_find_by_name_fuzzy"]
    er["CompanyEntity"], er["or_"], er["func"] = _CompanyEntity, lambda *a: ("or", a), _Func
    for i, (query, rows) in enumerate(CANDIDATE_SETS):
        for min_score in (75.0, 90.0):
            inputs = {"query": query, "candidates": rows, "min_score": min_score}

            def call(q: str = query, r: list = rows, m: float = min_score) -> Any:
                session = _Session([_Row(i_, n) for i_, n in r])
                found = fuzzy(session, q, q, min_score=m)
                return None if found is None else [found[0]["id"], found[1]]

            observe(f"fuzzy-{i}-{min_score}", "fuzzy_best", inputs, call)
    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION",
        "sources": sources,
        "environment": {
            "python": platform.python_version(),
            "rapidfuzz": rapidfuzz.__version__,
            "unicode": unicodedata.unidata_version,
        },
        "constants": {
            "flowworkshop.state_aid.legal_suffixes": sorted(sa["_LEGAL_SUFFIXES"]),
            "flowworkshop.state_aid.filler_words": sorted(sa["_FILLER_WORDS"]),
            "flowworkshop.sanctions.legal_suffixes": sorted(sn["_LEGAL_SUFFIXES"]),
            "flowworkshop.sanctions.fold_map": sn["_DIACRITIC_FOLD_MAP"],
            "audit_designer.sanctions.legal_suffixes": sorted(ds["RECHTSFORMZUSAETZE"]),
            "audit_designer.sanctions.fold_map": ds["_FALTUNG"],
            "audit_designer.sanctions.minimum_score": ds["STANDARD_MINDESTWERT"],
            "flowworkshop.entity_resolution.fuzzy_threshold": er["CONFIDENCE_FUZZY_THRESHOLD"],
            "flowworkshop.entity_resolution.lei_pattern": er["_LEI_RE"].pattern,
        },
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
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
