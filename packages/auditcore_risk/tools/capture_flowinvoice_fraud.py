"""Execute the pure parts of flowinvoice ``fraud_detection`` and record inputs/outputs.

Executed unchanged (blob-verified, imported from a flowinvoice checkout at the
pinned commit with its own environment):

* ``FraudDetectionManager.analyze_invoice`` with injected stand-ins for the five
  sub-checkers that return prepared results (or raise). Blocker/warning
  derivation, ``_calculate_risk_score`` and ``_determine_risk_level`` run as in
  production; the sub-checkers (DB, HTTP) are not called.
* ``TedChecker._calculate_statistics``, ``_detect_red_flags`` and
  ``_calculate_legitimacy_score`` on synthetic ``TedContract`` lists. The SQL
  selection ``_load_contracts`` needs Postgres and is NOT executed.
* ``DuplicateDetector._find_exact_duplicates``/``_find_fuzzy_duplicates`` with a
  session stand-in that returns prepared candidate documents. The SQL filters
  (exact: invoice number; fuzzy: ``created_at`` window, ``LIMIT 500``) are not
  executed; for the exact path only candidates with the matching number are
  handed over, as the SQL would.

    PYTHONPATH=<flowinvoice>/backend python tools/capture_flowinvoice_fraud.py \
        <flowinvoice checkout> tests/fixtures/flowinvoice_fraud_observed.json

All data are synthetic.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib
import json
import platform
import random
import subprocess
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPOSITORY = "janpow77/flowinvoice"
COMMIT = "fb2d18568d2eaf64574d131ceae51a936b9aac02"
BASE = "backend/app/services/fraud_detection/"
FILES = {
    BASE + "manager.py": "0a48b36753546c8954604616d4e1028b6c9b9b24",
    BASE + "ted_checker.py": "5618a2e0f090550443f5c74c8aaaee2ed188e420",
    BASE + "duplicate_detector.py": "ad6c7ff993aa2e9bd3afd246811b8a9e942c6b1d",
    BASE + "models.py": "e960f32633874444b9ddc0f323dd54f5b0242e59",
}


def git_blob(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode() + b"\0"
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


# --------------------------------------------------------------------------- manager


class Stub:
    """Async sub-checker stand-in returning a prepared result or raising."""

    def __init__(self, result: Any) -> None:
        self.result = result

    async def _answer(self, *args: Any, **kwargs: Any) -> Any:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    check_invoice = check_entity = verify_company = check_company = _answer


def build_signals(rng: random.Random) -> dict[str, Any]:
    signals: dict[str, Any] = {}
    for name in ("duplicate", "sanctions", "pep", "company", "ted"):
        roll = rng.random()
        if roll < 0.15:
            signals[name] = None  # check switched off
        elif roll < 0.25:
            signals[name] = {"failed": True}
        elif name == "duplicate":
            matches = [
                {
                    "match_type": rng.choice(["exact", "fuzzy"]),
                    "confidence": round(rng.uniform(0.3, 1.0), 3),
                }
                for _ in range(rng.randint(0, 3))
            ]
            signals[name] = {"is_duplicate": bool(matches), "matches": matches}
        elif name in ("sanctions", "pep"):
            matches = [
                {"match_score": round(rng.uniform(0.5, 1.0), 3)} for _ in range(rng.randint(0, 2))
            ]
            hit = bool(matches) and rng.random() < 0.7
            key = "is_sanctioned" if name == "sanctions" else "is_clean"
            signals[name] = {
                key: hit if name == "sanctions" else not hit,
                "matches": matches if hit else [],
                "error_message": rng.choice([None, None, "Timeout"]),
            }
        elif name == "company":
            pool = [
                "INVALID_VAT_ID",
                "COMPANY_DISSOLVED",
                "NOT_IN_REGISTER",
                "VIES_SERVICE_UNAVAILABLE",
                "NAME_MISMATCH",
                "YOUNG_COMPANY",
            ]
            signals[name] = {
                "risk_indicators": rng.sample(pool, rng.randint(0, 3)),
                "verification_score": round(rng.uniform(0.0, 1.0), 2),
            }
        else:
            flags = [
                {
                    "severity": rng.choice(["low", "medium", "high", "critical"]),
                    "flag_type": rng.choice(
                        [
                            "HIGH_CONTRACT_COUNT",
                            "HIGH_CONCENTRATION",
                            "EXTREME_CONCENTRATION",
                            "LOW_AUTHORITY_DIVERSITY",
                        ]
                    ),
                }
                for _ in range(rng.randint(0, 2))
            ]
            legitimacy: Any = round(rng.uniform(0.0, 1.0), 2)
            if rng.random() < 0.2:
                legitimacy = {"score": 42.0, "rating": "MITTEL", "factors": {}}
            signals[name] = {
                "red_flags": flags,
                "legitimacy_score": legitimacy,
                "total_contracts": rng.randint(0, 40),
                "statistics": {},
            }
    return signals


def manager_boundaries() -> list[dict[str, Any]]:
    none: dict[str, Any] = {
        "duplicate": None,
        "sanctions": None,
        "pep": None,
        "company": None,
        "ted": None,
    }
    cases: list[dict[str, Any]] = [dict(none)]
    for n in range(1, 9):
        cases.append({**none, "company": {"risk_indicators": ["W"] * n, "verification_score": 1.0}})
    for score in (0.0, 0.5, 1.0):
        cases.append({**none, "company": {"risk_indicators": [], "verification_score": score}})
    cases.append(
        {
            **none,
            "duplicate": {
                "is_duplicate": True,
                "matches": [{"match_type": "fuzzy", "confidence": 1.0}],
            },
            "company": {"risk_indicators": [], "verification_score": 0.5},
        }
    )
    cases.append(
        {**none, "sanctions": {"is_sanctioned": True, "error_message": None, "matches": []}}
    )
    cases.append({**none, "pep": {"is_clean": False, "error_message": None, "matches": []}})
    cases.append(
        {
            **none,
            "ted": {
                "red_flags": [{"severity": "high", "flag_type": "X"}],
                "legitimacy_score": 0.25,
                "total_contracts": 3,
                "statistics": {},
            },
        }
    )
    cases.append(
        {
            **none,
            "ted": {
                "red_flags": [{"severity": "low", "flag_type": "X"}],
                "legitimacy_score": {"score": 50.0},
                "total_contracts": 3,
                "statistics": {},
            },
        }
    )
    cases.append(
        {
            **none,
            "ted": {
                "red_flags": [],
                "legitimacy_score": {"score": 50.0},
                "total_contracts": 0,
                "statistics": {},
            },
        }
    )
    return cases


def run_manager(manager_mod: Any, models: Any, signals: dict[str, Any]) -> dict[str, Any]:
    config = models.FraudCheckConfig(
        check_duplicates=signals["duplicate"] is not None,
        check_sanctions=signals["sanctions"] is not None,
        check_pep=signals["pep"] is not None,
        check_company=signals["company"] is not None,
        check_ted=signals["ted"] is not None,
    )
    manager = manager_mod.FraudDetectionManager.__new__(manager_mod.FraudDetectionManager)
    manager.config = config
    failure = RuntimeError("Teilprüfung nicht verfügbar")

    def result(name: str, make: Any) -> Stub:
        value = signals[name]
        if value is None:
            return Stub(None)
        if value.get("failed"):
            return Stub(failure)
        return Stub(make(value))

    manager.duplicate_detector = result(
        "duplicate",
        lambda v: models.DuplicateResult(
            is_duplicate=v["is_duplicate"],
            matches=[
                models.DuplicateMatch(
                    original_invoice_id="d", match_type=m["match_type"], confidence=m["confidence"]
                )
                for m in v["matches"]
            ],
        ),
    )
    manager.sanctions_checker = result(
        "sanctions",
        lambda v: models.SanctionsResult(
            is_sanctioned=v["is_sanctioned"],
            error_message=v["error_message"],
            matches=[
                models.SanctionMatch(list_name="L", entity_name="E", match_score=m["match_score"])
                for m in v["matches"]
            ],
        ),
    )
    manager.pep_checker = result(
        "pep",
        lambda v: models.PEPResult(
            is_clean=v["is_clean"],
            hit_count=len(v["matches"]),
            checked_entities=1,
            error_message=v["error_message"],
            matches=[
                models.PEPMatch(
                    person_name="P",
                    position="X",
                    country="DE",
                    match_score=m["match_score"],
                    match_method="fuzzy",
                    source="s",
                    dataset="peps",
                )
                for m in v["matches"]
            ],
        ),
    )
    manager.company_verifier = result(
        "company",
        lambda v: models.CompanyVerificationResult(
            is_verified=True,
            risk_indicators=list(v["risk_indicators"]),
            verification_score=v["verification_score"],
        ),
    )
    manager.ted_checker = result("ted", lambda v: dict(v))
    try:
        out = asyncio.run(
            manager.analyze_invoice(
                invoice_number="RE-1",
                supplier_name="Lieferant",
                supplier_vat_id=None,
                total_amount=Decimal("100.00"),
                invoice_date=date(2025, 5, 1),
            )
        )
    except Exception as exc:  # noqa: BLE001 - record the original failure
        return {"exception": {"type": type(exc).__name__, "message": str(exc)}}
    return {
        "exception": None,
        "risk_level": str(out.risk_level),
        "risk_score": out.risk_score,
        "warnings": sorted(out.warnings),
        "blockers": sorted(out.blockers),
        "checks_performed": out.checks_performed,
    }


# --------------------------------------------------------------------------- TED

AUTHORITIES = ["Stadt Nord", "Land Süd", "Kreis West", "Hochschule Ost", "", None]


def ted_contract_sets(rng: random.Random, count: int) -> list[list[dict[str, Any]]]:
    sets: list[list[dict[str, Any]]] = [[]]
    for n, authorities in (
        (3, ["Stadt Nord"] * 3),
        (21, ["Stadt Nord"] * 21),
        (10, ["Stadt Nord"] * 7 + ["Land Süd"] * 3),
        (10, ["Stadt Nord"] * 8 + ["Land Süd"] * 2),
        (10, ["Stadt Nord"] * 9 + ["Land Süd"]),
        (2, ["Stadt Nord", "Land Süd"]),
        (4, ["A", "B", "B", "A"]),
        (3, [None, "", "Stadt Nord"]),
    ):
        sets.append(
            [
                {
                    "notice_id": f"N-{n}-{i}",
                    "contracting_authority_name": authorities[i],
                    "contract_value": float(10_000 * (i + 1)),
                    "contract_award_date": "2025-01-01",
                }
                for i in range(n)
            ]
        )
    for _ in range(count):
        n = rng.randint(0, 30)
        sets.append(
            [
                {
                    "notice_id": f"R-{i}",
                    "contracting_authority_name": rng.choice(AUTHORITIES[: rng.randint(1, 6)]),
                    "contract_value": rng.choice(
                        [None, 0.0, round(rng.uniform(1_000, 900_000), 2)]
                    ),
                    "contract_award_date": "2025-01-01",
                }
                for i in range(n)
            ]
        )
    return sets


def run_ted(ted_mod: Any, notices: list[dict[str, Any]]) -> dict[str, Any]:
    checker = ted_mod.TedChecker(session=None)
    contracts = [
        ted_mod.TedContract(
            ted_id=n["notice_id"],
            title="T",
            contractor_name="C",
            contractor_country="DE",
            award_date=date.fromisoformat(n["contract_award_date"]),
            value_eur=float(n["contract_value"]) if n["contract_value"] else None,
            currency="EUR",
            contracting_authority=n["contracting_authority_name"] or "",
            nuts_code=None,
            cpv_code=None,
            document_type="award",
        )
        for n in notices
    ]
    stats = checker._calculate_statistics(contracts)
    flags = checker._detect_red_flags(contracts, stats)
    legitimacy = checker._calculate_legitimacy_score(contracts, stats, flags)
    return {
        "statistics": stats,
        "red_flags": [
            {
                "severity": str(f.severity),
                "flag_type": f.flag_type,
                "description": f.description,
                "evidence": f.evidence,
            }
            for f in flags
        ],
        "legitimacy_score": legitimacy,
        "total_contracts": len(contracts),
    }


# --------------------------------------------------------------------------- duplicates


class Session:
    def __init__(self, documents: list[Any]) -> None:
        self.documents = documents

    async def execute(self, query: Any) -> Any:
        documents = self.documents
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: documents))


def document(i: int, number: str | None, amount: Any, day: Any, supplier: Any) -> Any:
    extracted: dict[str, Any] = {}
    if number is not None:
        extracted["invoice_number"] = {"value": number}
    if amount is not None:
        extracted["gross_amount"] = {"value": amount}
    if day is not None:
        extracted["invoice_date"] = {"value": day}
    if supplier is not None:
        extracted["supplier_name_address"] = {"value": supplier}
    return SimpleNamespace(
        id=f"doc-{i}", extracted_data=extracted, original_filename=f"r{i}.pdf", project_id="p1"
    )


def duplicate_cases(rng: random.Random, count: int) -> list[dict[str, Any]]:
    suppliers = [
        "Lieferant Nord GmbH",
        "lieferant nord",
        "Nord Bau",
        "Süd Handel KG",
        "GmbH Service",
        "Lief",
        "Lieferant",
    ]
    days = [
        "2025-05-01",
        "01.05.2025",
        "05/01/2025",
        "2025/05/03",
        "08.05.2025",
        "24.04.2025",
        "2025-05-09",
        "kein Datum",
        "",
    ]
    amounts = [
        "1000.00",
        "1.000,00",
        "1000,00",
        "1 020,00",
        "1020.01",
        "980",
        "979.99",
        "abc",
        "1000 €",
        1000,
        1015.5,
    ]
    cases = []
    for k in range(count):
        invoice = {
            "invoice_number": rng.choice(["RE-1", "re-1 ", "RE-2"]),
            "supplier_name": rng.choice(suppliers),
            "total_amount": rng.choice(["1000.00", "1000", "999.995", "1500.00"]),
            "invoice_date": "2025-05-01",
        }
        candidates = []
        for i in range(rng.randint(0, 6)):
            candidates.append(
                {
                    "id": f"doc-{i}",
                    "invoice_number": rng.choice(["RE-1", "re-1", "RE-1 ", "RE-2", None]),
                    "gross_amount": rng.choice(amounts + [None]),
                    "invoice_date": rng.choice(days + [None]),
                    "supplier_name": rng.choice(suppliers + [None]),
                }
            )
        cases.append({"name": f"dup-{k:03d}", "invoice": invoice, "candidates": candidates})
    return cases


def run_duplicates(dup_mod: Any, case: dict[str, Any]) -> dict[str, Any]:
    invoice = case["invoice"]
    docs = [
        document(i, c["invoice_number"], c["gross_amount"], c["invoice_date"], c["supplier_name"])
        for i, c in enumerate(case["candidates"])
    ]
    for doc, cand in zip(docs, case["candidates"], strict=True):
        doc.id = cand["id"]
    total = Decimal(invoice["total_amount"])
    wanted = invoice["invoice_number"].strip().upper()
    exact_docs = [
        d
        for d in docs
        if "invoice_number" in d.extracted_data
        and str(d.extracted_data["invoice_number"]["value"]).upper() == wanted
    ]
    out: dict[str, Any] = {}
    for mode, session_docs in (("exact", exact_docs), ("fuzzy", docs)):
        detector = dup_mod.DuplicateDetector(Session(session_docs))
        try:
            if mode == "exact":
                found = asyncio.run(
                    detector._find_exact_duplicates(
                        exact_hash="",
                        invoice_number=invoice["invoice_number"],
                        supplier_vat_id=None,
                        total_amount=total,
                        project_id=None,
                        exclude_document_id=None,
                    )
                )
            else:
                found = asyncio.run(
                    detector._find_fuzzy_duplicates(
                        supplier_name=invoice["supplier_name"],
                        supplier_vat_id=None,
                        amount=total,
                        amount_tolerance=0.02,
                        invoice_date=date.fromisoformat(invoice["invoice_date"]),
                        date_range_days=7,
                        project_id=None,
                        exclude_document_id=None,
                    )
                )
            out[mode] = [
                {
                    "id": m.original_invoice_id,
                    "match_type": m.match_type,
                    "confidence": m.confidence,
                    "details": m.details,
                }
                for m in found
            ]
        except Exception as exc:  # noqa: BLE001 - record the original failure
            out[mode] = {"exception": {"type": type(exc).__name__, "message": str(exc)}}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=20260923)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    head = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if head != COMMIT:
        raise SystemExit(f"checkout is at {head}, expected {COMMIT}")
    for path, blob in FILES.items():
        if git_blob((checkout / path).read_bytes()) != blob:
            raise SystemExit(f"{path} does not match the pinned blob")
    pkg = "app.services.fraud_detection."
    manager_mod = importlib.import_module(pkg + "manager")
    models = importlib.import_module(pkg + "models")
    ted_mod = importlib.import_module(pkg + "ted_checker")
    dup_mod = importlib.import_module(pkg + "duplicate_detector")
    for mod, path in (
        (manager_mod, "manager.py"),
        (ted_mod, "ted_checker.py"),
        (dup_mod, "duplicate_detector.py"),
    ):
        if Path(str(mod.__file__)).resolve() != checkout / BASE / path:
            raise SystemExit(f"{path} imported from an unexpected location")
    rng = random.Random(args.seed)
    manager_cases = [
        {"name": f"manager-{i:03d}", "signals": s, **run_manager(manager_mod, models, s)}
        for i, s in enumerate(manager_boundaries() + [build_signals(rng) for _ in range(250)])
    ]
    ted_cases = [
        {"name": f"ted-{i:03d}", "notices": n, **run_ted(ted_mod, n)}
        for i, n in enumerate(ted_contract_sets(rng, 120))
    ]
    duplicate_cases_out = [{**c, **run_duplicates(dup_mod, c)} for c in duplicate_cases(rng, 250)]
    ted = ted_mod.TedChecker
    document = {
        "source": {"repository": REPOSITORY, "commit": COMMIT, "files": FILES},
        "environment": {"python": platform.python_version()},
        "constants": {
            "ted": {
                k: getattr(ted, k)
                for k in (
                    "WARNING_CONTRACT_COUNT_12M",
                    "WARNING_CONCENTRATION_THRESHOLD",
                    "WARNING_EXTREME_CONCENTRATION_THRESHOLD",
                    "WARNING_MIN_AUTHORITY_COUNT",
                    "WARNING_GROWTH_THRESHOLD",
                )
            },
            "config": {
                k: getattr(models.FraudCheckConfig(), k)
                for k in (
                    "duplicate_fuzzy_tolerance",
                    "benford_min_samples",
                    "company_verify_threshold",
                )
            },
        },
        "manager": manager_cases,
        "ted": ted_cases,
        "duplicates": duplicate_cases_out,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, default=str) + "\n")
    print(
        f"{len(manager_cases)} manager, {len(ted_cases)} TED, "
        f"{len(duplicate_cases_out)} duplicate cases -> {args.output}"
    )


if __name__ == "__main__":
    main()
