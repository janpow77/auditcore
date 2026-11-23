"""Student t distribution without SciPy: CDF via the regularized incomplete beta function.

Used only for the comparison value of small samples (``limits``); the official
precision keeps the z coefficient of Annex II of Delegated Regulation (EU)
2023/67. Algorithm: continued fraction of the incomplete beta function
(Lentz's method, as in Press et al., *Numerical Recipes*, 3rd ed., § 6.4),
quantile by bisection.
"""

from __future__ import annotations

import math

_EPSILON = 1e-15
_TINY = 1e-300


def _beta_fraction(a: float, b: float, x: float) -> float:
    """Continued fraction of I_x(a, b) (modified Lentz)."""
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1.0)
    d = 1.0 / (d if abs(d) > _TINY else _TINY)
    value = d
    for m in range(1, 500):
        for numerator in (
            m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
            -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1)),
        ):
            d = 1.0 + numerator * d
            d = 1.0 / (d if abs(d) > _TINY else _TINY)
            c = 1.0 + numerator / c
            c = c if abs(c) > _TINY else _TINY
            value *= c * d
        if abs(c * d - 1.0) < _EPSILON:
            break
    return value


def regularized_beta(a: float, b: float, x: float) -> float:
    """I_x(a, b) for a, b > 0 and 0 ≤ x ≤ 1."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    log_front = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1) / (a + b + 2):
        return math.exp(log_front) * _beta_fraction(a, b, x) / a
    return 1.0 - math.exp(log_front) * _beta_fraction(b, a, 1.0 - x) / b


def t_cdf(t: float, df: int) -> float:
    """P(T ≤ t) for Student's t with ``df`` degrees of freedom."""
    tail = 0.5 * regularized_beta(df / 2, 0.5, df / (df + t * t))
    return 1.0 - tail if t >= 0 else tail


def t_quantile(probability: float, df: int) -> float:
    """t with P(T ≤ t) = ``probability`` (0.5 < probability < 1), by bisection."""
    if not 0.5 < probability < 1:
        raise ValueError("probability must lie in (0.5, 1).")
    if isinstance(df, bool) or not isinstance(df, int) or df < 1:
        raise ValueError("df must be an integer ≥ 1.")
    if df == 1:
        return math.tan(math.pi * (probability - 0.5))
    low, high = 0.0, 1.0
    while t_cdf(high, df) < probability:
        high *= 2
    for _ in range(200):
        middle = (low + high) / 2
        if t_cdf(middle, df) < probability:
            low = middle
        else:
            high = middle
        if high - low < 1e-12:
            break
    return (low + high) / 2
