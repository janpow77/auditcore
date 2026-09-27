"""Eigenschaftstests der Invarianten aus ``docs/spezifikation.md`` (Hypothesis).

Synthetische Zahlenfolgen; jede Testfunktion nennt ihre Invariante.
"""

from __future__ import annotations

import math
import random
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_statistics import (
    StatisticsInputError,
    benford_test,
    chi2_survival,
    expected_share,
)
from auditcore_statistics.conformity import NIGRINI_2012, assess
from auditcore_statistics.significance import chi_square_test, digit_z_test

EINSTELLUNG = settings(max_examples=150, deadline=None)
BETRAG = st.one_of(
    st.integers(min_value=-(10**9), max_value=10**9),
    st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False),
    st.decimals(
        min_value=-(10**9), max_value=10**9, allow_nan=False, allow_infinity=False, places=4
    ),
)
EINTRAG = st.one_of(BETRAG, st.none(), st.just(float("nan")))
POSITIV = st.integers(min_value=1, max_value=10**12)
MODUS = st.sampled_from([(1, None), (2, "exclude"), (2, "pad")])


def _auswertbar(values: list[object], digits: int, short: str | None) -> bool:
    try:
        benford_test(values, digits=digits, short_values=short)  # type: ignore[arg-type]
    except StatisticsInputError:
        return False
    return True


def test_i1_erwartete_anteile_summieren_zu_eins() -> None:
    """I1: Benford-Erwartungswerte log10(1 + 1/d) summieren über 1..9 und 10..99 zu 1."""
    assert math.fsum(expected_share(d) for d in range(1, 10)) == pytest.approx(1.0, abs=1e-12)
    assert math.fsum(expected_share(d) for d in range(10, 100)) == pytest.approx(1.0, abs=1e-12)
    assert all(expected_share(d) > expected_share(d + 1) for d in range(1, 99))


@EINSTELLUNG
@given(st.lists(EINTRAG, min_size=1, max_size=200), MODUS)
def test_i2_jeder_wert_ist_gezaehlt_oder_als_ausschluss_ausgewiesen(values, modus) -> None:
    """I2: analysiert + fehlend + null + kurz ausgeschlossen = Eingabelänge;
    beobachtete Anzahlen summieren zur Zahl der analysierten Werte."""
    digits, short = modus
    if not _auswertbar(values, digits, short):
        return
    r = benford_test(values, digits=digits, short_values=short)  # type: ignore[arg-type]
    assert r.analysed + r.missing + r.zero + r.short_excluded == len(values)
    assert sum(row.observed_count for row in r.rows) == r.analysed
    assert math.fsum(row.observed_share for row in r.rows) == pytest.approx(1.0, abs=1e-12)
    assert r.negative_absolute == sum(1 for v in values if v is not None and v == v and v < 0)


@EINSTELLUNG
@given(st.lists(BETRAG, min_size=1, max_size=120), MODUS, st.randoms(use_true_random=False))
def test_i3_reihenfolge_der_werte_ist_ohne_einfluss(values, modus, rnd: random.Random) -> None:
    """I3: Permutationsinvarianz – gleiche Zeilen, Ausschlüsse, Statistik und p-Wert."""
    digits, short = modus
    if not _auswertbar(values, digits, short):
        return
    gemischt = list(values)
    rnd.shuffle(gemischt)
    a = benford_test(values, digits=digits, short_values=short)  # type: ignore[arg-type]
    b = benford_test(gemischt, digits=digits, short_values=short)  # type: ignore[arg-type]
    assert a == b


