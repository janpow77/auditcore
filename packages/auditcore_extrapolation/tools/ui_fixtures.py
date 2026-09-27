"""Write the UI fixtures of packages-js/ui-core from the real contract functions.

    python tools/ui_fixtures.py ../../packages-js/ui-core/test/fixtures

Synthetic data only; the fixtures are the answers of auditcore_extrapolation.web
to the requests below, so that the Vue and React tests use genuine responses.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from auditcore_extrapolation.web import attributes, catalogue, evaluate, residual

EVALUATION_REQUEST: dict[str, object] = {
    "method": "mus.standard",
    "confidence_level": 0.9,
    "factor_profile": "kom_2017_tables",
    "materiality_rate": 0.02,
    "strata": [{"name": "Programm", "book_value": 1_000_000, "systemic_error": 2_000}],
    "units": [
        {"id": "V-01", "stratum": "Programm", "book_value": 20_000, "random_error": 1_000},
        {"id": "V-02", "stratum": "Programm", "book_value": 10_000, "systemic_error": 500},
        {"id": "V-03", "stratum": "Programm", "book_value": 5_000},
        {
            "id": "V-04",
            "stratum": "Programm",
            "book_value": 8_000,
            "anomalous_error": 800,
            "anomalous_reason": "Einmaliger Übertragungsfehler",
            "anomalous_corrected": True,
        },
        {
            "id": "V-05",
            "stratum": "Programm",
            "book_value": 200_000,
            "random_error": 4_000,
            "exhaustive": True,
        },
    ],
}
PERIODS_REQUEST: dict[str, object] = {
    "method": "mus.standard",
    "confidence_level": 0.9,
    "factor_profile": "kom_2017_tables",
    "materiality_rate": 0.02,
    "system_assessment": 3,
    "periods": [{"name": "1. Halbjahr"}, {"name": "2. Halbjahr"}],
    "strata": [
        {"name": "Programm", "period": "1. Halbjahr", "book_value": 1_000_000},
        {"name": "Programm", "period": "2. Halbjahr", "book_value": 1_500_000},
    ],
    "units": [
        {
            "id": "V-01",
            "period": "1. Halbjahr",
            "stratum": "Programm",
            "book_value": 40_000,
            "subsample": {
                "estimator": "ratio",
                "strata": [
                    {"name": "Vollerhebung", "book_value": 10_000},
                    {"name": "Stichprobe", "book_value": 30_000},
                ],
                "units": [
                    {
                        "id": "LP",
                        "stratum": "Vollerhebung",
                        "book_value": 10_000,
                        "random_error": 300,
                        "exhaustive": True,
                    },
                    {"id": "R-1", "stratum": "Stichprobe", "book_value": 2_000, "random_error": 40},
                    {"id": "R-2", "stratum": "Stichprobe", "book_value": 3_000},
                ],
            },
        },
        {"id": "V-02", "period": "1. Halbjahr", "stratum": "Programm", "book_value": 25_000},
        {"id": "V-03", "period": "1. Halbjahr", "stratum": "Programm", "book_value": 30_000},
        {
            "id": "V-01",
            "period": "2. Halbjahr",
            "stratum": "Programm",
            "book_value": 50_000,
            "random_error": 2_500,
        },
        {"id": "V-04", "period": "2. Halbjahr", "stratum": "Programm", "book_value": 20_000},
        {"id": "V-05", "period": "2. Halbjahr", "stratum": "Programm", "book_value": 45_000},
    ],
}
GROUPS_REQUEST: dict[str, object] = {
    "method": "srs.mean_per_unit",
    "confidence_level": 0.8,
    "factor_profile": "kom_2017_tables",
    "materiality_rate": 0.02,
    "strata": [
        {"name": "P1", "group": "Programm 1", "book_value": 500_000, "population_size": 400},
        {"name": "P2", "group": "Programm 2", "book_value": 300_000, "population_size": 250},
    ],
    "units": [
        {"id": f"A-{i}", "stratum": "P1", "book_value": 1_000, "random_error": error}
        for i, error in enumerate((40, 0, 0, 10, 0))
    ]
    + [
        {"id": f"B-{i}", "stratum": "P2", "book_value": 1_000, "random_error": error}
        for i, error in enumerate((0, 0, 5, 0))
    ],
}
INVOICES = [
    {
        "id": f"R-{i}",
        "stratum": "Rechnungen",
        "book_value": 500,
        "random_error": 25 if i == 0 else 0,
    }
    for i in range(4)
]
MULTISTAGE_REQUEST: dict[str, object] = {
    "method": "mus.standard",
    "confidence_level": 0.9,
    "factor_profile": "kom_2017_tables",
    "materiality_rate": 0.02,
    "periods": [{"name": "1. Halbjahr"}, {"name": "2. Halbjahr"}],
    "strata": [
        {"name": "P1", "period": "1. Halbjahr", "group": "Programm 1", "book_value": 600_000},
        {"name": "P2", "period": "1. Halbjahr", "group": "Programm 2", "book_value": 400_000},
        {"name": "P1", "period": "2. Halbjahr", "group": "Programm 1", "book_value": 900_000},
        {"name": "P2", "period": "2. Halbjahr", "group": "Programm 2", "book_value": 500_000},
    ],
    "units": [
        {
            "id": "OP-1",
            "period": "1. Halbjahr",
            "stratum": "P1",
            "book_value": 60_000,
            "subsample": {
                "estimator": "ratio",
                "strata": [
                    {"name": "Lead-Partner", "book_value": 20_000},
                    {"name": "Projektpartner", "book_value": 40_000},
                ],
                "units": [
                    {
                        "id": "LP",
                        "stratum": "Lead-Partner",
                        "book_value": 20_000,
                        "random_error": 400,
                        "exhaustive": True,
                    },
                    {
                        "id": "PP-2",
                        "stratum": "Projektpartner",
                        "book_value": 10_000,
                        "subsample": {
                            "estimator": "ratio",
                            "strata": [{"name": "Rechnungen", "book_value": 10_000}],
                            "units": INVOICES,
                        },
                    },
                ],
            },
        },
        {"id": "OP-2", "period": "1. Halbjahr", "stratum": "P1", "book_value": 30_000},
        {
            "id": "OP-3",
            "period": "1. Halbjahr",
            "stratum": "P2",
            "book_value": 25_000,
            "random_error": 500,
        },
        {"id": "OP-4", "period": "1. Halbjahr", "stratum": "P2", "book_value": 20_000},
        {
            "id": "OP-1",
            "period": "2. Halbjahr",
            "stratum": "P1",
            "book_value": 70_000,
            "random_error": 1_400,
        },
        {"id": "OP-5", "period": "2. Halbjahr", "stratum": "P1", "book_value": 40_000},
        {"id": "OP-6", "period": "2. Halbjahr", "stratum": "P2", "book_value": 35_000},
        {
            "id": "OP-7",
            "period": "2. Halbjahr",
            "stratum": "P2",
            "book_value": 15_000,
            "random_error": 300,
        },
    ],
}
ATTRIBUTES_NORMAL: dict[str, object] = {
    "approach": "normal",
    "deviations": 3,
    "sample_size": 150,
    "confidence_level": 0.95,
    "factor_profile": "kom_2017_tables",
    "tolerable_rate": 0.05,
}
ATTRIBUTES_DISCOVERY: dict[str, object] = {
    "approach": "discovery",
    "deviations": 0,
    "sample_size": 59,
    "confidence_level": 0.95,
    "tolerable_rate": 0.05,
}
RESIDUAL_REQUEST: dict[str, object] = {
    "audit_population": 1000,
    "total_error_rate": 0.025,
    "financial_corrections": 2.1,
}


def main(target: Path) -> None:
    files = {
        "extrapolation-profiles.json": catalogue(),
        "extrapolation-request.json": EVALUATION_REQUEST,
        "extrapolation-evaluation.json": evaluate(EVALUATION_REQUEST),
        "extrapolation-residual.json": residual(RESIDUAL_REQUEST),
        "extrapolation-multistage-request.json": MULTISTAGE_REQUEST,
        "extrapolation-multistage-evaluation.json": evaluate(MULTISTAGE_REQUEST),
        "attributes-normal.json": attributes(ATTRIBUTES_NORMAL),
        "attributes-discovery.json": attributes(ATTRIBUTES_DISCOVERY),
        "extrapolation-periods-request.json": PERIODS_REQUEST,
        "extrapolation-periods-evaluation.json": evaluate(PERIODS_REQUEST),
        "extrapolation-groups-request.json": GROUPS_REQUEST,
        "extrapolation-groups-evaluation.json": evaluate(GROUPS_REQUEST),
    }
    for name, data in files.items():
        text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        (target / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
