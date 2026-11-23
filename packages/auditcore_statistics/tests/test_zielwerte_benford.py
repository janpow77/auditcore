"""Zielwerte zu runden Beträgen im Test der ersten zwei Ziffern (Version 0.5.0).

Die Erwartungen sind unabhängig vom Rechenkern nachgerechnet: Die ersten zwei
Ziffern stammen hier aus der Exponentialschreibweise (``f"{x:.14e}"``, also
Ziffer vor und erste Ziffer nach dem Komma des Signifikanden), nicht aus
``Decimal``. Synthetische Daten, kein Echtbestand.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from decimal import Decimal

import pytest

import auditcore_statistics
from auditcore_statistics import benford_test, expected_share
from auditcore_statistics.benford import SHORT_SHARE_WARNING
from auditcore_statistics.conformity import assess
from auditcore_statistics.web import analyse

ROUND_AMOUNTS = [100, 200, 500, 1000, 2000, 5000, 10000]


def _b3_values() -> list[float | int]:
    """2 000 benfordverteilte Beträge (10 bis 100 000) und 400 runde Beträge."""
    rng = random.Random(9)
    spread = [round(10 ** rng.uniform(1, 5), 2) for _ in range(2000)]
    return [*spread, *(rng.choice(ROUND_AMOUNTS) for _ in range(400))]


def _first_two(value: float | int) -> int:
    mantissa = f"{abs(value):.14e}"  # z. B. "5.00000000000000e+02" für 500
    return int(mantissa[0] + mantissa[2])


def test_b3_round_amounts_stay_in_the_test_and_show_the_deviation() -> None:
    """Fall B3: 2 400 Werte, MAD 0,00350, „Keine Übereinstimmung“, χ² 1 018,9 (89 FG).

    Nachrechnung: MAD = Σ |beobachtet − log10(1 + 1/d)| / 90 über d = 10..99;
    χ² = Σ (B_d − n·p_d)² / (n·p_d). Vor 0.5.0 fielen mit ``exclude`` 401 Werte
    heraus (MAD 0,00148, „Akzeptable Übereinstimmung“).
    """
    values = _b3_values()
    counts = Counter(_first_two(v) for v in values)
    n = len(values)
    mad = math.fsum(abs(counts[d] / n - expected_share(d)) for d in range(10, 100)) / 90
    chi2 = math.fsum(
        (counts[d] - n * expected_share(d)) ** 2 / (n * expected_share(d)) for d in range(10, 100)
    )
    assert n == 2400 and round(mad, 5) == 0.00350 and round(chi2, 1) == 1018.9

    for rule in ("pad", "exclude"):
        result = benford_test(values, digits=2, short_values=rule)  # type: ignore[arg-type]
        conformity = assess(result, "first_two", "nigrini.2012")
        assert result.analysed == 2400 and result.short_excluded == 0 and result.warnings == ()
        assert conformity.mad == pytest.approx(mad, abs=1e-15)
        assert conformity.mad_label == "Keine Übereinstimmung"
        assert result.chi2_statistic == pytest.approx(chi2, rel=1e-12)
        assert result.degrees_of_freedom == 89 and result.p_value < 1e-4

    via_rest = analyse({"test": "first_two", "profile": "nigrini.2012", "values": values})
    assert via_rest["distribution"]["analysed"] == 2400
    assert via_rest["conformity"]["mad_label"] == "Keine Übereinstimmung"


def test_b7_only_genuinely_single_digit_values_are_short() -> None:
    """Fall B7: 500, 1 000 und 10,00 zählen zu 50, 10 und 10; nur 0,07 und 5 sind kurz.

    12 Werte: 1 fehlend (None), 1 null, 1 negativ (−12,5 → 12). ``exclude``:
    10 Werte erreichen die Ziffernbildung, 2 davon kurz → 8 ausgewertet,
    Anteil kurz 2 / 10 = 20 % > 5 % → Warnung. ``pad``: 0,07 → 70, 5 → 50.
    """
    values = [500, 1000, 10.00, 123, 45.6, -12.5, 0, None, 0.07, 5, 2500, 99]
    excluded = benford_test(values, digits=2, short_values="exclude")
    groups = {r.digit: r.observed_count for r in excluded.rows if r.observed_count}
    assert groups == {10: 2, 12: 2, 25: 1, 45: 1, 50: 1, 99: 1}
    assert (excluded.analysed, excluded.short_excluded, excluded.missing, excluded.zero) == (
        8,
        2,
        1,
        1,
    )
    assert excluded.short_share == pytest.approx(0.2)
    assert len(excluded.warnings) == 1 and "20,0 %" in excluded.warnings[0]

    padded = benford_test(values, digits=2)
    groups = {r.digit: r.observed_count for r in padded.rows if r.observed_count}
    assert groups == {10: 2, 12: 2, 25: 1, 45: 1, 50: 2, 70: 1, 99: 1}
    assert padded.short_values == "pad" and padded.analysed == 10 and padded.warnings == ()


def test_round_amounts_in_every_notation_give_the_same_group() -> None:
    """500 = 500,00 = 5E+2 = 500.0 → 50; 1 000 = 1E+3 = 10,00 · 100 → 10."""
    forms: list[int | float | Decimal] = [500, 500.0, Decimal("500.00"), Decimal("5E+2"), 5e2]
    result = benford_test(forms, digits=2, short_values="exclude")
    assert result.short_excluded == 0 and result.rows[50 - 10].observed_count == len(forms)
    huge = benford_test([1e300, Decimal("1E+300")], digits=2, short_values="exclude")
    assert huge.rows[0].observed_count == 2


def test_short_share_warning_threshold() -> None:
    """Genau 5 % kurz: keine Warnung; darüber: Warnung (Anwendungsvorgabe, keine Norm)."""
    assert SHORT_SHARE_WARNING == 0.05
    at_limit = benford_test([5] + [12] * 19, digits=2, short_values="exclude")
    assert at_limit.short_share == pytest.approx(0.05) and at_limit.warnings == ()
    above = benford_test([5, 7] + [12] * 18, digits=2, short_values="exclude")
    assert above.warnings and "10,0 %" in above.warnings[0]


def test_lower_bound_excludes_small_absolute_values_and_counts_them() -> None:
    """Untergrenze 10 auf den Betrag: 9,99 und −3 fallen weg, −10 bleibt (10 ≥ 10)."""
    result = benford_test([9.99, -3, -10, 10, 123], digits=2, lower_bound=10)
    assert (result.analysed, result.below_lower_bound, result.lower_bound) == (3, 2, 10.0)
    assert result.to_dict()["excluded"]["below_lower_bound"] == 2
    for bad in (0, -1, math.inf, True):
        with pytest.raises(ValueError, match="lower_bound"):
            benford_test([12], digits=2, lower_bound=bad)


def test_version_strings_agree() -> None:
    result = benford_test([12], digits=1)
    assert result.to_dict()["library"] == f"auditcore_statistics {auditcore_statistics.__version__}"
    assert result.method == "auditcore_statistics.benford/2"


def test_digits_are_read_without_context_rounding() -> None:
    """29 Neunen (10**29 − 1) gehören zur Gruppe 99, nicht nach Rundung auf
    28 Stellen zur Gruppe 10; ebenso ``Decimal('9.999…')`` mit 29 Ziffern."""
    long = Decimal("9." + "9" * 28)
    result = benford_test([10**29 - 1, long, 5, Decimal("5.00")], digits=2, short_values="pad")
    groups = {row.digit: row.observed_count for row in result.rows if row.observed_count}
    assert groups == {50: 2, 99: 2}


def test_every_value_is_counted_with_a_lower_bound() -> None:
    """I2 mit Untergrenze: analysiert + fehlend + null + kurz + unter der Grenze = Eingabe."""
    values = [None, 0, 3, 9.99, 12, 500, 5, -40, 1_000]
    r = benford_test(values, digits=2, short_values="exclude", lower_bound=10)
    total = r.analysed + r.missing + r.zero + r.short_excluded + r.below_lower_bound
    assert total == len(values)
    assert (r.analysed, r.below_lower_bound) == (4, 3)


def test_legacy_names_stay_importable_from_benford() -> None:
    from auditcore_statistics.benford import LegacyDtype, numpy_round

    assert numpy_round(2.5, 0) == 2.0 and LegacyDtype is not None
