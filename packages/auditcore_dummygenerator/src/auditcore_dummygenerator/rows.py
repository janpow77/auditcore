"""Row assembly and ordered worker batches for :class:`TestDataGenerator`.

The field, deviation and catalog rules stay in ``generator.py``, whose bytes the
profile registry fingerprints. This module only sequences those rules into rows
and splits large requests into seeded batches, exactly as the recorded legacy
implementation did.
"""

from __future__ import annotations

import os
import random
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from multiprocessing import cpu_count, get_context
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from auditcore_dummygenerator.generator import TestDataGenerator

#: Legacy JSON request, field specification, batch configuration or row: string keys,
#: caller-defined values. The generator never validates this shape beyond key lookups.
JsonObject = dict[str, Any]
Row = JsonObject
#: joblib's ``Parallel`` and ``delayed``, resolved only when a joblib batch runs.
JoblibApi = tuple[Any, Any]
BatchWorker = Callable[[JsonObject], list[Row]]
JoblibBackend = Callable[[], JoblibApi]

#: Minimum rows per worker before a request is split.
MIN_BATCH_SIZE = 100

#: Belegliste (receipt list) criteria in legacy precedence: field-name fragment, criteria key.
RECEIPT_LIST_CRITERIA = (
    ("vorhabennummer", "vorhabennummern"),
    ("aktenzeichen", "aktenzeichen"),
    ("kostenstelle", "kostenstellen"),
    ("kategorie", "kategorien"),
)


class BatchGenerationError(RuntimeError):
    """A worker failed or returned fewer rows; no partial success is returned."""


def get_optimal_workers() -> int:
    """Ermittelt die optimale Anzahl an Worker-Prozessen."""
    value = int(os.environ.get("MAX_WORKERS", cpu_count()))
    if value < 1:
        raise ValueError("MAX_WORKERS must be a positive integer")
    return min(cpu_count(), value)


def run_batch(batch_config: JsonObject) -> list[Row]:
    """
    Worker-Funktion für parallele Batch-Generierung.
    Wird in separaten Prozessen ausgeführt.
    """
    from auditcore_dummygenerator.generator import TestDataGenerator

    generator = TestDataGenerator(
        seed=batch_config["seed"], base_date=batch_config.get("base_date")
    )
    request = batch_config["request"]
    start_idx = batch_config["start_idx"]
    batch_size = batch_config["batch_size"]

    # Kopie des Requests mit angepasster Zeilenanzahl
    batch_request = deepcopy(request)
    batch_request["rows"] = batch_size

    # Auto-increment Startwerte anpassen
    fields = batch_request.get("fields", [])
    for field in fields:
        if field.get("type") == "auto_increment":
            params = field.get("params", {}).copy()
            original_start = params.get("start", 1)
            step = params.get("step", 1)
            params["start"] = original_start + (start_idx * step)
            field["params"] = params

    return generator._generate_rows_sequential(batch_request)


def generate_sequential(generator: TestDataGenerator, request: JsonObject) -> list[Row]:
    """Generate all rows in one call sequence of the generator's RNG."""
    rows_count = request.get("rows", 100)
    countries = request.get("countries", "DE+AT")
    fields = request.get("fields", [])
    deviation = request.get("deviation", {"rate": 0, "scenario": "NONE"})
    belegliste_options = request.get("beleglisteOptions")

    country_list = ["DE", "AT"] if countries == "DE+AT" else [countries]
    counters = _auto_increment_starts(fields)
    results = []

    for i in range(rows_count):
        country = generator.rng.choice(country_list)
        row: Row = {}
        for field in fields:
            field_name = field.get("name", f"field_{i}")
            row[field_name] = _field_value(
                generator, field, field_name, country, row, counters, belegliste_options
            )

        if deviation.get("rate", 0) > 0:
            row = generator.apply_deviation(
                row, deviation.get("scenario", "NONE"), deviation.get("rate", 0)
            )

        results.append(row)

    return results


def _auto_increment_starts(fields: list[JsonObject]) -> JsonObject:
    """Initial counter per auto-increment field name."""
    counters = {}
    for field in fields:
        if field.get("type") == "auto_increment":
            counters[field["name"]] = field.get("params", {}).get("start", 1)
    return counters


