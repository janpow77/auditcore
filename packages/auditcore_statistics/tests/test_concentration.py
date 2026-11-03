"""Konzentrationsmaße: Gini, Lorenzkurve, HHI und CR_k."""

import math
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from auditcore_statistics import (
    StatisticsInputError,
    concentration_ratio,
    gini,
    herfindahl_hirschman,
    lorenz_curve,
)


def _trapz_gini(values: list[float]) -> float:
    curve = lorenz_curve(values)
    assert curve is not None
    x, y = curve.population_share, curve.value_share
    area = sum((x[i] - x[i - 1]) * (y[i] + y[i - 1]) / 2 for i in range(1, len(x)))
    return 1 - 2 * area


def test_gleichverteilung_und_maximum() -> None:
    assert gini([5, 5, 5, 5]) == 0
    assert gini([0, 0, 0, 10]) == pytest.approx(0.75)


def test_lorenzkurve() -> None:
    curve = lorenz_curve([1, 3, Decimal(6)])
    assert curve is not None
    assert curve.population_share == pytest.approx((0, 1 / 3, 2 / 3, 1))
    assert curve.value_share == pytest.approx((0, 0.1, 0.4, 1))
    assert curve.count == 3
    assert curve.gini == pytest.approx(_trapz_gini([1, 3, 6]))


@pytest.mark.parametrize("values", [[], [0, 0]])
def test_ohne_konzentration(values: list[float]) -> None:
    assert gini(values) is None
    assert lorenz_curve(values) is None
    assert herfindahl_hirschman(values) is None
    assert concentration_ratio(values, 1) is None


@pytest.mark.parametrize("bad", [[-1, 2], [float("nan")], [True], ["3"]])
def test_ungueltige_werte(bad: list[object]) -> None:
    with pytest.raises(StatisticsInputError):
        gini(bad)  # type: ignore[arg-type]


def test_hhi_und_cr() -> None:
    assert herfindahl_hirschman([1, 1, 2]) == pytest.approx(0.375)
    assert concentration_ratio([1, 1, 2], 1) == pytest.approx(0.5)
    assert concentration_ratio([1, 1, 2], 10) == pytest.approx(1)
    with pytest.raises(StatisticsInputError):
        concentration_ratio([1], 0)


@given(st.lists(st.floats(min_value=0, max_value=1e9), min_size=1, max_size=60))
def test_gini_gleich_trapezregel_und_im_bereich(values: list[float]) -> None:
    coefficient = gini(values)
    if coefficient is None:
        return
    assert -1e-9 <= coefficient <= (len(values) - 1) / len(values) + 1e-9
    assert coefficient == pytest.approx(_trapz_gini(values), abs=1e-9)


def test_lorenz_teilsummen_kompensiert() -> None:
    werte = [0.1] * 10
    kurve = lorenz_curve(werte)
    assert kurve is not None
    gesamt = math.fsum(werte)
    erwartet = [math.fsum(sorted(werte)[:k]) / gesamt for k in range(len(werte) + 1)]
    assert list(kurve.value_share) == erwartet


def test_eine_einheit_hhi_eins_gini_null() -> None:
    assert gini([5]) == 0.0
    assert herfindahl_hirschman([5]) == 1.0
    assert concentration_ratio([5], 3) == 1.0
