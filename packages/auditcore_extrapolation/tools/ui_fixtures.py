"""Write the UI fixtures of packages-js/ui-core from the real contract functions.

    python tools/ui_fixtures.py ../../packages-js/ui-core/test/fixtures

Synthetic data only; the fixtures are the answers of auditcore_extrapolation.web
to the requests below, so that the Vue and React tests use genuine responses.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from auditcore_extrapolation.web import catalogue, evaluate, residual

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
    }
    for name, data in files.items():
        text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        (target / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