def _field_value(
    generator: TestDataGenerator,
    field: JsonObject,
    field_name: str,
    country: str,
    row: Row,
    counters: JsonObject,
    belegliste_options: JsonObject | None,
) -> object:
    """Advance auto-increment counters, then apply Belegliste criteria or the field rule."""
    field_type = field.get("type", "number")
    params = field.get("params", {}).copy()

    if field_type == "auto_increment":
        current = counters.get(field_name, 1)
        params["_current"] = current
        step = params.get("step", 1)
        counters[field_name] = current + step

    if belegliste_options and field_type in ["number", "weighted_list"]:
        distribution = _receipt_list_distribution(
            field_name, belegliste_options.get("criteria", {})
        )
        if distribution is not None:
            return generator.generate_weighted_choice(distribution.get("items", []))

    return generator.generate_field(field_type, params, country, row)


def _receipt_list_distribution(field_name: str, criteria: JsonObject) -> JsonObject | None:
    """Return the first configured distribution whose fragment occurs in the field name."""
    for fragment, key in RECEIPT_LIST_CRITERIA:
        if fragment in field_name.lower() and criteria.get(key):
            distribution: JsonObject = criteria[key]
            return distribution
    return None


def generate_parallel(
    generator: TestDataGenerator,
    request: JsonObject,
    n_workers: int | None,
    *,
    worker: BatchWorker,
    joblib_backend: JoblibBackend | None,
) -> list[Row]:
    """Split large requests into ordered seeded batches; fall back to sequential generation."""
    rows_count = request.get("rows", 100)
    if n_workers is not None and n_workers < 1:
        raise ValueError("n_workers must be a positive integer")
    n_workers = n_workers or generator.max_workers or get_optimal_workers()
    actual_workers = min(n_workers, max(1, rows_count // MIN_BATCH_SIZE))

    if actual_workers <= 1:
        return generator._generate_rows_sequential(request)

    configs = batch_configs(generator, request, rows_count, actual_workers)
    if joblib_backend is not None:
        results = _run_joblib(configs, actual_workers, worker, joblib_backend)
    else:
        results = _run_process_pool(configs, actual_workers, worker)

    if len(results) != rows_count:
        raise BatchGenerationError("Worker result count differs from requested rows")
    return results


def batch_configs(
    generator: TestDataGenerator, request: JsonObject, rows_count: int, workers: int
) -> list[JsonObject]:
    """Split rows into ordered batches with one derived seed per batch."""
    batch_size = rows_count // workers
    remainder = rows_count % workers
    base_seed = generator.seed if generator.seed is not None else random.randint(0, 2**31)

    configs = []
    current_idx = 0
    for i in range(workers):
        # Die ersten ``remainder`` Batches bekommen je eine Zeile mehr.
        size = batch_size + (1 if i < remainder else 0)
        configs.append(
            {
                "base_date": generator.base_date,
                "seed": base_seed + i * 1000,  # Unterschiedliche Seeds pro Batch
                "request": deepcopy(request),
                "start_idx": current_idx,
                "batch_size": size,
                "auto_increment_start": current_idx,
                "batch_index": i,
            }
        )
        current_idx += size
    return configs


def _run_joblib(
    configs: list[JsonObject],
    workers: int,
    worker: BatchWorker,
    joblib_backend: JoblibBackend,
) -> list[Row]:
    """joblib verwenden wenn verfügbar (performanter)."""
    try:
        parallel, delayed = joblib_backend()
        batch_results = parallel(n_jobs=workers, backend="loky")(
            delayed(worker)(config) for config in configs
        )
    except Exception as exc:
        raise BatchGenerationError("Parallel generation failed") from exc
    results: list[Row] = []
    for batch_result in batch_results:
        results.extend(batch_result)
    return results


def _run_process_pool(configs: list[JsonObject], workers: int, worker: BatchWorker) -> list[Row]:
    """Fallback auf ProcessPoolExecutor; Ergebnisse in Batch-Reihenfolge."""
    indexed_results: dict[int, list[Row]] = {}
    with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("spawn")) as executor:
        futures = {executor.submit(worker, config): config["batch_index"] for config in configs}
        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                indexed_results[batch_idx] = future.result()
            except Exception as exc:
                for pending in futures:
                    pending.cancel()
                raise BatchGenerationError(f"Batch {batch_idx} failed") from exc

    results: list[Row] = []
    for i in range(workers):
        if i in indexed_results:
            results.extend(indexed_results[i])
    return results