@EINSTELLUNG
@given(st.lists(POSITIV, min_size=1, max_size=120), MODUS, st.integers(-6, 6))
def test_i4_vorzeichen_skala_und_datentyp_sind_ohne_einfluss(values, modus, exponent: int) -> None:
    """I4: −x, x · 10^k und int/float/Decimal desselben Werts liefern dieselben Ziffern."""
    digits, short = modus
    if not _auswertbar(values, digits, short):
        return
    basis = benford_test(values, digits=digits, short_values=short)  # type: ignore[arg-type]
    skaliert = [Decimal(v).scaleb(exponent) for v in values]
    negativ = [-v for v in values]
    als_float = [float(v) for v in values if v < 2**53]
    for andere in (skaliert, negativ):
        r = benford_test(andere, digits=digits, short_values=short)  # type: ignore[arg-type]
        assert r.rows == basis.rows
    assert benford_test(negativ, digits=digits, short_values=short).negative_absolute == len(values)  # type: ignore[arg-type]
    if len(als_float) == len(values):
        r = benford_test(als_float, digits=digits, short_values=short)  # type: ignore[arg-type]
        assert r.rows == basis.rows


@EINSTELLUNG
@given(st.lists(POSITIV, min_size=1, max_size=200), MODUS)
def test_i5_statistik_nichtnegativ_p_wert_im_einheitsintervall(values, modus) -> None:
    """I5: χ² ≥ 0, p ∈ [0, 1], Freiheitsgrade 8 bzw. 89."""
    digits, short = modus
    if not _auswertbar(values, digits, short):
        return
    r = benford_test(values, digits=digits, short_values=short)  # type: ignore[arg-type]
    assert r.chi2_statistic >= 0
    assert 0.0 <= r.p_value <= 1.0
    assert r.degrees_of_freedom == (8 if digits == 1 else 89)


@EINSTELLUNG
@given(
    st.floats(min_value=0, max_value=500, allow_nan=False),
    st.floats(min_value=0, max_value=500, allow_nan=False),
    st.integers(min_value=1, max_value=120),
)
def test_i5_p_wert_faellt_mit_der_statistik(x: float, y: float, dof: int) -> None:
    """I5: ``chi2_survival`` ist monoton fallend in der Statistik und liegt in [0, 1]."""
    lo, hi = sorted((x, y))
    p_lo, p_hi = chi2_survival(lo, dof), chi2_survival(hi, dof)
    assert 0.0 <= p_hi <= p_lo + 1e-12 <= 1.0 + 1e-12


@EINSTELLUNG
@given(
    st.lists(POSITIV, min_size=1, max_size=100),
    st.one_of(st.none(), st.floats(min_value=1e-6, max_value=1 - 1e-6)),
)
def test_i6_aussage_nur_mit_ausdruecklichem_niveau(values, level) -> None:
    """I6: ohne Signifikanzniveau keine Aussage (``None``); mit Niveau genau p < α."""
    r = benford_test(values, digits=1, significance_level=level)
    if level is None:
        assert r.deviates_at_level is None
    else:
        assert r.deviates_at_level is (r.p_value < level)


@EINSTELLUNG
@given(
    st.lists(POSITIV, min_size=1, max_size=200), st.sampled_from(["first", "first_two", "second"])
)
def test_i7_konformitaet_mad_band_und_z_test_konsistent(values, test) -> None:
    """I7: MAD ≥ 0 und liegt im gemeldeten Band; auffällige Ziffern sind genau z > z_krit;
    der Zweitziffertest hat 10 Zeilen mit Erwartungsanteilen, die zu 1 summieren."""
    digits = 1 if test == "first" else 2
    short = None if digits == 1 else "pad"
    c = assess(benford_test(values, digits=digits, short_values=short), test, "nigrini.2012")  # type: ignore[arg-type]
    grenzen = NIGRINI_2012.mad_bounds[test]
    assert c.mad >= 0
    unten = 0.0 if c.mad_level == 0 else grenzen[c.mad_level - 1]
    assert unten <= c.mad
    if c.mad_level < len(grenzen):
        assert c.mad < grenzen[c.mad_level]
    assert c.exceeding_digits == tuple(r.digit for r in c.rows if r.z > c.z_critical)
    assert sum(r.observed_count for r in c.rows) == c.analysed
    if test == "second":
        assert len(c.rows) == 10
        assert math.fsum(r.expected_share for r in c.rows) == pytest.approx(1.0, abs=1e-12)


