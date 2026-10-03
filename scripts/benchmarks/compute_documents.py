"""Reproduzierbarer End-to-End-Vergleich mit ausschließlich synthetischen Daten.

Aufruf im Repo mit installierten Paketen: python scripts/benchmarks/compute_documents.py
--output scratchpad/after.json. Für den Vergleich die unveränderten Paketquellen
über PYTHONPATH laden. Die Ergebnis-Hashes müssen in beiden Läufen gleich sein.
OCR misst einen simulierten Gateway-Wartepfad, keine echte OCR-Inferenz.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import platform
import resource
import statistics
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from auditcore_compute import engine_report
from auditcore_compute.finance import share_cents
from auditcore_documents.pipeline.stages.ocr import OcrRouting, OcrStage, RouterResult
from auditcore_documents.web.batch_checks import BatchCheckService
from auditcore_documents.web.batch_input import FIELDS

ROOT = Path(__file__).resolve().parents[2]


def digest(value: object) -> str:
    if isinstance(value, np.ndarray):
        data = value.tobytes()
    else:
        data = json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def measure(call: Callable[[], object], repeats: int = 7) -> dict[str, object]:
    started = time.perf_counter()
    initial = call()
    first_ms = (time.perf_counter() - started) * 1000
    expected = digest(initial)
    timings = []
    for _ in range(repeats):
        started = time.perf_counter()
        result = call()
        timings.append((time.perf_counter() - started) * 1000)
        assert digest(result) == expected
    return {"first_ms": first_ms, "median_ms": statistics.median(timings), "sha256": expected}


def batch() -> dict[str, object]:
    fixture = ROOT / "packages/auditcore_documents/tests/fixtures/batch/bestand.csv"
    with fixture.open() as stream:
        data = list(csv.reader(stream, delimiter=";"))
    header = [name.strip().lower() for name in data[0]]
    columns = {
        field.name: header.index(alias)
        for field in FIELDS
        for alias in field.aliases
        if alias in header
    }
    template = [{name: row[i] or None for name, i in columns.items()} for row in data[1:]]
    rows = [{**template[i % len(template)], "ref": f"SYNTHETIC-{i}"} for i in range(5000)]
    service = BatchCheckService(clock=lambda: datetime(2026, 10, 3, tzinfo=UTC))
    return measure(lambda: service.check({"documents": rows}), 5)


def ocr(concurrency: int) -> dict[str, object]:
    async def router(data: bytes, **kwargs: str) -> tuple[RouterResult | None, str | None]:
        await asyncio.sleep(0.01)
        return RouterResult(text=data.decode(), confidence=0.9, model="simulated"), None

    options = {"max_concurrent_pages": concurrency} if concurrency > 1 else {}
    stage = OcrStage(routing=OcrRouting(**options), timer=lambda: 0)
    pages = [(number, f"Seite {number}".encode()) for number in range(1, 21)]
    return measure(
        lambda: asyncio.run(stage._router_pages(router, Path("synthetic.pdf"), pages, 0)), 3
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--parallel-ocr", action="store_true")
    args = parser.parse_args()
    amounts = np.random.default_rng(20261003).integers(-50_000_000, 50_000_000, 500_000)
    rates = ["0.4", "0.5", "0.6", "0.75", "0.85"] * 100_000
    result = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "seed": 20261003,
        "note": "Batch-Service inkl. Eingabe/Ergebnis; ohne HTTP/DB. OCR-Gateway simuliert.",
        "share_5000": measure(lambda: share_cents(amounts[:5000], "0.4")),
        "share_500000": measure(lambda: share_cents(amounts, "0.4")),
        "variable_rates_500000": measure(lambda: share_cents(amounts, rates), 5),
        "documents_5000": batch(),
        "ocr_20_pages": ocr(4 if args.parallel_ocr else 1),
        "engine": [item.as_dict() for item in engine_report()],
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({name: value for name, value in result.items() if name != "engine"}))


if __name__ == "__main__":
    main()
