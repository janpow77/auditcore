"""Capture actual results before changing the source; never import the new package."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

SOURCE_COMMIT = "05bc5ac560dfff3bc7181323240745215492d09a"
SOURCE_BLOB = "a9204a0883948e3f3626db12e23ea120983fc901"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != SOURCE_BLOB:
        raise SystemExit("Source does not match the reviewed GitHub blob")
    sys.path.insert(0, str(args.source.resolve().parent))
    spec = importlib.util.spec_from_file_location("generator", args.source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["generator"] = module
    spec.loader.exec_module(module)
    # Capture a fixed, available backend; no optional joblib installation needed.
    module.JOBLIB_AVAILABLE = False
    calls: list[tuple[str, list[object]]] = []
    for country in ("DE", "AT", "UNKNOWN"):
        for method in (
            "first_name",
            "last_name",
            "street",
            "city",
            "postal_code",
            "iban",
            "bic",
            "ustid",
            "phone",
        ):
            calls.append(("generate_" + method, [country]))
    calls.extend(
        [
            ("generate_house_number", []),
            ("generate_date_range", ["2024-01-01", "2024-12-31"]),
            ("generate_date_after", ["2024-01-01", 1, 30]),
            ("generate_amount", [1.0, 1000.0, 2]),
            ("generate_amount_relative", [1000.0, 0.5, 1.0]),
            ("generate_invoice_no", []),
            ("generate_invoice_no", ["custom"]),
            ("generate_company", []),
            ("generate_purpose_text", []),
            (
                "generate_weighted_choice",
                [[{"value": "a", "weight": 2}, {"value": "b", "weight": 1}]],
            ),
            ("generate_weighted_choice", [[]]),
            ("generate_number", []),
            ("generate_boolean", []),
            ("generate_field", ["unrecognized", {}, "DE", {}]),
            (
                "generate_field",
                ["amount_eur_relative", {"refFieldName": "value"}, "AT", {"value": "12,50"}],
            ),
            (
                "generate_field",
                ["amount_eur_relative", {"refFieldName": "value"}, "AT", {"value": "invalid"}],
            ),
            ("generate_date_range", ["2024-02-01", "2024-01-01"]),
            ("generate_date_range", ["invalid", "2024-01-01"]),
            ("generate_weighted_choice", [[{"value": "a", "weight": 0}]]),
            ("generate_number", [5, 1]),
        ]
    )
    fields = [
        {"name": "id", "type": "auto_increment", "params": {"start": 10, "step": 3}},
        *[
            {"name": kind, "type": kind}
            for kind in (
                "first_name",
                "last_name",
                "street",
                "house_number",
                "postal_code",
                "city",
                "iban",
                "bic",
                "ustid",
                "phone",
                "date_range",
                "amount_eur",
                "invoice_no",
                "company",
                "purpose_text",
                "number",
                "boolean",
            )
        ],
        {"name": "paid", "type": "date_after", "params": {"refFieldName": "date_range"}},
        {
            "name": "relative",
            "type": "amount_eur_relative",
            "params": {"refFieldName": "amount_eur"},
        },
        {
            "name": "weighted",
            "type": "weighted_list",
            "params": {"items": [{"value": "x", "weight": 2}, {"value": "y", "weight": 1}]},
        },
    ]
    for country in ("DE", "AT", "DE+AT"):
        calls.append(("generate_rows", [{"rows": 5, "countries": country, "fields": fields}]))
    for scenario in (
        "NONE",
        "NEGATIVE_AMOUNTS",
        "BEZAHLT_VOR_RECHNUNG",
        "FOERDERFAEHIG_GT_GEZAHLT",
    ):
        calls.append(
            (
                "apply_deviation",
                [
                    {
                        "betrag": 100.0,
                        "foerderfaehig": 90.0,
                        "rechnungsdatum": "2024-01-15",
                        "bezahldatum": "2024-02-01",
                    },
                    scenario,
                    1.0,
                ],
            )
        )
    calls.append(("generate_rows", [{"rows": 0}]))
    calls.append(("generate_rows", [{"rows": -1}]))
    criteria = {
        key: {"items": [{"value": key + "-a", "weight": 1}, {"value": key + "-b", "weight": 2}]}
        for key in ("vorhabennummern", "aktenzeichen", "kostenstellen", "kategorien")
    }
    calls.append(
        (
            "generate_rows",
            [
                {
                    "rows": 5,
                    "fields": [
                        {"name": name, "type": "number"}
                        for name in ("vorhabennummer", "aktenzeichen", "kostenstelle", "kategorie")
                    ],
                    "beleglisteOptions": {"criteria": criteria},
                }
            ],
        )
    )
    calls.append(
        (
            "generate_rows_parallel",
            [{"rows": 200, "fields": fields[:1] + [{"name": "value", "type": "number"}]}, 2],
        )
    )
    records = []
    for method, positional in calls:
        case = {"method": method, "args": json.loads(json.dumps(positional)), "seed": 42}
        generator = module.TestDataGenerator(seed=42)
        try:
            case["output"] = getattr(generator, method)(*positional)
        except Exception as exc:
            case["exception"] = type(exc).__name__
        records.append(case)
    report = {
        "source_repository": "janpow77/flowaudit_testdatengenerator_frontend",
        "source_commit": SOURCE_COMMIT,
        "source_path": "backend/generator.py",
        "source_blob": blob,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "captured_at": datetime.now(UTC).isoformat(),
        "python_version": sys.version,
        "parallel_backend": "ProcessPoolExecutor",
        "records": records,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Observed {len(records)} original implementation cases")


if __name__ == "__main__":
    main()