@EINSTELLUNG
@given(
    st.integers(min_value=1, max_value=9),
    st.lists(st.integers(10, 10**6).filter(lambda n: len(str(n).rstrip("0")) >= 2), max_size=30),
)
def test_i8_einstellige_werte_im_zweiziffertest_nur_mit_ausdruecklicher_regel(d: int, rest) -> None:
    """I8: Zwei-Ziffern-Test verlangt ``short_values``; ``pad`` zählt d als 10·d,
    ``exclude`` weist den Wert als kurz aus (Werte mit einer signifikanten Ziffer,
    auch 10 oder 300, sind „kurz“)."""
    with pytest.raises(StatisticsInputError):
        benford_test([d, *rest], digits=2)
    pad = benford_test([d, *rest], digits=2, short_values="pad")
    assert pad.short_excluded == 0
    assert pad.rows[10 * d - 10].observed_count >= 1
    if rest:
        ex = benford_test([d, *rest], digits=2, short_values="exclude")
        assert ex.short_excluded == 1 and ex.analysed == len(rest)


@EINSTELLUNG
@given(
    st.lists(POSITIV, max_size=10),
    st.sampled_from([True, False, "12", "4,5", float("inf"), float("-inf"), Decimal("Infinity")]),
)
def test_i9_nicht_numerisches_wird_abgewiesen_nicht_umgedeutet(values, schlecht) -> None:
    """I9: Wahrheitswerte, Texte und unendliche Werte führen zu ``StatisticsInputError``."""
    with pytest.raises(StatisticsInputError):
        benford_test([*values, schlecht], digits=1)  # type: ignore[list-item]


@EINSTELLUNG
@given(
    st.lists(POSITIV, min_size=1, max_size=200),
    st.sampled_from(["first", "first_two", "second"]),
    st.one_of(st.none(), st.floats(min_value=0.001, max_value=0.5)),
)
def test_i10_chi_quadrat_test_kritische_werte_und_entscheidung(values, test, level) -> None:
    """I10: χ²/p gleich der Konformität; P(X ≥ krit) = Niveau; Entscheidung nur mit α."""
    digits = 1 if test == "first" else 2
    r = benford_test(values, digits=digits, short_values=None if digits == 1 else "pad")
    chi = chi_square_test(r, test, significance_level=level)
    c = assess(r, test, "nigrini.2012")
    assert (chi.chi2_statistic, chi.p_value) == (c.chi2_statistic, c.p_value)
    for entry in chi.critical_values:
        survival = chi2_survival(entry.value, chi.degrees_of_freedom)
        assert survival == pytest.approx(entry.level, rel=1e-9)
    values_by_level = [entry.value for entry in chi.critical_values]
    assert values_by_level == sorted(values_by_level)
    if level is None:
        assert chi.rejects is None and chi.critical_value is None
    else:
        assert chi.rejects is (chi.p_value < level)


@EINSTELLUNG
@given(
    st.lists(POSITIV, min_size=1, max_size=200),
    st.sampled_from(["first", "first_two", "second"]),
    st.one_of(st.none(), st.floats(min_value=0.1, max_value=5)),
)
def test_i11_auffaellige_ziffern_nur_gegen_ausdrueckliche_grenze(values, test, limit) -> None:
    """I11: z ≥ 0; mit Korrektur gleich der Konformität; Markierung genau z > z_krit."""
    digits = 1 if test == "first" else 2
    r = benford_test(values, digits=digits, short_values=None if digits == 1 else "pad")
    corrected = digit_z_test(r, test, continuity_correction=True, z_critical=limit)
    assert [row.z for row in corrected.rows] == [
        row.z for row in assess(r, test, "nigrini.2012").rows
    ]
    plain = digit_z_test(r, test, continuity_correction=False, z_critical=limit)
    for z in (corrected, plain):
        assert all(row.z >= 0 for row in z.rows)
        if limit is None:
            assert z.exceeding_digits is None
        else:
            assert z.exceeding_digits == tuple(row.digit for row in z.rows if row.z > limit)
