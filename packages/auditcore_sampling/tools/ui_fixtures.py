"""Write the UI fixtures of the sample-size planner from the real contract functions.

    python tools/ui_fixtures.py ../../packages-js/ui-core/test/fixtures

Synthetic data only (the worked examples of the guidance); the fixtures are the
answers of ``auditcore_sampling.web`` (contract ``auditcore_sampling.guidance/1``),
so that the Vue and React tests use genuine responses.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from auditcore_sampling.web import guidance_catalogue, guidance_size

REQUESTS: dict[str, dict[str, object]] = {
    "guidance.mus_conservative": {
        "method": "guidance.mus_conservative",
        "factor_profile": "kom_2017_tables",
        "confidence_level": 0.9,
        "book_value": 4_199_882_024,
        "anticipated_error_rate": 0.002,
        "materiality_rate": 0.02,
    },
    "guidance.srs_stratified": {
        "method": "guidance.srs_stratified",
        "factor_profile": "kom_2017_tables",
        "confidence_level": 0.8,
        "book_value": 1_396_535_319,
        "anticipated_error_rate": 0.018,
        "materiality_rate": 0.02,
        "finite_population_correction": False,
        "strata": [
            {"name": "Programm 1", "population_size": 3582, "sd": 444, "exhaustive": False},
            {"name": "Programm 2", "population_size": 1225, "sd": 9818, "exhaustive": False},
            {"name": "Hochwert", "population_size": 5, "exhaustive": True},
        ],
    },
    "guidance.nonstatistical": {
        "method": "guidance.nonstatistical",
        "rule": "cpr_2021_art79_2",
        "population_size": 187,
    },
}


def main(target: Path) -> None:
    files = {
        "samplesize-profiles.json": guidance_catalogue(),
        "samplesize-plans.json": {
            method: {"request": request, "response": guidance_size(request)}
            for method, request in REQUESTS.items()
        },
    }
    for name, data in files.items():
        text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
        (target / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
