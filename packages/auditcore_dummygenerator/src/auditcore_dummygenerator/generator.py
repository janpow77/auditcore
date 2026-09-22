"""Seeded synthetic rows extracted from the recorded FlowAudit implementation.

Source commit: 05bc5ac560dfff3bc7181323240745215492d09a.
MIT reuse/publication authorized by the rights holder on 2026-09-22; see NOTICE.
"""

from __future__ import annotations

import os
import random
import string
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from datetime import date, datetime, timedelta
from multiprocessing import cpu_count, get_context
from typing import Any, cast

# Optional: joblib für optimierte parallele Verarbeitung
try:
    from joblib import Parallel, delayed

    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False


def get_optimal_workers() -> int:
    """Ermittelt die optimale Anzahl an Worker-Prozessen."""
    value = int(os.environ.get("MAX_WORKERS", cpu_count()))
    if value < 1:
        raise ValueError("MAX_WORKERS must be a positive integer")
    return min(cpu_count(), value)


def _generate_batch(batch_config: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Worker-Funktion für parallele Batch-Generierung.
    Wird in separaten Prozessen ausgeführt.
    """
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


class BatchGenerationError(RuntimeError):
    """A worker failed or returned fewer rows; no partial success is returned."""


class TestDataGenerator:
    """Generate synthetic rows; seeded output retains the recorded legacy rules.

    A seed reproduces a fixed call sequence and batch layout. Supply base_date
    when date_after has no reference field and max_workers for stable batching.
    Names and banking identifiers are synthetic strings, not verified records.
    """

    __test__ = False
    # Minimale Zeilenanzahl für parallele Verarbeitung
    PARALLEL_THRESHOLD = 1000

    def __init__(
        self,
        seed: int | None = None,
        *,
        base_date: date | None = None,
        max_workers: int | None = None,
        use_joblib: bool | None = None,
    ) -> None:
        if max_workers is not None and max_workers < 1:
            raise ValueError("max_workers must be a positive integer")
        if use_joblib is True and not JOBLIB_AVAILABLE:
            raise ImportError("Install auditcore_dummygenerator[parallel] for joblib")
        self.base_date = base_date
        self.max_workers = max_workers
        self.use_joblib = JOBLIB_AVAILABLE if use_joblib is None else use_joblib
        self.seed = seed
        self.rng = random.Random(seed)

        self.first_names_de = [
            "Max",
            "Anna",
            "Peter",
            "Maria",
            "Thomas",
            "Julia",
            "Michael",
            "Sarah",
            "Andreas",
            "Lisa",
        ]
        self.first_names_at = [
            "Franz",
            "Elisabeth",
            "Josef",
            "Katharina",
            "Johann",
            "Theresia",
            "Leopold",
            "Rosa",
            "Karl",
            "Margarethe",
        ]
        self.last_names_de = [
            "Müller",
            "Schmidt",
            "Schneider",
            "Fischer",
            "Weber",
            "Meyer",
            "Wagner",
            "Becker",
            "Schulz",
            "Hoffmann",
        ]
        self.last_names_at = [
            "Gruber",
            "Huber",
            "Bauer",
            "Wagner",
            "Müller",
            "Pichler",
            "Steiner",
            "Moser",
            "Mayer",
            "Hofer",
        ]
        self.streets_de = [
            "Hauptstraße",
            "Bahnhofstraße",
            "Schulstraße",
            "Gartenstraße",
            "Berliner Straße",
            "Dorfstraße",
            "Lindenstraße",
            "Kirchstraße",
            "Waldstraße",
            "Bergstraße",
        ]
        self.streets_at = [
            "Hauptstraße",
            "Wiener Straße",
            "Bahnhofstraße",
            "Kirchengasse",
            "Schulgasse",
            "Feldgasse",
            "Berggasse",
            "Wiesengasse",
            "Mariahilfer Straße",
            "Ringstraße",
        ]
        self.cities_de = [
            ("Berlin", "10115"),
            ("Hamburg", "20095"),
            ("München", "80331"),
            ("Köln", "50667"),
            ("Frankfurt", "60311"),
        ]
        self.cities_at = [
            ("Wien", "1010"),
            ("Graz", "8010"),
            ("Linz", "4020"),
            ("Salzburg", "5020"),
            ("Innsbruck", "6020"),
        ]
        self.companies = [
            "TechCorp GmbH",
            "Digital Solutions AG",
            "InnoTech KG",
            "DataServ GmbH",
            "CloudSys AG",
            "NetWorks GmbH",
            "SoftDev KG",
            "IT-Service GmbH",
            "WebTech AG",
            "AppFactory GmbH",
        ]
        self.purposes = [
            "Beratungsleistung",
            "Softwarelizenz",
            "Hardwarebeschaffung",
            "Schulung",
            "Wartung",
            "Support",
            "Entwicklung",
            "Hosting",
            "Consulting",
            "Projektmanagement",
        ]

    def generate_first_name(self, country: str) -> str:
        """Draw a first name from the AT catalog, otherwise the DE catalog."""
        names = self.first_names_at if country == "AT" else self.first_names_de
        return self.rng.choice(names)

    def generate_last_name(self, country: str) -> str:
        """Draw a surname from the AT catalog, otherwise the DE catalog."""
        names = self.last_names_at if country == "AT" else self.last_names_de
        return self.rng.choice(names)

    def generate_street(self, country: str) -> str:
        """Draw a street from the AT catalog, otherwise the DE catalog."""
        streets = self.streets_at if country == "AT" else self.streets_de
        return self.rng.choice(streets)

    def generate_house_number(self) -> str:
        """Draw a synthetic house number with an optional letter suffix."""
        num = self.rng.randint(1, 150)
        suffix = self.rng.choice(["", "", "", "a", "b", "c"])
        return f"{num}{suffix}"

    def generate_city(self, country: str) -> tuple[str, str]:
        """Return a matching city and postal code pair from the country catalog."""
        cities = self.cities_at if country == "AT" else self.cities_de
        return self.rng.choice(cities)

    def generate_postal_code(self, country: str) -> str:
        """Draw a postal code independently from previous city draws."""
        _, postal = self.generate_city(country)
        return postal

    def generate_iban(self, country: str) -> str:
        """Return a synthetic IBAN-shaped string without validating its checksum."""
        country_code = "AT" if country == "AT" else "DE"
        check = self.rng.randint(10, 99)
        if country == "AT":
            bank = "".join([str(self.rng.randint(0, 9)) for _ in range(5)])
            account = "".join([str(self.rng.randint(0, 9)) for _ in range(11)])
            return f"{country_code}{check}{bank}{account}"
        else:
            bank = "".join([str(self.rng.randint(0, 9)) for _ in range(8)])
            account = "".join([str(self.rng.randint(0, 9)) for _ in range(10)])
            return f"{country_code}{check}{bank}{account}"

    def generate_bic(self, country: str) -> str:
        """Return a synthetic BIC-shaped string, not a registered bank identity."""
        bank_code = "".join(self.rng.choices(string.ascii_uppercase, k=4))
        country_code = "AT" if country == "AT" else "DE"
        location = "".join(self.rng.choices(string.ascii_uppercase + string.digits, k=2))
        branch = "".join(self.rng.choices(string.ascii_uppercase + string.digits, k=3))
        return f"{bank_code}{country_code}{location}{branch}"

    def generate_ustid(self, country: str) -> str:
        """Return a synthetic VAT identifier without checksum or registry validation."""
        if country == "AT":
            return f"ATU{self.rng.randint(10000000, 99999999)}"
        else:
            return f"DE{self.rng.randint(100000000, 999999999)}"

    def generate_phone(self, country: str) -> str:
        """Return a synthetic domestic phone number from the country profile."""
        if country == "AT":
            prefix = self.rng.choice(["0664", "0676", "0699", "0650", "0660"])
            number = "".join([str(self.rng.randint(0, 9)) for _ in range(7)])
            return f"{prefix} {number}"
        else:
            prefix = self.rng.choice(
                [
                    "0151",
                    "0152",
                    "0157",
                    "0160",
                    "0170",
                    "0171",
                    "0175",
                    "0176",
                    "0177",
                    "0178",
                    "0179",
                ]
            )
            number = "".join([str(self.rng.randint(0, 9)) for _ in range(7)])
            return f"{prefix} {number}"

    def generate_date_range(self, start: str, end: str) -> str:
        """Draw an inclusive ISO date; invalid or reversed ranges raise ValueError."""
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        delta = (end_date - start_date).days
        random_days = self.rng.randint(0, delta)
        result_date = start_date + timedelta(days=random_days)
        return result_date.strftime("%Y-%m-%d")

    def generate_date_after(self, ref_date: str, min_days: int, max_days: int) -> str:
        """Draw an ISO date offset from ref_date within the inclusive day range."""
        base_date = datetime.strptime(ref_date, "%Y-%m-%d")
        offset = self.rng.randint(min_days, max_days)
        result_date = base_date + timedelta(days=offset)
        return result_date.strftime("%Y-%m-%d")

    def generate_amount(self, min_val: float, max_val: float, decimals: int = 2) -> float:
        """Draw a float amount and apply the legacy Python round operation."""
        amount = self.rng.uniform(min_val, max_val)
        return round(amount, decimals)

    def generate_amount_relative(
        self, ref_amount: float, min_factor: float, max_factor: float
    ) -> float:
        """Multiply a reference amount by a drawn factor and round to two decimals."""
        factor = self.rng.uniform(min_factor, max_factor)
        return round(ref_amount * factor, 2)

    def generate_invoice_no(self, pattern: str = "numeric_8_10") -> str:
        """Draw a numeric invoice identifier or an INV-prefixed fallback."""
        if pattern == "numeric_8_10":
            length = self.rng.randint(8, 10)
            return "".join([str(self.rng.randint(0, 9)) for _ in range(length)])
        else:
            return f"INV-{self.rng.randint(100000, 999999)}"

    def generate_company(self) -> str:
        """Draw a company name from the built-in synthetic catalog."""
        return self.rng.choice(self.companies)

    def generate_purpose_text(self, min_words: int = 2, max_words: int = 8) -> str:
        """Draw and join purpose phrases; counts apply to phrases, not lexical words."""
        num_words = self.rng.randint(min_words, max_words)
        words = self.rng.choices(self.purposes, k=num_words)
        return " ".join(words)

    def generate_weighted_choice(self, items: list[dict[str, Any]]) -> str:
        """Draw a weighted value; empty input returns an empty string."""
        if not items:
            return ""
        values = [item.get("value", "") for item in items]
        weights = [item.get("weight", 1) for item in items]
        return cast(str, self.rng.choices(values, weights=weights, k=1)[0])

    def generate_number(self, min_val: int = 0, max_val: int = 100) -> int:
        """Draw an integer in the inclusive range; reversed bounds raise ValueError."""
        return self.rng.randint(min_val, max_val)

    def generate_boolean(self) -> bool:
        """Draw a boolean with equal probability."""
        return self.rng.choice([True, False])

    def generate_field(
        self, field_type: str, params: dict[str, Any], country: str, row_data: dict[str, Any]
    ) -> Any:
        """Dispatch legacy field rules with earlier row values available as references."""
        if field_type == "first_name":
            return self.generate_first_name(country)
        elif field_type == "last_name":
            return self.generate_last_name(country)
        elif field_type == "street":
            return self.generate_street(country)
        elif field_type == "house_number":
            return self.generate_house_number()
        elif field_type == "postal_code":
            return self.generate_postal_code(country)
        elif field_type == "city":
            city, _ = self.generate_city(country)
            return city
        elif field_type == "iban":
            return self.generate_iban(country)
        elif field_type == "bic":
            return self.generate_bic(country)
        elif field_type == "ustid":
            return self.generate_ustid(country)
        elif field_type == "phone":
            return self.generate_phone(country)
        elif field_type == "date_range":
            start = params.get("start", "2020-01-01")
            end = params.get("end", "2025-12-31")
            return self.generate_date_range(start, end)
        elif field_type == "date_after":
            ref_field = params.get("refFieldName", "")
            ref_date = row_data.get(
                ref_field, (self.base_date or datetime.now().date()).isoformat()
            )
            min_days = params.get("minDays", 0)
            max_days = params.get("maxDays", 30)
            return self.generate_date_after(ref_date, min_days, max_days)
        elif field_type == "amount_eur":
            min_val = params.get("min", 100)
            max_val = params.get("max", 10000)
            decimals = params.get("decimals", 2)
            return self.generate_amount(min_val, max_val, decimals)
        elif field_type == "amount_eur_relative":
            ref_field = params.get("refFieldName", "")
            ref_amount = row_data.get(ref_field, 1000)
            if isinstance(ref_amount, str):
                try:
                    ref_amount = float(ref_amount.replace(",", "."))
                except (TypeError, ValueError):
                    ref_amount = 1000
            min_factor = params.get("minFactor", 0.5)
            max_factor = params.get("maxFactor", 1.0)
            return self.generate_amount_relative(ref_amount, min_factor, max_factor)
        elif field_type == "invoice_no":
            pattern = params.get("pattern", "numeric_8_10")
            return self.generate_invoice_no(pattern)
        elif field_type == "company":
            return self.generate_company()
        elif field_type == "purpose_text":
            min_words = params.get("minWords", 2)
            max_words = params.get("maxWords", 8)
            return self.generate_purpose_text(min_words, max_words)
        elif field_type == "weighted_list":
            items = params.get("items", [])
            return self.generate_weighted_choice(items)
        elif field_type == "number":
            min_val = params.get("min", 0)
            max_val = params.get("max", 100)
            return self.generate_number(min_val, max_val)
        elif field_type == "boolean":
            return self.generate_boolean()
        elif field_type == "auto_increment":
            return params.get("_current", 1)
        else:
            return ""

    def apply_deviation(self, row: dict[str, Any], scenario: str, rate: float) -> dict[str, Any]:
        """Apply the selected legacy test-error profile to row in place and return it."""
        if self.rng.random() > rate:
            return row

        if scenario == "NONE":
            return row
        elif scenario == "FOERDERFAEHIG_GT_GEZAHLT":
            for key in row:
                if "förderfähig" in key.lower() or "foerderfaehig" in key.lower():
                    ref_key = None
                    for k in row:
                        if "gezahlt" in k.lower() or "betrag" in k.lower():
                            ref_key = k
                            break
                    if ref_key and isinstance(row[ref_key], (int, float)):
                        row[key] = row[ref_key] * self.rng.uniform(1.1, 1.5)
        elif scenario == "BEZAHLT_VOR_RECHNUNG":
            for key in row:
                if "bezahldatum" in key.lower() or "wertstellung" in key.lower():
                    for ref_key in row:
                        if "rechnungsdatum" in ref_key.lower():
                            try:
                                ref_date = datetime.strptime(row[ref_key], "%Y-%m-%d")
                                row[key] = (
                                    ref_date - timedelta(days=self.rng.randint(1, 30))
                                ).strftime("%Y-%m-%d")
                            except (TypeError, ValueError):
                                pass
        elif scenario == "NEGATIVE_AMOUNTS":
            for key in row:
                if (
                    "betrag" in key.lower() or "amount" in key.lower() or "eur" in key.lower()
                ) and isinstance(row[key], (int, float)):
                    row[key] = -abs(row[key])

        return row

    def generate_rows(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        """Generiert Zeilen - nutzt automatisch Parallel Processing bei großen Datensätzen."""
        rows_count = request.get("rows", 100)

        # Bei großen Datensätzen parallele Verarbeitung nutzen
        if rows_count >= self.PARALLEL_THRESHOLD:
            return self.generate_rows_parallel(request)

        return self._generate_rows_sequential(request)

    def _generate_rows_sequential(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        """Sequentielle Generierung für kleine Datensätze."""
        rows_count = request.get("rows", 100)
        countries = request.get("countries", "DE+AT")
        fields = request.get("fields", [])
        deviation = request.get("deviation", {"rate": 0, "scenario": "NONE"})
        belegliste_options = request.get("beleglisteOptions")

        country_list = ["DE", "AT"] if countries == "DE+AT" else [countries]

        auto_increment_counters = {}
        for field in fields:
            if field.get("type") == "auto_increment":
                start = field.get("params", {}).get("start", 1)
                auto_increment_counters[field["name"]] = start

        results = []

        for i in range(rows_count):
            country = self.rng.choice(country_list)
            row = {}

            for field in fields:
                field_name = field.get("name", f"field_{i}")
                field_type = field.get("type", "number")
                params = field.get("params", {}).copy()

                if field_type == "auto_increment":
                    current = auto_increment_counters.get(field_name, 1)
                    params["_current"] = current
                    step = params.get("step", 1)
                    auto_increment_counters[field_name] = current + step

                if belegliste_options and field_type in ["number", "weighted_list"]:
                    criteria = belegliste_options.get("criteria", {})
                    if "vorhabennummer" in field_name.lower() and criteria.get("vorhabennummern"):
                        dist = criteria["vorhabennummern"]
                        row[field_name] = self.generate_weighted_choice(dist.get("items", []))
                        continue
                    elif "aktenzeichen" in field_name.lower() and criteria.get("aktenzeichen"):
                        dist = criteria["aktenzeichen"]
                        row[field_name] = self.generate_weighted_choice(dist.get("items", []))
                        continue
                    elif "kostenstelle" in field_name.lower() and criteria.get("kostenstellen"):
                        dist = criteria["kostenstellen"]
                        row[field_name] = self.generate_weighted_choice(dist.get("items", []))
                        continue
                    elif "kategorie" in field_name.lower() and criteria.get("kategorien"):
                        dist = criteria["kategorien"]
                        row[field_name] = self.generate_weighted_choice(dist.get("items", []))
                        continue

                value = self.generate_field(field_type, params, country, row)
                row[field_name] = value

            if deviation.get("rate", 0) > 0:
                row = self.apply_deviation(
                    row, deviation.get("scenario", "NONE"), deviation.get("rate", 0)
                )

            results.append(row)

        return results

    def generate_rows_parallel(
        self, request: dict[str, Any], n_workers: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Parallele Generierung für große Datensätze.

        Args:
            request: Generierungsanfrage
            n_workers: Anzahl der Worker-Prozesse (default: CPU-Kerne)

        Returns:
            Liste der generierten Zeilen
        """
        rows_count = request.get("rows", 100)
        if n_workers is not None and n_workers < 1:
            raise ValueError("n_workers must be a positive integer")
        n_workers = n_workers or self.max_workers or get_optimal_workers()

        # Mindestens 100 Zeilen pro Worker
        min_batch_size = 100
        actual_workers = min(n_workers, max(1, rows_count // min_batch_size))

        if actual_workers <= 1:
            return self._generate_rows_sequential(request)

        # Batches aufteilen
        batch_size = rows_count // actual_workers
        remainder = rows_count % actual_workers

        batch_configs = []
        current_idx = 0
        base_seed = self.seed if self.seed is not None else random.randint(0, 2**31)

        for i in range(actual_workers):
            # Letzter Batch bekommt den Rest
            size = batch_size + (1 if i < remainder else 0)

            # Deep copy des Requests für jeden Batch
            batch_request = deepcopy(request)

            batch_configs.append(
                {
                    "base_date": self.base_date,
                    "seed": base_seed + i * 1000,  # Unterschiedliche Seeds pro Batch
                    "request": batch_request,
                    "start_idx": current_idx,
                    "batch_size": size,
                    "auto_increment_start": current_idx,
                    "batch_index": i,
                }
            )
            current_idx += size

        results = []

        # joblib verwenden wenn verfügbar (performanter)
        if self.use_joblib:
            try:
                batch_results = Parallel(n_jobs=actual_workers, backend="loky")(
                    delayed(_generate_batch)(config) for config in batch_configs
                )
            except Exception as exc:
                raise BatchGenerationError("Parallel generation failed") from exc
            for batch_result in batch_results:
                results.extend(batch_result)
        else:
            # Fallback auf ProcessPoolExecutor
            with ProcessPoolExecutor(
                max_workers=actual_workers, mp_context=get_context("spawn")
            ) as executor:
                futures = {
                    executor.submit(_generate_batch, config): config["batch_index"]
                    for config in batch_configs
                }

                # Ergebnisse in der richtigen Reihenfolge sammeln
                indexed_results = {}
                for future in as_completed(futures):
                    batch_idx = futures[future]
                    try:
                        indexed_results[batch_idx] = future.result()
                    except Exception as exc:
                        for pending in futures:
                            pending.cancel()
                        raise BatchGenerationError(f"Batch {batch_idx} failed") from exc

                # In korrekter Reihenfolge zusammenführen
                for i in range(actual_workers):
                    if i in indexed_results:
                        results.extend(indexed_results[i])

        if len(results) != rows_count:
            raise BatchGenerationError("Worker result count differs from requested rows")
        return results

    def generate_rows_parallel_joblib(
        self, request: dict[str, Any], n_jobs: int = -1
    ) -> list[dict[str, Any]]:
        """
        Parallele Generierung mit joblib (wenn verfügbar).

        Args:
            request: Generierungsanfrage
            n_jobs: Anzahl der Jobs (-1 = alle CPUs)

        Returns:
            Liste der generierten Zeilen
        """
        if not JOBLIB_AVAILABLE:
            return self.generate_rows_parallel(request, n_workers=n_jobs if n_jobs > 0 else None)

        return self.generate_rows_parallel(request, n_workers=n_jobs if n_jobs > 0 else None)
