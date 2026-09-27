"""Invarianten aus docs/spezifikation.md als Eigenschaftstests (Hypothesis).

Alle Werte sind synthetisch; kein Netz, keine Dateien. Der Parallelweg wird
nur über :func:`auditcore_dummygenerator.rows.batch_configs` geprüft, damit
die Tests keine Prozesse starten.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_dummygenerator import TestDataGenerator, list_profiles, profile_reference
from auditcore_dummygenerator.rows import batch_configs

EXAMPLES = settings(max_examples=150, deadline=None)
SEEDS = st.integers(min_value=0, max_value=2**31)
COUNTRIES = st.sampled_from(["DE", "AT", "DE+AT"])
DAYS = st.dates(min_value=date(2000, 1, 1), max_value=date(2040, 12, 31))

FIELD_TYPES = (
    "first_name", "last_name", "street", "house_number", "postal_code", "city", "iban",
    "bic", "ustid", "phone", "date_range", "date_after", "amount_eur",
    "amount_eur_relative", "invoice_no", "company", "purpose_text", "weighted_list",
    "number", "boolean",
)  # fmt: skip


@st.composite
def requests(draw: st.DrawFn) -> dict[str, object]:
    types = draw(st.lists(st.sampled_from(FIELD_TYPES), min_size=1, max_size=8))
    fields: list[dict[str, object]] = [
        {"name": f"feld_{index}", "type": field_type} for index, field_type in enumerate(types)
    ]
    return {"rows": draw(st.integers(0, 30)), "countries": draw(COUNTRIES), "fields": fields}


def _generator(seed: int, base: date) -> TestDataGenerator:
    return TestDataGenerator(seed=seed, base_date=base, max_workers=1)


@EXAMPLES
@given(SEEDS, DAYS, requests())
def test_i1_same_seed_and_reference_date_give_same_rows(
    seed: int, base: date, request: dict[str, object]
) -> None:
    """I1: frische Instanz, gleicher Seed, gleiches Bezugsdatum → gleiche Zeilen."""
    assert _generator(seed, base).generate_rows(request) == _generator(seed, base).generate_rows(
        request
    )


@EXAMPLES
@given(SEEDS, DAYS, requests())
def test_i2_row_count_and_field_order(seed: int, base: date, request: dict[str, object]) -> None:
    """I2: genau ``rows`` Zeilen, jede mit genau den Feldnamen in Anfragereihenfolge."""
    rows = _generator(seed, base).generate_rows(request)
    names = [field["name"] for field in request["fields"]]  # type: ignore[attr-defined]
    assert len(rows) == request["rows"]
    assert all(list(row) == names for row in rows)


@EXAMPLES
@given(SEEDS, st.integers(-(10**6), 10**6), st.integers(0, 10**6), st.integers(0, 4))
def test_i3_amounts_and_numbers_stay_in_range(seed: int, low: int, width: int, digits: int) -> None:
    """I3: Beträge und Zahlen liegen im geschlossenen Intervall der Parameter."""
    generator = TestDataGenerator(seed=seed, max_workers=1)
    amount = generator.generate_amount(low, low + width, digits)
    assert low <= amount <= low + width
    assert round(amount, digits) == amount
    assert low <= generator.generate_number(low, low + width) <= low + width


@EXAMPLES
@given(SEEDS, st.integers(-1000, 1000), st.integers(-50, 50), st.integers(0, 40))
def test_i4_auto_increment_counts_from_start_by_step(
    seed: int, start: int, step: int, count: int
) -> None:
    """I4: Auto-Increment ergibt start, start+step, … in Zeilenreihenfolge."""
    request = {
        "rows": count,
        "countries": "DE",
        "fields": [
            {"name": "nr", "type": "auto_increment", "params": {"start": start, "step": step}}
        ],
    }
    rows = TestDataGenerator(seed=seed, max_workers=1).generate_rows(request)
    assert [row["nr"] for row in rows] == [start + index * step for index in range(count)]


@EXAMPLES
@given(SEEDS, st.sampled_from(["DE", "AT", "FR", ""]))
def test_i5_identifiers_have_the_documented_shape(seed: int, country: str) -> None:
    """I5: IBAN-, BIC- und USt-IdNr.-Form je Land (AT, sonst DE); keine Prüfziffernzusage."""
    generator = TestDataGenerator(seed=seed, max_workers=1)
    code = "AT" if country == "AT" else "DE"
    iban = generator.generate_iban(country)
    assert re.fullmatch(rf"{code}\d{{2}}\d{{{16 if code == 'AT' else 18}}}", iban)
    bic = generator.generate_bic(country)
    assert re.fullmatch(rf"[A-Z]{{4}}{code}[A-Z0-9]{{5}}", bic)
    pattern = r"ATU\d{8}" if code == "AT" else r"DE\d{9}"
    assert re.fullmatch(pattern, generator.generate_ustid(country))


@EXAMPLES
@given(SEEDS, DAYS, st.integers(0, 3000), st.integers(-500, 500), st.integers(0, 500))
def test_i6_dates_stay_in_their_ranges(
    seed: int, start: date, span: int, min_days: int, extra: int
) -> None:
    """I6: date_range liegt im geschlossenen Bereich, date_after im Versatzbereich."""
    generator = TestDataGenerator(seed=seed, max_workers=1)
    end = start + timedelta(days=span)
    drawn = date.fromisoformat(generator.generate_date_range(start.isoformat(), end.isoformat()))
    assert start <= drawn <= end
    after = date.fromisoformat(
        generator.generate_date_after(start.isoformat(), min_days, min_days + extra)
    )
    assert timedelta(days=min_days) <= after - start <= timedelta(days=min_days + extra)


@EXAMPLES
@given(SEEDS, st.sampled_from(["DE", "AT", "CH"]))
def test_i7_city_and_postal_code_come_from_the_country_catalog(seed: int, country: str) -> None:
    """I7: generate_city liefert ein zusammengehöriges Paar des Länderkatalogs (AT, sonst DE)."""
    generator = TestDataGenerator(seed=seed, max_workers=1)
    catalog = generator.cities_at if country == "AT" else generator.cities_de
    assert generator.generate_city(country) in catalog


@EXAMPLES
@given(SEEDS, st.floats(-1e6, 1e6, allow_nan=False), st.sampled_from(["betrag", "amount_eur"]))
def test_i8_deviation_only_as_requested(seed: int, value: float, key: str) -> None:
    """I8: Rate 0 oder Szenario NONE lässt die Zeile gleich; NEGATIVE_AMOUNTS macht Beträge ≤ 0."""
    generator = TestDataGenerator(seed=seed, max_workers=1)
    assert generator.apply_deviation({key: value}, "NEGATIVE_AMOUNTS", 0.0) == {key: value}
    assert generator.apply_deviation({key: value}, "NONE", 1.0) == {key: value}
    changed = generator.apply_deviation({key: value, "text": "x"}, "NEGATIVE_AMOUNTS", 1.0)
    assert changed == {key: -abs(value), "text": "x"}


@EXAMPLES
@given(st.integers(0, 2**31), st.integers(0, 50_000), st.integers(1, 64))
def test_i9_parallel_batches_cover_all_rows_once(seed: int, rows: int, workers: int) -> None:
    """I9: Batches decken 0…rows−1 lückenlos ab; Seeds seed + i·1000; Größen differieren ≤ 1."""
    generator = TestDataGenerator(seed=seed, max_workers=1)
    configs = batch_configs(generator, {"rows": rows}, rows, workers)
    sizes = [config["batch_size"] for config in configs]
    assert sum(sizes) == rows and max(sizes) - min(sizes) <= 1
    starts = [config["start_idx"] for config in configs]
    assert starts == [sum(sizes[:index]) for index in range(workers)]
    assert [config["seed"] for config in configs] == [seed + i * 1000 for i in range(workers)]


def test_i10_profile_references_match_the_registry() -> None:
    """I10: jede Profilreferenz nennt ID, Version und die geprüften Fingerabdrücke des Registers."""
    profiles = list_profiles()
    assert len({profile["artifact_id"] for profile in profiles}) == len(profiles)

    @given(st.sampled_from([profile["artifact_id"] for profile in profiles]))
    def check(artifact_id: str) -> None:
        reference = profile_reference(artifact_id)
        profile = next(p for p in profiles if p["artifact_id"] == artifact_id)
        assert reference["version"] == profile["version"]
        assert reference["content_hash"] == profile["content_hash"]

    check()
