"""Seeded synthetic rows extracted from the recorded FlowAudit implementation.

Source commit: 05bc5ac560dfff3bc7181323240745215492d09a.
MIT reuse/publication authorized by the rights holder on 2026-09-22; see NOTICE.
"""

from __future__ import annotations

import random
import string
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any, cast

from auditcore_dummygenerator import rows
from auditcore_dummygenerator.rows import (
    BatchGenerationError,
    JoblibApi,
    JsonObject,
    get_optimal_workers,
)
from auditcore_dummygenerator.rows import run_batch as _generate_batch

__all__ = ["JOBLIB_AVAILABLE", "BatchGenerationError", "TestDataGenerator", "get_optimal_workers"]

# Optional: joblib für optimierte parallele Verarbeitung
try:
    from joblib import Parallel, delayed

    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False


_DE_MOBILE_PREFIXES = (
    "0151", "0152", "0157", "0160", "0170", "0171", "0175", "0176", "0177", "0178", "0179",
)  # fmt: skip


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
            "Max", "Anna", "Peter", "Maria", "Thomas",
            "Julia", "Michael", "Sarah", "Andreas", "Lisa",
        ]  # fmt: skip
        self.first_names_at = [
            "Franz", "Elisabeth", "Josef", "Katharina", "Johann",
            "Theresia", "Leopold", "Rosa", "Karl", "Margarethe",
        ]  # fmt: skip
        self.last_names_de = [
            "Müller", "Schmidt", "Schneider", "Fischer", "Weber",
            "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
        ]  # fmt: skip
        self.last_names_at = [
            "Gruber", "Huber", "Bauer", "Wagner", "Müller",
            "Pichler", "Steiner", "Moser", "Mayer", "Hofer",
        ]  # fmt: skip
        self.streets_de = [
            "Hauptstraße", "Bahnhofstraße", "Schulstraße", "Gartenstraße", "Berliner Straße",
            "Dorfstraße", "Lindenstraße", "Kirchstraße", "Waldstraße", "Bergstraße",
        ]  # fmt: skip
        self.streets_at = [
            "Hauptstraße", "Wiener Straße", "Bahnhofstraße", "Kirchengasse", "Schulgasse",
            "Feldgasse", "Berggasse", "Wiesengasse", "Mariahilfer Straße", "Ringstraße",
        ]  # fmt: skip
        self.cities_de = [
            ("Berlin", "10115"), ("Hamburg", "20095"), ("München", "80331"),
            ("Köln", "50667"), ("Frankfurt", "60311"),
        ]  # fmt: skip
        self.cities_at = [
            ("Wien", "1010"), ("Graz", "8010"), ("Linz", "4020"),
            ("Salzburg", "5020"), ("Innsbruck", "6020"),
        ]  # fmt: skip
        self.companies = [
            "TechCorp GmbH", "Digital Solutions AG", "InnoTech KG", "DataServ GmbH",
            "CloudSys AG", "NetWorks GmbH", "SoftDev KG", "IT-Service GmbH",
            "WebTech AG", "AppFactory GmbH",
        ]  # fmt: skip
        self.purposes = [
            "Beratungsleistung", "Softwarelizenz", "Hardwarebeschaffung", "Schulung",
            "Wartung", "Support", "Entwicklung", "Hosting", "Consulting", "Projektmanagement",
        ]  # fmt: skip

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
        bank_length, account_length = (5, 11) if country == "AT" else (8, 10)
        bank = self._digits(bank_length)
        account = self._digits(account_length)
        return f"{country_code}{check}{bank}{account}"

    def _digits(self, count: int) -> str:
        """Draw ``count`` decimal digits, one RNG call each."""
        return "".join([str(self.rng.randint(0, 9)) for _ in range(count)])

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
        return f"DE{self.rng.randint(100000000, 999999999)}"

    def generate_phone(self, country: str) -> str:
        """Return a synthetic domestic phone number from the country profile."""
        if country == "AT":
            prefix = self.rng.choice(["0664", "0676", "0699", "0650", "0660"])
        else:
            prefix = self.rng.choice(_DE_MOBILE_PREFIXES)
        return f"{prefix} {self._digits(7)}"

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
            return self._digits(self.rng.randint(8, 10))
        return f"INV-{self.rng.randint(100000, 999999)}"

    def generate_company(self) -> str:
        """Draw a company name from the built-in synthetic catalog."""
        return self.rng.choice(self.companies)

    def generate_purpose_text(self, min_words: int = 2, max_words: int = 8) -> str:
        """Draw and join purpose phrases; counts apply to phrases, not lexical words."""
        num_words = self.rng.randint(min_words, max_words)
        words = self.rng.choices(self.purposes, k=num_words)
        return " ".join(words)

    def generate_weighted_choice(self, items: list[JsonObject]) -> str:
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
        self, field_type: str, params: JsonObject, country: str, row_data: JsonObject
    ) -> Any:
        """Dispatch legacy field rules with earlier row values available as references."""
        # The literal ``field_type == ...`` comparisons are the dispatch contract that the
        # profile registry derives its field IDs from; producers run only when selected.
        rules: tuple[tuple[bool, Callable[[], object]], ...] = (
            (field_type == "first_name", lambda: self.generate_first_name(country)),
            (field_type == "last_name", lambda: self.generate_last_name(country)),
            (field_type == "street", lambda: self.generate_street(country)),
            (field_type == "house_number", lambda: self.generate_house_number()),
            (field_type == "postal_code", lambda: self.generate_postal_code(country)),
            (field_type == "city", lambda: self.generate_city(country)[0]),
            (field_type == "iban", lambda: self.generate_iban(country)),
            (field_type == "bic", lambda: self.generate_bic(country)),
            (field_type == "ustid", lambda: self.generate_ustid(country)),
            (field_type == "phone", lambda: self.generate_phone(country)),
            (field_type == "date_range", lambda: self._date_range_field(params)),
            (field_type == "date_after", lambda: self._date_after_field(params, row_data)),
            (field_type == "amount_eur", lambda: self._amount_field(params)),
            (
                field_type == "amount_eur_relative",
                lambda: self._relative_amount_field(params, row_data),
            ),
            (
                field_type == "invoice_no",
                lambda: self.generate_invoice_no(params.get("pattern", "numeric_8_10")),
            ),
            (field_type == "company", lambda: self.generate_company()),
            (field_type == "purpose_text", lambda: self._purpose_text_field(params)),
            (
                field_type == "weighted_list",
                lambda: self.generate_weighted_choice(params.get("items", [])),
            ),
            (
                field_type == "number",
                lambda: self.generate_number(params.get("min", 0), params.get("max", 100)),
            ),
            (field_type == "boolean", lambda: self.generate_boolean()),
            (field_type == "auto_increment", lambda: params.get("_current", 1)),
        )
        for selected, produce in rules:
            if selected:
                return produce()
        return ""

    def _date_range_field(self, params: JsonObject) -> str:
        return self.generate_date_range(
            params.get("start", "2020-01-01"), params.get("end", "2025-12-31")
        )

    def _date_after_field(self, params: JsonObject, row_data: JsonObject) -> str:
        ref_field = params.get("refFieldName", "")
        # The fallback reference date is evaluated even when the row supplies one.
        ref_date = row_data.get(ref_field, (self.base_date or datetime.now().date()).isoformat())
        return self.generate_date_after(
            ref_date, params.get("minDays", 0), params.get("maxDays", 30)
        )

    def _amount_field(self, params: JsonObject) -> float:
        return self.generate_amount(
            params.get("min", 100), params.get("max", 10000), params.get("decimals", 2)
        )

    def _relative_amount_field(self, params: JsonObject, row_data: JsonObject) -> float:
        ref_field = params.get("refFieldName", "")
        ref_amount = row_data.get(ref_field, 1000)
        if isinstance(ref_amount, str):
            try:
                ref_amount = float(ref_amount.replace(",", "."))
            except (TypeError, ValueError):
                ref_amount = 1000
        return self.generate_amount_relative(
            ref_amount, params.get("minFactor", 0.5), params.get("maxFactor", 1.0)
        )

    def _purpose_text_field(self, params: JsonObject) -> str:
        return self.generate_purpose_text(params.get("minWords", 2), params.get("maxWords", 8))

    def apply_deviation(self, row: JsonObject, scenario: str, rate: float) -> JsonObject:
        """Apply the selected legacy test-error profile to row in place and return it."""
        if self.rng.random() > rate:
            return row

        if scenario == "NONE":
            return row
        elif scenario == "FOERDERFAEHIG_GT_GEZAHLT":
            self._raise_eligible_above_paid(row)
        elif scenario == "BEZAHLT_VOR_RECHNUNG":
            self._pay_before_invoice(row)
        elif scenario == "NEGATIVE_AMOUNTS":
            self._negate_amounts(row)

        return row

    def _raise_eligible_above_paid(self, row: JsonObject) -> None:
        for key in row:
            if "förderfähig" in key.lower() or "foerderfaehig" in key.lower():
                ref_key = next(
                    (k for k in row if "gezahlt" in k.lower() or "betrag" in k.lower()), None
                )
                if ref_key and isinstance(row[ref_key], (int, float)):
                    row[key] = row[ref_key] * self.rng.uniform(1.1, 1.5)

    def _pay_before_invoice(self, row: JsonObject) -> None:
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

    @staticmethod
    def _negate_amounts(row: JsonObject) -> None:
        for key in row:
            if (
                "betrag" in key.lower() or "amount" in key.lower() or "eur" in key.lower()
            ) and isinstance(row[key], (int, float)):
                row[key] = -abs(row[key])

    def generate_rows(self, request: JsonObject) -> list[JsonObject]:
        """Generiert Zeilen - nutzt automatisch Parallel Processing bei großen Datensätzen."""
        rows_count = request.get("rows", 100)

        # Bei großen Datensätzen parallele Verarbeitung nutzen
        if rows_count >= self.PARALLEL_THRESHOLD:
            return self.generate_rows_parallel(request)

        return self._generate_rows_sequential(request)

    def _generate_rows_sequential(self, request: JsonObject) -> list[JsonObject]:
        """Sequentielle Generierung für kleine Datensätze."""
        return rows.generate_sequential(self, request)

    def generate_rows_parallel(
        self, request: JsonObject, n_workers: int | None = None
    ) -> list[JsonObject]:
        """Parallele Generierung großer Datensätze; ``n_workers`` default: CPU-Kerne."""
        return rows.generate_parallel(
            self,
            request,
            n_workers,
            worker=_generate_batch,
            joblib_backend=_joblib_backend if self.use_joblib else None,
        )

    def generate_rows_parallel_joblib(
        self, request: JsonObject, n_jobs: int = -1
    ) -> list[JsonObject]:
        """Parallele Generierung mit joblib (wenn verfügbar); ``n_jobs=-1``: alle CPUs."""
        # Both branches of the original implementation delegate identically.
        return self.generate_rows_parallel(request, n_workers=n_jobs if n_jobs > 0 else None)


def _joblib_backend() -> JoblibApi:
    """Resolve joblib at call time so an absent backend fails inside the batch guard."""
    return Parallel, delayed
