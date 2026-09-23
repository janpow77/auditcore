"""Execute the original flowinvoice ``RiskChecker.assess`` and record inputs/outputs.

Run inside a flowinvoice backend checkout at the pinned commit with its own
environment (``requirements-production.txt``); only ``app.services.risk_checker``,
``app.schemas.risk`` and ``app.models.enums`` are imported, no database or
network is touched::

    PYTHONPATH=<flowinvoice>/backend python tools/capture_flowinvoice_risk_checker.py \
        <flowinvoice checkout> tests/fixtures/flowinvoice_risk_checker_observed.json

The assessment timestamp is excluded from the record. All data are synthetic.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import random
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any

REPOSITORY = "janpow77/flowinvoice"
COMMIT = "fb2d18568d2eaf64574d131ceae51a936b9aac02"
FILES = {
    "backend/app/services/risk_checker.py": "b799e855c382760d0a84762b2949462692f7be01",
    "backend/app/schemas/risk.py": "43d4b75f44e12d979377e5502e73d587ccbe9a08",
    "backend/app/models/enums.py": "4abafed4dff667e6bbd00afccb9cbac3305460b5",
}


def git_blob(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode() + b"\0"
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def request(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "vendor_name": "Lieferant Nord GmbH",
        "invoice_date": "2025-05-15",
        "net_amount": 1234.56,
        "gross_amount": 1469.13,
        "description": "Wartung der Laboranlage im Vorhaben",
        "service_period_start": "2025-05-01",
        "service_period_end": "2025-05-10",
    }
    base.update(kw)
    return base


def context(**kw: Any) -> dict[str, Any]:
    return dict(kw)


def invoices(*items: tuple[float, str]) -> list[dict[str, Any]]:
    return [{"net_amount": a, "invoice_date": d} for a, d in items]


def boundary_cases() -> list[tuple[str, dict[str, Any]]]:
    cases: list[tuple[str, dict[str, Any]]] = []
    for amount in (49_999.99, 50_000.0, 50_000.01, 120_000.0):
        cases.append((f"hoch-absolut-{amount}", request(net_amount=amount)))
    for med, std, amount in (
        (1000.0, 200.0, 1400.0),
        (1000.0, 200.0, 1400.01),
        (0.0, 200.0, 5000.0),
        (1000.0, 0.0, 5000.0),
        (None, 200.0, 5000.0),
        (1000.0, None, 5000.0),
        (2000.0, 500.0, 60_000.0),
    ):
        cases.append(
            (
                f"hoch-relativ-{med}-{std}-{amount}",
                request(net_amount=amount, context=context(median_amount=med, std_deviation=std)),
            )
        )
    for freq, total in ((3, 10), (4, 10), (1, 3), (0, 10), (5, 0), (None, 10), (10, None)):
        cases.append(
            (
                f"lieferant-{freq}-{total}",
                request(context=context(vendor_frequency=freq, total_vendor_count=total)),
            )
        )
    for start, end in ((None, None), ("2025-05-01", None), (None, "2025-05-10")):
        cases.append(
            (
                f"zeitraum-{start}-{end}",
                request(service_period_start=start, service_period_end=end),
            )
        )
    descriptions = [
        "Pauschale Beratung",
        "PAUSCHAL vereinbart",
        "Festpreis Montage",
        "Einmalzahlung Lizenz",
        "Montage nach Stunden",
    ]
    for amount in (999.0, 1000.0, 1000.5, 1050.0, 1100.0, 20_000.0, 100_000.0):
        for text in descriptions[:: 2 if amount != 1100.0 else 1]:
            cases.append((f"rund-{amount}-{text}", request(net_amount=amount, description=text)))
    project = {"project_start": "2025-01-01", "project_end": "2025-12-31"}
    for start, end, inv in (
        ("2024-12-31", "2025-01-10", "2025-01-15"),
        ("2025-01-01", "2025-12-31", "2025-06-01"),
        ("2025-12-01", "2026-01-01", "2026-01-05"),
        (None, None, "2024-12-31"),
        (None, None, "2026-01-01"),
        ("2024-11-01", "2026-02-01", "2025-05-01"),
        (None, "2026-01-02", "2025-06-01"),
    ):
        cases.append(
            (
                f"projekt-{start}-{end}-{inv}",
                request(
                    service_period_start=start,
                    service_period_end=end,
                    invoice_date=inv,
                    context=context(**project),
                ),
            )
        )
    cases.append(
        (
            "projekt-nur-beginn",
            request(invoice_date="2020-01-01", context=context(project_start="2025-01-01")),
        )
    )
    for text in (
        "Diverse Leistungen",
        "diverses Material",
        "Diverser Kleinkram",
        "Diverse",
        "Sonstige Kosten",
        "sonstiger Aufwand",
        "Verschiedene Arbeiten",
        "Allgemeine Verwaltung",
        "Abrechnung nach Aufwand",
        "Pauschale  Leistung Q1",
        "Leistungen diverse",
        "Nachaufwand",
    ):
        cases.append((f"bezug-{text}", request(description=text)))
    for recipient, beneficiary in (
        ("Stadtwerke Nord", "Stadtwerke Nord"),
        ("  STADTWERKE nord ", "stadtwerke Nord"),
        ("Stadtwerke Nord GmbH", "Stadtwerke Nord"),
        ("Nord", "Stadtwerke Nord"),
        ("Hochschule Süd", "Stadtwerke Nord"),
        (None, "Stadtwerke Nord"),
        ("Stadtwerke Nord", None),
        ("", "Stadtwerke Nord"),
    ):
        cases.append(
            (
                f"empfaenger-{recipient}-{beneficiary}",
                request(invoice_recipient=recipient, beneficiary_name=beneficiary),
            )
        )
    for supplier, beneficiary in (
        ("DE123456789", "DE123456789"),
        ("de 123.456.789", "DE123456789"),
        ("DE-123/456\\789", " de123456789 "),
        ("DE123456789", "DE987654321"),
        (None, "DE123456789"),
        ("", "DE123456789"),
    ):
        cases.append(
            (
                f"selbst-{supplier}-{beneficiary}",
                request(supplier_vat_id=supplier, beneficiary_vat_id=beneficiary),
            )
        )
    split = [
        ("unter-drei", invoices((900.0, "2025-05-01"), (950.0, "2025-05-02"))),
        (
            "drei-im-fenster",
            invoices((900.0, "2025-05-01"), (950.0, "2025-05-10"), (980.0, "2025-05-31")),
        ),
        (
            "fenster-31-tage",
            invoices((900.0, "2025-05-01"), (950.0, "2025-05-10"), (980.0, "2025-06-01")),
        ),
        (
            "bandgrenzen",
            invoices((800.0, "2025-05-01"), (1000.0, "2025-05-02"), (799.99, "2025-05-03")),
        ),
        (
            "bandgrenzen-inklusiv",
            invoices((800.0, "2025-05-01"), (1000.0, "2025-05-02"), (850.0, "2025-05-03")),
        ),
        (
            "hoehere-schwelle",
            invoices((4100.0, "2025-03-01"), (4500.0, "2025-03-05"), (5000.0, "2025-03-20")),
        ),
        (
            "unsortiert",
            invoices((24_000.0, "2025-08-20"), (21_000.0, "2025-08-01"), (20_000.0, "2025-08-15")),
        ),
        (
            "zwei-schwellen",
            invoices(
                (900.0, "2025-01-01"),
                (910.0, "2025-01-02"),
                (920.0, "2025-01-03"),
                (45_000.0, "2025-02-01"),
                (46_000.0, "2025-02-02"),
                (47_000.0, "2025-02-03"),
            ),
        ),
        (
            "spaeteres-fenster",
            invoices(
                (9000.0, "2025-01-01"),
                (9100.0, "2025-03-01"),
                (9200.0, "2025-03-15"),
                (9300.0, "2025-03-30"),
            ),
        ),
        ("leer", []),
    ]
    for name, items in split:
        cases.append((f"splitting-{name}", request(context=context(vendor_invoices=items))))
    return cases


def random_cases(count: int, seed: int) -> list[tuple[str, dict[str, Any]]]:
    rng = random.Random(seed)
    texts = [
        "Wartung der Anlage",
        "Pauschale Beratung",
        "Diverse Leistungen",
        "Sonstige Kosten",
        "Abrechnung nach Aufwand",
        "Festpreis Montage",
        "Lizenz Software",
    ]
    names = ["Stadtwerke Nord", "Hochschule Süd", "Stadtwerke Nord GmbH", None]
    vats = ["DE123456789", "de 123 456 789", "DE987654321", None]
    out = []
    start = date(2025, 1, 1)
    for k in range(count):
        day = start + timedelta(days=rng.randint(-40, 400))
        amount = rng.choice(
            [
                float(rng.randint(1, 80) * 500),
                round(rng.uniform(100, 70_000), 2),
                rng.choice([1000.0, 5000.0, 50_000.0]),
            ]
        )
        ctx: dict[str, Any] = {}
        if rng.random() < 0.6:
            ctx = {
                "median_amount": rng.choice([None, 0.0, round(rng.uniform(500, 5000), 2)]),
                "std_deviation": rng.choice([None, 0.0, round(rng.uniform(50, 3000), 2)]),
                "vendor_frequency": rng.choice([None, 0, rng.randint(1, 12)]),
                "total_vendor_count": rng.choice([None, 0, rng.randint(1, 12)]),
                "project_start": rng.choice([None, "2025-01-01"]),
                "project_end": rng.choice([None, "2025-12-31"]),
            }
            if rng.random() < 0.5:
                threshold = rng.choice([1000, 5000, 10000, 25000, 50000])
                items = []
                for _ in range(rng.randint(0, 6)):
                    d = day + timedelta(days=rng.randint(-45, 45))
                    items.append(
                        {
                            "net_amount": round(threshold * rng.uniform(0.75, 1.02), 2),
                            "invoice_date": d.isoformat(),
                        }
                    )
                ctx["vendor_invoices"] = items
        svc_start = rng.choice([None, (day - timedelta(days=rng.randint(0, 60))).isoformat()])
        svc_end = rng.choice([None, (day + timedelta(days=rng.randint(0, 60))).isoformat()])
        out.append(
            (
                f"random-{seed}-{k:03d}",
                request(
                    net_amount=amount,
                    gross_amount=round(amount * 1.19, 2),
                    invoice_date=day.isoformat(),
                    description=rng.choice(texts),
                    service_period_start=svc_start,
                    service_period_end=svc_end,
                    invoice_recipient=rng.choice(names),
                    beneficiary_name=rng.choice(names),
                    supplier_vat_id=rng.choice(vats),
                    beneficiary_vat_id=rng.choice(vats),
                    context=ctx or None,
                ),
            )
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--random", type=int, default=250)
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
    module = importlib.import_module("app.services.risk_checker")
    schemas = importlib.import_module("app.schemas.risk")
    if Path(str(module.__file__)).resolve() != checkout / "backend/app/services/risk_checker.py":
        raise SystemExit("imported risk_checker from an unexpected location")
    checker = module.RiskChecker()
    results: list[dict[str, Any]] = []
    for name, data in boundary_cases() + random_cases(args.random, args.seed):
        req = schemas.RiskAssessmentRequest.model_validate(data)
        try:
            res = checker.assess(req)
        except Exception as exc:  # noqa: BLE001 - record the original failure
            results.append(
                {
                    "name": name,
                    "request": data,
                    "exception": {"type": type(exc).__name__, "message": str(exc)},
                }
            )
            continue
        results.append(
            {
                "name": name,
                "request": data,
                "exception": None,
                "findings": [
                    {
                        "indicator": str(f.indicator),
                        "severity": str(f.severity),
                        "description": f.description,
                        "evidence": f.evidence,
                        "recommendation": f.recommendation,
                    }
                    for f in res.findings
                ],
                "risk_score": res.risk_score,
                "highest_severity": None
                if res.highest_severity is None
                else str(res.highest_severity),
                "summary": res.summary,
                "assessment_version": res.assessment_version,
            }
        )
    constants = {
        k: getattr(module.RiskChecker, k)
        for k in (
            "HIGH_AMOUNT_ABSOLUTE",
            "HIGH_AMOUNT_SIGMA",
            "VENDOR_CONCENTRATION_THRESHOLD",
            "ROUND_AMOUNT_THRESHOLD",
            "SPLIT_INVOICE_THRESHOLDS",
            "SPLIT_INVOICE_PROXIMITY",
            "SPLIT_INVOICE_MIN_INVOICES",
            "SPLIT_INVOICE_TIME_WINDOW_DAYS",
        )
    }
    import pydantic  # type: ignore[import-not-found]

    document: dict[str, Any] = {
        "source": {
            "repository": REPOSITORY,
            "commit": COMMIT,
            "files": FILES,
            "symbols": ["RiskChecker", "RiskAssessmentRequest", "RiskAssessmentResult"],
        },
        "also_identical_in": {
            "repository": "janpow77/audit-portal",
            "path": "backend/app/services/risk_checker.py",
            "git_blob": "5e93b2b8c99ace75ccd8592410906e38d77f224f",
            "difference": "nur Formatierung zweier List-Comprehensions",
        },
        "environment": {"python": platform.python_version(), "pydantic": pydantic.__version__},
        "constants": constants,
        "cases": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=0) + "\n")
    failed = sum(1 for r in results if r["exception"])
    print(f"{len(results)} RiskChecker cases ({failed} original exceptions) -> {args.output}")


if __name__ == "__main__":
    main()
